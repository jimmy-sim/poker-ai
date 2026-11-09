"""Observe exact update counts and first work crossings without changing learning."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from poker_ai.postflop.frozen_batches import FrozenBatchTrainer, guard
from poker_ai.postflop.river_study import Deadline


@dataclass(frozen=True)
class CoordinatePoint:
    iteration_labels: tuple[int, ...]
    work_labels: tuple[int, ...]
    iteration: int
    previous_work: int
    total_work: int
    last_iteration_visits: int
    guard_sha256: str


def _labels(values: Sequence[int]) -> list[int]:
    result = list(values)
    if any(type(x) is not int or x <= 0 for x in result) or result != sorted(
        set(result)
    ):
        raise ValueError("observation labels must be sorted unique positive integers")
    return result


def observe(
    solver: FrozenBatchTrainer,
    *,
    iterations: Sequence[int],
    work: Sequence[int],
    capture: Callable[[CoordinatePoint], None],
    deadline: Deadline,
) -> None:
    """Warm start counts as iteration1; captures follow whole two-target steps.

    A work label is captured at its first complete iteration crossing. If exact
    iteration and work labels coincide, one callback receives both coordinates.
    The original comprehensive guard includes both ledgers, RNG and counters.
    No sampling, weighting or state-update operation is added or reordered.
    """
    pending_iteration, pending_work = _labels(iterations), _labels(work)
    if (
        not (pending_iteration or pending_work)
        or solver.iteration != 1
        or solver.nodes_visited != solver.initialization_visits
    ):
        raise ValueError("coordinate observer requires fresh exact initialization")
    previous, last = 0, solver.nodes_visited
    while pending_iteration or pending_work:
        deadline.check()
        at_iteration = tuple(x for x in pending_iteration if x == solver.iteration)
        at_work = tuple(x for x in pending_work if x <= solver.nodes_visited)
        if any(x < solver.iteration for x in pending_iteration) or any(
            x <= previous for x in at_work
        ):
            raise ArithmeticError("missed exact iteration or first work crossing")
        if at_iteration or at_work:
            before = guard(solver)
            capture(
                CoordinatePoint(
                    at_iteration,
                    at_work,
                    solver.iteration,
                    previous,
                    solver.nodes_visited,
                    last,
                    before,
                )
            )
            if guard(solver) != before:
                raise ArithmeticError("coordinate observer mutated training state")
            deadline.check()
            pending_iteration = [x for x in pending_iteration if x not in at_iteration]
            pending_work = [x for x in pending_work if x not in at_work]
        if pending_iteration or pending_work:
            previous = solver.nodes_visited
            solver.step()
            last = solver.nodes_visited - previous
