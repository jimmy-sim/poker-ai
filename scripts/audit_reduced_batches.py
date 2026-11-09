"""Comparison-only native audit of the fixed frozen-pass batch grid."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.reduced_batches import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/reduced-batch-study/native.json"),
    )
    parser.add_argument(
        "--own", type=Path, default=Path("results/reduced-batch-study/own.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.own, root / args.output)
    print(saved["status"])
    print(f"elapsed: {saved['seconds']:.6f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
