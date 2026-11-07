"""Replay public-board evidence and render tables/plots offline; no training."""

import argparse
from pathlib import Path

from poker_ai.postflop.public_report import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/public-board/study.json")
    )
    parser.add_argument(
        "--audit", type=Path, default=Path("results/public-board/independent.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/public-board/report")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = render(root, root / args.report, root / args.audit, root / args.output)
    print(
        "replay=passed; candidate_development_gate="
        f"{result['candidate_development_gate_passed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
