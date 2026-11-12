"""Inspect a fixed simulated public range; no actual private hand or action output."""

import argparse
import json
from pathlib import Path

from poker_ai.abstraction.public_range import ORDER, public_own_mass
from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.public_range_definition import check_inputs, contract
from poker_ai.postflop.range_protocol import range_context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("river", nargs="?", default="9h")
    parser.add_argument("--seat", type=int, choices=(0, 1), default=1)
    parser.add_argument(
        "--spot", choices=("dev_low_oop", "dev_medium_oop"), default="dev_medium_oop"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        c = contract(root)
        check_inputs(root, c)
        spot = load_spot(root / f"configs/learning-spots/{args.spot}.json")
        context = range_context(spot)
        board = spot.board + (parse_card(args.river),)
        mass = public_own_mass(board, context.priors[args.seat])
    except (ValueError, TypeError, ArithmeticError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            dict(
                candidate=c["candidate"],
                context_sha256=context.identifier,
                public_board=[format_card(x) for x in board],
                seat=args.seat,
                masses=dict(zip(ORDER, map(str, mass.masses), strict=True)),
                bins=dict(zip(ORDER, mass.bins, strict=True)),
                word=mass.word,
                maximum_bits=30,
                scope=(
                    "Fixed-prior public encoding only; no actual private hand, "
                    "strategy/action, compression or learned-strength result"
                ),
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
