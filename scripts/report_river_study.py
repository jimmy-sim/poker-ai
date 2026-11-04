"""Replay and render the saved complete river study and linked native audit."""

import argparse
from pathlib import Path

from poker_ai.postflop.river_report import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/river-integration/study.json")
    )
    parser.add_argument(
        "--audit", type=Path, default=Path("results/river-integration/independent.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/river-integration/report")
    )
    args = parser.parse_args()
    summary = render(
        Path(__file__).resolve().parents[1], args.report, args.audit, args.output
    )
    print(
        f"audit={summary['status']}; "
        f"candidate development gate={summary['candidate_passed']}"
    )
    return 0 if summary["candidate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
