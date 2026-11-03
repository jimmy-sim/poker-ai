"""Recompute paired inference from every raw hand and verify chance/seed grouping."""

import argparse
import csv
import gzip
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import numpy as np
from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.cards import Deck
from poker_ai.evaluation.statistics import summarize_pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    report = json.loads(raw)
    if report["status"] != "completed":
        raise ValueError("cannot audit an incomplete study as completed")
    config, mode = report["config"], report["mode"]
    directory = args.report.parent
    for filename, expected in report["artifacts_sha256"].items():
        if (
            Path(filename).name != filename
            or hashlib.sha256((directory / filename).read_bytes()).hexdigest()
            != expected
        ):
            raise ArithmeticError("match artifact fingerprint mismatch")
    deals, seeds = config[mode + "_deals"], config["agent_seeds"]
    expected_decks = [
        hashlib.sha256(
            bytes(
                Deck.shuffled(
                    Generator(PCG64(SeedSequence([config[mode + "_deal_seed"], i])))
                ).cards
            )
        ).hexdigest()
        for i in range(deals)
    ]
    if [r["opponent"] for r in report["results"]] != [
        o["name"] for o in config["opponents"]
    ]:
        raise ArithmeticError("opponent study is incomplete or duplicated")
    audits = []
    for result in report["results"]:
        if Path(result["raw_file"]).name != result["raw_file"]:
            raise ValueError("raw records must stay in the report directory")
        path = directory / result["raw_file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != result["raw_sha256"]:
            raise ArithmeticError("raw record fingerprint mismatch")
        data = list(
            csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode()))
        )
        expected_keys = {
            (deal, seed, seat)
            for deal in range(deals)
            for seed in seeds
            for seat in (0, 1)
        }
        seen = set()
        profits = np.empty((deals, len(seeds), 2), dtype=np.float64)
        lookups: dict[int, Counter[str]] = {seed: Counter() for seed in seeds}
        for row in data:
            deal, seed, seat = (
                int(row["deal"]),
                int(row["agent_seed"]),
                int(row["own_seat"]),
            )
            key = (deal, seed, seat)
            if key not in expected_keys or key in seen:
                raise ArithmeticError(
                    "missing/duplicate/foreign deal-policy-seat observation"
                )
            seen.add(key)
            if row["deck_sha256"] != expected_decks[deal]:
                raise ArithmeticError("deck tape differs from the declared chance seed")
            profit, actions = int(row["profit_chips"]), int(row["actions"])
            if (
                abs(profit) > max(config["rules"]["stacks"])
                or not 1 <= actions <= config["max_actions_per_hand"]
            ):
                raise ArithmeticError("invalid raw profit/action bounds")
            counts = {
                s: int(row["own_" + s])
                for s in ("matched", "unseen", "unaveraged", "shadow_failure")
            }
            if (
                any(v < 0 for v in counts.values())
                or sum(counts.values()) > actions
                or counts["shadow_failure"]
            ):
                raise ArithmeticError("invalid own lookup counts")
            lookups[seed].update(counts)
            profits[deal, seeds.index(seed), seat] = profit
        if seen != expected_keys:
            raise ArithmeticError("incomplete fixed-N study")
        for seed, counts in lookups.items():
            if {s: v for s, v in counts.items() if v} != result[
                "lookup_counts_by_seed"
            ][str(seed)]:
                raise ArithmeticError("lookup totals do not match raw records")
        recomputed = summarize_pairs(
            profits.mean(axis=1),
            big_blind=config["rules"]["big_blind"],
            maximum_loss=max(config["rules"]["stacks"]),
            alpha=config["inference"]["alpha"],
            family_size=config["inference"]["family_size"],
        )
        if recomputed != result["primary_inference"]:
            raise ArithmeticError(
                "reported inference differs from independently grouped raw records"
            )
        audits.append(
            {
                "opponent": result["opponent"],
                "raw_hands": len(data),
                "independent_decks": deals,
                "lookup_totals": {
                    s: sum(c[s] for c in lookups.values())
                    for s in ("matched", "unseen", "unaveraged", "shadow_failure")
                },
                "inference_exact_match": True,
            }
        )
    output = {
        "status": "passed",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "experiment_source": report["source"],
        "opponents": audits,
        "total_raw_hands": sum(a["raw_hands"] for a in audits),
        "independent_deal_draws_shared_across_opponents": deals,
        "distinct_full_decks_observed": len(set(expected_decks)),
        "interpretation": (
            "Each opponent inference has N independent decks; seats, fixed "
            "policies and opponents share those tapes and must not inflate N"
        ),
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        f"passed: {sum(a['raw_hands'] for a in audits)} raw hands; "
        "all grouping/inference checks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
