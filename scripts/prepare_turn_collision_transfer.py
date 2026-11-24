"""Run or freeze the one prospective score-free collision screen."""

import argparse
from pathlib import Path

from turn_collision_transfer_selection import freeze, screen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("screen", "freeze"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.stage == "screen":
        screen(root, args.output.resolve())
    else:
        freeze(root, args.output.resolve())


if __name__ == "__main__":
    main()
