"""Audit frozen fresh-game strategies after own training; never train a learner."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.fresh import audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/fresh-validation.json")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/fresh-validation/study.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/fresh-validation/independent.json")
    )
    args = parser.parse_args()
    result = audit(
        Path(__file__).resolve().parents[1], args.config, args.report, args.output
    )
    print(
        f"audit={result['status']}; "
        f"checked {len(result['comparisons'])} frozen own policies"
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
