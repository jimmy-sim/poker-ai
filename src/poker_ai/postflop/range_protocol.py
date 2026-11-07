"Prospective range-mass input binding and pure metric contracts; no learner."

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.range_mass import (
    MASS_ORDER,
    VERSION,
    RangeContext,
    RangeMassAbstraction,
    RangePrior,
)
from poker_ai.postflop.game import Spot, load_spot
from poker_ai.postflop.made_admission import build_representation
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree

CANDIDATE = "texture_range_q8_b8"
CONTROLS = ["exact", "public_b8", "texture_b8", "texture_made_b8", CANDIDATE]


def range_context(spot: Spot) -> RangeContext:
    first, second = (
        RangePrior.create((h.cards, h.weight) for h in prior) for prior in spot.ranges
    )
    return RangeContext((first, second))


def build_representation_control(
    source: SpotTree, name: str, model: CardAbstraction
) -> MatrixTree:
    if name == CANDIDATE:
        encoder = RangeMassAbstraction(model, range_context(source.spot))
        return MatrixTree.build(source, "texture_b8", encoder)
    return build_representation(source, name, model)


def validate_protocol(config: dict[str, Any]) -> None:
    limits = config["full_limits"]
    later = config["later_sampled"]
    if (
        config["schema_version"] != 1
        or config["status"] != "preregistered_correctness_only"
        or config["candidate"] != CANDIDATE
        or config["representations"] != CONTROLS
        or config["feature_version"] != VERSION
        or config["mass_intervals"] != 8
        or config["feature_order"] != list(MASS_ORDER)
        or config["feature_streets"] != [5]
        or config["range_semantics"]
        != "fixed declared prior; unconditional normalized mass; no betting posterior"
        or not config["spot_files"]
        or len(set(config["spot_files"])) != len(config["spot_files"])
        or set(config["spot_sha256"]) != set(config["spot_files"])
        or config["full_tree_backend"] != "fused_numba"
        or later["status"] != "not_run"
    ):
        raise ValueError("invalid prospective range-mass protocol")
    for values in (
        config["full_tree_checkpoints"],
        later["node_work_checkpoints"],
        later["seeds"],
    ):
        if (
            not values
            or values != sorted(set(values))
            or any(type(v) is not int or v < 1 for v in values)
        ):
            raise ValueError("invalid fixed checkpoint/seed list")
    if (
        set(limits)
        != {
            "exact_full_exploitability_pot",
            "candidate_full_excess_pot",
            "candidate_information_sets_relative_to_public_b8",
            "minimum_uniform_reach_average_coverage",
            "maximum_recall_violations",
            "independent_tolerance_chips",
        }
        or any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
            for v in limits.values()
        )
        or limits["maximum_recall_violations"] != 0
        or not 0 < limits["independent_tolerance_chips"] <= 1e-8
    ):
        raise ValueError("invalid full-stage limits")
    for key in ("median_exploitability_pot_limit", "worst_exploitability_pot_limit"):
        if type(later[key]) not in (int, float) or not math.isfinite(later[key]):
            raise ValueError("invalid sampled limit")
    if (
        later["sampling"] != "ordinary_external"
        or later["weighting"] != "linear"
        or later["initial_exact_expectation"] is not True
        or not 0
        <= later["median_exploitability_pot_limit"]
        <= later["worst_exploitability_pot_limit"]
        <= 1
    ):
        raise ValueError("invalid sampled-stage protocol")
    for value in (
        config["maximum_full_seconds"],
        config["maximum_tree_nodes"],
        later["maximum_seconds"],
        later["profile_iterations"],
        later["profile_repetitions"],
    ):
        if type(value) is not int or value < 1:
            raise ValueError("invalid fixed budget")


def check_inputs(root: Path, config: dict[str, Any]) -> dict[str, str]:
    "Verify fixed files before creating contexts; never builds/trains a game tree."
    validate_protocol(config)
    files = {
        config["model"]: config["model_sha256"],
        config["motivation_file"]: config["motivation_sha256"],
        **config["spot_sha256"],
    }
    if any(digest(root / name) != sha for name, sha in files.items()):
        raise ArithmeticError("range protocol input hash changed")
    return {
        name: range_context(load_spot(root / name)).identifier
        for name in config["spot_files"]
    }


def _number(row: dict[str, Any], key: str, maximum: float | None = None) -> float:
    value = row[key]
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or value < 0
        or (maximum is not None and value > maximum)
    ):
        raise ValueError(f"invalid metric {key}")
    return float(value)


def _grid(
    rows: list[dict[str, Any]], fields: tuple[str, ...], expected: set[tuple[Any, ...]]
) -> bool:
    for row in rows:
        if any(
            type(row[k]) is not int
            for k in fields
            if k in ("iteration", "seed", "node_work_checkpoint")
        ):
            raise ValueError("checkpoint/seed identities must be integers")
    ids = [tuple(r[k] for k in fields) for r in rows]
    return len(ids) == len(set(ids)) and set(ids) == expected


def _binding(rows: list[dict[str, Any]], contexts: dict[str, str]) -> bool:
    return all(
        r.get("range_context_sha256")
        == (contexts.get(r["spot_file"]) if r["representation"] == CANDIDATE else None)
        for r in rows
    )


def _contract_id(config: dict[str, Any], contexts: dict[str, str]) -> str:
    payload = ["range-mass-metric-contract-v1", config, contexts]
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def assess_full_metrics(
    rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    native: list[dict[str, Any]],
    config: dict[str, Any],
    contexts: dict[str, str],
    *,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Pure hypothetical metric gate; actual source/policy/work replay is separate.

    This function does not load or authenticate experiment receipts. Tests supply
    synthetic numbers. Future callers must verify raw policies and complete audit
    bindings before using a positive result as actual study admission.
    """
    validate_protocol(config)
    elapsed = _number({"elapsed": elapsed_seconds}, "elapsed")
    expected = {
        (p, e, t)
        for p in config["spot_files"]
        for e in CONTROLS
        for t in config["full_tree_checkpoints"]
    }
    complete = (
        _grid(rows, ("spot_file", "representation", "iteration"), expected)
        and _grid(native, ("spot_file", "representation", "iteration"), expected)
        and _grid(
            diagnostics,
            ("spot_file", "representation"),
            {(p, e) for p in config["spot_files"] for e in CONTROLS},
        )
    )
    for r in rows:
        _number(r, "exploitability_pot_fraction")
        _number(r, "uniform_reach_average_row_coverage", 1)
    for d in diagnostics:
        if (
            type(d["information_sets"]) is not int
            or d["information_sets"] < 1
            or type(d["recall_violations"]) is not int
            or d["recall_violations"] < 0
            or type(d["tree_nodes"]) is not int
            or not 1 <= d["tree_nodes"] <= config["maximum_tree_nodes"]
        ):
            raise ValueError("invalid partition metrics")
    limits = config["full_limits"]
    native_ok = all(
        _number(r, k) <= limits["independent_tolerance_chips"]
        for r in native
        for k in ("value_error_chips", "exploitability_error_chips")
    )
    binding = set(contexts) == set(config["spot_files"]) and _binding(
        rows + diagnostics + native, contexts
    )
    by_diag = {(d["spot_file"], d["representation"]): d for d in diagnostics}
    work_ok = True
    for r in rows:
        work = r["total_node_work"]
        if type(work) is not int or work < 0:
            raise ValueError("invalid full node-work count")
        diag = by_diag.get((r["spot_file"], r["representation"]))
        work_ok = (
            work_ok
            and diag is not None
            and work == 2 * r["iteration"] * diag["tree_nodes"]
        )
    budget_ok = elapsed <= config["maximum_full_seconds"]
    checks = []
    for path in config["spot_files"]:
        final = {
            r["representation"]: r
            for r in rows
            if r["spot_file"] == path
            and r["iteration"] == config["full_tree_checkpoints"][-1]
        }
        diag = {d["representation"]: d for d in diagnostics if d["spot_file"] == path}
        if set(final) != set(CONTROLS) or set(diag) != set(CONTROLS):
            checks.append(
                {"spot_file": path, "passed": False, "reason": "missing final metrics"}
            )
            continue
        exact = final["exact"]["exploitability_pot_fraction"]
        candidate = final[CANDIDATE]["exploitability_pot_fraction"]
        ratio = (
            diag[CANDIDATE]["information_sets"] / diag["public_b8"]["information_sets"]
        )
        criteria = {
            "exact_accuracy": exact <= limits["exact_full_exploitability_pot"],
            "candidate_accuracy": candidate - exact
            <= limits["candidate_full_excess_pot"],
            "compression": ratio
            <= limits["candidate_information_sets_relative_to_public_b8"],
            "coverage": min(
                r["uniform_reach_average_row_coverage"] for r in final.values()
            )
            >= limits["minimum_uniform_reach_average_coverage"],
            "recall": all(d["recall_violations"] == 0 for d in diag.values()),
        }
        checks.append(
            {"spot_file": path, "passed": all(criteria.values()), "criteria": criteria}
        )
    passed = (
        complete
        and binding
        and native_ok
        and work_ok
        and budget_ok
        and all(r["passed"] for r in checks)
    )
    return {
        "complete": complete,
        "context_binding": binding,
        "native_metrics_passed": native_ok and complete,
        "work_metrics_passed": work_ok and complete,
        "budget_passed": budget_ok,
        "checks": checks,
        "eligible_for_sampled_comparison": passed,
        "contract_sha256": _contract_id(config, contexts),
        "fresh_global_admission": False,
        "scope": (
            "metric thresholds only; real source/policy/work replay remains required"
        ),
    }


def assess_sampled_metrics(
    rows: list[dict[str, Any]],
    native: list[dict[str, Any]],
    full: dict[str, Any],
    config: dict[str, Any],
    contexts: dict[str, str],
    *,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Pure numeric threshold/receipt contract, never a raw-policy verifier."""
    validate_protocol(config)
    elapsed = _number({"elapsed": elapsed_seconds}, "elapsed")
    later, limits = config["later_sampled"], config["full_limits"]
    expected = {
        (p, e, s, w)
        for p in config["spot_files"]
        for e in CONTROLS
        for s in later["seeds"]
        for w in later["node_work_checkpoints"]
    }
    fields = ("spot_file", "representation", "seed", "node_work_checkpoint")
    complete = _grid(rows, fields, expected) and _grid(native, fields, expected)
    work_ok, method_ok, recall_ok = True, True, True
    for row in rows:
        _number(row, "exploitability_pot_fraction")
        _number(row, "uniform_reach_average_row_coverage", 1)
        for key in (
            "total_node_work",
            "previous_node_work",
            "last_iteration_node_work",
            "initialization_node_work",
            "recall_violations",
        ):
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError("invalid sampled work/recall count")
        work_ok = work_ok and (
            0
            < row["initialization_node_work"]
            <= row["previous_node_work"]
            < row["node_work_checkpoint"]
            <= row["total_node_work"]
            and row["total_node_work"] - row["previous_node_work"]
            == row["last_iteration_node_work"]
            > 0
        )
        method_ok = method_ok and (
            row["sampling"] == later["sampling"]
            and row["weighting"] == later["weighting"]
            and row["initial_exact_expectation"] is True
        )
        recall_ok = recall_ok and row["recall_violations"] == 0
    binding = set(contexts) == set(config["spot_files"]) and _binding(
        rows + native, contexts
    )
    native_ok = all(
        _number(r, k) <= limits["independent_tolerance_chips"]
        for r in native
        for k in ("value_error_chips", "exploitability_error_chips")
    )
    checks = []
    for path in config["spot_files"]:
        for name in ("exact", CANDIDATE):
            final = [
                r
                for r in rows
                if r["spot_file"] == path
                and r["representation"] == name
                and r["node_work_checkpoint"] == later["node_work_checkpoints"][-1]
            ]
            seeds = {r["seed"] for r in final}
            if seeds != set(later["seeds"]) or len(final) != len(seeds):
                checks.append(
                    {"spot_file": path, "representation": name, "passed": False}
                )
                continue
            values = [r["exploitability_pot_fraction"] for r in final]
            passed = (
                statistics.median(values) <= later["median_exploitability_pot_limit"]
                and max(values) <= later["worst_exploitability_pot_limit"]
            )
            checks.append({"spot_file": path, "representation": name, "passed": passed})
    final_rows = [
        r
        for r in rows
        if r["node_work_checkpoint"] == later["node_work_checkpoints"][-1]
    ]
    coverage_ok = all(
        r["uniform_reach_average_row_coverage"]
        >= limits["minimum_uniform_reach_average_coverage"]
        for r in final_rows
    )
    budget_ok = elapsed <= later["maximum_seconds"]
    passed = (
        full.get("eligible_for_sampled_comparison") is True
        and full.get("contract_sha256") == _contract_id(config, contexts)
        and complete
        and binding
        and native_ok
        and work_ok
        and method_ok
        and recall_ok
        and coverage_ok
        and budget_ok
        and all(r["passed"] for r in checks)
    )
    return {
        "complete": complete,
        "context_binding": binding,
        "development_metrics_passed": passed,
        "work_metrics_passed": work_ok and complete,
        "method_passed": method_ok,
        "recall_passed": recall_ok,
        "coverage_passed": coverage_ok,
        "budget_passed": budget_ok,
        "checks": checks,
        "fresh_global_admission": False,
        "scope": (
            "metric thresholds only; separate full replay/audit and "
            "frozen fresh design required"
        ),
    }
