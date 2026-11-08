"""Toy trajectory parity: observations and suffix extraction never change learning."""

import itertools
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_math import window_mass
from poker_ai.evaluation.averaging_history_observe import HistoryPoint, observe_history
from poker_ai.postflop.node_profile import trainer
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import assert_equal, fingerprint
from poker_ai.postflop.training_isolation import sentinel_tree

CASES = list(
    itertools.product(
        ("full", "external"), ("signed", "clipped"), ("uniform", "linear")
    )
)


def cell(traversal: str, regret: str, average: str) -> dict[str, Any]:
    return dict(
        traversal=traversal,
        bridge="common",
        regret_rule=regret,
        regret_weight="linear",
        average_weight=average,
        seed=7 if traversal == "external" else None,
    )


@pytest.mark.parametrize("traversal,regret,average", CASES)
def test_observer_and_suffix_leave_exact_unobserved_toy_trajectory_unchanged(
    traversal: str, regret: str, average: str
) -> None:
    tree = sentinel_tree()
    case = cell(traversal, regret, average)
    engine = "nodes" if traversal == "external" else "parent"
    plain, observed = trainer(tree, case, engine), trainer(tree, case, engine)
    plain.initialize_exact()
    observed.initialize_exact()
    initial = observed.nodes_visited
    labels = [initial + k for k in (1, 91, 513, 1025)]
    points: list[HistoryPoint] = []
    observe_history(
        observed,
        labels,
        np.zeros(len(tree.keys), dtype=np.bool_),
        points.append,
        Deadline(5),
    )
    expected = {p.observation.iteration: p for p in points}
    while plain.iteration < observed.iteration:
        plain.step()
        if plain.iteration in expected:
            point = expected[plain.iteration]
            assert point.observation.state_sha256 == fingerprint(plain)
            assert point.observation.total_work == plain.nodes_visited
            assert point.current.tobytes() == plain.current_policy.tobytes()
            assert point.cumulative_average.tobytes() == plain.strategy_sum.tobytes()
    assert_equal(plain, observed)
    assert sorted(t for p in points for _, t in p.observation.labels) == labels
    for point in points:
        assert not point.current.flags.writeable
        assert not point.cumulative_average.flags.writeable
        assert not np.shares_memory(point.cumulative_average, observed.strategy_sum)
        for _, threshold in point.observation.labels:
            assert (
                point.observation.previous_work
                < threshold
                <= point.observation.total_work
            )
    before = fingerprint(observed)
    mass = window_mass(
        tree, points[0].cumulative_average, points[-1].cumulative_average
    )
    tree.validate_policy(tree.normalize(mass))
    assert fingerprint(observed) == before
    # The independently frozen dense backend must reach the same exact endpoint.
    dense = trainer(tree, case, "parent")
    dense.initialize_exact()
    while dense.iteration < observed.iteration:
        dense.step()
    assert_equal(dense, observed)


@pytest.mark.parametrize(
    "traversal,regret",
    list(itertools.product(("full", "external"), ("signed", "clipped"))),
)
def test_current_paths_match_across_average_weights_at_every_observation(
    traversal: str, regret: str
) -> None:
    tree = sentinel_tree()
    engine = "nodes" if traversal == "external" else "parent"
    histories = []
    for average in ("uniform", "linear"):
        solver = trainer(tree, cell(traversal, regret, average), engine)
        solver.initialize_exact()
        points: list[HistoryPoint] = []
        observe_history(
            solver,
            [solver.nodes_visited + k for k in (1, 201, 1001)],
            np.zeros(len(tree.keys), dtype=np.bool_),
            points.append,
            Deadline(5),
        )
        histories.append((solver, points))
    a, b = histories
    assert len(a[1]) == len(b[1])
    for first, second in zip(a[1], b[1], strict=True):
        assert first.current.tobytes() == second.current.tobytes()
        assert first.learning_path_sha256 == second.learning_path_sha256
        assert first.observation.iteration == second.observation.iteration
        assert first.observation.total_work == second.observation.total_work
    for name in ("regrets", "current_policy"):
        assert getattr(a[0], name).tobytes() == getattr(b[0], name).tobytes()
    assert a[0].sampled_keys == b[0].sampled_keys
    assert a[0].rng.bit_generator.state == b[0].rng.bit_generator.state
    assert a[0].strategy_sum.tobytes() != b[0].strategy_sum.tobytes()


@pytest.mark.parametrize(
    "mutation", ["regrets", "average", "rng", "keys", "work", "iteration"]
)
def test_frozen_outer_guard_rejects_mutation_in_a_history_callback(
    mutation: str,
) -> None:
    tree = sentinel_tree()
    solver = trainer(tree, cell("external", "signed", "linear"), "nodes")
    solver.initialize_exact()

    def corrupt(point: HistoryPoint) -> None:
        if mutation == "regrets":
            solver.regrets[0, 0] += 1
        elif mutation == "average":
            solver.strategy_sum[0, 0] += 1
        elif mutation == "rng":
            solver.rng.random()
        elif mutation == "keys":
            solver.sampled_keys.add("deliberate-corruption")
        elif mutation == "work":
            solver.nodes_visited += 1
        else:
            solver.iteration += 1

    with pytest.raises(ArithmeticError, match="mutated training state"):
        observe_history(
            solver,
            [solver.nodes_visited + 1],
            np.zeros(len(tree.keys), dtype=np.bool_),
            corrupt,
            Deadline(5),
        )


@pytest.mark.parametrize("traversal,regret,average", CASES)
def test_suffix_equals_sum_of_actual_later_weighted_increments(
    traversal: str, regret: str, average: str
) -> None:
    tree = sentinel_tree()
    case = cell(traversal, regret, average)
    solver = trainer(tree, case, "nodes" if traversal == "external" else "parent")
    solver.initialize_exact()
    while solver.iteration < 16:
        solver.step()
    cutoff = solver.strategy_sum.copy()
    increments = []
    while solver.iteration < 32:
        before = solver.strategy_sum.copy()
        solver.step()
        increments.append(solver.strategy_sum - before)
    mass = window_mass(tree, cutoff, solver.strategy_sum)
    np.testing.assert_allclose(mass, np.sum(increments, axis=0), rtol=0, atol=1e-12)
