"""Admitted saved-current diagnosis; no new learning or modified strategies."""

import argparse
from pathlib import Path

from poker_ai.evaluation.batch_current_run import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/batch-current-diagnosis/own.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.output)
    print(saved["status"])
    print(f"elapsed: {saved['seconds']:.9f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
