"""Five-card category boundaries, tie-breaker priority, and invariants."""

from collections.abc import Iterable
from typing import cast

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from poker_ai.cards import parse_card
from poker_ai.evaluator import HandCategory, HandRank, evaluate_five

HANDS = st.lists(
    st.integers(min_value=0, max_value=51), min_size=5, max_size=5, unique=True
)


def hand(text: str) -> tuple[int, ...]:
    return tuple(map(parse_card, text.split()))


@pytest.mark.parametrize(
    ("cards", "category", "tiebreakers"),
    [
        ("As Kd Qh Jc 9s", HandCategory.HIGH_CARD, (14, 13, 12, 11, 9)),
        ("7c 5d 4h 3s 2c", HandCategory.HIGH_CARD, (7, 5, 4, 3, 2)),
        ("2c 2d Ah Ks Qc", HandCategory.ONE_PAIR, (2, 14, 13, 12)),
        ("Ac Ad Kh Ks 2c", HandCategory.TWO_PAIR, (14, 13, 2)),
        ("Ac Ad 2h 2s Kc", HandCategory.TWO_PAIR, (14, 2, 13)),
        ("3c 3d 3h As Kc", HandCategory.THREE_OF_A_KIND, (3, 14, 13)),
        ("Ac 2d 3h 4s 5c", HandCategory.STRAIGHT, (5,)),
        ("2c 3d 4h 5s 6c", HandCategory.STRAIGHT, (6,)),
        ("Ac Kd Qh Js Tc", HandCategory.STRAIGHT, (14,)),
        ("Ac Jc 9c 5c 2c", HandCategory.FLUSH, (14, 11, 9, 5, 2)),
        ("7c 5c 4c 3c 2c", HandCategory.FLUSH, (7, 5, 4, 3, 2)),
        ("2c 2d 2h As Ac", HandCategory.FULL_HOUSE, (2, 14)),
        ("Ac Ad Ah As 2c", HandCategory.FOUR_OF_A_KIND, (14, 2)),
        ("Ac 2c 3c 4c 5c", HandCategory.STRAIGHT_FLUSH, (5,)),
        ("9h Th Jh Qh Kh", HandCategory.STRAIGHT_FLUSH, (13,)),
        ("Th Jh Qh Kh Ah", HandCategory.STRAIGHT_FLUSH, (14,)),
    ],
)
def test_known_hand_ranks(
    cards: str, category: HandCategory, tiebreakers: tuple[int, ...]
) -> None:
    assert evaluate_five(hand(cards)) == HandRank(category, tiebreakers)


@pytest.mark.parametrize(
    ("weaker", "stronger"),
    [
        ("As Kd Qh Jc 9s", "2c 2d 3h 4s 5c"),
        ("Ac Ad Kh Qs Jc", "3c 3d 2h 2s 4c"),
        ("Ac Ad Kh Ks Qc", "2c 2d 2h 3s 4c"),
        ("Ac Ad Ah Ks Qc", "Ac 2d 3h 4s 5c"),
        ("Ac Kd Qh Js Tc", "7c 5c 4c 3c 2c"),
        ("Ac Kc Qc Jc 9c", "2c 2d 2h 3s 3c"),
        ("Ac Ad Ah Ks Kc", "2c 2d 2h 2s 3c"),
        ("Ac Ad Ah As Kc", "Ac 2c 3c 4c 5c"),
    ],
)
def test_weakest_next_category_beats_strongest_previous(
    weaker: str, stronger: str
) -> None:
    assert evaluate_five(hand(stronger)) > evaluate_five(hand(weaker))


@pytest.mark.parametrize(
    ("stronger", "weaker"),
    [
        # High-card tie-breakers, in priority order.
        ("Ac 9d 7h 4s 2c", "Kc Qd Jh 8s 6c"),
        ("Ac Kd 7h 4s 2c", "As Qd Jh 8c 6s"),
        ("Ac Kd Qh 4s 2c", "As Kc Jh 9d 6s"),
        ("Ac Kd Qh Js 2c", "As Kc Qd Th 9s"),
        ("Ac Kd Qh Js 9c", "As Kc Qd Jh 8s"),
        # The pair rank precedes all three kickers.
        ("3c 3d 4h 5s 6c", "2c 2d Ah Ks Qc"),
        ("2c 2d Ah Ks Qc", "2h 2s Kh Qd Jc"),
        ("2c 2d Ah Ks 3c", "2h 2s Ac Qd Jc"),
        ("2c 2d Ah Ks Qc", "2h 2s Ac Kd Jc"),
        # Two pair: higher pair, lower pair, then the remaining card.
        ("Ac Ad 2c 2d 3h", "Kc Kd Qc Qd Ah"),
        ("Ac Ad 4c 4d 2h", "Ah As 3c 3d Kh"),
        ("Ac Ad 2c 2d Kh", "Ah As 2h 2s Qc"),
        # Trips, then both kickers.
        ("3c 3d 3h 4s 5c", "2c 2d 2h As Kc"),
        ("2c 2d 2h As Kc", "2c 2d 2s Kh Qc"),
        ("2c 2d 2h As Kc", "2c 2d 2s Ah Qc"),
        # Straights use their highest card; the wheel is five-high.
        ("2c 3d 4h 5s 6c", "Ac 2d 3h 4s 5c"),
        ("Ac Kd Qh Js Tc", "Kc Qd Jh Ts 9c"),
        # Flushes compare all five ranks, not just the highest.
        ("Ac 9c 7c 4c 2c", "Kh Qh Jh 8h 6h"),
        ("Ac Kc 7c 4c 2c", "Ah Qh Jh 8h 6h"),
        ("Ac Kc Qc 4c 2c", "Ah Kh Jh 9h 6h"),
        ("Ac Kc Qc Jc 2c", "Ah Kh Qh Th 9h"),
        ("Ac Kc Qc Jc 9c", "Ah Kh Qh Jh 8h"),
        # Full houses compare trips before the pair.
        ("3c 3d 3h 2c 2d", "2c 2d 2h Ac Ad"),
        ("2c 2d 2h Ac Ad", "2c 2d 2s Kc Kd"),
        # Quads compare the four-card rank before the kicker.
        ("3c 3d 3h 3s 2c", "2c 2d 2h 2s Ac"),
        ("2c 2d 2h 2s Ac", "2c 2d 2h 2s Kc"),
        ("2c 3c 4c 5c 6c", "Ac 2c 3c 4c 5c"),
        ("Ac Kc Qc Jc Tc", "Kh Qh Jh Th 9h"),
    ],
)
def test_tiebreaker_priority(stronger: str, weaker: str) -> None:
    higher, lower = evaluate_five(hand(stronger)), evaluate_five(hand(weaker))
    assert higher.category == lower.category
    assert higher > lower


@pytest.mark.parametrize(
    "cards", ["Qc Kd Ah 2s 3c", "Jc Qd Kh As 2c", "Ac Ad 2h 3s 4c"]
)
def test_ace_cannot_wrap_a_straight_or_replace_a_missing_rank(cards: str) -> None:
    assert evaluate_five(hand(cards)).category not in (
        HandCategory.STRAIGHT,
        HandCategory.STRAIGHT_FLUSH,
    )


def test_equal_ranks_tie_regardless_of_suit() -> None:
    assert evaluate_five(hand("Ac Kd Qh Js 9c")) == evaluate_five(
        hand("Ah Ks Qc Jd 9h")
    )
    assert evaluate_five(hand("Ac Kc Qc Jc Tc")) == evaluate_five(
        hand("Ah Kh Qh Jh Th")
    )


@given(cards=HANDS, order=st.permutations(tuple(range(5))))
def test_card_order_does_not_change_rank(
    cards: list[int], order: tuple[int, ...]
) -> None:
    assert evaluate_five(cards) == evaluate_five(cards[index] for index in order)


@given(cards=HANDS, suits=st.permutations((0, 1, 2, 3)))
def test_global_suit_relabeling_does_not_change_rank(
    cards: list[int], suits: tuple[int, ...]
) -> None:
    relabeled = tuple(4 * (card // 4) + suits[card % 4] for card in cards)
    assert evaluate_five(cards) == evaluate_five(relabeled)


def test_iterable_input_is_consumed_once_without_mutating_input() -> None:
    cards = list(hand("Ac 2d 3h 4s 5c"))
    original = cards.copy()
    assert evaluate_five(iter(cards)) == HandRank(HandCategory.STRAIGHT, (5,))
    assert evaluate_five(cards) == evaluate_five(original)
    assert cards == original


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 6, 7, 52])
def test_requires_exactly_five_cards(count: int) -> None:
    with pytest.raises(ValueError, match="exactly five"):
        evaluate_five(range(count))


@pytest.mark.parametrize("cards", [(0, 1, 2, 3, 0), (0, 1, 2, 3, 3)])
def test_rejects_duplicate_physical_cards(cards: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_five(cards)


@pytest.mark.parametrize("bad_card", [-1, 52, 1 << 60])
def test_rejects_invalid_card_ids(bad_card: int) -> None:
    with pytest.raises(ValueError):
        evaluate_five((0, 1, 2, 3, bad_card))


@pytest.mark.parametrize("bad_card", [True, False, 1.0, np.int64(4), "Ac", None])
def test_rejects_invalid_card_types(bad_card: object) -> None:
    with pytest.raises(TypeError):
        evaluate_five((0, 1, 2, 3, cast(int, bad_card)))


def test_rejects_noniterable_input() -> None:
    with pytest.raises(TypeError):
        evaluate_five(cast(Iterable[int], None))
