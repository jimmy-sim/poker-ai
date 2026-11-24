"""Fictional full-pass checks for one isolated signed-regret discount."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_regret_recency.capture import capture_path  # noqa: E402
from known_turn_regret_recency.learning import RecencyTrainer  # noqa: E402
from turn_exact_transfer.capture import replay_path  # noqa: E402
from turn_exact_transfer.learning import PathSpec  # noqa: E402

from poker_ai.evaluation.opponent_learning_contexts import software_context  # noqa: E402
from poker_ai.finite import ArrayTree  # noqa: E402
from poker_ai.postflop.controlled_training import (  # noqa: E402
    ControlledTrainer,
    Rules,
    expected_pass,
)
from poker_ai.postflop.river_study import Deadline  # noqa: E402
from poker_ai.training.mccfr import Updates  # noqa: E402


def fictional_tree() -> ArrayTree:
    """Return the existing fictional finite game, never a poker study input."""
    return software_context(0).scoring["coarse"].partition


def control(tree: ArrayTree) -> ControlledTrainer:
    """Historical signed/linear full learner on the same fictional tree."""
    return ControlledTrainer(
        tree,
        Generator(PCG64(0)),
        traversal="full",
        rules=Rules("signed", "linear", "linear"),
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )


def test_exact_initialization_and_rng_are_unchanged() -> None:
    tree = fictional_tree()
    old = control(tree)
    candidate = RecencyTrainer(tree, Generator(PCG64(0)))
    old.initialize_exact()
    candidate.initialize_exact()
    np.testing.assert_array_equal(candidate.regrets, old.regrets)
    np.testing.assert_array_equal(candidate.strategy_sum, old.strategy_sum)
    np.testing.assert_array_equal(candidate.current_policy, old.current_policy)
    assert candidate.iteration == old.iteration == 1
    assert candidate.nodes_visited == old.nodes_visited == 2 * len(old.tree.player)
    assert candidate.rng.bit_generator.state == old.rng.bit_generator.state


def test_discount_only_owned_signed_legal_regrets_after_warm() -> None:
    tree = fictional_tree()
    candidate = RecencyTrainer(tree, Generator(PCG64(0)))
    i = next(
        i
        for i, actions in enumerate(candidate.tree.actions)
        if candidate.tree.owners[i] == 0 and len(actions) >= 2
    )
    other = next(i for i, owner in enumerate(candidate.tree.owners) if owner == 1)
    candidate.regrets[i, :2] = [3.0, -4.0]
    candidate.regrets[other, 0] = 7.0
    candidate._apply(Updates({}, {}), 0, 2)
    factor = 2.0**1.5 / (1.0 + 2.0**1.5)
    np.testing.assert_allclose(candidate.regrets[i, :2], [3.0 * factor, -2.0])
    assert candidate.regrets[other, 0] == 7.0
    assert np.all(candidate.regrets[candidate.tree.legal == 0.0] == 0.0)
    assert np.all(candidate.strategy_sum == 0.0)


def test_normal_full_pass_update_differs_only_by_fixed_discount() -> None:
    tree = fictional_tree()
    old = control(tree)
    candidate = RecencyTrainer(tree, Generator(PCG64(0)))
    old.initialize_exact()
    candidate.initialize_exact()
    before_rng = candidate.rng.bit_generator.state
    updates = expected_pass(old.tree, old.current_policy, 0)
    old._apply(updates, 0, 2)
    candidate._apply(updates, 0, 2)
    expected = old.regrets.copy()
    owned = old.tree.owners == 0
    values = expected[owned]
    factor = 2.0**1.5 / (1.0 + 2.0**1.5)
    expected[owned] = values * np.where(values >= 0.0, factor, 0.5)
    np.testing.assert_allclose(candidate.regrets, expected, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(candidate.strategy_sum, old.strategy_sum)
    assert candidate.rng.bit_generator.state == before_rng
    fresh_old = control(tree)
    fresh_candidate = RecencyTrainer(tree, Generator(PCG64(0)))
    fresh_old.initialize_exact()
    fresh_candidate.initialize_exact()
    fresh_old.step()
    fresh_candidate.step()
    assert fresh_candidate.nodes_visited == fresh_old.nodes_visited
    assert fresh_old.nodes_visited == 4 * len(tree.player)
    assert fresh_candidate.iteration == fresh_old.iteration == 2
    tree.validate_policy(fresh_candidate.current_policy)
    tree.validate_policy(fresh_candidate.average_policy)


def test_fictional_capture_replays_and_refuses_overwrite(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    spec = PathSpec(0, "FICTIONAL_SIGNAL_GAME", "signed_full_exact_turn_regret_recency")
    folder = tmp_path / "candidate"
    summary = capture_path(
        scoring, spec, folder, "a" * 64, (80, 240, 720), Deadline(180)
    )
    assert summary["status"] == "completed"
    assert len(summary["captures"]) == 6
    assert [row["metadata"]["work_label"] for row in summary["captures"]] == [
        80,
        80,
        240,
        240,
        720,
        720,
    ]
    assert replay_path(scoring, folder) == summary
    before = (folder / "summary.json").read_bytes()
    with pytest.raises(FileExistsError, match="exists"):
        capture_path(scoring, spec, folder, "a" * 64, (80, 240, 720), Deadline(180))
    assert (folder / "summary.json").read_bytes() == before
    assert json.loads(before)["binding"] == "a" * 64
