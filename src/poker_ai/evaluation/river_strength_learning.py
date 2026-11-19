"""Own bounded B4 river-information learning, before any reference comparison.

A path is one game, seed and information key. Both arms use the same original
signed/linear IID B4 updater, exact initialization and node-work crossings.
The callback receives snapshots only; it may not change trainer state or RNG.
"""

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint, observe
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.range_protocol import CANDIDATE, build_representation_control
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.river_strength_representation import (
    RIVER_CANDIDATE,
    build_river_candidate,
)
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.tree import SpotTree

ARMS = (CANDIDATE, RIVER_CANDIDATE)
GAMES = ("dev_low_oop", "dev_medium_oop")
SEEDS = (20261301, 20261302, 20261303)
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "uniform_average", "linear_average")
CONFIG = "configs/river-strength-known-vulnerabilities.json"
CONFIG_SHA256 = "af538bc3d73441c17672998cd3954b25d6eda3dd645407214d5ef18e3d695bff"
Capture = Callable[
    [BatchPoint, ReducedDispatchBatchTrainer, dict[str, FloatArray]], None
]


@dataclass(frozen=True)
class PathSpec:
    index: int
    game: str
    seed: int
    arm: str


def paths() -> tuple[PathSpec, ...]:
    """Fixed game/seed/arm order, including paired seed labels."""
    return tuple(
        PathSpec(index, game, seed, arm)
        for index, (game, seed, arm) in enumerate(
            (g, s, a) for g in GAMES for s in SEEDS for a in ARMS
        )
    )


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Build one own finite spot from legal observations only, no frozen policy."""
    if game not in GAMES or arm not in ARMS:
        raise ValueError("outside the prospective river-strength grid")
    source = SpotTree.build(load_spot(root / f"configs/learning-spots/{game}.json"))
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    exact = MatrixTree.build(source)
    partition = (
        build_river_candidate(source, model)
        if arm == RIVER_CANDIDATE
        else build_representation_control(source, arm, model)
    )
    if recall_violations(partition):
        raise ArithmeticError("river candidate violates abstract recall")
    masks = river_mask(exact, 0), river_mask(exact, 1)
    return ScoringContext(exact, partition, partition.exact_to_abstract, masks)


def readouts(
    solver: ReducedDispatchBatchTrainer,
) -> dict[str, FloatArray]:
    """Copy current and both average policies without exposing trainer arrays."""
    tree = solver.tree
    result = {
        "current": solver.current_policy.copy(),
        "uniform_average": tree.normalize(solver.ledger("uniform")),
        "linear_average": tree.normalize(solver.ledger("linear")),
    }
    for policy in result.values():
        tree.validate_policy(policy)
        policy.flags.writeable = False
    return result


def train(
    tree: ArrayTree,
    seed: int,
    labels: Sequence[int],
    deadline: Deadline,
    capture: Capture,
) -> ReducedDispatchBatchTrainer:
    """Train one whole path; observer enforces exact first crossings and purity."""
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("outside the fixed seed list")
    if not labels or list(labels) != sorted(set(labels)):
        raise ValueError("work labels must be unique and ordered")
    solver = ReducedDispatchBatchTrainer(
        tree,
        Generator(PCG64(seed)),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    solver.initialize_exact()

    def at(point: BatchPoint) -> None:
        capture(point, solver, readouts(solver))

    observe(solver, labels, at, deadline)
    return solver


def config_grid(config: dict[str, Any]) -> None:
    """Reject a changed prospective grid before source-bound work starts."""
    expected = [(p.game, p.seed, p.arm) for p in paths()]
    actual = [
        (game, seed, arm)
        for game in config["games"]
        for seed in config["seeds"]
        for arm in config["arms"]
    ]
    if (
        actual != expected
        or config["training"]["node_work_labels"] != list(LABELS)
        or config["training"]["readouts"] != list(READOUTS)
        or config["training"]["paths"] != len(expected)
        or config["training"]["logical_profiles"]
        != len(expected) * len(LABELS) * len(READOUTS)
    ):
        raise ValueError("prospective river-strength grid changed")


def contract(root: Path) -> dict[str, Any]:
    """Require the public prospective bytes and every pinned finite input."""
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ArithmeticError("prospective river-strength contract changed")
    config: dict[str, Any] = json.loads(raw)
    config_grid(config)
    for name, expected in config["input_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ArithmeticError(f"pinned river-strength input changed: {name}")
    return config
