"""Frozen inputs and cached-result integrity for fixed-turn continuations."""

import gzip
import itertools
import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.opponent_decision_inputs import CONFIG_SHA as PRIOR_CONFIG_SHA
from poker_ai.evaluation.opponent_decision_view import load as load_prior
from poker_ai.evaluation.turn_continuation_math import PANELS
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

CONFIG = "configs/turn-continuations.json"
CONFIG_SHA = "f11617a633bb2abb78ceb3e25cd1750468e5c82493cd2e43a1964c1484b3a678"
FOLDER = "results/turn-continuations"
ENTRIES = (
    "scripts/diagnose_turn_continuations.py",
    "scripts/inspect_turn_continuations.py",
)


def contract(root: Path) -> dict[str, Any]:
    path = root / CONFIG
    if digest(path) != CONFIG_SHA:
        raise ArithmeticError("frozen continuation protocol changed")
    result: dict[str, Any] = json.loads(path.read_text())
    return result


def prior(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    folder = root / config["decision_folder"]
    if (
        not folder.resolve().is_relative_to(root.resolve())
        or config["decision_config_sha256"] != PRIOR_CONFIG_SHA
        or digest(folder / "manifest.json") != config["decision_manifest_sha256"]
        or digest(folder / "summary.json") != config["decision_summary_sha256"]
    ):
        raise ArithmeticError("bound prior saved-decision evidence changed")
    summaries, _ = load_prior(root, folder)
    return summaries


def validate_response(response: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    """Finite complete menus/support and ROOT accounting; no per-row ordering."""
    json.dumps((response, rows), allow_nan=False)
    target = response["target"]
    roots = response["root_values_chips"]
    increments = response["root_increments_chips"]
    infos = response["turn_info_ids"]
    if (
        type(target) is not int
        or target not in (0, 1)
        or set(roots) != set(PANELS)
        or any(type(v) not in (int, float) for v in roots.values())
        or len(increments) != 3
        or any(type(v) not in (int, float) for v in increments)
        or infos != sorted(set(infos))
        or any(type(i) is not int or i < 0 for i in infos)
        or [r["exact_info"] for r in rows] != infos
    ):
        raise ArithmeticError("complete ordered continuation panels/turn rows required")
    values = [roots[name] for name in PANELS]
    errors = [
        abs((b - a) - g)
        for a, b, g in zip(values, values[1:], increments, strict=False)
    ]
    errors.append(abs(sum(increments) - response["source_unilateral_gain_chips"]))
    if any(g < -1e-9 for g in increments) or any(e > 1e-9 for e in errors):
        raise ArithmeticError("continuation root stage ordering/accounting changed")
    for row in rows:
        count = len(row["actions"])
        q = row["conditional_action_values_chips"]
        p = row["saved_probabilities"]
        if (
            type(row["exact_info"]) is not int
            or row["support"] < 0
            or row["saved_reach_mass"] < 0
            or row["prior_loss_chips"] < -1e-9
            or not count
            or len(p) != count
            or any(x < 0 for x in p)
            or abs(sum(p) - 1) > 1e-12
            or set(q) != set(PANELS)
            or any(len(v) != count for v in q.values())
            or any(type(v) not in (int, float) for values in q.values() for v in values)
            or (row["support"] == 0 and any(any(v) for v in q.values()))
        ):
            raise ArithmeticError(
                "invalid continuation turn menu/support/action values"
            )
    available = {r["exact_info"]: r for r in rows}
    if response["supported_turn_rows"] != sum(r["support"] > 0 for r in rows):
        raise ArithmeticError("supported turn-row count changed")
    groups = response["top_turn_groups"]
    if len({g["abstract_info"] for g in groups}) != len(groups):
        raise ArithmeticError("duplicate displayed continuation group")
    for group in groups:
        expected = [
            r["exact_info"]
            for r in rows
            if r["abstract_info"] == group["abstract_info"] and r["support"] > 0
        ]
        if group["infos"] != expected or any(
            i not in available for i in group["infos"]
        ):
            raise ArithmeticError(
                "displayed group contains missing/unsupported turn rows"
            )


def validate_profiles(profiles: list[dict[str, Any]], config: dict[str, Any]) -> None:
    expected = set(itertools.product(config["games"], config["seeds"], config["arms"]))
    if (
        len(profiles) != 24
        or {(p["game"], p["seed"], p["arm"]) for p in profiles} != expected
        or any([r["target"] for r in p["responses"]] != [0, 1] for p in profiles)
        or any(
            type(p["coordinate"]) is not int
            or p["coordinate"]
            != 3 * config["games"].index(p["game"]) + config["seeds"].index(p["seed"])
            for p in profiles
        )
        or sum(len(r["root_values_chips"]) for p in profiles for r in p["responses"])
        != 192
    ):
        raise ArithmeticError("complete24/48/192 continuation inventory required")


def load(root: Path, folder: Path) -> list[dict[str, Any]]:
    """Check bound input/output hashes and schema; full math is a separate run."""
    config = contract(root)
    prior(root, config)
    if (folder / "failure.json").exists() or any(folder.rglob("*.tmp")):
        raise ArithmeticError("refuse failed/interrupted continuation cache")
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest["status"] != "complete_fixed_turn_continuations"
        or manifest["config_sha256"] != CONFIG_SHA
        or manifest["source_sha256"] != sha(manifest["source"]["sha256"])
        or [manifest[k] for k in ("profiles", "responses", "root_values")]
        != [24, 48, 192]
        or manifest["constructors_blocked"] is not True
        or manifest["maximum_seconds"] != config["maximum_seconds"]
        or type(manifest["seconds"]) not in (int, float)
        or not 0 <= manifest["seconds"] <= config["maximum_seconds"]
        or any(
            manifest[k] is not False
            for k in (
                "training_performed",
                "reference_constructed",
                "new_independent_audit",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
        or manifest["decision_manifest_sha256"] != config["decision_manifest_sha256"]
    ):
        raise ArithmeticError(
            "complete source-bound data-only continuation receipt required"
        )
    check_source(root, manifest["source"])
    expected = {
        f"details/{coordinate:02d}-{arm}.json.gz"
        for coordinate in range(6)
        for arm in config["arms"]
    } | {"summary.json", "partial.json"}
    if set(manifest["outputs"]) != expected:
        raise ArithmeticError("complete continuation output inventory required")
    for name, expected_sha in manifest["outputs"].items():
        path = folder / name
        if (
            not path.resolve().is_relative_to(folder.resolve())
            or digest(path) != expected_sha
        ):
            raise ArithmeticError("cached continuation output bytes changed")
    profiles: list[dict[str, Any]] = json.loads((folder / "summary.json").read_text())[
        "profiles"
    ]
    validate_profiles(profiles, config)
    for profile in profiles:
        expected_name = f"details/{profile['coordinate']:02d}-{profile['arm']}.json.gz"
        if profile["details_file"] != expected_name or expected_name not in expected:
            raise ArithmeticError("continuation detail identity changed")
        with gzip.open(folder / expected_name, "rt") as stream:
            detail = json.load(stream)
        if any(
            detail[k] != profile[k]
            for k in ("coordinate", "game", "seed", "arm", "source_id")
        ):
            raise ArithmeticError("continuation profile/detail identity mismatch")
        if [r["target"] for r in detail["responses"]] != [0, 1]:
            raise ArithmeticError("both ordered continuation detail seats required")
        for response, full in zip(
            profile["responses"], detail["responses"], strict=True
        ):
            validate_response(response, full["turn_rows"])
            response["turn_rows"] = full["turn_rows"]
    if type(manifest["turn_rows"]) is not int or manifest["turn_rows"] != sum(
        len(r["turn_rows"]) for p in profiles for r in p["responses"]
    ):
        raise ArithmeticError("complete turn-row total changed")
    return profiles
