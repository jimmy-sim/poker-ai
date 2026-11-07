"""Observable public-board controls, with explicit and intentionally lossy texture.

Ranks are 2..14, suits are arbitrary labels. Canonicalization removes only global
suit names and flop order. Texture additionally discards exact ranks, suit/rank
associations and cross-street suit identity; it is not a sufficient poker state.
Neither API accepts private cards, dealer decks or actual future cards.
"""

from collections import Counter
from typing import NamedTuple

from poker_ai.abstraction.potential import SUIT_PERMUTATIONS
from poker_ai.cards import cards_to_mask

STRAIGHT_WINDOWS = (frozenset((14, 2, 3, 4, 5)),) + tuple(
    frozenset(range(low, low + 5)) for low in range(2, 11)
)


class BoardTexture(NamedTuple):
    rank_counts: tuple[int, ...]
    suit_counts: tuple[int, ...]
    high_cards: int
    aces: int
    straight_occupancy: int


def _validate(board: tuple[int, ...]) -> None:
    if len(board) not in (0, 3, 4, 5):
        raise ValueError("need an observed Hold'em board of length 0, 3, 4 or 5")
    cards_to_mask(board)


def canonical_public_board(board: tuple[int, ...]) -> tuple[int, ...]:
    """Minimum over global suit renamings; unordered flop, ordered turn/river.

    A single renaming applies across the full observed history, so suit links
    across streets survive. No suit choice is based on a player's hidden cards.
    """
    _validate(board)
    return min(
        tuple(sorted(4 * (c // 4) + suits[c % 4] for c in board[:3]))
        + tuple(4 * (c // 4) + suits[c % 4] for c in board[3:])
        for suits in SUIT_PERMUTATIONS
    )


def board_texture(board: tuple[int, ...]) -> BoardTexture:
    """Fixed-domain coarse features, including wheel-aware straight occupancy.

    Multiplicities are descending and zero-padded to five ranks/four suits.
    High cards count physical cards of rank >=10; aces count physical aces.
    Straight occupancy counts DISTINCT ranks, never treating pairs as connected.
    Empty-board features are zero; history omits this constant preflop prefix.
    """
    _validate(board)
    ranks = [c // 4 + 2 for c in board]
    rank_counts = sorted(Counter(ranks).values(), reverse=True)
    suit_counts = sorted(Counter(c % 4 for c in board).values(), reverse=True)
    return BoardTexture(
        tuple(rank_counts + [0] * (5 - len(rank_counts))),
        tuple(suit_counts + [0] * (4 - len(suit_counts))),
        sum(r >= 10 for r in ranks),
        ranks.count(14),
        max(len(set(ranks) & window) for window in STRAIGHT_WINDOWS),
    )


def board_texture_history(board: tuple[int, ...]) -> tuple[BoardTexture, ...]:
    """Retain every already-observed street, using that prefix's cards alone."""
    _validate(board)
    return tuple(board_texture(board[:n]) for n in (3, 4, 5) if n <= len(board))
