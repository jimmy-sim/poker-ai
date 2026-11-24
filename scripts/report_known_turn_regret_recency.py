"""Report the fixed known wet/dry regret-recency comparison."""

import argparse
from pathlib import Path

from known_turn_regret_recency.report import report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain earlier regret-recency report")
    report(root, args.output.resolve())


if __name__ == "__main__":
    main()
