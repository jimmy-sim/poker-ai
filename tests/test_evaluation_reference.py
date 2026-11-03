import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, new_hand
from poker_ai.evaluation.openspiel import OpenSpielBaseline
from poker_ai.training.no_limit import NoLimitRules

RULES = NoLimitRules(
    action_abstraction=ActionAbstraction(
        fractions=((1, 1),), include_minimum=False, include_all_in=True
    )
)


def test_native_root_has_no_dependence_on_synthetic_opponent_cards() -> None:
    adapter = OpenSpielBaseline(RULES, simulations=8, world_samples=4)
    state = new_hand(RULES.stacks, Deck.shuffled(Generator(PCG64(42))), button=1)
    assert state.actor is not None
    observation = state.observe(state.actor)
    unused = [c for c in range(52) if c not in observation.hole_cards]
    first = adapter.search(observation, 41, dummy=(unused[0], unused[1]))
    second = adapter.search(observation, 41, dummy=(unused[2], unused[3]))
    assert first == second
    assert adapter.search(observation, 41, dummy=(unused[0], unused[1])) == first


def test_native_replay_handles_later_street_raise_offsets() -> None:
    adapter = OpenSpielBaseline(RULES, simulations=8, world_samples=4)
    state = new_hand(RULES.stacks, Deck.shuffled(Generator(PCG64(43))), button=1)
    for action in [
        Action(ActionKind.RAISE_TO, 6),
        Action(ActionKind.CALL),
        Action(ActionKind.RAISE_TO, 12),
        Action(ActionKind.CALL),
        Action(ActionKind.CHECK),
    ]:
        state = state.apply(action)
    assert state.actor is not None
    obs = state.observe(state.actor)
    native = adapter.from_observation(obs)
    assert native.current_player() == state.actor
    assert native.to_struct().pot_size == state.pot


def test_native_matches_complete_full_world_action_and_payout_traces() -> None:
    from poker_ai.evaluation.reference_validation import validate_native_traces

    result = validate_native_traces(RULES, seed=20261127, hands=50)
    assert result["hands"] == 50
    assert result["actions"] > 50
    assert result["showdowns"] > 0 and result["folds"] > 0
    assert result["max_payout_error"] == 0


@pytest.fixture(autouse=True)
def optional_reference() -> None:
    pytest.importorskip("pyspiel")
