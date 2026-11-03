"""Run fixed-seed conditional research bankroll simulations and analytic controls."""

import argparse
from pathlib import Path

from poker_ai.risk.experiment import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/bankroll-risk.json")
    )
    parser.add_argument(
        "--own-profiles",
        type=Path,
        default=Path("results/extensions/own-risk-profiles.json.gz"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/extensions/bankroll.json")
    )
    args = parser.parse_args()
    report = run_experiment(
        Path(__file__).resolve().parents[1], args.config, args.own_profiles, args.output
    )
    print(f"completed: {len(report['rows'])} risk cells and exact ruin controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
