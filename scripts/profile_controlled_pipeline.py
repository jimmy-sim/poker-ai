"""Measure saved-own scoring/checkpoint/report costs; no new postflop learning."""

import argparse
from pathlib import Path

from poker_ai.postflop.pipeline_cost import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/controlled-pipeline-check/own.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run(root, root / args.output)
    print(f"{result['status']}: old-own pipeline calibration; no new learning")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
