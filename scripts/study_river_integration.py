"""Run the prospective own-only frozen-update and fixed-work river study."""

import argparse
from pathlib import Path

from poker_ai.postflop.river_study import run_study


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/river-integration-study.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/river-integration/study.json")
    )
    args = parser.parse_args()
    report = run_study(Path(__file__).resolve().parents[1], args.config, args.output)
    print(
        f"{report['status']}: {len(report['rows'])} learning rows; "
        f"acceptance={report['acceptance']}"
    )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
