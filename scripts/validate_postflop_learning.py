"""Validate frozen own postflop policies with OpenSpiel; never train own agents."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.learning import validate_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_report(
        Path(__file__).resolve().parents[1], args.report, args.output
    )
    print(
        f"{report['status']}: independent checks of "
        f"{len(report['comparisons'])} own policies"
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
