"""Bind prospective PR #119 inputs before any mixed-policy trace."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_half_policy_mixture.plan import GAMES

CONTRACT = Path("configs/known-mixture-residual-map.json")
PROTOCOL = Path("docs/known-mixture-residual-map.md")
CONTRACT_SHA256 = "8cd5083d6e420db87942c6a44684639e73ec2817bad4ad810ccfca3af1ab4850"
PROTOCOL_SHA256 = "dec84465b26b9d4175c6a5ccef27abf54fd2884d0f5960bb8908b74dfb88b2a2"
PROTOCOL_COMMIT = "0edb30a2836af4f11b0a99e60f4ee695e4ff7051"
INPUT_FILES = (
    (
        "mixed_own_manifest_sha256",
        "results/known-turn-half-policy-mixture/own/manifest.json",
    ),
    (
        "mixed_own_result_sha256",
        "results/known-turn-half-policy-mixture/own/result.json",
    ),
    (
        "mixed_report_manifest_sha256",
        "results/known-turn-half-policy-mixture/report/manifest.json",
    ),
    (
        "mixed_report_sha256",
        "results/known-turn-half-policy-mixture/report/report.json",
    ),
    (
        "mixed_native_manifest_sha256",
        "results/known-turn-half-policy-mixture/native/manifest.json",
    ),
    (
        "parent_report_manifest_sha256",
        "results/known-turn-collision-medium-transfer/report/manifest.json",
    ),
    (
        "parent_report_sha256",
        "results/known-turn-collision-medium-transfer/report/report.json",
    ),
    ("lock_sha256", "uv.lock"),
)


def digest(path: Path) -> str:
    """Hash exact published bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract(root: Path) -> dict[str, Any]:
    """Require exact published protocol and every fixed prior input byte."""
    if (
        digest(root / CONTRACT) != CONTRACT_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published residual-map protocol changed")
    for path in (CONTRACT, PROTOCOL):
        published = subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        )
        if (root / path).read_bytes() != published:
            raise ArithmeticError("residual-map protocol differs from Git publication")
    data: dict[str, Any] = json.loads((root / CONTRACT).read_bytes())
    if (
        data["issue"] != 4
        or data["question"] != "saved_mixed_policy_residual_map"
        or tuple(data["games"]) != GAMES
        or len(data["mixed_files"]) != 4
        or data["seed_metadata"] != 0
        or data["stochastic_rng_used"] is not False
        or data["mixed_rows_per_game"] != 8340
        or data["initial_pot_chips"] != 36
        or data["arithmetic_tolerance_chips"] != 1e-9
        or data["row_nonnegative_slack_chips"] != 1e-12
        or data["turn_or_river_dominant_share"] != 0.60
        or data["concentrated_top_ten_share"] != 0.50
        or data["ranked_rows_per_street"] != 5
        or data["ranked_positive_rows_per_street"] != 10
        or data["forecast_seconds"] != 688.326
        or data["proof_cap_seconds"] != 180
        or data["own_cap_seconds"] != 900
        or data["peak_rss_bytes_exclusive"] != 1_500_000_000
    ):
        raise ArithmeticError("fixed residual-map contract changed")
    for index, item in enumerate(data["mixed_files"]):
        expected = (
            f"results/known-turn-half-policy-mixture/own/game{index:02d}-mixed.json.gz"
        )
        if item["path"] != expected or digest(root / expected) != item["sha256"]:
            raise ArithmeticError("fixed mixed snapshot changed")
    for field, relative_path in INPUT_FILES:
        if digest(root / relative_path) != data[field]:
            raise ArithmeticError(
                "fixed residual-map prerequisite changed: " + relative_path
            )
    return data
