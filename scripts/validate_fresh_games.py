"""Run the frozen procedure on fresh games only after development admission."""

import argparse
from pathlib import Path

from poker_ai.postflop.fresh_learning import run_validation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/fresh-validation.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/fresh-validation/study.json")
    )
    args = parser.parse_args()
    report = run_validation(
        Path(__file__).resolve().parents[1], args.config, args.output
    )
    print(f"status={report['status']}; gate={report['acceptance']}")
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
