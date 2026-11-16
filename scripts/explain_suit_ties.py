"""Show exact private-card suit ties; a card-representation demo, not a policy."""

import argparse
from collections.abc import Sequence

import suit_candidates_support as candidates
import suit_lookup_support as lookup

from poker_ai.cards import format_card, parse_card


def format_cards(cards: Sequence[int]) -> str:
    return " ".join(format_card(card) for card in cards) or "(empty)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hole", nargs=2, default=["2c", "3c"])
    parser.add_argument("--board", nargs="*", default=["4s", "5s", "6s"])
    parser.add_argument("--list-maps", action="store_true")
    args = parser.parse_args()
    try:
        hole = tuple(parse_card(card) for card in args.hole)
        board = tuple(parse_card(card) for card in args.board)
        original = candidates.BASE(hole, board)
        all_candidates = candidates.ALL(hole, board)
        reduced = candidates.reduced_cards(hole, board)
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    if original != all_candidates or original != reduced:
        raise ArithmeticError("canonicalization implementations disagree")
    slot = candidates.GEOMETRY[hole[0]][hole[1]]
    if slot is None:
        raise ArithmeticError("validated private cards have no geometry")
    private, indices = slot
    print("Exact card-representation demo; no agent decisions or training.")
    print(f"Input: private {format_cards(hole)}; board {format_cards(board)}")
    print(f"Private-minimum ties: {len(indices)} of 24 suit renamings")
    print(f"Smallest private description: {format_cards(private)}")
    print(f"Canonical result: {format_cards(reduced[0])}; {format_cards(reduced[1])}")
    print("Original, all-candidate and reduced outputs agree exactly.")
    if not board:
        print("The empty board requires no board-candidate comparisons.")
    if args.list_maps:
        suits = "cdhs"
        for index in indices:
            permutation = lookup.PERMUTATIONS[index]
            mapping = ", ".join(
                f"{source}->{suits[target]}"
                for source, target in zip(suits, permutation, strict=True)
            )
            transformed = tuple(sorted(candidates.TABLE[index][card] for card in board))
            selected = " [minimum board]" if transformed == reduced[1] else ""
            print(
                f"  map {index:2}: {mapping}; "
                f"board {format_cards(transformed)}{selected}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
