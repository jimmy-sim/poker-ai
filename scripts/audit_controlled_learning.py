"""Compare immutable controlled own checkpoints; never export a reference strategy."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.controlled_learning import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/controlled-learning/own.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/controlled-learning/native.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(run(root, root / args.own, root / args.output)["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
