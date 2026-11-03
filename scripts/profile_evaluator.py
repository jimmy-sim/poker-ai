"""Profile and time evaluators on fixed, pre-generated inputs; no reference data."""

import argparse
import cProfile
import hashlib
import io
import json
import platform
import pstats
import statistics
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

from numpy.random import PCG64, Generator

from poker_ai import evaluator
from poker_ai.evaluator import HandRank
from poker_ai.validation.five_card import source_provenance

Evaluate = Callable[[Iterable[int]], HandRank]


def batch(function: Evaluate, hands: list[tuple[int, ...]]) -> None:
    """Only evaluator calls belong in the timed region."""
    for hand in hands:
        function(hand)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if not isinstance(config, dict) or set(config) != {
        "samples",
        "repeats",
        "seed",
        "implementations",
    }:
        raise ValueError("expected samples, repeats, seed, implementations")
    for name in ("samples", "repeats", "seed"):
        if type(config[name]) is not int or config[name] < (0 if name == "seed" else 1):
            raise ValueError(f"invalid {name}")
    names = config["implementations"]
    if not isinstance(names, list) or not names or len(set(names)) != len(names):
        raise ValueError("implementations must be distinct names")
    functions: dict[str, Evaluate] = {}
    for name in names:
        if name not in ("evaluate_best", "evaluate_best_reference"):
            raise ValueError(f"unsupported implementation: {name}")
        functions[name] = cast(Evaluate, getattr(evaluator, name))

    root = Path(__file__).resolve().parents[1]
    provenance = source_provenance(
        root, args.config, entrypoints=("scripts/profile_evaluator.py",)
    )
    rows: list[dict[str, object]] = []
    for size in (5, 6, 7):
        rng = Generator(PCG64(config["seed"] + size))
        hands = [
            tuple(int(card) for card in rng.choice(52, size, replace=False))
            for _ in range(config["samples"])
        ]
        digest = hashlib.sha256(b"".join(bytes(hand) for hand in hands)).hexdigest()
        # Check equal outputs outside the timed region when comparing implementations.
        first = functions[names[0]]
        for hand in hands:
            expected = first(hand)
            if any(function(hand) != expected for function in functions.values()):
                raise AssertionError(f"implementations disagree on {hand}")
        durations: dict[str, list[float]] = {name: [] for name in names}
        for function in functions.values():
            batch(function, hands[: min(500, len(hands))])
        for repeat in range(config["repeats"]):
            order = names[repeat % len(names) :] + names[: repeat % len(names)]
            for name in order:
                start = time.perf_counter_ns()
                batch(functions[name], hands)
                durations[name].append((time.perf_counter_ns() - start) / 1e9)
        for name, function in functions.items():
            profiler = cProfile.Profile()
            profiler.runcall(batch, function, hands)
            stream = io.StringIO()
            pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(
                20
            )
            rows.append(
                {
                    "cards": size,
                    "implementation": name,
                    "seed": config["seed"] + size,
                    "input_sha256": digest,
                    "unprofiled_batch_seconds": durations[name],
                    "median_seconds_per_hand": statistics.median(durations[name])
                    / len(hands),
                    "cprofile_cumulative_top20": stream.getvalue(),
                }
            )
    report = {
        "schema_version": 1,
        "config": config,
        "source": provenance,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for row in rows:
        print(
            row["implementation"],
            row["cards"],
            "cards:",
            row["median_seconds_per_hand"],
            "seconds/hand",
        )
    print("Report:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
