"""Measure the fixed saved-window fallback intervention, never new training."""

import argparse
from pathlib import Path

from poker_ai.evaluation.window_fallback_run import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/window-fallback/own.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.output)
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
