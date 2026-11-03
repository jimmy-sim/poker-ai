"""Profile bounded own-game training and pair cached/dynamic action menu timings."""

import argparse
import cProfile
import io
import json
import pstats
import time
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import IndexedState, MatrixTree
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.toy.cfr import CFR
from poker_ai.training.mccfr import MCCFR
from poker_ai.validation.five_card import source_provenance


def sampler(tree: MatrixTree, seed: int, cached: bool = True) -> MCCFR:
    return MCCFR(
        lambda rng: IndexedState(tree, cached_actions=cached), Generator(PCG64(seed))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/holdem-learning.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/holdem-learning/profile.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = json.loads(args.config.read_text())
    source = source_provenance(
        root, args.config, entrypoints=("scripts/profile_postflop_learning.py",)
    )
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for filename in config["development_spots"]:
        t = time.perf_counter()
        tree = MatrixTree.build(SpotTree.build(load_spot(root / filename)))
        build_seconds = time.perf_counter() - t
        runs = []
        for repetition in range(config["profile_repetitions"]):
            samples = {}
            solvers = {}
            for cached in (False, True) if repetition % 2 == 0 else (True, False):
                solver = sampler(tree, config["seeds"][0], cached)
                t = time.perf_counter()
                solver.train(config["profile_iterations"])
                samples[str(cached)] = time.perf_counter() - t
                solvers[cached] = solver
            a, b = solvers[False], solvers[True]
            if a.nodes_visited != b.nodes_visited or a.rows.keys() != b.rows.keys():
                raise ArithmeticError("menu cache changed the sampled traversal")
            for key in a.rows:
                if not np.array_equal(
                    a.rows[key].regrets, b.rows[key].regrets
                ) or not np.array_equal(
                    a.rows[key].strategy_sum, b.rows[key].strategy_sum
                ):
                    raise ArithmeticError("menu cache changed own strategy updates")
            runs.append(samples)
        profile = cProfile.Profile()
        profile.enable()
        measured = sampler(tree, config["seeds"][0])
        measured.train(config["profile_iterations"])
        profile.disable()
        stream = io.StringIO()
        pstats.Stats(profile, stream=stream).strip_dirs().sort_stats(
            "cumtime"
        ).print_stats(12)
        full = CFR(tree, "cfr_plus")
        t = time.perf_counter()
        full.train(16)
        full_seconds = time.perf_counter() - t
        rows.append(
            {
                "spot": tree.source.spot.name,
                "nodes": len(tree.player),
                "information_sets": len(tree.keys),
                "build_seconds": build_seconds,
                "paired_seconds": runs,
                "cached_dynamic_mean_ratio": float(
                    np.mean([r["True"] / r["False"] for r in runs])
                ),
                "full_tree_16_iterations_seconds": full_seconds,
                "sampled_nodes": measured.nodes_visited,
                "cached_profile": stream.getvalue(),
            }
        )
        print(
            f"profiled: {tree.source.spot.name}; paired cache checks identical",
            flush=True,
        )
    report = {
        "status": "passed",
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "rows": rows,
        "limits": "paired local timings, not cross-machine speed or playing strength",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
