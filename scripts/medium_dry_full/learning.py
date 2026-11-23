"""Deterministic full expected passes under the published B4 signed rules."""

import copy
import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.random import PCG64, Generator
from river_generalization.learning import context as historical_context

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import ControlledTrainer, Rules
from poker_ai.postflop.river_study import Deadline

GAMES = ("new_low_wet_ip", "new_medium_dry_oop")
ARM = "signed_full_expectation"


@dataclass(frozen=True)
class FullPoint:
    """One first complete target-pair crossing in charged tree-node visits."""

    labels: tuple[int, ...]
    iteration: int
    previous_work: int
    total_work: int
    last_iteration_visits: int
    guard_sha256: str


Capture = Callable[[FullPoint, ControlledTrainer, dict[str, FloatArray]], None]


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Build the unchanged known spot and q8-turn/exact-river information key."""
    if game not in GAMES or arm != ARM:
        raise ValueError("outside full-expectation spot grid")
    return historical_context(root, game, "q8_turn_exact_river")


def readouts(solver: ControlledTrainer) -> dict[str, FloatArray]:
    """Return read-only snapshots; the linear average is the primary policy."""
    tree = solver.tree
    result = {
        "current": solver.current_policy.copy(),
        "linear_average": solver.average_policy.copy(),
    }
    for policy in result.values():
        tree.validate_policy(policy)
        policy.flags.writeable = False
    return result


def guard(solver: ControlledTrainer) -> str:
    """Bind all changing training state, including the deliberately unused RNG."""
    digest = hashlib.sha256()
    for array in (solver.regrets, solver.strategy_sum):
        digest.update(np.asarray(array, dtype="<f8").tobytes())
    digest.update(
        json.dumps(
            {
                "iteration": solver.iteration,
                "nodes_visited": solver.nodes_visited,
                "initialization_visits": solver.initialization_visits,
                "traversal": solver.traversal,
                "average_phase": solver.average_phase,
                "average_mass": solver.average_mass,
                "rules": [
                    solver.rules.regret_rule,
                    solver.rules.regret_weight,
                    solver.rules.average_weight,
                ],
                "rng_state": solver.rng.bit_generator.state,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    return digest.hexdigest()


def observe(
    solver: ControlledTrainer,
    labels: Sequence[int],
    capture: Capture,
    deadline: Deadline,
) -> None:
    """Capture each first full-pair work crossing without changing the learner.

    One expected target pass visits every tree node, even a zero-reach node.
    The exact initialization charges two such passes; a later iteration does
    target 0 then 1 and charges two more. The callback sees detached policies.
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
        or solver.rules != Rules("signed", "linear", "linear")
    ):
        raise ValueError("fresh prescribed full-expectation learner required")
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
                raise ArithmeticError("full-pass observer mutated training state")
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
    """One deterministic path; PCG64(0) is explicit and never sampled."""
    solver = ControlledTrainer(
        tree,
        Generator(PCG64(0)),
        traversal="full",
        rules=Rules("signed", "linear", "linear"),
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )
    solver.initialize_exact()
    if warm_capture is not None:
        before = guard(solver)
        warm_capture(solver)
        if guard(solver) != before:
            raise ArithmeticError("warm observer mutated training state")
    observe(solver, labels, capture, deadline)
    return solver
