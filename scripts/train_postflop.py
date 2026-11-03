"""Train own postflop controls; never import reference solvers or outputs."""

import argparse
from pathlib import Path
from typing import cast

from poker_ai.postflop.learning import run_training
from poker_ai.postflop.matrix import Encoding


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/holdem-learning.json")
    )
    parser.add_argument(
        "--phase", choices=("development", "heldout"), default="development"
    )
    parser.add_argument(
        "--encodings",
        nargs="+",
        choices=("exact", "legacy_b8", "public_b8"),
        default=["exact"],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/holdem-learning/development-exact.json"),
    )
    args = parser.parse_args()
    report = run_training(
        Path(__file__).resolve().parents[1],
        args.config,
        args.output,
        phase=args.phase,
        encodings=tuple(cast(Encoding, e) for e in args.encodings),
    )
    print(
        f"{report['status']}: own postflop training; gate={report['exact_acceptance']}"
    )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
