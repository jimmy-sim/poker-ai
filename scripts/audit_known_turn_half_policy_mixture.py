"""Audit only published own mixed policy scalars with pinned OpenSpiel."""

import argparse
from pathlib import Path

from known_turn_half_policy_mixture.native import audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(Path.cwd(), args.output)


if __name__ == "__main__":
    main()
