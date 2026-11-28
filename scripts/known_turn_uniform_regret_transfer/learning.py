"""Full expected exact-turn learning with uniform regret increments only."""

import copy
from collections.abc import Callable, Sequence

from medium_dry_full.learning import Capture, FullPoint, guard, readouts
from numpy.random import PCG64, Generator

from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_training import ControlledTrainer, Rules
from poker_ai.postflop.river_study import Deadline

RULES = Rules("signed", "uniform", "linear")


def observe(
    solver: ControlledTrainer,
    labels: Sequence[int],
    capture: Capture,
    deadline: Deadline,
) -> None:
    """Capture first complete target-pair crossings without mutating training.

    A full pass charges each tree node, including zero-reach nodes. Only the
    regret increment weight differs from the historical linear-regret path.
    """
    if (
        not labels
        or list(labels) != sorted(set(labels))
        or any(type(label) is not int or label <= 0 for label in labels)
        or solver.iteration != 1
        or solver.nodes_visited != solver.initialization_visits
        or solver.initialization_visits != 2 * len(solver.tree.player)
        or solver.traversal != "full"
        or solver.average_phase != "opponent_pass"
        or solver.average_mass != "chance_own_reach"
        or solver.rules != RULES
    ):
        raise ValueError("fresh prescribed uniform-regret learner required")
    initial_rng = copy.deepcopy(solver.rng.bit_generator.state)
    pending = list(labels)
    previous, last = 0, solver.nodes_visited
    while pending:
        deadline.check()
        if solver.rng.bit_generator.state != initial_rng:
            raise ArithmeticError("full traversal consumed RNG")
        crossed = tuple(label for label in pending if label <= solver.nodes_visited)
        if crossed:
            if any(previous >= label for label in crossed):
                raise ArithmeticError("missed first full-pair work crossing")
            before = guard(solver)
            capture(
                FullPoint(
                    crossed,
                    solver.iteration,
                    previous,
                    solver.nodes_visited,
                    last,
                    before,
                ),
                solver,
                readouts(solver),
            )
            if guard(solver) != before:
                raise ArithmeticError("uniform-regret observer mutated training state")
            pending = [label for label in pending if label not in crossed]
        if pending:
            previous = solver.nodes_visited
            solver.step()
            last = solver.nodes_visited - previous
            if last != 2 * len(solver.tree.player):
                raise ArithmeticError("full-pair node charge changed")


def train(
    tree: ArrayTree,
    labels: Sequence[int],
    deadline: Deadline,
    capture: Capture,
    warm_capture: Callable[[ControlledTrainer], None] | None = None,
) -> ControlledTrainer:
    """Run one deterministic path; the explicit PCG64(0) is never sampled."""
    solver = ControlledTrainer(
        tree,
        Generator(PCG64(0)),
        traversal="full",
        rules=RULES,
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )
    solver.initialize_exact()
    if warm_capture is not None:
        before = guard(solver)
        warm_capture(solver)
        if guard(solver) != before:
            raise ArithmeticError("warm observer mutated uniform-regret state")
    observe(solver, labels, capture, deadline)
    return solver
