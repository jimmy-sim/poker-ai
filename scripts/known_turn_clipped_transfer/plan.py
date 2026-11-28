"""Bind the published four-game clipped-regret transfer grid."""

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

CONFIG = Path("configs/known-turn-clipped-transfer.json")
PROTOCOL = Path("docs/known-turn-clipped-transfer.md")
CONFIG_SHA256 = "22b095d6009106ac19222b815e6a5d2e1368cc16d2c45b2b10623519afa1b4e1"
PROTOCOL_SHA256 = "ddcb88c3910a9de33e71f215221f8dea7db8024ed7683031bd58b2ccf51cb775"
PROTOCOL_COMMIT = "f7db2f68919f3bf5ef0555e8bba780eeb07b1798"
ARM = "clipped_full_exact_turn_river"
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
        raise ArithmeticError("published clipped-regret protocol changed")
    for path in (CONFIG, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError(
                "clipped-regret contract differs from Git publication"
            )
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["issue"] != 4
        or data["parent_merge"] != "f4a8322dc6990f2481632288869c83fcaef9746b"
        or [row["name"] for row in data["selection"]["games"]] != list(GAMES)
        or data["selection"]["previously_inspected"] is not True
        or data["selection"]["requires_turn_collisions"] is not True
        or data["candidate"]["rules"]
        != {
            "regret_rule": "clipped",
            "regret_weight": "linear",
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
        raise ArithmeticError("fixed clipped-regret grid changed")
    for name, expected in data["pinned_inputs_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"clipped-regret prerequisite changed: {name}")
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
