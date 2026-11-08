"""Diagnose retained own strategies; no training or online play."""

import argparse
from pathlib import Path

from poker_ai.postflop.policy_swaps import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/range-mass-policy-swaps.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/policy-swaps/study.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run(root, root / args.config, root / args.output)
    print(f"completed: {len(result['hybrids'])} saved cases; {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
