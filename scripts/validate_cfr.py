"""Run deterministic exact CFR comparisons and reproduce tables/plots.

Used for the original Phase 2 acceptance and the separately configured Tier A
gate in the trained-agent solver-validation pipeline.
"""

import argparse
import csv
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.toy.analysis import evaluate
from poker_ai.toy.cfr import CFR, Variant
from poker_ai.toy.games import GameName
from poker_ai.toy.tree import Tree
from poker_ai.validation.cfr import OpenSpielReference
from poker_ai.validation.five_card import source_provenance
from poker_ai.validation.toy_games import validate_game_rules


def load_config(path: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(path.read_text())
    required = {
        "games",
        "variants",
        "seed",
        "best_response_seeds",
        "units",
        "averaging",
        "exploitability_absolute_tolerance",
        "strategy_mean_l1_tolerance",
        "best_response_absolute_tolerance",
        "kuhn_final_value_error_limit",
        "kuhn_final_exploitability_limit",
        "leduc_final_exploitability_limit",
    }
    if set(config) != required or set(config["games"]) != {"kuhn", "leduc"}:
        raise ValueError("invalid CFR config fields")
    if config["seed"] is not None:
        raise ValueError("full-tree CFR is deterministic; seed must be null")
    if config["variants"] != ["cfr", "cfr_plus", "linear", "discounted"]:
        raise ValueError("declare all four variants in their fixed order")
    for checkpoints in config["games"].values():
        if (
            not checkpoints
            or any(type(t) is not int or t <= 0 for t in checkpoints)
            or checkpoints != sorted(set(checkpoints))
        ):
            raise ValueError("checkpoints must be increasing positive integers")
    seeds = config["best_response_seeds"]
    if (
        not seeds
        or any(type(s) is not int or s < 0 for s in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError("invalid independent BR seeds")
    for key in required:
        if key.endswith(("tolerance", "limit")):
            if (
                type(config[key]) not in (int, float)
                or not np.isfinite(config[key])
                or config[key] <= 0
            ):
                raise ValueError("all tolerances must be finite and positive")
    return config


def plot(rows: list[dict[str, Any]], output: Path) -> list[Path]:
    os.environ.setdefault("MPLCONFIGDIR", str(output.parent / "runs" / "mpl-cache"))
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "poker-ai-phase2"
    pyplot = importlib.import_module("matplotlib.pyplot")
    fig, axes = pyplot.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for axis, game in zip(axes, ("kuhn", "leduc"), strict=True):
        for variant in ("cfr", "cfr_plus", "linear", "discounted"):
            series = [
                row for row in rows if row["game"] == game and row["variant"] == variant
            ]
            axis.loglog(
                [r["iteration"] for r in series],
                [max(r["exploitability"], 1e-16) for r in series],
                marker="o",
                label=variant,
            )
        axis.set(
            title=game.title(),
            xlabel="Iterations (both players)",
            ylabel="Exploitability (ante chips/hand)",
        )
        axis.grid(True, which="both", alpha=0.2)
        axis.legend(fontsize=8)
    files = [
        output.with_name("cfr-convergence.png"),
        output.with_name("cfr-convergence.svg"),
    ]
    fig.savefig(files[0], dpi=160)
    fig.savefig(files[1], metadata={"Date": None})
    pyplot.close(fig)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    root = Path(__file__).resolve().parents[1]
    provenance = source_provenance(
        root, args.config, entrypoints=("scripts/validate_cfr.py",)
    )
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    rules: dict[str, dict[str, int]] = {}
    random_br_checks: list[dict[str, Any]] = []
    failures: list[str] = []
    games: tuple[GameName, ...] = ("kuhn", "leduc")
    variants: tuple[Variant, ...] = ("cfr", "cfr_plus", "linear", "discounted")
    for game in games:
        rules[game] = validate_game_rules(game)
        tree = Tree.build(game)
        independent = OpenSpielReference(tree, "cfr")
        for seed in config["best_response_seeds"]:
            policy = tree.normalize(
                Generator(PCG64(seed)).random(tree.legal.shape) * tree.legal
            )
            own_br = evaluate(tree, policy).exploitability
            reference_br = independent.exploitability(policy)
            gap = abs(own_br - reference_br)
            random_br_checks.append(
                {
                    "game": game,
                    "seed": seed,
                    "own": own_br,
                    "reference": reference_br,
                    "gap": gap,
                }
            )
            if gap > config["best_response_absolute_tolerance"]:
                failures.append(f"{game}: random policy BR mismatch seed={seed}")
        for variant in variants:
            own, reference = CFR(tree, variant), OpenSpielReference(tree, variant)
            own_seconds = reference_seconds = 0.0
            checkpoints = cast(list[int], config["games"][game])
            for iteration in range(1, checkpoints[-1] + 1):
                tick = time.perf_counter()
                own.step()
                own_seconds += time.perf_counter() - tick
                tick = time.perf_counter()
                reference.step()
                reference_seconds += time.perf_counter() - tick
                if iteration not in checkpoints:
                    continue
                policy = own.average_policy
                metrics = evaluate(tree, policy)
                ref_policy = reference.average_policy()
                ref_exploit = reference.exploitability()
                mapped_br = reference.exploitability(policy)
                reference_value = reference.value()
                mean_l1 = float(np.abs(policy - ref_policy).sum(axis=1).mean())
                gap = abs(metrics.exploitability - ref_exploit)
                br_gap = abs(metrics.exploitability - mapped_br)
                row = {
                    "game": game,
                    "variant": variant,
                    "iteration": iteration,
                    **asdict(metrics),
                    "reference_exploitability": ref_exploit,
                    "reference_value_player_zero": reference_value,
                    "exploitability_gap": gap,
                    "strategy_mean_l1": mean_l1,
                    "mapped_policy_br_gap": br_gap,
                    "kuhn_value_error": abs(metrics.value_player_zero + 1 / 18)
                    if game == "kuhn"
                    else None,
                    "own_training_seconds": own_seconds,
                    "reference_training_seconds": reference_seconds,
                }
                rows.append(row)
                if gap > config["exploitability_absolute_tolerance"]:
                    failures.append(
                        f"{game}/{variant}/{iteration}: exploitability agreement"
                    )
                if mean_l1 > config["strategy_mean_l1_tolerance"]:
                    failures.append(
                        f"{game}/{variant}/{iteration}: average-policy agreement"
                    )
                if br_gap > config["best_response_absolute_tolerance"]:
                    failures.append(
                        f"{game}/{variant}/{iteration}: mapped-policy best response"
                    )
                if iteration == checkpoints[-1]:
                    if (
                        metrics.exploitability
                        > config[f"{game}_final_exploitability_limit"]
                    ):
                        failures.append(f"{game}/{variant}: final convergence limit")
                    if (
                        game == "kuhn"
                        and abs(metrics.value_player_zero + 1 / 18)
                        > config["kuhn_final_value_error_limit"]
                    ):
                        failures.append(f"{game}/{variant}: Kuhn value error")
                print(
                    f"{game}/{variant} t={iteration}: "
                    f"exploitability={metrics.exploitability:.8g}; "
                    f"reference gap={gap:.3g}; mean L1={mean_l1:.3g}",
                    flush=True,
                )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.output.with_name("cfr-convergence.csv")
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    artifacts = [csv_path] + plot(rows, args.output)
    report = {
        "schema_version": 1,
        "status": "failed" if failures else "passed",
        "config": config,
        "rules": rules,
        "rows": rows,
        "random_policy_br_checks": random_br_checks,
        "failures": failures,
        "source": provenance,
        "validation_seconds": time.perf_counter() - started,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            **{
                name: importlib.metadata.version(name)
                for name in ("numpy", "open_spiel", "matplotlib")
            },
        },
        "artifacts_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts
        },
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], args.output, flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
