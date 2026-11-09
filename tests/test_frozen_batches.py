"""Independent tiny-game arithmetic, trajectory, alias and observation contracts."""

import copy
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.evaluation.frozen_batch_math import proofs
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.frozen_batch_software import parity
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import (
    BatchPoint,
    FrozenBatchTrainer,
    guard,
    mean_updates,
    observe,
)
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.training_isolation import sentinel_tree
from poker_ai.training.mccfr import Updates


def learner(batch: int = 4) -> FrozenBatchTrainer:
    result = FrozenBatchTrainer(sentinel_tree(), Generator(PCG64(7)), batch_size=batch)
    result.initialize_exact()
    return result


def test_sparse_mean_counts_missing_as_zero_and_charges_every_visit() -> None:
    a = Updates({"a": np.array([-2.0, 2.0])}, {"x": np.array([0.25, 0.75])}, 7)
    b = Updates({"b": np.array([4.0, -4.0])}, {"x": np.array([0.75, 0.25])}, 11)
    before = copy.deepcopy([a, b])
    result = mean_updates(iter([a, b]), 2)
    assert result.visited == 18
    np.testing.assert_array_equal(result.regrets["a"], [-1, 1])
    np.testing.assert_array_equal(result.regrets["b"], [2, -2])
    np.testing.assert_array_equal(result.averages["x"], [0.5, 0.5])
    for actual, old in zip((a, b), before, strict=True):
        for key in old.regrets:
            np.testing.assert_array_equal(actual.regrets[key], old.regrets[key])
            assert not np.shares_memory(result.regrets[key], actual.regrets[key])
    result.averages["x"][:] = 99
    np.testing.assert_array_equal(a.averages["x"], [0.25, 0.75])


@pytest.mark.parametrize("count", [0, -1, True, 1.0])
def test_invalid_batch_count(count: Any) -> None:
    with pytest.raises(ValueError):
        mean_updates([], count)
    with pytest.raises(ValueError):
        FrozenBatchTrainer(sentinel_tree(), Generator(PCG64(7)), batch_size=count)


@pytest.mark.parametrize(
    "samples,count",
    [
        ([], 1),
        ([Updates({}, {}, 1)], 2),
        ([Updates({}, {}, 1)] * 2, 1),
        ([Updates({}, {}, 0)], 1),
        ([Updates({}, {}, True)], 1),
        ([Updates({"a": np.array([np.nan])}, {}, 1)], 1),
        ([Updates({}, {"a": np.array([-1.0])}, 1)], 1),
        ([Updates({"a": np.array([[1.0]])}, {}, 1)], 1),
        (
            [
                Updates({"a": np.array([1.0])}, {}, 1),
                Updates({"a": np.array([1.0, 2.0])}, {}, 1),
            ],
            2,
        ),
    ],
)
def test_reject_incomplete_or_invalid_raw_samples(
    samples: list[Updates], count: int
) -> None:
    with pytest.raises(ValueError):
        mean_updates(samples, count)


def test_clip_after_mean_is_not_average_of_clips() -> None:
    values = [np.array([-2.0, 2.0]), np.array([2.0, -2.0])]
    result = mean_updates([Updates({"a": v}, {}, 1) for v in values], 2)
    np.testing.assert_array_equal(np.maximum(result.regrets["a"], 0), [0, 0])
    np.testing.assert_array_equal(sum(np.maximum(v, 0) for v in values) / 2, [1, 1])


def test_exact_conditional_moments_and_clipping_noncommutation() -> None:
    rows = proofs()
    assert sum(r["single_tapes"] for r in rows) == 54
    assert sum(r["independent_pair_tapes"] for r in rows) == 972
    assert all(r["variance_halving_error"] <= 1e-12 for r in rows)
    assert any(r["maximum_expected_clip_vs_clip_expected"] > 0.04 for r in rows)


def test_dual_B1_old_paths_and_all_batches_independent_dense_reference() -> None:
    rows = parity()
    assert len(rows) == 120
    assert sum(r["old_B1_bit_match"] for r in rows) == 40
    assert {r["batch_size"] for r in rows} == {1, 4, 16}


def test_warm_mass_derivation_and_readout_exports_do_not_alias() -> None:
    solver = learner()
    np.testing.assert_array_equal(warm_mass(solver.tree), solver.warm_sum)
    for weight in ("uniform", "linear"):
        mass = solver.ledger(weight)
        assert not mass.flags.writeable
        mass.flags.writeable = True
        mass[:] = 17
        assert not np.array_equal(mass, solver.uniform_sum)
    with pytest.raises(ValueError):
        solver.ledger("bogus")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        learner().initialize_exact()
    with pytest.raises(ValueError):
        FrozenBatchTrainer(
            solver.tree, Generator(PCG64(7)), batch_size=1, rules=Rules()
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "uniform_sum",
        "warm_sum",
        "regrets",
        "strategy_sum",
        "rng",
        "keys",
        "work",
        "row_evaluations",
        "sampled_traversals",
        "batch_size",
        "rules",
    ],
)
def test_observer_guards_both_books_raw_state_rng_and_counters(mutation: str) -> None:
    solver = learner()

    def capture(point: BatchPoint) -> None:
        if mutation in ("uniform_sum", "warm_sum", "regrets", "strategy_sum"):
            getattr(solver, mutation)[0, 0] += 1
        elif mutation == "rng":
            solver.rng.random()
        elif mutation == "keys":
            solver.sampled_keys.add("invalid")
        elif mutation == "work":
            solver.nodes_visited += 1
        elif mutation == "rules":
            solver.rules = Rules("clipped", "uniform", "linear")
        else:
            setattr(solver, mutation, getattr(solver, mutation) + 1)

    with pytest.raises(ArithmeticError, match="observer mutated"):
        observe(solver, [solver.nodes_visited], capture, Deadline(5))


@pytest.mark.parametrize("batch", [1, 4, 16])
def test_observed_and_unobserved_paths_are_identical(batch: int) -> None:
    a, b = learner(batch), learner(batch)
    target = a.nodes_visited + 300
    points: list[BatchPoint] = []
    observe(a, [1, a.nodes_visited, target], points.append, Deadline(5))
    while b.nodes_visited < target:
        b.step()
    assert guard(a) == guard(b)
    assert points[0].previous_work == 0
    assert points[0].labels == (1, a.initialization_visits)
    last = points[-1]
    assert last.previous_work < target <= last.total_work
    assert last.last_iteration_visits == last.total_work - last.previous_work
    assert a.sampled_traversals == 2 * batch * (a.iteration - 1)


@pytest.mark.parametrize("labels", [[], [2, 1], [1, 1], [True], [0]])
def test_observer_rejects_ambiguous_labels(labels: list[Any]) -> None:
    with pytest.raises(ValueError):
        observe(learner(), labels, lambda p: None, Deadline(5))


def test_rejected_owner_update_mutates_neither_book() -> None:
    solver = learner()
    i = next(i for i, p in enumerate(solver.tree.owners) if p == 1)
    before = guard(solver)
    with pytest.raises(ValueError):
        solver._apply(
            Updates({solver.tree.keys[i]: np.ones(len(solver.tree.actions[i]))}, {}, 1),
            0,
            2,
        )
    assert guard(solver) == before
