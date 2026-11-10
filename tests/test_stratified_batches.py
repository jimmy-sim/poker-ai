"""Independent trajectory oracle and final-callback/state mutation checks."""

import copy
from dataclasses import replace
from typing import Any

import numpy as np
import pytest
from numpy.random import default_rng

from poker_ai.evaluation.private_prefix_oracle import DenseOracle, parity
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint
from poker_ai.postflop.frozen_batches import guard as old_guard
from poker_ai.postflop.private_prefix import PrefixPlan
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.stratified_batches import StratifiedBatchTrainer, guard, observe
from poker_ai.postflop.training_isolation import sentinel_tree
from poker_ai.toy.tree import Tree


def solver(batch: int = 4) -> StratifiedBatchTrainer:
    result = StratifiedBatchTrainer(sentinel_tree(), default_rng(7), batch_size=batch)
    result.initialize_exact()
    return result


def test_independent_full_warm_traversal_updater_and_joint_selector_all_endpoints() -> (
    None
):
    rows = parity()
    assert len(rows) == 120
    assert sum(r["B1_original_bit_match"] for r in rows) == 40
    assert max(r["maximum_array_error"] for r in rows) <= 1e-12
    assert {r["iteration"] for r in rows} == {1, 2, 3, 8, 17}
    assert {r["regret_weight"] for r in rows} == {"uniform", "linear"}


def test_oracle_does_not_call_production_traversal_sampler_or_updater(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("oracle called shared production arithmetic")

    monkeypatch.setattr("poker_ai.training.mccfr.external_updates", forbidden)
    monkeypatch.setattr(
        "poker_ai.postflop.controlled_training.expected_pass", forbidden
    )
    monkeypatch.setattr(
        "poker_ai.postflop.controlled_training.ControlledTrainer._apply", forbidden
    )
    monkeypatch.setattr(PrefixPlan, "build", forbidden)
    oracle = DenseOracle(sentinel_tree(), 7, Rules("clipped", "linear", "linear"))
    for _ in range(16):
        oracle.step(4)
    assert oracle.iteration == 17 and oracle.nodes > 100


@pytest.mark.parametrize("game", ["kuhn", "leduc"])
def test_B1_exact_delegation_bypasses_prefix_plan_and_retains_every_old_guard(
    game: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("B1 attempted a private prefix plan")

    monkeypatch.setattr(PrefixPlan, "build", forbidden)
    tree = Tree.build(game)
    new = StratifiedBatchTrainer(tree, default_rng(19), batch_size=1)
    old = ReducedDispatchBatchTrainer(tree, default_rng(19), batch_size=1)
    new.initialize_exact()
    old.initialize_exact()
    for _ in range(20):
        assert old_guard(new) == old_guard(old)
        assert new.prefix_plan is None
        new.step()
        old.step()


@pytest.mark.parametrize("batch", [True, 0, -1, 1.0, 2**53 + 1])
def test_bad_batch_size_before_any_rng_draw(batch: Any) -> None:
    rng = default_rng(7)
    before = copy.deepcopy(rng.bit_generator.state)
    with pytest.raises(ValueError):
        StratifiedBatchTrainer(sentinel_tree(), rng, batch_size=batch)
    assert before == rng.bit_generator.state


def test_prefix_setup_no_randomness_warm_cost_and_independent_ledger_exports() -> None:
    rng = default_rng(7)
    before = copy.deepcopy(rng.bit_generator.state)
    own = StratifiedBatchTrainer(sentinel_tree(), rng, batch_size=4)
    assert own.prefix_setup_seconds >= 0
    assert own.iteration == own.nodes_visited == 0
    own.initialize_exact()
    assert own.initialization_visits == own.nodes_visited == 2 * len(own.tree.player)
    assert before == rng.bit_generator.state
    for weight in ("uniform", "linear"):
        exported = own.ledger(weight)
        assert not exported.flags.writeable
        exported.flags.writeable = True
        exported[:] = 99
        assert not np.array_equal(exported, own.ledger(weight))
    np.testing.assert_array_equal(own.warm_sum, own.strategy_sum)
    with pytest.raises(ValueError):
        own.initialize_exact()


@pytest.mark.parametrize(
    "mutation",
    [
        "regrets",
        "strategy_sum",
        "uniform_sum",
        "warm_sum",
        "rng",
        "keys",
        "nodes_visited",
        "iteration",
        "sampled_traversals",
        "row_evaluations",
        "last_pass_rows",
        "batch_size",
        "rules",
        "prefix_plan",
        "plan_internal",
    ],
)
def test_last_callback_guard_catches_plan_and_all_old_state(mutation: str) -> None:
    own = solver()

    def capture(point: BatchPoint) -> None:
        assert point.guard_sha256 == guard(own)
        if mutation in ("regrets", "strategy_sum", "uniform_sum", "warm_sum"):
            getattr(own, mutation)[0, 0] += 1
        elif mutation == "rng":
            own.rng.random()
        elif mutation == "keys":
            own.sampled_keys.add("corrupt")
        elif mutation == "last_pass_rows":
            own.last_pass_rows = (999, 999)
        elif mutation == "rules":
            own.rules = Rules("clipped", "linear", "linear")
        elif mutation in ("prefix_plan", "plan_internal"):
            assert own.prefix_plan is not None
            if mutation == "prefix_plan":
                own.prefix_plan = replace(own.prefix_plan, root_node=999)
            else:
                object.__setattr__(own.prefix_plan, "cdf", (0.1, 0.9, 1))
        else:
            setattr(own, mutation, getattr(own, mutation) + 1)

    with pytest.raises(ArithmeticError, match="observer mutated"):
        observe(own, [own.nodes_visited], capture, Deadline(5))


def test_observer_preserves_trajectory_and_charges_first_crossings() -> None:
    observed, plain = solver(), solver()
    initial = observed.nodes_visited
    points: list[BatchPoint] = []
    observe(observed, [initial, initial + 1, initial + 777], points.append, Deadline(5))
    while plain.iteration < observed.iteration:
        plain.step()
    assert guard(plain) == guard(observed)
    assert points[0].total_work == initial
    assert tuple(label for p in points for label in p.labels) == (
        initial,
        initial + 1,
        initial + 777,
    )
    assert all(
        p.previous_work < label <= p.total_work for p in points for label in p.labels
    )
    assert (
        points[-1].last_iteration_visits
        == points[-1].total_work - points[-1].previous_work
    )
    assert observed.sampled_traversals == 2 * 4 * (observed.iteration - 1)


def test_missing_plan_and_invalid_labels_fail_without_training() -> None:
    own = solver()
    before = old_guard(own)
    own.prefix_plan = None
    with pytest.raises(ArithmeticError, match="requires.*plan"):
        own.step()
    assert before == old_guard(own)
    for labels in ([], [True], [2, 1], [1, 1]):
        with pytest.raises(ValueError):
            observe(own, labels, lambda _: None, Deadline(5))
    assert before == old_guard(own)
