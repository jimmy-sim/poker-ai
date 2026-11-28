"""Bind the published four-game uniform-regret transfer grid."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_collision_medium_transfer.plan import (
    CANDIDATE as PRIOR_ARM,
)
from known_turn_collision_medium_transfer.plan import (
    GAMES as PRIOR_GAMES,
)
from known_turn_collision_medium_transfer.plan import (
    context as prior_context,
)
from turn_exact_transfer.learning import PathSpec

from poker_ai.postflop.controlled_scoring import ScoringContext

CONFIG = Path("configs/known-turn-uniform-regret-transfer.json")
PROTOCOL = Path("docs/known-turn-uniform-regret-transfer.md")
CONFIG_SHA256 = "871696e7cc9cb269149714e835638126584d6ed5258bee7dfebd601764c86c17"
PROTOCOL_SHA256 = "aeeaf57db47bd60e74ad861a1db64fc3440bfb56d90f7dd24c4a96595e715dd8"
PROTOCOL_COMMIT = "ae2887ac8f25901c21abb34812eaeb484529a1af"
ARM = "signed_full_exact_turn_uniform_regret"
GAMES: tuple[str, ...] = PRIOR_GAMES
LABELS = (10_000_000, 20_000_000, 40_000_000)
READOUTS = ("current", "linear_average")
PROFILE_WORK = 5_000_000
MAX_RSS = 1_500_000_000
EXPECTED_WORK = (10_117_956, 20_235_912, 40_205_562)


def digest(path: Path) -> str:
    """SHA-256 of an exact published or archived input."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[PathSpec, ...]:
    """One deterministic candidate per already inspected game, fixed order."""
    return tuple(PathSpec(index, game, ARM) for index, game in enumerate(GAMES))


def contract(root: Path) -> dict[str, Any]:
    """Require exact prospective bytes and every immutable prerequisite."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published uniform-regret protocol changed")
    for path in (CONFIG, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError(
                "uniform-regret contract differs from Git publication"
            )
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["issue"] != 4
        or data["parent_merge"] != "75e7e1f5e330dcf3e6bb280e5c98ea96261d13d9"
        or [row["name"] for row in data["selection"]["games"]] != list(GAMES)
        or data["selection"]["previously_inspected"] is not True
        or data["selection"]["requires_turn_collisions"] is not True
        or data["candidate"]["rules"]
        != {
            "regret_rule": "signed",
            "regret_weight": "uniform",
            "average_weight": "linear",
        }
        or data["control"]["rules"]
        != {
            "regret_rule": "signed",
            "regret_weight": "linear",
            "average_weight": "linear",
        }
        or data["training"]["matched_work_labels"] != list(LABELS)
        or data["training"]["readouts"] != list(READOUTS)
        or tuple(
            data["training"]["expected_actual_work_by_label"][str(label)]
            for label in LABELS
        )
        != EXPECTED_WORK
        or data["training"]["candidate_policy_cases"] != 24
        or data["training"]["control_policy_cases_reused"] != 24
        or data["training"]["stochastic_rng_used"] is not False
        or data["compute"]["profile_paths"] != 12
        or data["compute"]["profile_work_label"] != PROFILE_WORK
        or data["compute"]["profile_repeats_per_candidate_path"] != 3
        or data["compute"]["workers"] != 2
        or data["compute"]["max_worker_peak_rss_bytes_exclusive"] != MAX_RSS
        or data["compute"]["caps_seconds"]
        != {
            "proof_whole": 180,
            "profile_whole": 900,
            "own_whole": 7200,
            "native_audit_whole": 900,
        }
        or data["native"]["candidate_cases"] != 24
        or data["native"]["tolerance_chips"] != 1e-9
        or data["default_promotion"] is not False
    ):
        raise ArithmeticError("fixed uniform-regret grid changed")
    for name, expected in data["pinned_inputs_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"uniform-regret prerequisite changed: {name}")
    for row in data["selection"]["games"]:
        if digest(root / row["path"]) != row["sha256"]:
            raise ArithmeticError("frozen known spot changed")
    return data


def context(root: Path, game: str) -> ScoringContext:
    """Reuse exact-turn representation on a fixed known game."""
    contract(root)
    if game not in GAMES:
        raise ValueError("outside fixed four-game grid")
    return prior_context(root, game, PRIOR_ARM)
