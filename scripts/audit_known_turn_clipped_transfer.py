"""Run the one data-only native admission or 24-case comparison-only audit."""

import argparse
from pathlib import Path

from known_turn_clipped_transfer.native import admit, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("admit", "audit"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain earlier native stage output")
    if args.stage == "admit":
        admit(root, args.output.resolve())
    else:
        audit(root, args.output.resolve())


if __name__ == "__main__":
    main()
