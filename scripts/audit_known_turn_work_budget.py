"""Thin comparison-only scalar audit for four published own paths."""

import argparse
from pathlib import Path

from known_turn_work_budget.native import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    audit(Path(__file__).resolve().parents[1], args.output.resolve())


if __name__ == "__main__":
    main()
