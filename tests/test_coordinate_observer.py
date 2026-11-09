"""Independent unobserved trajectories and exact complete-step event locations."""

from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.coordinate_observer import CoordinatePoint, observe
from poker_ai.postflop.frozen_batches import guard
from poker_ai.postflop.frozen_batches import observe as observe_work
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.training_isolation import sentinel_tree


def learner(batch: int = 4, clipped: bool = False) -> ReducedDispatchBatchTrainer:
    solver = ReducedDispatchBatchTrainer(
        sentinel_tree(),
        Generator(PCG64(7)),
        batch_size=batch,
        rules=Rules("clipped" if clipped else "signed", "linear", "linear"),
    )
    solver.initialize_exact()
    return solver


@pytest.mark.parametrize("batch", [1, 4, 16])
@pytest.mark.parametrize("clipped", [False, True])
def test_combined_observer_matches_independent_unobserved_steps(
    batch: int,
    clipped: bool,
) -> None:
    direct = learner(batch, clipped)
    trace = {1: (direct.nodes_visited, guard(direct))}
    for _ in range(15):
        direct.step()
        trace[direct.iteration] = (direct.nodes_visited, guard(direct))
    initial = trace[1][0]
    labels = sorted({initial - 1, initial, initial + 1, trace[7][0], trace[16][0]})
    target_iterations = [1, 2, 7, 16]
    # Independent first-crossing table from the separate uninterrupted trajectory.
    crossings = {
        label: next(i for i in trace if trace[i][0] >= label) for label in labels
    }
    actual = learner(batch, clipped)
    points: list[CoordinatePoint] = []
    observe(
        actual,
        iterations=target_iterations,
        work=labels,
        capture=points.append,
        deadline=Deadline(30),
    )
    assert [p.iteration for p in points] == sorted(
        set(target_iterations + list(crossings.values()))
    )
    for point in points:
        assert point.iteration_labels == tuple(
            i for i in target_iterations if i == point.iteration
        )
        assert point.work_labels == tuple(
            x for x in labels if crossings[x] == point.iteration
        )
        assert point.guard_sha256 == trace[point.iteration][1]
        assert point.total_work == trace[point.iteration][0]
        previous = 0 if point.iteration == 1 else trace[point.iteration - 1][0]
        assert point.previous_work == previous
        assert point.last_iteration_visits == point.total_work - previous
    assert guard(actual) == guard(direct)
    np.testing.assert_array_equal(actual.current_policy, direct.current_policy)
    np.testing.assert_array_equal(actual.ledger("linear"), direct.ledger("linear"))
    np.testing.assert_array_equal(actual.ledger("uniform"), direct.ledger("uniform"))


def test_work_only_is_exactly_the_original_observer() -> None:
    a, b = learner(), learner()
    labels = [a.nodes_visited + 1, a.nodes_visited + 100, a.nodes_visited + 300]
    old: list[Any] = []
    new: list[CoordinatePoint] = []
    observe_work(a, labels, old.append, Deadline(30))
    observe(b, iterations=[], work=labels, capture=new.append, deadline=Deadline(30))
    assert guard(a) == guard(b)
    assert [(p.labels, p.iteration, p.guard_sha256) for p in old] == [
        (p.work_labels, p.iteration, p.guard_sha256) for p in new
    ]


@pytest.mark.parametrize("labels", [[True], [0], [-1], [2, 2], [3, 2], [1.0]])
@pytest.mark.parametrize("axis", ["iterations", "work"])
def test_invalid_coordinate_labels_rejected(labels: list[Any], axis: str) -> None:
    values: dict[str, list[Any]] = dict(iterations=[], work=[])
    values[axis] = labels
    with pytest.raises(ValueError):
        observe(learner(), **values, capture=lambda _: None, deadline=Deadline(30))


def test_empty_or_nonfresh_observation_rejected() -> None:
    a = learner()
    with pytest.raises(ValueError):
        observe(
            a, iterations=[], work=[], capture=lambda _: None, deadline=Deadline(30)
        )
    a.step()
    with pytest.raises(ValueError):
        observe(
            a, iterations=[3], work=[], capture=lambda _: None, deadline=Deadline(30)
        )


@pytest.mark.parametrize(
    "field", ["regrets", "strategy_sum", "uniform_sum", "warm_sum", "rng", "counter"]
)
def test_callback_cannot_mutate_either_book_rng_regrets_or_work(field: str) -> None:
    a = learner()

    def corrupt(_: CoordinatePoint) -> None:
        if field == "rng":
            a.rng.random()
        elif field == "counter":
            a.nodes_visited += 1
        else:
            getattr(a, field)[0, 0] += 1

    with pytest.raises(ArithmeticError, match="mutated"):
        observe(a, iterations=[1], work=[], capture=corrupt, deadline=Deadline(30))


def test_last_capture_cannot_escape_stage_deadline() -> None:
    deadline = Deadline(30)

    def expire(_: CoordinatePoint) -> None:
        deadline.started -= 31

    with pytest.raises(TimeoutError):
        observe(learner(), iterations=[1], work=[], capture=expire, deadline=deadline)


def test_capture_exception_propagates_without_another_training_step() -> None:
    a = learner()
    before = guard(a)

    def fail(_: CoordinatePoint) -> None:
        raise RuntimeError("retain interrupted capture")

    with pytest.raises(RuntimeError, match="interrupted"):
        observe(a, iterations=[1, 2], work=[], capture=fail, deadline=Deadline(30))
    assert guard(a) == before
