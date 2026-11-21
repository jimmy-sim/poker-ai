"""Unchanged signed B4 trainer with same-path uniform and linear readouts."""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator
from river_generalization.learning import readouts
from river_strength.representation import build_river_candidate

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint, observe
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.tree import SpotTree

CONFIG = Path("configs/river-uniform-readout-spots.json")
CONFIG_SHA256 = "ca45d9a8a1b0b24490911c3e54e2707cd0c2c4f92650401e51ba3bcbde414745"
GAMES = (
    "uniform_medium_dry_oop_a",
    "uniform_medium_dry_oop_b",
    "uniform_medium_wet_oop",
    "uniform_low_wet_ip",
)
SEEDS = (20261411, 20261412, 20261413)
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "uniform_average", "linear_average")
ARM = "q8_turn_exact_river"
Capture = Callable[
    [BatchPoint, ReducedDispatchBatchTrainer, dict[str, FloatArray]], None
]


@dataclass(frozen=True)
class PathSpec:
    index: int
    game: str
    seed: int
    arm: str = ARM


def paths() -> tuple[PathSpec, ...]:
    """Fixed four-spot/three-seed order for worker assignment and pairing."""
    return tuple(
        PathSpec(index, game, seed)
        for index, (game, seed) in enumerate(
            (game, seed) for game in GAMES for seed in SEEDS
        )
    )


def contract(root: Path) -> dict[str, Any]:
    """Check immutable published protocol and source inputs before own work."""
    from river_uniform_readout.selection import digest

    if digest(root / CONFIG) != CONFIG_SHA256:
        raise ArithmeticError("prospective uniform-readout protocol changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        tuple(row["name"] for row in config["strata"]) != GAMES
        or tuple(config["seeds"]) != SEEDS
        or tuple(config["training"]["node_work_labels"]) != LABELS
        or tuple(config["training"]["readouts"]) != READOUTS
        or config["representation"] != ARM
        or config["training"]["paths"] != 12
        or config["training"]["logical_profiles"] != 108
    ):
        raise ArithmeticError("prospective uniform-readout grid changed")
    for name, expected in config["input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned uniform-readout input changed: {name}")
    return config


def context(root: Path, game: str) -> ScoringContext:
    """Build a frozen own finite spot from public and acting-player cards only."""
    if game not in GAMES:
        raise ValueError("outside the prospective uniform-readout grid")
    source = SpotTree.build(
        load_spot(root / f"configs/river-uniform-readout-spots/{game}.json")
    )
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    exact = MatrixTree.build(source)
    partition = build_river_candidate(source, model)
    if recall_violations(partition):
        raise ArithmeticError("river candidate violates abstract recall")
    masks = river_mask(exact, 0), river_mask(exact, 1)
    return ScoringContext(exact, partition, partition.exact_to_abstract, masks)


def train(
    tree: ArrayTree,
    seed: int,
    labels: Sequence[int],
    deadline: Deadline,
    capture: Capture,
) -> ReducedDispatchBatchTrainer:
    """Train one signed B4 path; observations cannot mutate its RNG or ledgers."""
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
