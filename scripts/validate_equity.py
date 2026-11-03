"""Independent exact outcome counts plus seeded Monte Carlo checks against Treys."""

import argparse
import importlib
import importlib.metadata
import json
import platform
import time
from collections import Counter
from dataclasses import asdict
from itertools import combinations
from pathlib import Path

from numpy.random import PCG64, Generator

from poker_ai.cards import format_card, parse_card
from poker_ai.equity import EquityResult, exact_equity, monte_carlo_equity
from poker_ai.validation.five_card import source_provenance


def serialize(result: EquityResult) -> dict[str, object]:
    return {
        **asdict(result),
        "trials": result.trials,
        "equity": result.equity,
        "outcome_variance": result.outcome_variance,
        "standard_error": result.standard_error,
        "confidence_interval": result.confidence_interval,
    }


def reference_counts(
    hero: tuple[int, ...],
    villain: tuple[int, ...] | None,
    board: tuple[int, ...],
    dead: tuple[int, ...],
) -> tuple[int, int, int]:
    """Independently construct the legal deck and evaluate outcomes with Treys."""
    treys = importlib.import_module("treys")
    oracle = treys.Evaluator()
    encoded = [int(treys.Card.new(format_card(card))) for card in range(52)]
    known = set(hero + (() if villain is None else villain) + board + dead)
    deck = tuple(card for card in range(52) if card not in known)
    opponents = (villain,) if villain is not None else combinations(deck, 2)
    counts: Counter[str] = Counter()
    for opponent in opponents:
        available = tuple(card for card in deck if card not in opponent)
        for runout in combinations(available, 5 - len(board)):
            community = board + runout
            first = int(
                oracle.evaluate([], [encoded[card] for card in hero + community])
            )
            second = int(
                oracle.evaluate([], [encoded[card] for card in opponent + community])
            )
            counts[
                "win" if first < second else "tie" if first == second else "loss"
            ] += 1
    return counts["win"], counts["tie"], counts["loss"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if not isinstance(config, dict) or set(config) != {
        "samples",
        "seed",
        "confidence_level",
        "max_states",
        "cases",
    }:
        raise ValueError("invalid equity validation config keys")
    for name in ("samples", "seed", "max_states"):
        if type(config[name]) is not int or config[name] < (0 if name == "seed" else 1):
            raise ValueError(f"invalid {name}")
    if not isinstance(config["cases"], list) or not config["cases"]:
        raise ValueError("at least one case is required")
    root = Path(__file__).resolve().parents[1]
    source = source_provenance(
        root, args.config, entrypoints=("scripts/validate_equity.py",)
    )
    rows = []
    started = time.perf_counter()
    for index, case in enumerate(config["cases"]):
        if not isinstance(case, dict) or set(case) != {
            "name",
            "hero",
            "villain",
            "board",
            "dead_cards",
        }:
            raise ValueError("invalid case keys")
        hero = tuple(map(parse_card, case["hero"]))
        villain = (
            None if case["villain"] is None else tuple(map(parse_card, case["villain"]))
        )
        board, dead = (
            tuple(map(parse_card, case["board"])),
            tuple(map(parse_card, case["dead_cards"])),
        )
        exact = exact_equity(
            hero, villain, board, dead_cards=dead, max_states=config["max_states"]
        )
        reference = reference_counts(hero, villain, board, dead)
        sampled = monte_carlo_equity(
            hero,
            villain,
            board,
            dead_cards=dead,
            rng=Generator(PCG64(config["seed"] + index)),
            samples=config["samples"],
            confidence_level=config["confidence_level"],
        )
        bounds = sampled.confidence_interval
        coverage = bounds is not None and bounds[0] <= exact.equity <= bounds[1]
        matches = (exact.wins, exact.ties, exact.losses) == reference
        rows.append(
            {
                "name": case["name"],
                "settings": case,
                "seed": config["seed"] + index,
                "reference_counts": reference,
                "exact": serialize(exact),
                "monte_carlo": serialize(sampled),
                "exact_matches_reference": matches,
                "mc_interval_contains_exact": coverage,
                "absolute_mc_error": abs(sampled.equity - exact.equity),
            }
        )
        print(
            case["name"],
            "exact/reference:",
            matches,
            "MC interval:",
            coverage,
            flush=True,
        )
    passed = all(
        row["exact_matches_reference"] and row["mc_interval_contains_exact"]
        for row in rows
    )
    report = {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "config": config,
        "cases": rows,
        "validation_seconds": time.perf_counter() - started,
        "source": source,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": importlib.metadata.version("numpy"),
            "treys": importlib.metadata.version("treys"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], args.output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
