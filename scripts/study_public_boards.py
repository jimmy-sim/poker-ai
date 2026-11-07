"""Run every fixed public-board control; retain failures without changing limits."""

import argparse
from pathlib import Path

from poker_ai.postflop.public_study import run_study


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/public-board-study.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/public-board/study.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = run_study(root, root / args.config, root / args.output)
    print(
        f"status={report['status']}; candidate_learning_gate="
        f"{report['acceptance']['candidate_learning_gate_passed']}"
    )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
