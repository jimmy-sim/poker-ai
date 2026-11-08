"""Replay and plot full-control admission only; no reference call or training."""

import argparse
from pathlib import Path

from poker_ai.postflop.range_admission_report import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/range-mass-admission/study.json"),
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=Path("results/range-mass-admission/independent.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/range-mass-admission/report")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = render(root, root / args.report, root / args.audit, root / args.output)
    print(
        f"replay=passed; full_control_admission="
        f"{result['full_control_admission_passed']}; sampled=not_run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
