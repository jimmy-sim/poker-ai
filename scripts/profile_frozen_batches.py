"""Time every fixed prefix or replay the complete saved compute forecast."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.frozen_batch_profile import run
from poker_ai.evaluation.frozen_batch_protocol import read_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/frozen-pass-batches/profile.json"),
    )
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = (
        read_profile(root, root / args.replay)
        if args.replay
        else run(root, root / args.output)
    )
    print(saved["status"])
    print(json.dumps(saved["forecast"], sort_keys=True))
    return (
        0 if saved["forecast"]["decision"] == "fits_requires_checked_admission" else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
