"""Frozen inputs and publication pins for the read-only attribution."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_regret_recency.plan import context as recency_context

from poker_ai.postflop.controlled_scoring import ScoringContext

CONFIG = Path("configs/known-turn-loss-attribution.json")
PROTOCOL = Path("docs/known-turn-loss-attribution.md")
CONFIG_SHA256 = "04651be71f6d81906e748eb091bff9200153b19387e7548b3e0a6b122547fa36"
PROTOCOL_SHA256 = "74def4594411e7f718ac688b8a953b5cf3849b1c074f1386e79bb3b9afa5e0dc"
PARENT = "4c26fbea5e1249474d72d64a05d907825d118e9e"
CONTROL = "signed_full_exact_turn_river"
CANDIDATE = "signed_full_exact_turn_regret_recency"
GAMES = ("collision_medium_wet_oop-02", "full_new_medium_dry_oop")
WORK = (10_117_956, 10_012_410)
READOUT = "linear_average"


def digest(path: Path) -> str:
    """Hash exactly the named checked-in file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract(root: Path) -> dict[str, Any]:
    """Require the original protocol bytes and every pinned old artifact."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published loss-attribution protocol changed")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["schema_version"] != 1
        or data["issue"] != 4
        or data["parent_merge"] != PARENT
        or [row["name"] for row in data["games"]] != list(GAMES)
        or [row["actual_node_work"] for row in data["games"]] != list(WORK)
        or data["arms"] != [CONTROL, CANDIDATE]
        or data["control"] != CONTROL
        or data["candidate"] != CANDIDATE
        or data["seed"] != 0
        or data["work_label"] != 10_000_000
        or data["readout"] != READOUT
        or data["saved_policy_cases"] != 4
        or data["responding_seat_traces"] != 8
        or data["hard_cap_seconds"] != 900
        or data["failure_save_reserve_seconds"] != 120
        or data["concentration_threshold_positive_worsening_mass"] != 0.5
        or data["known_row_share_threshold_positive_worsening_mass"] != 0.5
        or data["default_promotion"] is not False
    ):
        raise ArithmeticError("fixed loss-attribution contract changed")
    for row in data["games"]:
        if digest(root / row["spot"]) != row["spot_sha256"]:
            raise ArithmeticError("known game input changed")
    for name, expected in data["prerequisite_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned prerequisite changed: {name}")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, "HEAD"], cwd=root, check=False
    ).returncode:
        raise ArithmeticError("parent history absent")
    return data


def context(root: Path, game: str) -> ScoringContext:
    """Build the same exact acting keys used by both old policy arms."""
    contract(root)
    if game not in GAMES:
        raise ValueError("outside two known development games")
    return recency_context(root, game)
