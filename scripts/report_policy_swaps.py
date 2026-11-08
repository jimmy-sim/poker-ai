"""Replay own response diagnosis with recorded native checks; no new solver run."""

import argparse
from pathlib import Path

from poker_ai.postflop.policy_swap_report import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/policy-swaps/study.json")
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=Path("results/policy-swaps/independent.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/policy-swaps/report")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = render(root, root / args.report, root / args.audit, root / args.output)
    print(
        f"replay=passed; cases={result['hybrid_profiles_checked']}; "
        f"diagnosis only, no training"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
