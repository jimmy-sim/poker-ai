"""Analytical toy-game rules and imperfect-information boundaries."""

import pytest

from poker_ai.toy.games import ToyState


def walk(state: ToyState, actions: tuple[int, ...]) -> ToyState:
    for action in actions:
        state = state.child(action)
    return state


def test_kuhn_payoffs_and_fold_costs() -> None:
    assert walk(ToyState("kuhn"), (2, 0, 1, 1)).payoff == 1
    assert walk(ToyState("kuhn"), (2, 0, 2, 1)).payoff == 2
    assert walk(ToyState("kuhn"), (2, 0, 1, 2, 0)).payoff == -1
    assert walk(ToyState("kuhn"), (0, 2, 2, 0)).payoff == 1


def test_leduc_round_bets_cap_and_pair() -> None:
    state = walk(ToyState("leduc"), (0, 5, 2, 2))
    assert state.actions == (0, 1) and state.paid == (3, 5)
    state = state.child(1)
    assert state.chance and state.street == 1 and state.actor == 0
    state = walk(state, (1, 2, 1))
    assert state.terminal and state.paid == (9, 9) and state.payoff == 9


def test_leduc_same_rank_ties_and_public_card_removal() -> None:
    state = walk(ToyState("leduc"), (0, 1, 1, 1))
    assert state.chance and state.actions == (2, 3, 4, 5)
    state = walk(state, (2, 1, 1))
    assert state.payoff == 0


def test_information_key_hides_opponent_and_remembers_actions() -> None:
    a = walk(ToyState("leduc"), (0, 1))
    b = walk(ToyState("leduc"), (0, 5))
    assert a.information == b.information
    assert a.child(1).information != b.child(1).information
    assert a.information != a.child(1).child(2).information


def test_illegal_moves_and_nonterminal_payoff() -> None:
    with pytest.raises(ValueError):
        ToyState("kuhn").child(3)
    with pytest.raises(ValueError):
        walk(ToyState("kuhn"), (0, 1)).child(0)
    with pytest.raises(ValueError):
        _ = ToyState("kuhn").payoff
