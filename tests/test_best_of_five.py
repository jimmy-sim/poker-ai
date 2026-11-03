"""Best-five selection over five to seven cards, including Hold'em edge cases."""

from typing import cast

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from poker_ai.cards import parse_card
from poker_ai.evaluator import (
    HandCategory,
    HandRank,
    evaluate_best,
    evaluate_best_reference,
    evaluate_five,
)

HANDS = st.lists(st.integers(0, 51), min_size=5, max_size=7, unique=True)
SEVEN_CARDS = st.lists(st.integers(0, 51), min_size=7, max_size=7, unique=True)


def hand(text: str) -> tuple[int, ...]:
    return tuple(map(parse_card, text.split()))


@pytest.mark.parametrize(
    ("cards", "category", "tiebreakers"),
    [
        ("Ac Kd Qh Js 9c 7d", HandCategory.HIGH_CARD, (14, 13, 12, 11, 9)),
        ("Ac Kd Qh Js 9c 7d 2h", HandCategory.HIGH_CARD, (14, 13, 12, 11, 9)),
        ("2c 2d Ah Ks Qc Jd", HandCategory.ONE_PAIR, (2, 14, 13, 12)),
        ("2c 2d Ah Ks Qc Jd 9h", HandCategory.ONE_PAIR, (2, 14, 13, 12)),
        ("Ac Ad Kh Ks Qc Qd 2h", HandCategory.TWO_PAIR, (14, 13, 12)),
        ("3c 3d 3h As Kc Qd 2s", HandCategory.THREE_OF_A_KIND, (3, 14, 13)),
        ("Ac 2d 3h 4s 5c 6d", HandCategory.STRAIGHT, (6,)),
        ("Ac 2d 3h 4s 5c 6d 7h", HandCategory.STRAIGHT, (7,)),
        ("Ac 2d 3h 4s 4c 5d Kh", HandCategory.STRAIGHT, (5,)),
        ("Ac Kd Qh Js Tc Td 2h", HandCategory.STRAIGHT, (14,)),
        ("Ah Kh Qh Jh 9h 8h 2c", HandCategory.FLUSH, (14, 13, 12, 11, 9)),
        ("Ah Kh Qh 8h 2h Js Tc", HandCategory.FLUSH, (14, 13, 12, 8, 2)),
        ("Ac Ad Ah Kc Kd Kh", HandCategory.FULL_HOUSE, (14, 13)),
        ("Ac Ad Ah Kc Kd Kh 2s", HandCategory.FULL_HOUSE, (14, 13)),
        ("3c 3d 3h Ac Ad Kc Kd", HandCategory.FULL_HOUSE, (3, 14)),
        ("2c 2d 2h 2s Kc Ac", HandCategory.FOUR_OF_A_KIND, (2, 14)),
        ("2c 2d 2h 2s Kc Qd Ac", HandCategory.FOUR_OF_A_KIND, (2, 14)),
        ("As 2h 3h 4h 5h 6h", HandCategory.STRAIGHT_FLUSH, (6,)),
        ("2h 3h 4h 5h 6h 7h 8h", HandCategory.STRAIGHT_FLUSH, (8,)),
        ("Ac 2c 3c 4c 5c Ah Ad", HandCategory.STRAIGHT_FLUSH, (5,)),
        ("2d 3h Ac Kc Qc Jc Tc", HandCategory.STRAIGHT_FLUSH, (14,)),
    ],
)
def test_best_five_known_cases(
    cards: str, category: HandCategory, tiebreakers: tuple[int, ...]
) -> None:
    assert evaluate_best(hand(cards)) == HandRank(category, tiebreakers)


def test_board_can_play_without_using_either_hole_card() -> None:
    board = hand("Tc Jc Qc Kc Ac")
    assert evaluate_best(board + hand("2d 3h")) == evaluate_best(board + hand("4d 5h"))
    assert evaluate_best(board + hand("2d 3h")) == evaluate_five(board)


def test_hole_card_can_improve_board_quad_kicker() -> None:
    board = hand("2c 2d 2h 2s Kc")
    assert evaluate_best(board + hand("Ac 3h")) > evaluate_best(board + hand("Qd Jh"))
    assert evaluate_best(board + hand("Qd Jh")) == evaluate_five(board)


@given(cards=SEVEN_CARDS)
def test_adding_cards_cannot_weaken_best_hand(cards: list[int]) -> None:
    assert evaluate_best(cards) >= evaluate_best(cards[:6]) >= evaluate_best(cards[:5])
    assert evaluate_best(cards[:5]) == evaluate_five(cards[:5])


@given(cards=HANDS, data=st.data())
def test_input_order_does_not_affect_selection(
    cards: list[int], data: st.DataObject
) -> None:
    permutation = data.draw(st.permutations(cards))
    assert evaluate_best(cards) == evaluate_best(permutation)


@given(cards=HANDS, suits=st.permutations((0, 1, 2, 3)))
def test_suit_relabeling_does_not_affect_selection(
    cards: list[int], suits: tuple[int, ...]
) -> None:
    assert evaluate_best(cards) == evaluate_best(
        4 * (card // 4) + suits[card % 4] for card in cards
    )


def test_accepts_one_pass_iterables_without_mutating_input() -> None:
    cards = list(hand("Ac Ad Ah Kc Kd Kh 2s"))
    original = cards.copy()
    assert evaluate_best(iter(cards)) == HandRank(HandCategory.FULL_HOUSE, (14, 13))
    assert cards == original


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 8, 52])
def test_rejects_unsupported_card_counts(count: int) -> None:
    with pytest.raises(ValueError, match="five to seven"):
        evaluate_best(range(count))


@pytest.mark.parametrize("extra", [0, 1, 2, 3, 4])
def test_rejects_duplicates_even_in_discardable_cards(extra: int) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_best((0, 1, 2, 3, 4, 5, extra))


@pytest.mark.parametrize("extra", [-1, 52, 1 << 60])
def test_rejects_out_of_range_cards_even_when_a_royal_flush_exists(extra: int) -> None:
    with pytest.raises(ValueError):
        evaluate_best(hand("Ac Kc Qc Jc Tc 2d") + (extra,))


@pytest.mark.parametrize("extra", [True, False, 1.0, np.int64(4), "Ac", None])
def test_rejects_invalid_card_types(extra: object) -> None:
    with pytest.raises(TypeError):
        evaluate_best(hand("Ac Kc Qc Jc Tc 2d") + (cast(int, extra),))


@given(cards=HANDS)
def test_direct_matches_preserved_subset_reference(cards: list[int]) -> None:
    assert evaluate_best(cards) == evaluate_best_reference(cards)
