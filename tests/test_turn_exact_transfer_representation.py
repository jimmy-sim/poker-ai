"""Exact-turn adapter invariants on already known finite input fixtures."""

import sys
from pathlib import Path

import numpy as np
import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import recall_violations
from poker_ai.postflop.tree import SpotTree
from poker_ai.training.holdem import exact_information

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from river_strength.representation import build_river_candidate  # noqa: E402
from turn_exact_transfer.learning import (  # noqa: E402
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    contract,
    paths,
)
from turn_exact_transfer.representation import exact_turn_candidate  # noqa: E402


@pytest.mark.parametrize("name", ("dev_low_oop", "dev_medium_oop"))
def test_exact_turn_only_splits_historical_turn_groups(name: str) -> None:
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{name}.json"))
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    control = build_river_candidate(source, model)
    candidate = exact_turn_candidate(source, control)
    assert candidate is not control
    assert candidate.keys == source.keys
    assert len(control.keys) <= len(candidate.keys)
    assert recall_violations(candidate) == 0
    assert recall_violations(control) == 0
    np.testing.assert_array_equal(candidate.player, control.player)
    np.testing.assert_array_equal(candidate.chance_edges, control.chance_edges)
    np.testing.assert_array_equal(candidate.terminal_values, control.terminal_values)
    seen = {4: 0, 5: 0}
    for i, node in enumerate(source.representatives):
        state = source.states[node]
        assert state.dealer is not None
        observed = state.dealer.observe(state.actor)
        seen[len(observed.board)] += 1
        assert candidate.keys[i] == exact_information(observed)
        if len(observed.board) == 5:
            assert control.keys[int(control.exact_to_abstract[i])] == candidate.keys[i]
        assert (
            control.actions[int(control.exact_to_abstract[i])] == candidate.actions[i]
        )
    assert seen[4] > 0 and seen[5] > 0


def test_adapter_rejects_control_from_another_exact_source() -> None:
    spot = load_spot(ROOT / "configs/learning-spots/dev_low_oop.json")
    source = SpotTree.build(spot)
    other = SpotTree.build(spot)
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    control = build_river_candidate(other, model)
    with pytest.raises(ValueError, match="same exact source"):
        exact_turn_candidate(source, control)


def test_frozen_grid_and_source_pins_without_selected_tree_measurement() -> None:
    plan, freeze = contract(ROOT)
    assert tuple(plan["work_labels"]) == LABELS
    assert len(freeze["spot_sha256"]) == 3
    fixed = paths()
    assert len(fixed) == 8
    assert tuple(row.game for row in fixed[::2]) == GAMES
    assert all(row.arm == CONTROL for row in fixed[::2])
    assert all(row.arm == CANDIDATE for row in fixed[1::2])
    assert all(row.seed == 0 for row in fixed)
