"""Independently check saved fallback fills without reference strategy export."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.window_fallback import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/window-fallback/own.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/window-fallback/native.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.own, root / args.output)
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
