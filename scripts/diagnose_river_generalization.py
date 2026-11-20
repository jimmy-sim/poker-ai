"""Run the published bounded read-only medium/dry saved-policy diagnosis."""

import argparse
from pathlib import Path

from river_generalization_diagnosis.analysis import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain existing diagnostic output")
    run(root, args.output.resolve())


if __name__ == "__main__":
    main()
