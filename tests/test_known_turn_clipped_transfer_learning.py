"""Fictional arithmetic checks for the isolated clipped-regret candidate."""

import sys
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_clipped_transfer.capture import capture_path  # noqa: E402
from known_turn_clipped_transfer.learning import RULES, train  # noqa: E402
from known_turn_clipped_transfer.proof import fictional_math  # noqa: E402
from turn_exact_transfer.capture import replay_path  # noqa: E402
from turn_exact_transfer.learning import PathSpec  # noqa: E402

from poker_ai.evaluation.opponent_learning_contexts import software_context  # noqa: E402
from poker_ai.postflop.controlled_training import (  # noqa: E402
    ControlledTrainer,
    Rules,
    expected_pass,
)
from poker_ai.postflop.river_study import Deadline  # noqa: E402


def test_clipping_changes_negative_regrets_and_preserves_work() -> None:
    tree = software_context(0).scoring["coarse"].partition
    old = ControlledTrainer(
        tree,
        Generator(PCG64(0)),
        traversal="full",
        rules=Rules("signed", "linear", "linear"),
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )
    new = ControlledTrainer(
        tree,
        Generator(PCG64(0)),
        traversal="full",
        rules=RULES,
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )
    old.initialize_exact()
    new.initialize_exact()
    np.testing.assert_array_equal(new.regrets, np.maximum(old.regrets, 0))
    np.testing.assert_array_equal(new.strategy_sum, old.strategy_sum)
    np.testing.assert_array_equal(new.current_policy, old.current_policy)
    assert new.nodes_visited == old.nodes_visited == 2 * len(tree.player)
    assert new.rng.bit_generator.state == old.rng.bit_generator.state
    updates = expected_pass(tree, old.current_policy, 0)
    from poker_ai.training.mccfr import Updates

    forced = {key: value.copy() for key, value in updates.regrets.items()}
    first = next(iter(forced))
    forced[first][:] = -1.0
    forced_updates = Updates(forced, updates.averages, updates.visited)
    old._apply(forced_updates, 0, 2)
    new._apply(forced_updates, 0, 2)
    assert np.any(old.regrets < 0)
    assert not np.any(new.regrets < 0)
    np.testing.assert_allclose(
        new.regrets, np.maximum(old.regrets, 0), rtol=0, atol=1e-12
    )
    np.testing.assert_array_equal(new.strategy_sum, old.strategy_sum)
    old.step()
    new.step()
    assert new.nodes_visited == old.nodes_visited
    tree.validate_policy(new.current_policy)
    tree.validate_policy(new.average_policy)


def test_observer_rejects_linear_rules_and_capture_replays(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    summary = capture_path(
        scoring,
        PathSpec(0, "FICTIONAL_SIGNAL_GAME", "clipped_full_exact_turn_river"),
        tmp_path / "candidate",
        "a" * 64,
        (80, 240, 720),
        Deadline(180),
    )
    assert summary["status"] == "completed"
    assert len(summary["captures"]) == 6
    assert replay_path(scoring, tmp_path / "candidate") == summary
    with pytest.raises(FileExistsError):
        capture_path(
            scoring,
            PathSpec(0, "FICTIONAL_SIGNAL_GAME", "clipped_full_exact_turn_river"),
            tmp_path / "candidate",
            "a" * 64,
            (80,),
            Deadline(180),
        )
    old = ControlledTrainer(
        scoring.partition,
        Generator(PCG64(0)),
        traversal="full",
        rules=Rules("signed", "linear", "linear"),
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )
    old.initialize_exact()
    from known_turn_clipped_transfer.learning import observe

    with pytest.raises(ValueError, match="clipped-regret"):
        observe(old, (80,), lambda *_: None, Deadline(180))


def test_train_guard_does_not_change_rng_or_state() -> None:
    tree = software_context(0).scoring["coarse"].partition
    rows: list[tuple[int, int]] = []

    def capture(point: object, solver: ControlledTrainer, _: object) -> None:
        from medium_dry_full.learning import FullPoint

        assert isinstance(point, FullPoint)
        rows.append((point.iteration, solver.nodes_visited))

    solver = train(tree, (80, 240, 720), Deadline(180), capture)
    assert rows[-1][1] >= 720
    assert solver.rng.bit_generator.state == Generator(PCG64(0)).bit_generator.state


def test_fictional_proof_checks_clipped_arithmetic() -> None:
    result = fictional_math()
    assert result["status"] == "proof_passed"
    assert result["negative_signed_entries"] > 0
    assert result["negative_clipped_entries"] == 0
    assert result["real_policy_opened"] is False
