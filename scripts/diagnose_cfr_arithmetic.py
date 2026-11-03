"""Compare all eight IEEE contraction choices; no strategy is fitted to outputs."""

import argparse
import importlib
import importlib.metadata
import itertools
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.arithmetic import ScalarCFRPlus
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/holdem-learning/arithmetic.json")
    )
    parser.add_argument("--jit-profile", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = root / "configs/holdem-learning.json"
    path = root / json.loads(config.read_text())["development_spots"][1]
    source = source_provenance(
        root, config, entrypoints=("scripts/diagnose_cfr_arithmetic.py",)
    )
    started = time.perf_counter()
    tree = MatrixTree.build(SpotTree.build(load_spot(path)))
    reference = Reference(tree.source)
    native = []
    for iteration in range(1, 4):
        reference.train_to(iteration)
        native.append(reference.policy())
    rows: list[dict[str, Any]] = []
    for value, regret, average in itertools.product((False, True), repeat=3):
        scalar = ScalarCFRPlus(
            tree, fused_values=value, fused_regrets=regret, fused_averages=average
        )
        for iteration in range(1, 4):
            scalar.step()
            difference = [
                sum(abs(a - b) for a, b in zip(x, y, strict=True))
                for x, y in zip(
                    scalar.average_policy, native[iteration - 1], strict=True
                )
            ]
            rows.append(
                {
                    "fused_values": value,
                    "fused_regrets": regret,
                    "fused_averages": average,
                    "iteration": iteration,
                    "maximum_row_l1": max(difference),
                    "mean_row_l1": float(np.mean(difference)),
                }
            )
    paired = []
    first_call = None
    compiler_versions = None
    if args.jit_profile:
        module = importlib.import_module("poker_ai.postflop.jit_cfr")
        first = module.FusedCFRPlus(tree)
        t = time.perf_counter()
        first.step()
        first_call = time.perf_counter() - t
        compiler_versions = {
            name: importlib.metadata.version(name) for name in ("numba", "llvmlite")
        }
        for repetition in range(3):
            scalar = ScalarCFRPlus(
                tree, fused_values=True, fused_regrets=False, fused_averages=True
            )
            compiled = module.FusedCFRPlus(tree)
            timings = {}
            for label in (
                ("scalar", "jit") if repetition % 2 == 0 else ("jit", "scalar")
            ):
                solver = scalar if label == "scalar" else compiled
                t = time.perf_counter()
                for _ in range(16):
                    solver.step()
                timings[label] = time.perf_counter() - t
            if not np.array_equal(
                np.concatenate(scalar.average_policy),
                np.concatenate(tree.exact_policy(compiled.average_policy)),
            ):
                raise ArithmeticError("JIT/scalar profile changed the learned policy")
            paired.append(timings)
    report = {
        "status": "completed",
        "source": source,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "rows": rows,
        "compiler_versions": compiler_versions,
        "jit_first_call_compile_or_cache_load_seconds": first_call,
        "paired_16_iteration_seconds": paired,
        "profile_scope": "identical fused own scalar/JIT policies; local timings only",
        "scope": (
            "arithmetic diagnosis, not strategy/seed selection; initial failed "
            "NumPy comparison retained; no reference output enters own training"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("completed: all eight scalar arithmetic controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
