"""Native comparison-only checks/costs of committed saved-own profiles."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.controlled_pipeline import audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/controlled-pipeline-check/own.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/controlled-pipeline-check/native.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = audit(root, root / args.own, root / args.output)
    print(f"{result['status']}: comparison-only native pipeline calibration")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
