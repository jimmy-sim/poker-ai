"""Compare own river-switch profile values with the pinned native reference."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.river_distinctions import audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/river-distinction-diagnosis.json")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/river-distinctions/diagnosis.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/river-distinctions/independent.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = audit(root, root / args.config, root / args.report, root / args.output)
    print(f"native river audit: {result['status']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
