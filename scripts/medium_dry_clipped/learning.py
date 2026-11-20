"""Matched-work signed versus clipped updater on the unchanged river key."""

from collections.abc import Callable, Sequence
from pathlib import Path

from numpy.random import PCG64, Generator
from river_generalization.learning import context as historical_context
from river_generalization.learning import readouts

from medium_dry_clipped.gate import ARMS, GAMES, SEEDS
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint, observe
from poker_ai.postflop.river_study import Deadline

Capture = Callable[
    [BatchPoint, ReducedDispatchBatchTrainer, dict[str, FloatArray]], None
]


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Both update rules see precisely the same published exact-river key."""
    if game not in GAMES or arm not in ARMS:
        raise ValueError("outside clipped-regret grid")
    return historical_context(root, game, "q8_turn_exact_river")


def train(
    tree: ArrayTree,
    seed: int,
    arm: str,
    labels: Sequence[int],
    deadline: Deadline,
    capture: Capture,
) -> ReducedDispatchBatchTrainer:
    """Change only regret clipping; match RNG, sampling and node work."""
    if type(seed) is not int or seed not in SEEDS or arm not in ARMS:
        raise ValueError("outside fixed seed/arm grid")
    if not labels or list(labels) != sorted(set(labels)):
        raise ValueError("work labels must be unique and ordered")
    solver = ReducedDispatchBatchTrainer(
        tree,
        Generator(PCG64(seed)),
        batch_size=4,
        rules=Rules(
            "signed" if arm == "signed_linear" else "clipped", "linear", "linear"
        ),
    )
    solver.initialize_exact()

    def at(point: BatchPoint) -> None:
        capture(point, solver, readouts(solver))

    observe(solver, labels, at, deadline)
    return solver
