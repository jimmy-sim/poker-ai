"""Run the single admitted four-policy read-only attribution."""

import argparse
from pathlib import Path

from known_turn_loss_attribution.analysis import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.output)


if __name__ == "__main__":
    main()
