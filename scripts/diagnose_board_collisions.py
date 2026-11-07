"""Rank conflicting texture rows using frozen own continuation strategies."""

import argparse
from pathlib import Path

from poker_ai.postflop.collision_diagnosis import diagnose


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/board-collision-diagnosis.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/board-diagnosis/diagnosis.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = diagnose(root, root / args.config, root / args.output)
    for case in result["cases"]:
        print(
            f"{case['spot']}/{case['panel']}: "
            f"{case['conflicting_rows']} conflicting rows; "
            f"supported decision weight={case['supported_uniform_decision_weight']:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
