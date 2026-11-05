"""Replay and render complete fresh results, retaining missed performance limits."""

import argparse
from pathlib import Path

from poker_ai.postflop.fresh_report import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/fresh-validation.json")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/fresh-validation/study.json")
    )
    parser.add_argument(
        "--audit", type=Path, default=Path("results/fresh-validation/independent.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/fresh-validation/report")
    )
    args = parser.parse_args()
    result = render(
        Path(__file__).resolve().parents[1],
        args.config,
        args.report,
        args.audit,
        args.output,
    )
    print(
        f"audit={result['audit_status']}; "
        f"fresh procedure gate={result['fresh_gate_passed']}"
    )
    return 0 if result["fresh_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
