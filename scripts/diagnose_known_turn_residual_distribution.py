"""Run one bounded stage of the prospective known-row diagnosis."""

import argparse
from pathlib import Path

from known_turn_residual_distribution.workflow import execute


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("proof", "admission", "analysis"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute(Path(__file__).resolve().parents[1], args.output.resolve(), args.stage)


if __name__ == "__main__":
    main()
