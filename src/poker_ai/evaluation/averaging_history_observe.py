"""Copy current policies/cumulative averages through the frozen checkpoint guard."""

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import Observation, observe
from poker_ai.postflop.controlled_scoring import BoolArray
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.river_study import Deadline


@dataclass(frozen=True)
class HistoryPoint:
    observation: Observation
    current: FloatArray
    cumulative_average: FloatArray
    learning_path_sha256: str


def learning_path_sha(solver: ControlledTrainer, current: FloatArray) -> str:
    """Bind raw learning path without its deliberately different average weights."""
    digest = hashlib.sha256()
    for array in (solver.regrets, current):
        digest.update(np.asarray(array, dtype="<f8").tobytes())
    digest.update(json.dumps(solver.rng.bit_generator.state, sort_keys=True).encode())
    digest.update(json.dumps(sorted(solver.sampled_keys)).encode())
    digest.update(
        json.dumps(
            [solver.iteration, solver.nodes_visited, solver.initialization_visits]
        ).encode()
    )
    return digest.hexdigest()


def observe_history(
    solver: ControlledTrainer,
    work: Sequence[int],
    river: BoolArray,
    capture: Callable[[HistoryPoint], None],
    deadline: Deadline,
) -> None:
    """Keep first complete crossings and the original RNG/arrays/work fingerprints.

    This observer neither resets time weights nor accumulates a new average. It
    only copies OWN arrays; the frozen outer guard rejects callback mutations of
    regrets, strategy sums, policy, RNG, keys or counters. No reference is imported.
    """

    def snapshot(packet: Observation) -> None:
        current = solver.current_policy.copy()
        cumulative = solver.strategy_sum.copy()
        current.flags.writeable = cumulative.flags.writeable = False
        capture(
            HistoryPoint(
                packet, current, cumulative, learning_path_sha(solver, current)
            )
        )

    observe(solver, work, (), river, snapshot, deadline)
