"""Bind the published half-mixture contract and all eight prior snapshots."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_collision_medium_transfer.plan import context as prior_context

from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext

CONTRACT = Path("configs/known-turn-half-policy-mixture.json")
PROTOCOL = Path("docs/known-turn-half-policy-mixture.md")
CONTRACT_SHA256 = "d6e5f8dc66a7f7b74d8fa0e81565de893fde7aca11fa9bfcf1f7f8e7ae253aa7"
PROTOCOL_SHA256 = "838d55b9f63c2a182c1307735b7cadd49f5f4fd31fff63f3a868088dd34a16d4"
PROTOCOL_COMMIT = "e868fcdd80afef343fa1a472607d586a8b0e138a"
ARMS = ("signed_full_q8_turn_exact_river", "signed_full_exact_turn_river")
GAMES = (
    "collision_medium_dry_oop_a",
    "collision_medium_wet_oop_a",
    "collision_medium_dry_oop_b",
    "collision_medium_wet_oop_b",
)


def digest(path: Path) -> str:
    """Return SHA-256 of one exact pinned file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract(root: Path) -> dict[str, Any]:
    """Require published protocol bytes, prior results and fixed work limits."""
    if (
        digest(root / CONTRACT) != CONTRACT_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published half-mixture protocol changed")
    for path in (CONTRACT, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("half-mixture protocol differs from Git publication")
    data: dict[str, Any] = json.loads((root / CONTRACT).read_bytes())
    if (
        data["issue"] != 4
        or data["prior_pr"] != 116
        or data["question"] != "equal_weight_lifted_behavior_policy_mixture"
        or data["control"] != ARMS[0]
        or data["other_parent"] != ARMS[1]
        or tuple(data["games"]) != GAMES
        or len(data["inputs"]) != 8
        or data["policy_weight_control"] != 0.5
        or data["policy_weight_other"] != 0.5
        or data["readout"] != "linear_average"
        or data["work_label"] != 40_000_000
        or data["charged_work"] != 40_205_562
        or data["seed_metadata"] != 0
        or data["stochastic_rng_used"] is not False
        or data["initial_pot_chips"] != 36
        or data["absolute_fraction_max"] != 0.01
        or data["worst_fraction_max"] != 0.025
        or data["paired_improvement_fraction_max"] != -0.001
        or data["paired_remaining_fraction_max"] != 0.001
        or data["required_improved_games"] != 3
        or data["arithmetic_tolerance_chips"] != 1e-9
        or data["probability_tolerance"] != 1e-12
        or data["proof_cap_seconds"] != 180
        or data["own_cap_seconds"] != 900
        or data["native_cap_seconds"] != 900
        or data["peak_rss_bytes_exclusive"] != 1_500_000_000
        or data["reference"] != "OpenSpiel 2.0.2"
        or data["reference_tolerance_chips"] != 1e-9
        or data["prior_result"] != "negative"
    ):
        raise ArithmeticError("half-mixture fixed grid changed")
    expected_grid = [
        (game, arm, index)
        for index, (game, arm) in enumerate(
            (game, arm) for game in GAMES for arm in ARMS
        )
    ]
    if [
        (row["game"], row["arm"], row["path_index"]) for row in data["inputs"]
    ] != expected_grid:
        raise ArithmeticError("eight fixed parent policies changed")
    for row in data["inputs"]:
        for key in ("summary", "snapshot"):
            path = root / row[f"{key}_path"]
            if digest(path) != row[f"{key}_sha256"]:
                raise ArithmeticError(f"pinned parent {key} changed")
    for path_key in (
        "report",
        "own_manifest",
        "freeze",
        "prior_native_job",
        "prior_report_job",
    ):
        if digest(root / data[f"{path_key}_path"]) != data[f"{path_key}_sha256"]:
            raise ArithmeticError(f"pinned prior {path_key} changed")
    if digest(root / "uv.lock") != data["lock_sha256"]:
        raise ArithmeticError("locked dependencies changed")
    return data


def parent_context(root: Path, game: str, arm: str) -> ScoringContext:
    """Rebuild the unchanged published game and selected partition."""
    if game not in GAMES or arm not in ARMS:
        raise ValueError("outside fixed mixture grid")
    return prior_context(root, game, arm)


def parent_policy(
    root: Path, row: dict[str, Any], scoring: ScoringContext
) -> FloatArray:
    """Read one pinned 40m final-average parent with full receipt checks."""
    summary: dict[str, Any] = json.loads((root / row["summary_path"]).read_bytes())
    captures = [
        capture
        for capture in summary["captures"]
        if capture["metadata"]["work_label"] == 40_000_000
        and capture["metadata"]["readout"] == "linear_average"
    ]
    if (
        summary["status"] != "completed"
        or summary["path"]
        != dict(index=row["path_index"], game=row["game"], arm=row["arm"], seed=0)
        or summary["final_work"] != row["charged_work"]
        or len(captures) != 1
    ):
        raise ArithmeticError("fixed parent summary changed")
    capture = captures[0]
    metadata = capture["metadata"]
    if (
        metadata["path_index"] != row["path_index"]
        or metadata["game"] != row["game"]
        or metadata["arm"] != row["arm"]
        or metadata["seed"] != 0
        or metadata["total_work"] != row["charged_work"]
        or capture["receipt"]["sha256"] != row["snapshot_sha256"]
        or capture["receipt"]["policy_sha256"] != row["policy_sha256"]
    ):
        raise ArithmeticError("fixed parent capture changed")
    return read_snapshot(
        root / row["snapshot_path"], scoring.partition, capture["receipt"], metadata
    )
