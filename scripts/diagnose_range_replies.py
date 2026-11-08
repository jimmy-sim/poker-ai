"""Diagnose retained own strategies; no training or online play."""

import argparse
from pathlib import Path

from poker_ai.postflop.range_reply import diagnose


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/range-mass-reply-diagnosis.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/range-mass-replies/diagnosis.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = diagnose(root, root / args.config, root / args.output)
    print(f"completed: {len(result['cases'])} saved cases; {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
