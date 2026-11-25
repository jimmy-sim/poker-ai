"""One-time score-free selection and immutable frozen-cohort publication."""

import argparse
from pathlib import Path

from known_turn_collision_medium_transfer.selection import freeze, screen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("screen", "freeze"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.stage == "screen":
        if args.output is None:
            parser.error("screen requires --output")
        screen(root, args.output.resolve())
    else:
        if args.output is not None:
            parser.error("freeze accepts no --output")
        freeze(root)


if __name__ == "__main__":
    main()
