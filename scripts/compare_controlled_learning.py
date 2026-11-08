"""Run admitted original controlled learning, or toy correctness only."""

import argparse
from pathlib import Path

from poker_ai.postflop.learning_correctness import run as correctness
from poker_ai.postflop.learning_run import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--correctness", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output or Path(
        "results/runs/controlled-learning/"
        + ("correctness.json" if args.correctness else "own.json")
    )
    saved = (correctness if args.correctness else run)(root, root / output)
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
