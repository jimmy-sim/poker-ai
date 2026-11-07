"""Inspect visible-board features; this does not train or choose a poker action."""

import argparse
import json

from poker_ai.abstraction.public_board import (
    board_texture_history,
    canonical_public_board,
)
from poker_ai.cards import format_card, parse_card


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cards", nargs="*", help="0, 3, 4 or 5 cards, e.g. Ac Kc 2d 7c")
    args = parser.parse_args()
    try:
        board = tuple(parse_card(c) for c in args.cards)
        canonical = canonical_public_board(board)
        history = board_texture_history(board)
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "observed_board": [format_card(c) for c in board],
                "suit_canonical_board": [format_card(c) for c in canonical],
                "lossy_texture_history": [
                    {"board_length": length, **texture._asdict()}
                    for length, texture in zip((3, 4, 5), history, strict=False)
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
