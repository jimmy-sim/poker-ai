"""Comparison-only OpenSpiel scalar audit of the published own diagnosis."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.batch_currents import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/batch-current-diagnosis/own.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/batch-current-diagnosis/native.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.own, root / args.output)
    print(saved["status"])
    print(f"elapsed: {saved['seconds']:.9f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
