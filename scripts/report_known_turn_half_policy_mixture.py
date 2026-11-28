"""Apply the frozen four-game strength decision to published audited policies."""

import argparse
from pathlib import Path

from known_turn_half_policy_mixture.report import report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report(Path.cwd(), args.output)


if __name__ == "__main__":
    main()
