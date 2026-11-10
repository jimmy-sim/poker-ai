"""Run the complete admitted known-game matched-update comparison; no default change."""

import argparse
from pathlib import Path

from poker_ai.evaluation.matched_update_run import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/matched-update-study/own.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.output)
    print(f"{saved['status']}: {saved['seconds']:.9f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
