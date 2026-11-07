"""Audit frozen own policies and cross-play after public-board training."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.public_board import audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/public-board-study.json")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/public-board/study.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/public-board/independent.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = audit(root, root / args.config, root / args.report, root / args.output)
    print(
        f"audit={result['status']}; policies={len(result['comparisons'])}; "
        f"crossplay={len(result['crossplay'])}"
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
