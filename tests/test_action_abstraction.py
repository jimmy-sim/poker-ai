"""Legal raise endpoints, pot-after-call arithmetic and mapping identities."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy.random import PCG64, Generator

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, HoldemState, Observation, new_hand


def observation(state: HoldemState) -> Observation:
    assert state.actor is not None
    return state.observe(state.actor)


def test_preflop_pot_after_call_and_no_duplicate_sizes() -> None:
    state = new_hand((200, 200), Deck(), button=1)
    assert ActionAbstraction().raises(observation(state)) == (4, 6, 10, 200)
    # Three-chip pot + one-chip call = four; .5/1/2 pot increments are 2/4/8.
    assert ActionAbstraction(fractions=((1, 2), (2, 4))).raises(observation(state)) == (
        4,
        200,
    )


def test_short_all_in_and_closed_raising() -> None:
    short = new_hand((200, 3), Deck(), button=1)
    assert ActionAbstraction().raises(observation(short)) == (3,)
    closed = new_hand((200, 200), Deck(), button=1).apply(
        Action(ActionKind.RAISE_TO, 200)
    )
    assert ActionAbstraction().raises(observation(closed)) == ()


def test_round_half_up_for_odd_pot_sizes() -> None:
    state = new_hand((200, 200), Deck(), button=1)
    state = state.apply(Action(ActionKind.RAISE_TO, 5)).apply(Action(ActionKind.CALL))
    # Opening half of ten is five. An eleven-chip pot is tested with a public
    # observation replacement below; card identities cannot affect sizing.
    from dataclasses import replace

    observed = replace(observation(state), pot=11)
    assert ActionAbstraction().raises(observed) == (2, 6, 11, 22, 195)


def test_pseudo_harmonic_matches_calling_frequency_identity_and_seed() -> None:
    state = new_hand((200, 200), Deck(), button=1)
    obs = observation(state)
    abstraction = ActionAbstraction()
    result = abstraction.translation(obs, 8)
    assert tuple(amount for amount, _ in result) == (6, 10)
    price, pot = 2, 4
    lower, upper = 6 - price, 10 - price
    actual = 8 - price
    p = result[0][1]
    assert p / (1 + lower / pot) + (1 - p) / (1 + upper / pot) == pytest.approx(
        1 / (1 + actual / pot)
    )
    assert abstraction.translation(obs, 8, scheme="nearest") == ((6, 1.0),)
    a, b = Generator(PCG64(19)), Generator(PCG64(19))
    assert [abstraction.translate(obs, 8, rng=a) for _ in range(30)] == [
        abstraction.translate(obs, 8, rng=b) for _ in range(30)
    ]
    assert abstraction.translation(obs, 6) == ((6, 1.0),)
    with pytest.raises(ValueError):
        abstraction.translation(obs, 201)


@given(st.integers(4, 300), st.integers(4, 300))
def test_every_discrete_raise_is_legal_and_preserves_chips(a: int, b: int) -> None:
    state = new_hand((a, b), Deck(), button=1)
    amounts = ActionAbstraction().raises(observation(state))
    assert tuple(sorted(set(amounts))) == amounts
    for amount in amounts:
        changed = state.apply(Action(ActionKind.RAISE_TO, amount))
        assert sum(changed.stacks) + changed.pot == a + b


def test_nominal_short_big_blind_price_is_not_inferred_from_posted_chips() -> None:
    state = new_hand((100, 1, 100), Deck(), button=2)
    assert max(state.street_commitments) == 1
    assert state.current_bet == 2
    assert ActionAbstraction().raises(observation(state)) == (4, 6, 10, 100)


@given(st.integers(4, 200))
def test_translation_is_legal_and_preserves_pseudo_harmonic_identity(
    total: int,
) -> None:
    obs = observation(new_hand((200, 200), Deck(), button=1))
    abstraction = ActionAbstraction()
    distribution = abstraction.translation(obs, total)
    assert sum(p for _, p in distribution) == pytest.approx(1)
    assert all(
        amount in abstraction.raises(obs) and 0 <= p <= 1 for amount, p in distribution
    )
    actual_call_frequency = 1 / (1 + (total - 2) / 4)
    translated_call_frequency = sum(
        p / (1 + (amount - 2) / 4) for amount, p in distribution
    )
    assert actual_call_frequency == pytest.approx(translated_call_frequency)
