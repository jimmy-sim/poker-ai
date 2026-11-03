"""Run fixed own-only Bayesian toy-game experiment."""

import argparse
from pathlib import Path

from poker_ai.opponent_modeling.experiment import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/opponent-modeling.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/extensions/opponents.json")
    )
    args = parser.parse_args()
    report = run_experiment(
        Path(__file__).resolve().parents[1], args.config, args.output
    )
    print(f"completed: {len(report['rows'])} Bayesian checkpoint rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
