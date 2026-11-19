"""River-exact candidate keeps q8 earlier and only acting legal information later."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.range_mass import RangeMassAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree, observation_key, recall_violations
from poker_ai.postflop.range_protocol import (
    RIVER_CANDIDATE,
    build_representation_control,
    range_context,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.training.holdem import exact_information

ROOT = Path(__file__).resolve().parents[1]
SPOTS = ("dev_low_oop", "dev_medium_oop")


@pytest.mark.parametrize("name", SPOTS)
def test_river_candidate_is_q8_before_river_and_exact_on_river(name: str) -> None:
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{name}.json"))
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    control = build_representation_control(source, "texture_range_q8_b8", model)
    candidate = build_representation_control(source, RIVER_CANDIDATE, model)
    exact = MatrixTree.build(source)
    seen = {4: 0, 5: 0}
    for i, node in enumerate(source.representatives):
        state = source.states[node]
        assert state.dealer is not None
        observed = state.dealer.observe(state.actor)
        assert observed.seat == observed.actor == state.actor
        key = candidate.keys[int(candidate.exact_to_abstract[i])]
        if len(observed.board) == 5:
            seen[5] += 1
            assert key == exact_information(observed)
            assert key == exact.keys[i]
        else:
            seen[4] += 1
            assert len(observed.board) == 4
            assert key == control.keys[int(control.exact_to_abstract[i])]
    assert seen[4] > 0 and seen[5] > 0
    assert len(control.keys) <= len(candidate.keys) <= len(exact.keys)
    assert recall_violations(candidate) == 0
    np.testing.assert_array_equal(candidate.player, control.player)
    np.testing.assert_array_equal(candidate.valid, control.valid)
    np.testing.assert_array_equal(candidate.chance_edges, control.chance_edges)


def test_river_key_uses_observation_not_hidden_opponent() -> None:
    spot = load_spot(ROOT / "configs/learning-spots/dev_low_oop.json")
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    encoder = RangeMassAbstraction(model, range_context(spot))
    source = SpotTree.build(spot)
    river = [
        (state.dealer.observe(state.actor), state.dealer.hole_cards[1 - state.actor])
        for state in source.states
        if not state.chance
        and not state.terminal
        and state.dealer is not None
        and len(state.dealer.board) == 5
    ]
    own, first_hidden = river[0]
    hidden = next(
        observed
        for observed, opponent in river
        if observed == own and opponent != first_hidden
    )
    changed_river = next(
        observed
        for observed, _ in river
        if observed.hole_cards == own.hole_cards
        and observed.actor == own.actor
        and observed.history == own.history
        and observed.board != own.board
    )
    assert observation_key(own, RIVER_CANDIDATE, encoder) == observation_key(
        hidden, RIVER_CANDIDATE, encoder
    )
    assert observation_key(own, RIVER_CANDIDATE, encoder) != observation_key(
        changed_river, RIVER_CANDIDATE, encoder
    )
    with pytest.raises(ValueError, match="acting player"):
        observation_key(replace(own, seat=1 - own.seat), RIVER_CANDIDATE, encoder)
    with pytest.raises(ValueError, match="acting player"):
        observation_key(replace(own, terminal=True), RIVER_CANDIDATE, encoder)
