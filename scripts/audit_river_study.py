"""Independently audit a complete own river-study policy artifact after training."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.river import validate_study


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/river-integration/study.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/river-integration/independent.json"),
    )
    args = parser.parse_args()
    result = validate_study(
        Path(__file__).resolve().parents[1], args.report, args.output
    )
    print(
        f"{result['status']}: {len(result['comparisons'])} frozen-policy native checks"
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
