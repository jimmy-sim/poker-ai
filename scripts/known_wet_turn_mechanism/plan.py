"""Frozen one-game wet turn comparison and historical source prerequisites."""

import hashlib
import json
from pathlib import Path
from typing import Any

from known_turn_mechanism.gate import SOURCE as PARENT_SOURCE
from known_turn_mechanism.gate import source_fingerprint as parent_fingerprint
from river_strength.representation import build_river_candidate
from turn_exact_transfer.learning import CANDIDATE as CANDIDATE
from turn_exact_transfer.learning import CONTROL as CONTROL
from turn_exact_transfer.learning import PathSpec
from turn_exact_transfer.representation import exact_turn_candidate

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import recall_violations
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.tree import SpotTree

CONFIG = Path("configs/known-wet-turn-mechanism.json")
PROTOCOL = Path("docs/known-wet-turn-mechanism.md")
SPOT = Path(
    "results/turn-collision-transfer/screen/attempts/collision_medium_wet_oop-02.json"
)
CONFIG_SHA256 = "7bce95dc29bbc7be48130127e46053ebfe66c002820f408817023ab89cd8f334"
PROTOCOL_SHA256 = "6c118d6e1b78aa41410cfe6dbaf3523b38b679e4a55d528a3c8b5e0796a7e0f0"
SPOT_SHA256 = "cea60f6a69d07904078f6930238c7dcbbbb2dba6b36eceb215198b329564a616"
PARENT_FINGERPRINT = "6e09c02673ca596e6082ea8d0a57ba12cd2533acfaf2c777991c4d29f395e0f4"
PARENT_SOURCE_SHA256 = (
    "ef0965c0afca9d3da99402741022b945e5b0427877a9bde2be04f8d6ac611f68"
)
GAME = "collision_medium_wet_oop-02"
ARMS = (CONTROL, CANDIDATE)
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "linear_average")


def digest(path: Path) -> str:
    """Return SHA-256 of an exact file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[PathSpec, PathSpec]:
    """The sole known input, control then candidate, unused RNG seed zero."""
    return PathSpec(0, GAME, CONTROL), PathSpec(1, GAME, CANDIDATE)


def contract(root: Path) -> dict[str, Any]:
    """Guard the prospective contract and its immutable qualification chain."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published known-wet protocol changed")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["issue"] != 4
        or data["input"]["file"] != SPOT.as_posix()
        or data["input"]["sha256"] != SPOT_SHA256
        or tuple(data["arms"]) != ARMS
        or tuple(data["work_labels"]) != LABELS
        or tuple(data["readouts"]) != READOUTS
        or data["seed_per_arm"] != [0]
        or data["worker_count"] != 2
        or data["profile"]["repeats_per_path"] != 3
        or data["budgets_seconds"]["whole_own"] != 7200
        or data["budgets_seconds"]["native_audit"] != 900
        or data["source_parent_fingerprint"] != PARENT_FINGERPRINT
    ):
        raise ArithmeticError("known-wet fixed grid changed")
    if digest(root / SPOT) != SPOT_SHA256:
        raise ArithmeticError("known-wet input changed")
    for name, expected in data["prerequisite_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"known-wet prerequisite changed: {name}")
    if (
        parent_fingerprint(root) != PARENT_FINGERPRINT
        or digest(root / PARENT_SOURCE / "manifest.json") != PARENT_SOURCE_SHA256
    ):
        raise ArithmeticError("qualified historical source changed")
    return data


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Construct identical exact game and chance; change only acting turn keys."""
    if game != GAME or arm not in ARMS:
        raise ValueError("outside frozen known-wet game/arm grid")
    contract(root)
    source = SpotTree.build(load_spot(root / SPOT))
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    control = build_river_candidate(source, model)
    exact = exact_turn_candidate(source, control)
    partition = control if arm == CONTROL else exact
    if recall_violations(partition):
        raise ArithmeticError("known-wet representation violates recall")
    masks = river_mask(exact, 0), river_mask(exact, 1)
    return ScoringContext(exact, partition, partition.exact_to_abstract, masks)
