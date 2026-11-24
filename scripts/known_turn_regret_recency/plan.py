"""Frozen known wet/dry inputs and immutable exact-turn controls."""

import hashlib
import json
from pathlib import Path
from typing import Any

from known_turn_mechanism.plan import CANDIDATE as HISTORICAL_ARM
from known_turn_mechanism.plan import GAME as DRY_GAME
from known_turn_mechanism.plan import context as dry_context
from known_wet_turn_mechanism.plan import GAME as WET_GAME
from known_wet_turn_mechanism.plan import context as wet_context
from turn_exact_transfer.learning import PathSpec

from poker_ai.postflop.controlled_scoring import ScoringContext

CONFIG = Path("configs/known-turn-regret-recency.json")
PROTOCOL = Path("docs/known-turn-regret-recency.md")
CONFIG_SHA256 = "e2e5ad2eb22e09e9f4874e678f8916c522d1713c6d20087d746694771558ff3e"
PROTOCOL_SHA256 = "1f779e42d236b7bc77c5a614afbf75cb6fa1860d7f8a8fc313bfd0ffa026aed1"
GAMES = (WET_GAME, DRY_GAME)
ARM = "signed_full_exact_turn_regret_recency"
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "linear_average")
EXPECTED_WORK = ((266262, 1065048, 10117956), (127818, 1022544, 10012410))
WET_TURN_ROWS = (1611, 4041, 7506, 1618, 4824, 1619, 40, 0, 5838, 1596)
WET_RIVER_ROWS = (1679, 1697, 1821, 1839, 2, 2361, 1152, 7974, 7507, 1689)


def digest(path: Path) -> str:
    """SHA-256 of exactly the named checked-in file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[PathSpec, PathSpec]:
    """One deterministic new candidate per known game, wet then dry."""
    return PathSpec(0, WET_GAME, ARM), PathSpec(1, DRY_GAME, ARM)


def contract(root: Path) -> dict[str, Any]:
    """Reject changed prospective protocol, controls, inputs, or work rules."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published regret-recency protocol changed")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["issue"] != 4
        or data["parent_merge"] != "ec9c0d2f068f486bb0ad9fa34e64f73098381520"
        or [row["game"] for row in data["inputs"]] != list(GAMES)
        or data["candidate_path_order"] != list(GAMES)
        or data["seed_per_candidate_path"] != [0]
        or data["candidate_paths"] != 2
        or data["candidate_saved_policy_cases"] != 12
        or data["control_saved_policy_cases"] != 12
        or data["work_labels"] != list(LABELS)
        or data["readouts"] != list(READOUTS)
        or data["candidate_regret_update"]["discount_start_iteration"] != 2
        or data["candidate_regret_update"]["positive_or_zero_factor"]
        != "t^1.5 / (1 + t^1.5)"
        or data["candidate_regret_update"]["negative_factor"] != 0.5
        or data["budgets_seconds"]["whole_own"] != 7200
        or data["budgets_seconds"]["native_audit"] != 900
        or data["profile"]["path_count"] != 6
        or data["profile"]["work_label"] != 1_000_000
        or data["profile"]["strict_admission"] != "2*(2*T+600)<7200"
        or data["native"]["candidate_cases"] != 12
        or data["native"]["tolerance_chips"] != 1e-9
        or data["default_promotion"] is not False
    ):
        raise ArithmeticError("fixed regret-recency grid changed")
    for row, expected_work in zip(data["inputs"], EXPECTED_WORK, strict=True):
        final_check = (
            root
            / Path(row["control_own_manifest"]).parent.parent
            / "final-checks/manifest.json"
        )
        if (
            row["initial_pot_chips"] != 36
            or tuple(row["control_actual_node_work"]) != expected_work
            or digest(root / row["spot"]) != row["spot_sha256"]
            or digest(root / row["control_own_manifest"])
            != row["control_own_manifest_sha256"]
            or digest(root / row["control_native_manifest"])
            != row["control_native_manifest_sha256"]
            or digest(root / row["control_report_manifest"])
            != row["control_report_manifest_sha256"]
            or digest(final_check) != row["control_final_checks_sha256"]
        ):
            raise ArithmeticError("known-game immutable input or control changed")
    wet, dry = data["inputs"]
    if (
        tuple(wet["fixed_turn_rows"]) != WET_TURN_ROWS
        or tuple(wet["fixed_river_rows"]) != WET_RIVER_ROWS
        or dry["fixed_turn_rows"] != [2445, 30, 1]
        or dry["fixed_river_rows"] != []
    ):
        raise ArithmeticError("known decision rows changed")
    for name, expected in data["prerequisite_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"regret-recency prerequisite changed: {name}")
    return data


def context(root: Path, game: str) -> ScoringContext:
    """Build unchanged exact acting turn/river keys for one known game."""
    contract(root)
    if game == WET_GAME:
        return wet_context(root, game, HISTORICAL_ARM)
    if game == DRY_GAME:
        return dry_context(root, game, HISTORICAL_ARM)
    raise ValueError("outside two known exact-turn games")
