"""Unbiased own initialization, consistent linear weighting and resumable visits."""

from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    Weighting,
    exact_initial_expectation,
    load_learning_checkpoint,
    save_learning_checkpoint,
)
from poker_ai.toy.games import ToyState
from poker_ai.toy.tree import Tree
from poker_ai.training.mccfr import MCCFR, Updates


def test_initial_expectation_manual_kuhn_and_no_fake_sample_visits() -> None:
    tree = Tree.build("kuhn")
    solver = PostflopMCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(7)))
    before = solver.rng.bit_generator.state
    exact_initial_expectation(solver, tree)
    row = solver.rows["0:0:None:"]
    np.testing.assert_allclose(row.regrets, [-1 / 8, 1 / 8], atol=1e-15)
    np.testing.assert_allclose(row.strategy_sum, [1 / 6, 1 / 6], atol=1e-15)
    assert solver.rng.bit_generator.state == before
    assert (
        solver.iteration == 1 and solver.nodes_visited == 0 and not solver.sampled_keys
    )
    assert solver.warm_node_equivalent == 2 * len(tree.player)
    assert all(r.strategy_sum.sum() > 0 for r in solver.rows.values())
    with pytest.raises(ValueError):
        exact_initial_expectation(solver, tree)


def test_uniform_control_preserves_original_sampled_trajectory() -> None:
    original = MCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(11)))
    control = PostflopMCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(11)))
    original.train(300)
    control.train(300)
    assert original.nodes_visited == control.nodes_visited
    assert original.rows.keys() == control.rows.keys() == control.sampled_keys
    for key in original.rows:
        np.testing.assert_array_equal(
            original.rows[key].regrets, control.rows[key].regrets
        )
        np.testing.assert_array_equal(
            original.rows[key].strategy_sum, control.rows[key].strategy_sum
        )


def test_linear_weights_both_regret_and_average(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.postflop import sampling

    solver = PostflopMCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(1)), "linear")
    solver.policy("probe", (0, 1))

    def fixed_updates(
        root: object, target: int, policy: object, selector: object
    ) -> Updates:
        return (
            Updates(
                {"probe": np.array([1.0, -1.0])}, {"probe": np.array([0.5, 0.5])}, 1
            )
            if target == 0
            else Updates({}, {}, 1)
        )

    monkeypatch.setattr(sampling, "external_updates", fixed_updates)
    solver.train(2)
    np.testing.assert_array_equal(solver.rows["probe"].regrets, [3.0, -3.0])
    np.testing.assert_array_equal(solver.rows["probe"].strategy_sum, [1.5, 1.5])


@pytest.mark.parametrize("linear", [False, True])
@pytest.mark.parametrize("warm", [False, True])
def test_weighted_initialized_resume_restores_all_semantics(
    tmp_path: Path, linear: bool, warm: bool
) -> None:
    tree = Tree.build("kuhn")
    weighting: Weighting = "linear" if linear else "uniform"
    original = PostflopMCCFR(
        lambda rng: ToyState("kuhn"), Generator(PCG64(23)), weighting
    )
    if warm:
        exact_initial_expectation(original, tree)
    original.train(20)
    path = tmp_path / "own.json"
    config = {"learning": {"sampling_weighting": weighting}}
    save_learning_checkpoint(original, path, config=config, provenance={"test": True})
    restored = load_learning_checkpoint(
        path, lambda rng: ToyState("kuhn"), expected_config=config
    )
    original.train(10)
    restored.train(10)
    assert original.iteration == restored.iteration
    assert original.rng.bit_generator.state == restored.rng.bit_generator.state
    assert original.sampled_keys == restored.sampled_keys
    assert original.warm_node_equivalent == restored.warm_node_equivalent
    for key in original.rows:
        np.testing.assert_array_equal(
            original.rows[key].regrets, restored.rows[key].regrets
        )
        np.testing.assert_array_equal(
            original.rows[key].strategy_sum, restored.rows[key].strategy_sum
        )
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="metadata"):
        load_learning_checkpoint(
            path, lambda rng: ToyState("kuhn"), expected_config=config
        )
