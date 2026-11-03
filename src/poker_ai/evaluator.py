"""High-poker evaluation with explicit tie-breakers and best-five selection.

Larger HandRank values mean stronger hands. Category takes precedence; equal
categories compare rank tuples lexicographically. Suits never break ties. A royal
flush is an ace-high straight flush, not an additional category.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations

from poker_ai.cards import cards_to_mask


class HandCategory(IntEnum):
    """Standard high-poker categories, weakest to strongest."""

    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


@dataclass(frozen=True, order=True, slots=True)
class HandRank:
    """An immutable comparison key produced by the evaluators.

    Tie-breaker tuples, in comparison priority order:
      high card/flush: all five ranks, descending;
      one pair: pair rank, then three descending kickers;
      two pair: higher pair, lower pair, kicker;
      trips: trip rank, then two descending kickers;
      straight/straight flush: highest rank, with the wheel encoded as 5;
      full house: trip rank, pair rank;
      quads: quad rank, kicker.

    These are ordinal keys, not probabilities, equities, or a linear EV scale.
    """

    category: HandCategory
    tiebreakers: tuple[int, ...]


def evaluate_five(cards: Iterable[int]) -> HandRank:
    """Rank exactly five distinct valid card IDs in standard high poker.

    Validate through the shared bitmask boundary, then count ranks and inspect
    suits. Sorting (multiplicity, rank) groups in descending order puts the
    strategically important ranks first for every multiplicity-based category.

    Ace is normally rank 14. Exactly A-2-3-4-5 is a five-high straight; it cannot
    wrap in any other sequence. The input iterable is consumed once and not
    mutated. This deliberately readable reference path has no poker-library or
    lookup-table dependency; profile it before optimization.
    """
    hand = tuple(cards)
    if len(hand) != 5:
        raise ValueError(f"expected exactly five cards, got {len(hand)}")
    cards_to_mask(hand)

    counts = Counter(card // 4 + 2 for card in hand)
    ranks = tuple(sorted(counts, reverse=True))
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    pattern = tuple(count for count, _ in groups)
    group_ranks = tuple(rank for _, rank in groups)
    flush = len({card % 4 for card in hand}) == 1

    straight_high = 0
    if ranks == (14, 5, 4, 3, 2):
        straight_high = 5
    elif len(ranks) == 5 and ranks[0] - ranks[-1] == 4:
        straight_high = ranks[0]

    if flush and straight_high:
        return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_high,))
    if pattern == (4, 1):
        return HandRank(HandCategory.FOUR_OF_A_KIND, group_ranks)
    if pattern == (3, 2):
        return HandRank(HandCategory.FULL_HOUSE, group_ranks)
    if flush:
        return HandRank(HandCategory.FLUSH, ranks)
    if straight_high:
        return HandRank(HandCategory.STRAIGHT, (straight_high,))
    if pattern == (3, 1, 1):
        return HandRank(HandCategory.THREE_OF_A_KIND, group_ranks)
    if pattern == (2, 2, 1):
        return HandRank(HandCategory.TWO_PAIR, group_ranks)
    if pattern == (2, 1, 1, 1):
        return HandRank(HandCategory.ONE_PAIR, group_ranks)
    return HandRank(HandCategory.HIGH_CARD, ranks)


def evaluate_best_reference(cards: Iterable[int]) -> HandRank:
    """Return the strongest five-card rank from five to seven distinct cards.

    Inspect every five-card subset: C(5, 5)=1, C(6, 5)=6, C(7, 5)=21.
    Any subset may win, including all five board cards in Hold'em. No rule here
    forces use of a particular number of hole cards.

    Validate all input cards before selection, including cards that would be
    discarded. Reuse the independently validated five-card reference evaluator;
    repeated subset validation is a deliberate correctness-first cost to profile
    before introducing an optimized core. Consume iterables once without mutation.
    """
    hand = tuple(cards)
    if not 5 <= len(hand) <= 7:
        raise ValueError(f"expected five to seven cards, got {len(hand)}")
    cards_to_mask(hand)
    return max(evaluate_five(subset) for subset in combinations(hand, 5))


_WHEEL_RANK_MASK = (1 << 14) | (1 << 5) | (1 << 4) | (1 << 3) | (1 << 2)


def _straight_high(rank_mask: int) -> int:
    """Find the highest five-rank run, then check the ace-low wheel.

    Intersecting five shifted masks leaves each possible starting rank's bit.
    Its highest set bit plus four is the straight's high card. Rank bits are
    numbered 2 through 14, so bit_length() + 3 gives that high rank.
    """
    starts = (
        rank_mask
        & (rank_mask >> 1)
        & (rank_mask >> 2)
        & (rank_mask >> 3)
        & (rank_mask >> 4)
    )
    if starts:
        return starts.bit_length() + 3
    return 5 if rank_mask & _WHEEL_RANK_MASK == _WHEEL_RANK_MASK else 0


def _highest_ranks(rank_mask: int, count: int) -> tuple[int, ...]:
    """Extract descending rank bits; category logic guarantees enough ranks."""
    ranks = []
    for _ in range(count):
        rank = rank_mask.bit_length() - 1
        ranks.append(rank)
        rank_mask ^= 1 << rank
    return tuple(ranks)


def evaluate_best(cards: Iterable[int]) -> HandRank:
    """Directly classify the best five of five through seven valid cards.

    Preserve evaluate_five for five-card inputs. For six/seven cards, count each
    rank once and collect a rank mask per suit. A single suit can contain five
    cards at these input sizes. Test categories from strongest to weakest, with
    the same comparison keys as the reference. No external table is used.
    """
    hand = tuple(cards)
    if not 5 <= len(hand) <= 7:
        raise ValueError(f"expected five to seven cards, got {len(hand)}")
    if len(hand) == 5:
        return evaluate_five(hand)
    cards_to_mask(hand)
    counts = [0] * 15
    suit_masks = [0] * 4
    rank_mask = 0
    for card in hand:
        rank = card // 4 + 2
        bit = 1 << rank
        counts[rank] += 1
        suit_masks[card % 4] |= bit
        rank_mask |= bit
    flush_mask = next((mask for mask in suit_masks if mask.bit_count() >= 5), 0)
    if flush_mask:
        straight_flush = _straight_high(flush_mask)
        if straight_flush:
            return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_flush,))
    quads = [rank for rank in range(14, 1, -1) if counts[rank] == 4]
    if quads:
        return HandRank(
            HandCategory.FOUR_OF_A_KIND,
            (quads[0],) + _highest_ranks(rank_mask ^ (1 << quads[0]), 1),
        )
    trips = [rank for rank in range(14, 1, -1) if counts[rank] >= 3]
    pairs = [rank for rank in range(14, 1, -1) if counts[rank] >= 2]
    if trips:
        other_pairs = [rank for rank in pairs if rank != trips[0]]
        if other_pairs:
            return HandRank(HandCategory.FULL_HOUSE, (trips[0], other_pairs[0]))
    if flush_mask:
        return HandRank(HandCategory.FLUSH, _highest_ranks(flush_mask, 5))
    straight = _straight_high(rank_mask)
    if straight:
        return HandRank(HandCategory.STRAIGHT, (straight,))
    if trips:
        return HandRank(
            HandCategory.THREE_OF_A_KIND,
            (trips[0],) + _highest_ranks(rank_mask ^ (1 << trips[0]), 2),
        )
    if len(pairs) >= 2:
        kickers = rank_mask ^ (1 << pairs[0]) ^ (1 << pairs[1])
        return HandRank(
            HandCategory.TWO_PAIR, tuple(pairs[:2]) + _highest_ranks(kickers, 1)
        )
    if pairs:
        return HandRank(
            HandCategory.ONE_PAIR,
            (pairs[0],) + _highest_ranks(rank_mask ^ (1 << pairs[0]), 3),
        )
    return HandRank(HandCategory.HIGH_CARD, _highest_ranks(rank_mask, 5))
