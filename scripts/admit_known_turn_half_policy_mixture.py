"""Run the published data-only strict forecast after fictional proof."""

import argparse
from pathlib import Path

from known_turn_half_policy_mixture.admission import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd(), args.output)


if __name__ == "__main__":
    main()
