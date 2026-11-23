"""Fixed full-work q8-turn control and exact-turn candidate on frozen spots."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from river_full_broader.gate import source_fingerprint as parent_fingerprint
from river_strength.representation import build_river_candidate
from river_turn_loss.analysis import fingerprint as diagnosis_fingerprint

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import recall_violations
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.tree import SpotTree
from turn_exact_transfer.representation import exact_turn_candidate

CONFIG = Path("configs/turn-exact-transfer.json")
FREEZE = Path("configs/turn-exact-transfer-freeze.json")
CONFIG_SHA256 = "311572209b135d8098781e49b5b0d65e3c1f91f4ab6be83b0be3e974804ed6b0"
FREEZE_SHA256 = "b62040a4746504a9f14377305fc31c8882c0cbfe2a720157a4bd5006ecacc3a9"
PARENT = "5aafb939fdc4ac75b06480dbd8203efddbd0e1f1b02170ab086ff8bf61668ac6"
DIAGNOSIS = "5c33aa0cdfddefe33a69be2c93526223bde1df49eda2957f1f5de4d82901957f"
GAMES = (
    "full_new_medium_dry_oop",
    "turn_exact_new_medium_dry_oop",
    "turn_exact_new_medium_wet_oop",
    "turn_exact_new_low_wet_ip",
)
CONTROL = "signed_full_q8_turn_exact_river"
CANDIDATE = "signed_full_exact_turn_river"
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "linear_average")


@dataclass(frozen=True)
class PathSpec:
    """One frozen spot, representation and deterministic unused RNG seed."""

    index: int
    game: str
    arm: str
    seed: int = 0


def paths() -> tuple[PathSpec, ...]:
    """Known mechanistic pair first, then three new input pairs."""
    return tuple(
        PathSpec(index, game, arm)
        for index, (game, arm) in enumerate(
            (game, arm) for game in GAMES for arm in (CONTROL, CANDIDATE)
        )
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind immutable selection and exact-work grid before constructing a game."""
    if digest(root / CONFIG) != CONFIG_SHA256 or digest(root / FREEZE) != FREEZE_SHA256:
        raise ArithmeticError("prospective contract or one-time freeze changed")
    plan: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    freeze: dict[str, Any] = json.loads((root / FREEZE).read_bytes())
    if (
        tuple(plan["path_spots"]) != GAMES
        or tuple(plan["arms"]) != (CONTROL, CANDIDATE)
        or tuple(plan["work_labels"]) != LABELS
        or tuple(plan["readouts"]) != READOUTS
        or plan["seed_per_arm"] != 0
        or plan["paths"] != 8
        or plan["saved_policy_cases"] != 48
        or plan["worker_count"] != 3
        or plan["budgets_seconds"]["whole_own"] != 7200
        or plan["budgets_seconds"]["native_audit"] != 900
        or freeze["format"] != "turn-exact-transfer-cohort-v1"
        or freeze["config_sha256"] != CONFIG_SHA256
        or freeze["selection_source_commit"]
        != "c036dd920dacd82a80e87d8886586e5f9d807d63"
        or len(freeze["known_spot_sha256"]) != 21
        or len(freeze["spot_sha256"]) != 3
    ):
        raise ArithmeticError("fixed exact-turn grid or freeze changed")
    for name, expected in plan["selection_input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned prerequisite changed: {name}")
    for name, expected in freeze["spot_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"frozen input changed: {name}")
    for name, expected in freeze["known_spot_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"prior known input changed: {name}")
    if parent_fingerprint(root) != PARENT or diagnosis_fingerprint(root) != DIAGNOSIS:
        raise ArithmeticError("parent or diagnostic source changed")
    return plan, freeze


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Construct one exact game with only the declared information-key difference."""
    if game not in GAMES or arm not in (CONTROL, CANDIDATE):
        raise ValueError("outside frozen spot/arm grid")
    _, freeze = contract(root)
    spot = (
        Path("configs/river-full-broader-spots/full_new_medium_dry_oop.json")
        if game == GAMES[0]
        else Path(f"configs/turn-exact-transfer-spots/{game}.json")
    )
    if game != GAMES[0] and spot.as_posix() not in freeze["spot_sha256"]:
        raise ArithmeticError("selected spot absent from one-time freeze")
    source = SpotTree.build(load_spot(root / spot))
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    control = build_river_candidate(source, model)
    exact = exact_turn_candidate(source, control)
    partition = control if arm == CONTROL else exact
    if recall_violations(partition):
        raise ArithmeticError("fixed turn representation violates recall")
    masks = river_mask(exact, 0), river_mask(exact, 1)
    return ScoringContext(exact, partition, partition.exact_to_abstract, masks)
