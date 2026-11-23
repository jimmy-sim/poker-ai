"""Build one fixed comparison report from published own and native bytes."""

import argparse
from pathlib import Path

from river_full_broader.report import report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report(Path(__file__).resolve().parents[1], args.output.resolve())


if __name__ == "__main__":
    main()
