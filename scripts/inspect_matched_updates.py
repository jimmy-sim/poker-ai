"""Browse verified same-update B1-prefix and batched saved action tables."""

import argparse
from pathlib import Path

from poker_ai.evaluation.matched_update_data import READOUTS, SEEDS
from poker_ai.evaluation.matched_update_viewer import (
    Selection,
    browse,
    display,
    load_pair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game", choices=("dev_low_oop", "dev_medium_oop"), default="dev_medium_oop"
    )
    parser.add_argument(
        "--representation",
        choices=("exact", "texture_range_q8_b8"),
        default="texture_range_q8_b8",
    )
    parser.add_argument("--rule", choices=("signed", "clipped"), default="signed")
    parser.add_argument("--seed", type=int, choices=SEEDS, default=SEEDS[0])
    parser.add_argument("--batch", type=int, choices=(4, 16), default=4)
    parser.add_argument("--readout", choices=READOUTS, default="linear_average")
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    if args.rank < 1:
        parser.error("choose a positive rank")
    request = Selection(
        args.game, args.representation, args.rule, args.seed, args.batch, args.readout
    )
    try:
        comparison = load_pair(
            Path(__file__).resolve().parents[1],
            request,
            lambda line: print(line, flush=True),
        )
        if args.interactive:
            browse(comparison, args.seat, args.rank)
        else:
            print(display(comparison, args.seat, args.rank))
    except (ValueError, ArithmeticError, FileNotFoundError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
