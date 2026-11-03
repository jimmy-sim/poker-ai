"""Simulate conditional bankrolls from measured own-baseline six-hand blocks."""

import argparse
from pathlib import Path

from poker_ai.risk.empirical import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/empirical-bankroll.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/extensions/empirical-bankroll.json"),
    )
    args = parser.parse_args()
    report = run_experiment(
        Path(__file__).resolve().parents[1], args.config, args.output
    )
    print(f"completed: {len(report['rows'])} measured-return risk cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
