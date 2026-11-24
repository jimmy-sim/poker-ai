"""Build the fixed known-case report from published own/reference bytes."""

import argparse
from pathlib import Path

from known_wet_turn_mechanism.report import report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report(Path(__file__).resolve().parents[1], args.output.resolve())


if __name__ == "__main__":
    main()
