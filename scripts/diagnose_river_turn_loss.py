"""Run one fictional proof or the preregistered saved-policy diagnosis."""

import argparse
from pathlib import Path

from river_turn_loss.analysis import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("proof", "diagnose"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.output.resolve(), args.stage)


if __name__ == "__main__":
    main()
