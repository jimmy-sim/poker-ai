"""Replay own response diagnosis with recorded native checks; no new solver run."""

import argparse
from pathlib import Path

from poker_ai.postflop.reply_report import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/saved-replies/diagnosis.json")
    )
    parser.add_argument(
        "--audit", type=Path, default=Path("results/saved-replies/independent.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/saved-replies/report")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = render(root, root / args.report, root / args.audit, root / args.output)
    print(f"replay=passed; cases={len(result['cases'])}; diagnosis only, no training")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
