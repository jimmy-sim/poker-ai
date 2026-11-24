"""Frozen two-known-game matched-work grid and historical source pins."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from known_turn_mechanism.gate import source_fingerprint as dry_fingerprint
from known_turn_mechanism.plan import context as dry_context
from known_turn_regret_recency.gate import source_fingerprint as recency_fingerprint
from known_wet_turn_mechanism.gate import source_fingerprint as wet_fingerprint
from known_wet_turn_mechanism.plan import context as wet_context
from turn_exact_transfer.learning import PathSpec

from poker_ai.postflop.controlled_scoring import ScoringContext

CONFIG = Path("configs/known-turn-work-budget.json")
PROTOCOL = Path("docs/known-turn-work-budget.md")
CONFIG_SHA256 = "f181957b4db74418b8ba9bad266f68bdac7435d75702e668b3020067eada9355"
PROTOCOL_SHA256 = "58e2efaed3067c7ca4a8bcaaa4826a69553c9bbdebbc7568008055394cf9a05b"
PARENT = "91260be0132412ac58cf7bf045adc9684cf098a0"
GAMES = ("collision_medium_wet_oop-02", "full_new_medium_dry_oop")
CONTROL = "signed_full_q8_turn_exact_river"
CANDIDATE = "signed_full_exact_turn_river"
LABELS = (10_000_000, 20_000_000, 40_000_000)
READOUTS = ("current", "linear_average")
PROFILE_WORK = 1_000_000
MAX_RSS = 1_500_000_000


def digest(path: Path) -> str:
    """Hash one pinned file without changing its bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[PathSpec, ...]:
    """Controls first per game; index parity fixes two worker partitions."""
    return tuple(
        PathSpec(index, game, arm)
        for index, (game, arm) in enumerate(
            (game, arm) for game in GAMES for arm in (CONTROL, CANDIDATE)
        )
    )


def contract(root: Path) -> dict[str, Any]:
    """Guard published prospective bytes and every reused training input."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published work-budget protocol changed")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["schema_version"] != 1
        or data["issue"] != 4
        or data["parent_merge"] != PARENT
        or tuple(row["name"] for row in data["games"]) != GAMES
        or [row["role"] for row in data["games"]] != ["known_primary", "known_contrast"]
        or data["control"] != CONTROL
        or data["candidate"] != CANDIDATE
        or data["seeds"] != [0]
        or tuple(data["charged_work_labels"]) != LABELS
        or tuple(data["readouts"]) != READOUTS
        or data["profile_work_label"] != PROFILE_WORK
        or data["profile_repeats_per_path"] != 3
        or data["profile_paths"] != 4
        or data["workers"] != 2
        or data["profile_whole_cap_seconds"] != 900
        or data["own_whole_cap_seconds"] != 7200
        or data["reference_audit_cap_seconds"] != 900
        or data["fictional_proof_cap_seconds"] != 180
        or data["failure_save_reserve_seconds_within_caps"] != 120
        or data["max_worker_peak_rss_bytes"] != MAX_RSS
        or data["native_scalar_tolerance_chips"] != 1e-9
        or data["nonnegative_row_gain_slack_chips"] != 1e-12
        or data["default_promotion"] is not False
    ):
        raise ArithmeticError("fixed work-budget grid changed")
    if list(data["worker_partition"].values()) != [
        ["wet_control", "dry_control"],
        ["wet_candidate", "dry_candidate"],
    ]:
        raise ArithmeticError("fixed work-budget worker partition changed")
    for row in data["games"]:
        if (
            row["initial_pot_chips"] != 36
            or digest(root / row["spot"]) != row["spot_sha256"]
        ):
            raise ArithmeticError("fixed known-game input changed")
    for name, expected in data["prerequisite_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError("pinned work-budget prerequisite changed: " + name)
    pins = data["historical_source_fingerprints"]
    if (
        wet_fingerprint(root) != pins["wet_exact_turn_study"]
        or dry_fingerprint(root) != pins["dry_exact_turn_study"]
        or recency_fingerprint(root) != pins["recency_negative_report"]
    ):
        raise ArithmeticError("historical source fingerprint changed")
    for role, game, report in (
        ("wet", GAMES[0], root / "results/known-wet-turn-mechanism/report/report.json"),
        (
            "dry",
            GAMES[1],
            root / "results/known-turn-exact-mechanism/report/report.json",
        ),
    ):
        cases = json.loads(report.read_bytes())["cases"]
        old = [row for row in cases if row["work_label"] == LABELS[0]]
        if len(old) != 4 or {row["actual_node_work"] for row in old} != {
            data["historical_10m_actual_work"][role]
        }:
            raise ArithmeticError("historical ten-million work changed")
        for row in old:
            if row["arm"] not in (CONTROL, CANDIDATE) or row["readout"] not in READOUTS:
                raise ArithmeticError("historical ten-million case changed")
            arm = "control" if row["arm"] == CONTROL else "candidate"
            key = f"{role}_{arm}_{row['readout']}"
            if (
                row["game"] != game
                or row["policy_sha256"] != data["historical_10m_policy_sha256"][key]
            ):
                raise ArithmeticError("historical ten-million policy changed: " + key)
    prior = data["planning_prior_seconds"]
    expected_bound = 2 * (4 * math.fsum(prior.values()) + 600) + 120
    if (
        set(prior)
        != {
            "wet_control_10m",
            "wet_candidate_10m",
            "dry_control_10m",
            "dry_candidate_10m",
        }
        or not math.isclose(
            expected_bound, data["planning_bound_seconds_not_admission"], abs_tol=1e-10
        )
        or expected_bound >= 7200
    ):
        raise ArithmeticError("historical planning bound changed")
    return data


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Use original qualified constructors, changing only the declared keys."""
    if arm not in (CONTROL, CANDIDATE):
        raise ValueError("outside fixed known-game arms")
    if game == GAMES[0]:
        return wet_context(root, game, arm)
    if game == GAMES[1]:
        return dry_context(root, game, arm)
    raise ValueError("outside fixed known-game grid")
