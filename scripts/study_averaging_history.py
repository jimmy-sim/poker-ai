"""Run admitted observations along the same original 10m-work trajectories."""

import argparse
from pathlib import Path

from poker_ai.evaluation.averaging_history_run import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/averaging-history/own.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(run(root, root / args.output)["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
