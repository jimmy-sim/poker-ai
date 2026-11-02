"""Encoding boundaries, set identities, and conservation of cards when dealing."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import cast

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy.random import PCG64, Generator

from poker_ai.cards import (
    DECK_SIZE,
    FULL_DECK_MASK,
    Deck,
    card_bit,
    cards_to_mask,
    format_card,
    make_card,
    mask_to_cards,
    parse_card,
    rank_of,
    suit_of,
)

CARD_LISTS = st.lists(st.integers(min_value=0, max_value=51), unique=True)
MASKS = st.integers(min_value=0, max_value=(1 << 52) - 1)


@pytest.mark.parametrize(
    ("text", "card"),
    [
        ("2c", 0),
        ("2d", 1),
        ("2h", 2),
        ("2s", 3),
        ("3c", 4),
        ("Th", 34),
        ("Ac", 48),
        ("Ad", 49),
        ("Ah", 50),
        ("As", 51),
    ],
)
def test_known_card_ids(text: str, card: int) -> None:
    assert parse_card(text) == card
    assert format_card(card) == text


def test_all_cards_round_trip_and_have_unique_bits() -> None:
    expected_text = {rank + suit for rank in "23456789TJQKA" for suit in "cdhs"}
    assert {format_card(card) for card in range(DECK_SIZE)} == expected_text
    for card in range(DECK_SIZE):
        assert parse_card(format_card(card)) == card
        assert make_card(rank_of(card), suit_of(card)) == card
        assert mask_to_cards(card_bit(card)) == (card,)
        assert card_bit(card).bit_count() == 1
    assert cards_to_mask(range(DECK_SIZE)) == (1 << 52) - 1 == FULL_DECK_MASK


def test_rank_and_suit_conventions() -> None:
    assert (rank_of(parse_card("2c")), suit_of(parse_card("2c"))) == (2, 0)
    assert (rank_of(parse_card("Th")), suit_of(parse_card("Th"))) == (10, 2)
    assert (rank_of(parse_card("As")), suit_of(parse_card("As"))) == (14, 3)


@pytest.mark.parametrize(
    "text", ["", "A", "10s", "as", "AS", "A♠", "Ac ", " Ac", "1c", "Ax"]
)
def test_parse_rejects_noncanonical_notation(text: str) -> None:
    with pytest.raises(ValueError):
        parse_card(text)


@pytest.mark.parametrize("value", [None, 0, True, b"Ac"])
def test_parse_rejects_non_strings(value: object) -> None:
    with pytest.raises(TypeError):
        parse_card(cast(str, value))


@pytest.mark.parametrize("card", [-1, 52, 1 << 60])
@pytest.mark.parametrize("operation", [format_card, rank_of, suit_of, card_bit])
def test_rejects_out_of_range_card_ids(
    card: int, operation: Callable[[int], object]
) -> None:
    with pytest.raises(ValueError):
        operation(card)


@pytest.mark.parametrize("value", [None, True, False, 1.0, "1", np.int64(1)])
@pytest.mark.parametrize("operation", [format_card, rank_of, suit_of, card_bit])
def test_rejects_non_builtin_integer_card_ids(
    value: object, operation: Callable[[int], object]
) -> None:
    with pytest.raises(TypeError):
        operation(cast(int, value))


@pytest.mark.parametrize(("rank", "suit"), [(1, 0), (15, 0), (2, -1), (14, 4)])
def test_make_card_rejects_invalid_rank_or_suit(rank: int, suit: int) -> None:
    with pytest.raises(ValueError):
        make_card(rank, suit)


@pytest.mark.parametrize("value", [True, 2.0, np.int64(2)])
def test_make_card_rejects_non_builtin_integer_components(value: object) -> None:
    with pytest.raises(TypeError):
        make_card(cast(int, value), 0)
    with pytest.raises(TypeError):
        make_card(2, cast(int, value))


def test_empty_and_known_card_masks() -> None:
    assert cards_to_mask(()) == 0
    assert mask_to_cards(0) == ()
    assert cards_to_mask([51, 0, 34]) == (1 << 51) | (1 << 34) | 1
    assert mask_to_cards((1 << 51) | (1 << 34) | 1) == (0, 34, 51)
    assert mask_to_cards(FULL_DECK_MASK) == tuple(range(52))


def test_cards_to_mask_accepts_one_pass_iterables() -> None:
    assert cards_to_mask(iter([0, 34, 51])) == (1 << 51) | (1 << 34) | 1


@pytest.mark.parametrize("cards", [(0, 0), (51, 0, 51)])
def test_cards_to_mask_rejects_duplicates(cards: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        cards_to_mask(cards)


def test_cards_to_mask_validates_each_card() -> None:
    with pytest.raises(ValueError):
        cards_to_mask([0, 52])
    with pytest.raises(TypeError):
        cards_to_mask([0, cast(int, True)])


@pytest.mark.parametrize("mask", [-1, 1 << 52, FULL_DECK_MASK | (1 << 80)])
def test_mask_rejects_bits_outside_the_deck(mask: int) -> None:
    with pytest.raises(ValueError):
        mask_to_cards(mask)
    with pytest.raises(ValueError):
        Deck.shuffled(Generator(PCG64(7)), excluded_mask=mask)


@pytest.mark.parametrize("value", [True, False, 1.0, np.int64(1), "1", None])
def test_mask_rejects_non_builtin_integers(value: object) -> None:
    with pytest.raises(TypeError):
        mask_to_cards(cast(int, value))


@given(cards=CARD_LISTS)
def test_mask_round_trip_preserves_card_set(cards: list[int]) -> None:
    mask = cards_to_mask(cards)
    assert mask.bit_count() == len(cards)
    assert mask_to_cards(mask) == tuple(sorted(cards))


@given(mask=MASKS)
def test_every_valid_mask_round_trips(mask: int) -> None:
    assert cards_to_mask(mask_to_cards(mask)) == mask


@given(left=MASKS, right=MASKS)
def test_bit_operations_match_card_set_operations(left: int, right: int) -> None:
    left_cards = set(mask_to_cards(left))
    right_cards = set(mask_to_cards(right))
    assert set(mask_to_cards(left | right)) == left_cards | right_cards
    assert set(mask_to_cards(left & right)) == left_cards & right_cards
    assert set(mask_to_cards(left ^ right)) == left_cards ^ right_cards


def test_default_deck_and_immutability() -> None:
    deck = Deck()
    assert deck.cards == tuple(range(52))
    assert deck.mask == FULL_DECK_MASK
    assert len(deck) == 52
    with pytest.raises(FrozenInstanceError):
        deck.__setattr__("cards", ())


def test_deck_rejects_mutable_or_invalid_contents() -> None:
    with pytest.raises(TypeError):
        Deck(cast(tuple[int, ...], [0, 1]))
    with pytest.raises(ValueError, match="duplicate"):
        Deck((0, 0))
    with pytest.raises(ValueError):
        Deck((52,))
    with pytest.raises(TypeError):
        Deck((cast(int, True),))


def test_deal_order_and_exhaustion() -> None:
    deck = Deck(tuple(map(parse_card, ["As", "Kh", "Qd"])))
    first, remaining = deck.draw(2)
    last, empty = remaining.draw(1)
    assert tuple(map(format_card, first)) == ("As", "Kh")
    assert tuple(map(format_card, last)) == ("Qd",)
    assert len(empty) == 0
    assert empty.mask == 0
    assert empty.draw(0) == ((), empty)
    with pytest.raises(ValueError):
        empty.draw(1)
    assert len(deck) == 3


@given(cards=CARD_LISTS, requested=st.integers(min_value=0, max_value=52))
def test_draw_conserves_cards_and_preserves_original(
    cards: list[int], requested: int
) -> None:
    deck = Deck(tuple(cards))
    count = min(requested, len(cards))
    drawn, remaining = deck.draw(count)
    assert drawn + remaining.cards == tuple(cards)
    assert len(drawn) == count
    assert len(remaining) == len(cards) - count
    assert cards_to_mask(drawn) & remaining.mask == 0
    assert cards_to_mask(drawn) | remaining.mask == deck.mask
    assert deck.cards == tuple(cards)


@pytest.mark.parametrize("count", [-1, 53])
def test_overdraw_or_negative_draw_fails_without_mutation(count: int) -> None:
    deck = Deck()
    with pytest.raises(ValueError):
        deck.draw(count)
    assert len(deck) == 52


@pytest.mark.parametrize("value", [True, 1.0, "1", np.int64(1), None])
def test_draw_count_requires_builtin_integer(value: object) -> None:
    with pytest.raises(TypeError):
        Deck().draw(cast(int, value))


def test_shuffle_replays_rng_stream_and_consumes_it() -> None:
    rng = Generator(PCG64(20261102))
    replay_rng = Generator(PCG64(20261102))
    first, second = Deck.shuffled(rng), Deck.shuffled(rng)
    assert first == Deck.shuffled(replay_rng)
    assert second == Deck.shuffled(replay_rng)
    assert first != second
    assert first.mask == second.mask == FULL_DECK_MASK


@given(excluded=MASKS)
def test_shuffle_excludes_known_cards_and_conserves_the_rest(excluded: int) -> None:
    deck = Deck.shuffled(Generator(PCG64(20261102)), excluded_mask=excluded)
    assert len(deck) == 52 - excluded.bit_count()
    assert deck.mask & excluded == 0
    assert deck.mask | excluded == FULL_DECK_MASK
    assert all(
        isinstance(card, int) and not isinstance(card, bool) for card in deck.cards
    )


def test_shuffle_with_no_remaining_cards() -> None:
    assert Deck.shuffled(Generator(PCG64(7)), excluded_mask=FULL_DECK_MASK) == Deck(())


def test_shuffle_requires_explicit_generator() -> None:
    with pytest.raises(TypeError):
        Deck.shuffled(cast(Generator, None))
