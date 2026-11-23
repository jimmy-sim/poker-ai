"""Audit published exact-turn own policies against pinned reference scalars."""

import argparse
from pathlib import Path

from turn_exact_transfer.native import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(Path(__file__).resolve().parents[1], args.output.resolve())


if __name__ == "__main__":
    main()
