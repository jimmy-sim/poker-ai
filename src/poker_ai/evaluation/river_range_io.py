"""Bound read-only inputs, complete local-panel schemas and cached integrity."""

import gzip
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.river_range_math import local_group
from poker_ai.evaluation.turn_continuation_io import load as load_continuations
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

CONFIG = "configs/river-range-reweighting.json"
CONFIG_SHA = "1a54c73475a6d41abe3a4b8f24ed48ed2fae43cda7a7b0f7eeceb1353a8db321"
FOLDER = "results/river-range-reweighting"
ENTRIES = (
    "scripts/diagnose_river_range_weights.py",
    "scripts/inspect_river_range_weights.py",
)
SUFFIXES = ("fine_reply", "restricted_reply")
WEIGHTS = ("actual_posterior", "compatible_prior")
GROUPS = ("declared_partition", "full_static_probe_refinement")


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("frozen river range-weight protocol changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return result


def prior(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    for prefix, config_file in (
        ("continuation", "configs/turn-continuations.json"),
        ("decision", "configs/own-opponent-decisions.json"),
    ):
        folder = root / config[prefix + "_folder"]
        if (
            not folder.resolve().is_relative_to(root.resolve())
            or digest(root / config_file) != config[prefix + "_config_sha256"]
            or digest(folder / "manifest.json") != config[prefix + "_manifest_sha256"]
        ):
            raise ArithmeticError("bound range-weight source evidence changed")
    continuation = root / config["continuation_folder"]
    if digest(continuation / "summary.json") != config["continuation_summary_sha256"]:
        raise ArithmeticError("bound continuation summary changed")
    # This checks both cached publications and all original own/native/source
    # pins. It does not rerun the original full mathematical archive replay.
    load_continuations(root, continuation)
    result: list[dict[str, Any]] = json.loads(
        (root / config["decision_folder"] / "summary.json").read_text()
    )["profiles"]
    return result


def validate_profiles(profiles: list[dict[str, Any]], config: dict[str, Any]) -> None:
    json.dumps(profiles, allow_nan=False)
    expected = set(itertools.product(config["games"], config["seeds"], config["arms"]))
    if (
        len(profiles) != 24
        or len({p["source_id"] for p in profiles}) != 24
        or {(p["game"], p["seed"], p["arm"]) for p in profiles} != expected
    ):
        raise ArithmeticError("complete24-profile local range panel required")
    count = 0
    for p in profiles:
        if type(p["coordinate"]) is not int or p["coordinate"] != 3 * config[
            "games"
        ].index(p["game"]) + config["seeds"].index(p["seed"]):
            raise ArithmeticError("local profile coordinate changed")
        if [r["target"] for r in p["responses"]] != [0, 1] or any(
            type(r["target"]) is not int for r in p["responses"]
        ):
            raise ArithmeticError("both ordered local responding seats required")
        for r in p["responses"]:
            if [s["suffix"] for s in r["suffixes"]] != list(SUFFIXES):
                raise ArithmeticError("both ordered own continuation suffixes required")
            if r["suffixes"][0]["river_info_ids"] != r["suffixes"][1]["river_info_ids"]:
                raise ArithmeticError(
                    "own suffixes must retain the same river inventory"
                )
            for s in r["suffixes"]:
                if [x["range_weights"] for x in s["panels"]] != list(WEIGHTS):
                    raise ArithmeticError("both ordered range-weight panels required")
                infos = s["river_info_ids"]
                if infos != sorted(set(infos)) or any(
                    type(i) is not int or i < 0 for i in infos
                ):
                    raise ArithmeticError(
                        "ordered unique river information rows required"
                    )
                for panel in s["panels"]:
                    count += 1
                    if set(panel["group_controls"]) != set(GROUPS):
                        raise ArithmeticError("both local grouping controls required")
                    for m in panel["group_controls"].values():
                        if (
                            not 0 <= m["supported_uniform_decision_weight"] <= 1 + 1e-12
                            or m["local_sharing_cost_chips_per_weighted_decision"]
                            < -1e-9
                            or any(
                                type(m[k]) is not int
                                for k in (
                                    "total_groups",
                                    "supported_groups",
                                    "strict_conflicting_groups",
                                )
                            )
                            or not 0
                            <= m["strict_conflicting_groups"]
                            <= m["supported_groups"]
                            <= m["total_groups"]
                            or not 0
                            <= m["maximum_posterior_total_variation_within_group"]
                            <= 1 + 1e-12
                            or (
                                p["arm"] == "fine_self"
                                and (
                                    m["local_sharing_cost_chips_per_weighted_decision"]
                                    != 0
                                    or m["strict_conflicting_groups"] != 0
                                )
                            )
                        ):
                            raise ArithmeticError(
                                "invalid local metrics/units/singleton control"
                            )
    if count != 192:
        raise ArithmeticError("complete48/96/192 local comparison inventory required")


def validate_suffix(
    summary: dict[str, Any], detail: dict[str, Any], combos: int
) -> None:
    """Validate cached local arithmetic without constructing an engine/learner."""
    json.dumps((summary, detail), allow_nan=False)
    rows = detail["rows"]
    infos = summary["river_info_ids"]
    if (
        detail["suffix"] != summary["suffix"]
        or [r["exact_info"] for r in rows] != infos
        or infos != sorted(set(infos))
        or any(type(i) is not int for i in infos)
        or [p["range_weights"] for p in summary["panels"]] != list(WEIGHTS)
    ):
        raise ArithmeticError("complete matching suffix river rows required")
    lookup = {r["exact_info"]: r for r in rows}
    for r in rows:
        n = len(r["actions"])
        compatible = r["compatible"]
        posterior = r["actual_posterior"]
        prior_weights = r["compatible_prior"]
        q = r["combo_action_values_chips"]
        numeric = (
            posterior
            + prior_weights
            + r["saved_probabilities"]
            + r["actual_action_values_chips"]
            + r["prior_action_values_chips"]
            + [v for vector in q for v in vector]
            + [
                r["counterfactual_support"],
                r["saved_reach_mass"],
                r["uniform_decision_weight"],
            ]
        )
        if (
            type(r["exact_info"]) is not int
            or type(r["abstract_info"]) is not int
            or not n
            or len(set(r["actions"])) != n
            or any(
                len(r[k]) != n
                for k in (
                    "actual_action_values_chips",
                    "prior_action_values_chips",
                    "saved_probabilities",
                )
            )
            or len(compatible) != combos
            or any(type(v) is not bool for v in compatible)
            or len(posterior) != combos
            or len(prior_weights) != combos
            or len(q) != combos
            or any(len(v) != n for v in q)
            or any(type(v) not in (int, float) for v in numeric)
            or any(v < 0 for v in posterior + prior_weights + r["saved_probabilities"])
            or abs(sum(prior_weights) - 1) > 1e-12
            or abs(sum(r["saved_probabilities"]) - 1) > 1e-12
            or r["counterfactual_support"] < 0
            or r["saved_reach_mass"] < 0
            or not 0 <= r["uniform_decision_weight"] <= 1 + 1e-12
            or abs(sum(posterior) - (1 if r["counterfactual_support"] > 0 else 0))
            > 1e-12
            or any(
                (posterior[k] != 0 or prior_weights[k] != 0 or any(q[k]))
                for k in range(combos)
                if not compatible[k]
            )
        ):
            raise ArithmeticError("invalid complete river combo/menu/support row")
        for pkey, qkey in (
            ("actual_posterior", "actual_action_values_chips"),
            ("compatible_prior", "prior_action_values_chips"),
        ):
            for a in range(n):
                expected = math.fsum(r[pkey][k] * q[k][a] for k in range(combos))
                if abs(expected - r[qkey][a]) > 1e-9:
                    raise ArithmeticError("cached local range mixture changed")
    total = math.fsum(r["uniform_decision_weight"] for r in rows)
    if rows and abs(total - 1) > 1e-12:
        raise ArithmeticError("fixed pre-filter river weighting changed")
    if set(detail["groups"]) != set(WEIGHTS):
        raise ArithmeticError("both detailed range panels required")
    ranked = [
        g for g in detail["groups"][WEIGHTS[0]][GROUPS[0]] if g["supported_rows"] > 0
    ]
    ranked.sort(key=lambda g: (-g["local_cost"], g["abstract_info"]))
    if summary["top_groups"] != ranked[:10]:
        raise ArithmeticError("supported deterministic local display inventory changed")
    for panel in summary["panels"]:
        name = panel["range_weights"]
        qfield = (
            "actual_action_values_chips"
            if name == WEIGHTS[0]
            else "prior_action_values_chips"
        )
        if set(detail["groups"][name]) != set(GROUPS):
            raise ArithmeticError("both detailed group controls required")
        for control, metrics in panel["group_controls"].items():
            groups = detail["groups"][name][control]
            if sorted(i for g in groups for i in g["infos"]) != infos or len(
                {g["group_id"] for g in groups}
            ) != len(groups):
                raise ArithmeticError(
                    "complete disjoint local group inventory required"
                )
            costs, flags, weights = [], [], []
            for group in groups:
                members = [lookup[i] for i in group["infos"]]
                active = [r for r in members if r["counterfactual_support"] > 0]
                if group["supported_infos"] != [r["exact_info"] for r in active] or any(
                    r["abstract_info"] != group["abstract_info"] for r in members
                ):
                    raise ArithmeticError(
                        "local group changed support/parent partition"
                    )
                menus = {tuple(r["actions"]) for r in members}
                if len(menus) != 1 or (
                    control == GROUPS[1]
                    and len({canonical_static(r) for r in members}) != 1
                ):
                    raise ArithmeticError(
                        "local group changes concrete menu/static signature"
                    )
                width = len(next(iter(menus)))
                measured = local_group(
                    np.array([r[qfield] for r in active], dtype=np.float64).reshape(
                        len(active), width
                    ),
                    np.array([r["uniform_decision_weight"] for r in active]),
                )
                if (
                    abs(float(measured["local_cost"]) - group["local_cost"]) > 1e-9
                    or measured["strict_conflict"] != group["strict_conflict"]
                    or measured["supported_rows"] != group["supported_rows"]
                    or abs(float(measured["weight"]) - group["weight"]) > 1e-12
                ):
                    raise ArithmeticError("cached group local arithmetic changed")
                costs.append(group["local_cost"])
                flags.append(group["strict_conflict"])
                weights.append(group["weight"])
            if (
                len(groups) != metrics["total_groups"]
                or sum(bool(g["supported_infos"]) for g in groups)
                != metrics["supported_groups"]
                or sum(flags) != metrics["strict_conflicting_groups"]
                or abs(
                    math.fsum(costs)
                    - metrics["local_sharing_cost_chips_per_weighted_decision"]
                )
                > 1e-9
                or abs(
                    math.fsum(weights) - metrics["supported_uniform_decision_weight"]
                )
                > 1e-12
            ):
                raise ArithmeticError("cached local aggregate accounting changed")


def canonical_static(row: dict[str, Any]) -> str:
    return json.dumps(row["static_features"], sort_keys=True, separators=(",", ":"))


def load(root: Path, folder: Path) -> list[dict[str, Any]]:
    config = contract(root)
    prior(root, config)
    if (folder / "failure.json").exists() or any(folder.rglob("*.tmp")):
        raise ArithmeticError("refuse failed/interrupted local range cache")
    m = json.loads((folder / "manifest.json").read_text())
    json.dumps(m, allow_nan=False)
    if (
        m["status"] != "complete_local_river_range_reweighting"
        or m["config_sha256"] != CONFIG_SHA
        or m["source_sha256"] != sha(m["source"]["sha256"])
        or [
            m[k] for k in ("profiles", "responses", "suffix_conditions", "local_panels")
        ]
        != [24, 48, 96, 192]
        or m["constructors_blocked"] is not True
        or m["continuation_manifest_sha256"] != config["continuation_manifest_sha256"]
        or m["maximum_seconds"] != 900
        or type(m["seconds"]) not in (int, float)
        or not 0 <= m["seconds"] <= 900
        or any(
            m[k] is not False
            for k in (
                "training_performed",
                "reference_constructed",
                "new_independent_audit",
                "feature_deployed",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
    ):
        raise ArithmeticError("complete source-bound local-only range receipt required")
    check_source(root, m["source"])
    expected = {
        f"details/{i:02d}-{a}.json.gz" for i in range(6) for a in config["arms"]
    } | {"summary.json", "partial.json", "panels.csv"}
    if set(m["outputs"]) != expected:
        raise ArithmeticError("complete local range output inventory required")
    for name, h in m["outputs"].items():
        p = folder / name
        if not p.resolve().is_relative_to(folder.resolve()) or digest(p) != h:
            raise ArithmeticError("cached local range output bytes changed")
    result: list[dict[str, Any]] = json.loads((folder / "summary.json").read_text())[
        "profiles"
    ]
    validate_profiles(result, config)
    profile_rows = sum(
        len(r["suffixes"][0]["river_info_ids"]) for p in result for r in p["responses"]
    )
    if (
        m["profile_river_rows"] != profile_rows
        or m["suffix_river_rows"] != 2 * profile_rows
        or m["group_control_csv_rows"] != 384
        or not 0 <= m["maximum_source_chip_error"] <= 1e-9
        or not 0 <= m["maximum_unitless_error"] <= 1e-12
    ):
        raise ArithmeticError("complete local row totals/source bounds required")
    for p in result:
        name = f"details/{p['coordinate']:02d}-{p['arm']}.json.gz"
        if p["details_file"] != name:
            raise ArithmeticError("local range detail path changed")
        p["_detail_sha256"] = m["outputs"][name]
    return result


def load_detail(folder: Path, profile: dict[str, Any]) -> dict[str, Any]:
    expected = f"details/{profile['coordinate']:02d}-{profile['arm']}.json.gz"
    if profile["details_file"] != expected:
        raise ArithmeticError("local range detail identity changed")
    if digest(folder / expected) != profile["_detail_sha256"]:
        raise ArithmeticError("lazy cached local detail bytes changed")
    with gzip.open(folder / expected, "rt") as stream:
        detail: dict[str, Any] = json.load(stream)
    if any(
        detail[k] != profile[k]
        for k in ("coordinate", "game", "seed", "arm", "source_id")
    ) or [r["target"] for r in detail["responses"]] != [0, 1]:
        raise ArithmeticError("matching ordered local range detail profile required")
    for response, full in zip(profile["responses"], detail["responses"], strict=True):
        combos = len(full["declared_opponent_range"])
        if not combos or [s["suffix"] for s in full["suffixes"]] != list(SUFFIXES):
            raise ArithmeticError(
                "complete ordered local suffix/range details required"
            )
        for summary, suffix in zip(response["suffixes"], full["suffixes"], strict=True):
            validate_suffix(summary, suffix, combos)
    return detail
