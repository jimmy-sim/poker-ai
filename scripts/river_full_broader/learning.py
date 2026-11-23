"""Fixed B4 controls and unchanged full expected learner on frozen spot inputs."""

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator
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

CONFIG = Path("configs/river-full-broader-spots.json")
CONFIG_SHA256 = "b9138262ba01758ad0dae9e997420ba355343ff2a3b784e26612be8561d60290"
FREEZE = Path("configs/river-full-broader-freeze.json")
GAMES = ("full_new_medium_dry_oop", "full_new_low_wet_ip")
SEEDS = (20261511, 20261512, 20261513)
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "linear_average")
CONTROL = "signed_external_b4"
CANDIDATE = "signed_full_expectation"
ControlCapture = Callable[
    [BatchPoint, ReducedDispatchBatchTrainer, dict[str, FloatArray]], None
]


@dataclass(frozen=True)
class PathSpec:
    """One prespecified spot/arm/seed path and fixed worker index."""

    index: int
    game: str
    seed: int
    arm: str


def paths() -> tuple[PathSpec, ...]:
    """Each stratum's three controls precede its one deterministic candidate."""
    rows = [
        (game, seed, CONTROL) if seed is not None else (game, 0, CANDIDATE)
        for game in GAMES
        for seed in (*SEEDS, None)
    ]
    return tuple(
        PathSpec(i, game, seed, arm) for i, (game, seed, arm) in enumerate(rows)
    )


def contract(root: Path) -> dict[str, Any]:
    """Read exactly the published prospective contract and declared path grid."""
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ArithmeticError("prospective full-broader contract changed")
    plan: dict[str, Any] = json.loads(raw)
    if (
        tuple(row["name"] for row in plan["strata"]) != GAMES
        or tuple(plan["control"]["seeds"]) != SEEDS
        or plan["candidate"]["seed"] != 0
        or tuple(plan["shared_training"]["work_labels"]) != LABELS
        or tuple(plan["shared_training"]["readouts"]) != READOUTS
        or plan["paths"] != 8
        or plan["worker_count"] != 3
    ):
        raise ArithmeticError("prospective full-broader path grid changed")
    for name, expected in plan["input_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ArithmeticError(f"pinned full-broader input changed: {name}")
    return plan


def context(root: Path, game: str) -> ScoringContext:
    """Build only the frozen finite game and unchanged river information key."""
    if game not in GAMES:
        raise ValueError("outside fixed full-broader spot grid")
    freeze: dict[str, Any] = json.loads((root / FREEZE).read_bytes())
    spot = Path(f"configs/river-full-broader-spots/{game}.json")
    expected = freeze["spot_sha256"].get(spot.as_posix())
    if (
        expected is None
        or hashlib.sha256((root / spot).read_bytes()).hexdigest() != expected
    ):
        raise ArithmeticError("frozen spot bytes changed")
    source = SpotTree.build(load_spot(root / spot))
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    exact = MatrixTree.build(source)
    partition = build_river_candidate(source, model)
    if recall_violations(partition):
        raise ArithmeticError("river candidate violates abstract recall")
    masks = river_mask(exact, 0), river_mask(exact, 1)
    return ScoringContext(exact, partition, partition.exact_to_abstract, masks)


def readouts(solver: ReducedDispatchBatchTrainer) -> dict[str, FloatArray]:
    """Copy current and linear-average B4 policies without exposing ledgers."""
    tree = solver.tree
    result = {
        "current": solver.current_policy.copy(),
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
    capture: ControlCapture,
) -> ReducedDispatchBatchTrainer:
    """One exact-initialized, signed, linear B4 path with charged node work."""
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("outside fixed B4 control seeds")
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
