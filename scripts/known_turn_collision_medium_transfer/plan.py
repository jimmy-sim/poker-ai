"""Published four-input conditional transfer contract and unchanged arms."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_work_budget.gate import source_fingerprint as previous_fingerprint
from river_generalization.selection import rank_signature
from river_strength.representation import build_river_candidate
from turn_exact_transfer.learning import PathSpec
from turn_exact_transfer.representation import exact_turn_candidate

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import parse_card
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import recall_violations
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.tree import SpotTree

CONFIG = Path("configs/known-turn-collision-medium-transfer.json")
PROTOCOL = Path("docs/known-turn-collision-medium-transfer.md")
CONFIG_SHA256 = "22dd4920162ffaa4edced960f9f4ec2a00784b5319041195c3899b8c1f428fde"
PROTOCOL_SHA256 = "a6d384f83bbc4565ef9fcf8dbef37c68b6c6d99355a8596075f02d47dbce6069"
PARENT = "436db1655f02f809f04231555a381f64ef346c70"
PROTOCOL_COMMIT = "682b5431e1ec7e2af7eb39d57a0dafa9a5e67e34"
CONTROL = "signed_full_q8_turn_exact_river"
CANDIDATE = "signed_full_exact_turn_river"
GAMES = (
    "collision_medium_dry_oop_a",
    "collision_medium_wet_oop_a",
    "collision_medium_dry_oop_b",
    "collision_medium_wet_oop_b",
)
LABELS = (10_000_000, 20_000_000, 40_000_000)
READOUTS = ("current", "linear_average")
PROFILE_WORK = 5_000_000
MAX_RSS = 1_500_000_000
SPOTS = Path("configs/known-turn-collision-medium-transfer-spots")


def digest(path: Path) -> str:
    """Hash one pinned input or publication byte string."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[PathSpec, ...]:
    """Controls first within each spot; parity defines the two workers."""
    return tuple(
        PathSpec(index, game, arm)
        for index, (game, arm) in enumerate(
            (game, arm) for game in GAMES for arm in (CONTROL, CANDIDATE)
        )
    )


def contract(root: Path) -> dict[str, Any]:
    """Require unchanged published protocol, old source and all 49 prior inputs."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published conditional transfer protocol changed")
    for path in (CONFIG, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("conditional protocol differs from Git publication")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    select = data["selection"]
    if (
        data["schema_version"] != 1
        or data["issue"] != 4
        or data["parent_merge"] != PARENT
        or tuple(row["name"] for row in select["strata"]) != GAMES
        or [row["texture"] for row in select["strata"]] != ["dry", "wet", "dry", "wet"]
        or {row["template"] for row in select["strata"]}
        != {"configs/learning-spots/dev_medium_oop.json"}
        or {row["position"] for row in select["strata"]} != {"oop"}
        or select["seed"] != 20261625
        or select["max_candidates_per_stratum"] != 20
        or select["max_board_draws_per_candidate"] != 10_000
        or select["max_tree_nodes"] != 200_000
        or select["private_combos_per_seat"] != 5
        or select["range_weight_values"] != [1, 2, 3]
        or select["minimum_collided_exact_turn_rows"] != 4
        or select["require_zero_river_collisions"] is not True
        or select["whole_cap_seconds"] != 900
        or select["failure_save_reserve_within_cap_seconds"] != 120
        or data["arms"] != [CONTROL, CANDIDATE]
        or data["training_seed_label"] != 0
        or data["training_seed_is_unused"] is not True
        or tuple(data["matched_work_labels"]) != LABELS
        or data["readouts"] != list(READOUTS)
        or data["profile"]["work_label"] != PROFILE_WORK
        or data["profile"]["repeats_per_path"] != 3
        or data["profile"]["paths"] != 24
        or data["profile"]["workers"] != 2
        or data["caps"]
        != {
            "proof_whole_seconds": 180,
            "profile_whole_seconds": 900,
            "own_whole_seconds": 7200,
            "audit_whole_seconds": 900,
            "max_worker_peak_rss_bytes": MAX_RSS,
            "failure_save_reserve_within_caps_seconds": 120,
        }
        or data["native"]["version"] != "OpenSpiel 2.0.2"
        or data["native"]["installed_license_sha256"]
        != "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
        or data["native"]["tolerance_chips"] != 1e-9
        or data["native"]["comparison_only"] is not True
        or data["default_promotion"] is not False
    ):
        raise ArithmeticError("fixed conditional transfer grid changed")
    old = data["prior_inspected_input_sha256"]
    if (
        len(old) != 49
        or len([name for name in old if name.startswith("configs/")]) != 24
        or len(
            [
                name
                for name in old
                if name.startswith("results/turn-collision-transfer/screen/attempts/")
            ]
        )
        != 25
    ):
        raise ArithmeticError("49 prior inspected inputs missing")
    for name, expected in {**old, **data["prerequisite_sha256"]}.items():
        if digest(root / name) != expected:
            raise ArithmeticError("pinned prior input changed: " + name)
    if (
        previous_fingerprint(root)
        != data["historical_source_fingerprints"]["pr114_work_budget"]
    ):
        raise ArithmeticError("historical PR114 source fingerprint changed")
    return data


def forbidden_signatures(
    root: Path, data: dict[str, Any]
) -> set[tuple[tuple[int, ...], int]]:
    """Exclude every prior inspected board rank pattern, regardless of suits."""
    return {
        rank_signature(
            [
                parse_card(card)
                for card in json.loads((root / name).read_bytes())["board"]
            ]
        )
        for name in data["prior_inspected_input_sha256"]
    }


def context(root: Path, game: str, arm: str) -> ScoringContext:
    """Construct the original q8 or exact acting-turn partition on one frozen spot."""
    if game not in GAMES or arm not in (CONTROL, CANDIDATE):
        raise ValueError("outside fixed conditional transfer grid")
    source = SpotTree.build(load_spot(root / SPOTS / f"{game}.json"))
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    control = build_river_candidate(source, model)
    exact = exact_turn_candidate(source, control)
    partition = control if arm == CONTROL else exact
    if recall_violations(partition):
        raise ArithmeticError("conditional transfer representation violates recall")
    masks = river_mask(exact, 0), river_mask(exact, 1)
    return ScoringContext(exact, partition, partition.exact_to_abstract, masks)
