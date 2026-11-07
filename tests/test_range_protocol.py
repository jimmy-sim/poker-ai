"""Pure synthetic acceptance contracts; no candidate learning/performance data."""

import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop.range_protocol import (
    CANDIDATE,
    CONTROLS,
    assess_full_metrics,
    assess_sampled_metrics,
    check_inputs,
    validate_protocol,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def design() -> tuple[dict[str, Any], dict[str, str]]:
    c = json.loads((ROOT / "configs/range-mass-protocol.json").read_text())
    return c, check_inputs(ROOT, c)


def synthetic_full(
    c: dict[str, Any], contexts: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows, diagnostics, native = [], [], []
    for p in c["spot_files"]:
        for e in CONTROLS:
            identity = {
                "spot_file": p,
                "representation": e,
                "range_context_sha256": contexts[p] if e == CANDIDATE else None,
                "synthetic_fixture": True,
            }
            diagnostics.append(
                {
                    **identity,
                    "information_sets": 750 if e == CANDIDATE else 1000,
                    "recall_violations": 0,
                    "tree_nodes": 2000,
                }
            )
            for t in c["full_tree_checkpoints"]:
                rows.append(
                    {
                        **identity,
                        "iteration": t,
                        "exploitability_pot_fraction": 0.005 if e == CANDIDATE else 0.0,
                        "uniform_reach_average_row_coverage": 0.95,
                        "total_node_work": 2 * t * 2000,
                    }
                )
                native.append(
                    {
                        **identity,
                        "iteration": t,
                        "value_error_chips": 1e-9,
                        "exploitability_error_chips": 0.0,
                    }
                )
    return rows, diagnostics, native


def full_gate(c: dict[str, Any], contexts: dict[str, str]) -> dict[str, Any]:
    rows, diag, native = synthetic_full(c, contexts)
    return assess_full_metrics(rows, diag, native, c, contexts, elapsed_seconds=900)


def synthetic_sampled(
    c: dict[str, Any], contexts: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows, native = [], []
    for p in c["spot_files"]:
        for e in CONTROLS:
            for s, value in zip(
                c["later_sampled"]["seeds"], (0.005, 0.01, 0.025), strict=True
            ):
                for w in c["later_sampled"]["node_work_checkpoints"]:
                    identity = {
                        "spot_file": p,
                        "representation": e,
                        "seed": s,
                        "node_work_checkpoint": w,
                        "range_context_sha256": contexts[p] if e == CANDIDATE else None,
                        "synthetic_fixture": True,
                    }
                    rows.append(
                        {
                            **identity,
                            "exploitability_pot_fraction": value,
                            "uniform_reach_average_row_coverage": 0.95,
                            "total_node_work": w + 10,
                            "previous_node_work": w - 10,
                            "last_iteration_node_work": 20,
                            "initialization_node_work": 2000,
                            "recall_violations": 0,
                            "sampling": "ordinary_external",
                            "weighting": "linear",
                            "initial_exact_expectation": True,
                        }
                    )
                    native.append(
                        {
                            **identity,
                            "value_error_chips": 0.0,
                            "exploitability_error_chips": 1e-9,
                        }
                    )
    return rows, native


def test_pinned_inputs_and_limits_preserve_predecessor(
    design: tuple[dict[str, Any], dict[str, str]],
) -> None:
    c, contexts = design
    old = json.loads((ROOT / "configs/made-category-admission.json").read_text())
    assert c["full_limits"] == old["limits"]
    assert c["full_tree_checkpoints"] == old["full_tree_checkpoints"]
    for k in (
        "seeds",
        "node_work_checkpoints",
        "median_exploitability_pot_limit",
        "worst_exploitability_pot_limit",
    ):
        assert c["later_sampled"][k] == old["later_sampled_comparison"][k]
    assert set(contexts) == set(c["spot_files"]) and all(
        len(v) == 64 for v in contexts.values()
    )


def test_full_boundary_contract_is_synthetic_and_never_global(
    design: tuple[dict[str, Any], dict[str, str]],
) -> None:
    c, contexts = design
    r = full_gate(c, contexts)
    assert r["complete"] and r["eligible_for_sampled_comparison"]
    assert r["work_metrics_passed"] and r["budget_passed"]
    assert not r["fresh_global_admission"]
    assert "metric thresholds only" in r["scope"]


@pytest.mark.parametrize(
    "change",
    [
        "missing_row",
        "duplicate_row",
        "missing_audit",
        "duplicate_audit",
        "missing_diag",
        "duplicate_diag",
        "candidate_accuracy",
        "exact_accuracy",
        "compression",
        "coverage_other_control",
        "recall",
        "context",
        "audit_error",
        "work",
        "budget",
    ],
)
def test_full_contract_failures_are_not_accepted(
    design: tuple[dict[str, Any], dict[str, str]], change: str
) -> None:
    c, contexts = design
    rows, diag, native = synthetic_full(c, contexts)
    elapsed = 900.0
    target = next(
        r for r in rows if r["representation"] == CANDIDATE and r["iteration"] == 4096
    )
    if change == "missing_row":
        rows.pop()
    elif change == "duplicate_row":
        rows.append(rows[-1])
    elif change == "missing_audit":
        native.pop()
    elif change == "duplicate_audit":
        native.append(native[-1])
    elif change == "missing_diag":
        diag.pop()
    elif change == "duplicate_diag":
        diag.append(diag[-1])
    elif change == "candidate_accuracy":
        target["exploitability_pot_fraction"] = math.nextafter(0.005, 1)
    elif change == "exact_accuracy":
        next(
            r for r in rows if r["representation"] == "exact" and r["iteration"] == 4096
        )["exploitability_pot_fraction"] = math.nextafter(0.001, 1)
    elif change == "compression":
        next(d for d in diag if d["representation"] == CANDIDATE)[
            "information_sets"
        ] = 751
    elif change == "coverage_other_control":
        next(
            r
            for r in rows
            if r["representation"] == "texture_b8" and r["iteration"] == 4096
        )["uniform_reach_average_row_coverage"] = math.nextafter(0.95, 0)
    elif change == "recall":
        diag[0]["recall_violations"] = 1
    elif change == "context":
        target["range_context_sha256"] = "wrong"
    elif change == "audit_error":
        native[0]["value_error_chips"] = math.nextafter(1e-9, 1)
    elif change == "work":
        target["total_node_work"] -= 1
    else:
        elapsed = 901.0
    assert not assess_full_metrics(
        rows, diag, native, c, contexts, elapsed_seconds=elapsed
    )["eligible_for_sampled_comparison"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("exploitability_pot_fraction", float("nan")),
        ("exploitability_pot_fraction", -1),
        ("uniform_reach_average_row_coverage", 1.1),
        ("iteration", True),
    ],
)
def test_invalid_full_numbers_rejected(
    design: tuple[dict[str, Any], dict[str, str]], key: str, value: Any
) -> None:
    c, contexts = design
    rows, diag, native = synthetic_full(c, contexts)
    rows[0][key] = value
    with pytest.raises(ValueError):
        assess_full_metrics(rows, diag, native, c, contexts, elapsed_seconds=1)


def test_sampled_boundary_and_full_stage_precondition(
    design: tuple[dict[str, Any], dict[str, str]],
) -> None:
    c, contexts = design
    rows, native = synthetic_sampled(c, contexts)
    full = full_gate(c, contexts)
    r = assess_sampled_metrics(rows, native, full, c, contexts, elapsed_seconds=7200)
    assert (
        r["complete"]
        and r["development_metrics_passed"]
        and not r["fresh_global_admission"]
    )
    full["eligible_for_sampled_comparison"] = False
    assert not assess_sampled_metrics(
        rows, native, full, c, contexts, elapsed_seconds=1
    )["development_metrics_passed"]


@pytest.mark.parametrize(
    "change",
    [
        "missing_seed",
        "duplicate",
        "missing_audit",
        "median",
        "worst",
        "coverage_other_control",
        "recall",
        "method",
        "initialization",
        "zero_initialization_work",
        "overshoot",
        "work_below_checkpoint",
        "context",
        "audit_error",
        "budget",
    ],
)
def test_sampled_contract_cannot_cherry_pick_or_skip_checks(
    design: tuple[dict[str, Any], dict[str, str]], change: str
) -> None:
    c, contexts = design
    rows, native = synthetic_sampled(c, contexts)
    elapsed = 7200.0
    target = next(
        r
        for r in rows
        if r["representation"] == CANDIDATE and r["node_work_checkpoint"] == 10000000
    )
    if change == "missing_seed":
        rows.remove(target)
    elif change == "duplicate":
        rows.append(target)
    elif change == "missing_audit":
        native.pop()
    elif change == "median":
        for r in rows:
            if (
                r["representation"] == CANDIDATE
                and r["node_work_checkpoint"] == 10000000
            ):
                r["exploitability_pot_fraction"] = 0.011
    elif change == "worst":
        target["exploitability_pot_fraction"] = 0.026
    elif change == "coverage_other_control":
        next(
            r
            for r in rows
            if r["representation"] == "texture_b8"
            and r["node_work_checkpoint"] == 10000000
        )["uniform_reach_average_row_coverage"] = 0.94
    elif change == "recall":
        target["recall_violations"] = 1
    elif change == "method":
        target["weighting"] = "uniform"
    elif change == "initialization":
        target["initial_exact_expectation"] = False
    elif change == "zero_initialization_work":
        target["initialization_node_work"] = 0
    elif change == "overshoot":
        target["previous_node_work"] = target["node_work_checkpoint"]
    elif change == "work_below_checkpoint":
        target["total_node_work"] = target["node_work_checkpoint"] - 1
    elif change == "context":
        target["range_context_sha256"] = "wrong"
    elif change == "audit_error":
        native[0]["exploitability_error_chips"] = 1e-8
    else:
        elapsed = 7201.0
    assert not assess_sampled_metrics(
        rows, native, full_gate(c, contexts), c, contexts, elapsed_seconds=elapsed
    )["development_metrics_passed"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("mass_intervals", 16),
        ("feature_streets", [4, 5]),
        ("range_semantics", "betting posterior"),
    ],
)
def test_protocol_rejects_semantic_changes(
    design: tuple[dict[str, Any], dict[str, str]], field: str, value: Any
) -> None:
    c, _ = design
    c = copy.deepcopy(c)
    c[field] = value
    with pytest.raises(ValueError):
        validate_protocol(c)


@pytest.mark.parametrize("field", ["model_sha256", "motivation_sha256", "spot_sha256"])
def test_changed_pinned_input_hashes_rejected(
    design: tuple[dict[str, Any], dict[str, str]], field: str
) -> None:
    c, _ = design
    c = copy.deepcopy(c)
    if field == "spot_sha256":
        c[field][c["spot_files"][0]] = "changed"
    else:
        c[field] = "changed"
    with pytest.raises(ArithmeticError, match="hash"):
        check_inputs(ROOT, c)


def test_full_pass_cannot_be_reused_across_range_contexts(
    design: tuple[dict[str, Any], dict[str, str]],
) -> None:
    config, contexts = design
    old_full = full_gate(config, contexts)
    different = dict(contexts)
    different[config["spot_files"][0]] = "f" * 64
    rows, native = synthetic_sampled(config, different)
    assessment = assess_sampled_metrics(
        rows, native, old_full, config, different, elapsed_seconds=1
    )
    assert assessment["complete"] and assessment["context_binding"]
    assert not assessment["development_metrics_passed"]
