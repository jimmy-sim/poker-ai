"""Run one capped four-game own 50:50 saved-policy comparison."""

import argparse
from pathlib import Path

from known_turn_half_policy_mixture.own import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd(), args.output)


if __name__ == "__main__":
    main()
