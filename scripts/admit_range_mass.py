"""Run the declared full-control admission; no sampled/fresh/global training."""

import argparse
from pathlib import Path

from poker_ai.postflop.range_admission import run_admission


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/range-mass-protocol.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/range-mass-admission/study.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run_admission(root, root / args.config, root / args.output)
    print(
        f"status={result['status']}; own_grid_complete="
        f"{result['acceptance']['own_grid_complete']}"
    )
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
