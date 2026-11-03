"""Public shadow histories reconcile without mutating the real chip ledger."""

from dataclasses import replace

import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.shadow import reconcile
from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, HoldemState, Observation, new_hand
from poker_ai.training.no_limit import NoLimitRules


def observed(state: HoldemState) -> Observation:
    assert state.actor is not None
    return state.observe(state.actor)


def raised(total: int, *, button: int = 1) -> HoldemState:
    state = new_hand((200, 200), Deck.shuffled(Generator(PCG64(42))), button=button)
    return state.apply(Action(ActionKind.RAISE_TO, total))


def test_on_grid_shadow_is_identical_to_actual_observation() -> None:
    state = raised(6).apply(Action(ActionKind.CALL))
    state = state.apply(Action(ActionKind.RAISE_TO, 6)).apply(Action(ActionKind.CALL))
    obs = observed(state)
    result = reconcile(obs, NoLimitRules(), episode_seed=5)
    assert result.failure is None and result.observation == obs
    assert all(r.actual_total == r.virtual_total for r in result.raises)


def test_off_grid_history_uses_separate_virtual_ledger() -> None:
    state = raised(7).apply(Action(ActionKind.CALL))
    obs = observed(state)
    result = reconcile(obs, NoLimitRules(), episode_seed=5, scheme="nearest")
    assert result.failure is None and result.observation is not None
    assert result.observation.pot == 12 and obs.pot == 14
    assert result.raises[0].virtual_total == 6
    assert result.observation.hole_cards == obs.hole_cards
    assert result.observation.board == obs.board
    assert observed(state) == obs  # Actual state was never modified.


def test_mapping_coin_is_consistent_for_the_same_earlier_prefix() -> None:
    state = raised(7)
    first = reconcile(observed(state), NoLimitRules(), episode_seed=99)
    state = state.apply(Action(ActionKind.CALL))
    later = reconcile(observed(state), NoLimitRules(), episode_seed=99)
    assert first.raises == later.raises
    changed_hole = replace(observed(state), hole_cards=(0, 1))
    assert (
        reconcile(changed_hole, NoLimitRules(), episode_seed=99).raises == later.raises
    )


def test_button_rotation_maps_player_roles_and_keeps_own_cards() -> None:
    state = raised(6, button=0).apply(Action(ActionKind.CALL))
    obs = observed(state)
    result = reconcile(obs, NoLimitRules(), episode_seed=7)
    assert result.failure is None and result.observation is not None
    assert result.observation.button == 1 and result.observation.seat == 0
    assert obs.seat == 1 and result.observation.hole_cards == obs.hole_cards
    assert not result.starting_stack_mismatch


def test_irreconcilable_virtual_all_in_is_explicit_failure() -> None:
    state = raised(150).apply(Action(ActionKind.CALL))
    obs = observed(state)
    result = reconcile(obs, NoLimitRules(), episode_seed=5, scheme="nearest")
    assert result.observation is None and result.failure is not None
    assert "terminated" in result.failure
    assert not state.terminal and state.stacks == (50, 50)


def test_inconsistent_public_action_cost_is_an_error() -> None:
    obs = observed(raised(7))
    history = (replace(obs.history[0], chips_paid=999),)
    with pytest.raises(ValueError, match="chip cost"):
        reconcile(replace(obs, history=history), NoLimitRules(), episode_seed=5)
