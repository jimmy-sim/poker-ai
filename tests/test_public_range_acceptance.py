"""Fictional grids test thresholds; these are NEVER empirical poker receipts."""

import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import public_range_definition as definition
from poker_ai.postflop.public_range_acceptance import assess_full, assess_sampled

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    c = definition.contract(ROOT)
    assert definition.check_inputs(ROOT, c) == c["contexts"]
    return c


def full_fixture(
    c: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows, layouts, audit = [], [], []
    for p in c["spot_files"]:
        for rep in c["representations"]:
            base = dict(
                spot_file=p,
                representation=rep,
                context_sha256=c["contexts"][p],
                synthetic_fixture=True,
            )
            layouts.append(
                base
                | dict(
                    information_sets=750 if rep == definition.CANDIDATE else 1000,
                    tree_nodes=2000,
                    recall_violations=0,
                    menus_compatible=True,
                )
            )
            for t in c["full"]["checkpoints"]:
                identity = base | dict(iteration=t)
                rows.append(
                    identity
                    | dict(
                        exploitability_pot=0.005
                        if rep == definition.CANDIDATE
                        else 0.0,
                        coverage=0.95,
                        total_node_work=2 * t * 2000,
                    )
                )
                audit.append(
                    identity
                    | dict(value_error_chips=1e-9, exploitability_error_chips=0.0)
                )
    return rows, layouts, audit


def full_pass(c: dict[str, Any]) -> dict[str, Any]:
    return assess_full(*full_fixture(c), c, elapsed_seconds=900, audit_seconds=900)


def sampled_fixture(
    c: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows, audit = [], []
    for p in c["spot_files"]:
        for rep in c["representations"]:
            for seed in c["sampled"]["seeds"]:
                for work in c["sampled"]["node_work_checkpoints"]:
                    for readout in c["sampled"]["readouts"]:
                        identity = dict(
                            spot_file=p,
                            representation=rep,
                            seed=seed,
                            work_checkpoint=work,
                            readout=readout,
                            context_sha256=c["contexts"][p],
                            synthetic_fixture=True,
                        )
                        method = {
                            k: c["sampled"][k]
                            for k in (
                                "sampling",
                                "batch_size",
                                "regret_mode",
                                "regret_weighting",
                                "average_weighting",
                                "initial_exact_expectation",
                            )
                        }
                        rows.append(
                            identity
                            | method
                            | dict(
                                exploitability_pot=0.01 if readout == "linear" else 0.9,
                                coverage=0.95,
                                tree_nodes=2000,
                                information_sets=750
                                if rep == definition.CANDIDATE
                                else 1000,
                                recall_violations=0,
                                menus_compatible=True,
                                total_node_work=work + 3,
                                previous_node_work=work - 7,
                                last_iteration_work=10,
                                initialization_work=4000,
                            )
                        )
                        audit.append(
                            identity
                            | dict(
                                value_error_chips=1e-9, exploitability_error_chips=0.0
                            )
                        )
    return rows, audit


def test_frozen_inputs_and_historical_limits_unchanged(config: dict[str, Any]) -> None:
    old = json.loads((ROOT / "configs/range-mass-protocol.json").read_text())
    assert config["full"]["limits"] == old["full_limits"]
    assert config["full"]["checkpoints"] == old["full_tree_checkpoints"]
    assert config["sampled"]["seeds"] == old["later_sampled"]["seeds"]
    assert (
        config["sampled"]["node_work_checkpoints"]
        == old["later_sampled"]["node_work_checkpoints"]
    )
    assert config["sampled"]["median_exploitability_pot_limit"] == 0.01
    assert config["sampled"]["worst_exploitability_pot_limit"] == 0.025
    assert config["sampled"]["maximum_seconds"] == 7200
    assert (
        config["full"]["maximum_seconds"]
        == config["full"]["maximum_audit_seconds"]
        == config["sampled"]["maximum_audit_seconds"]
        == 900
    )
    assert len(full_fixture(config)[0]) == 72
    assert len(sampled_fixture(config)[0]) == 324


def test_boundary_full_pass_is_metric_only_not_admission(
    config: dict[str, Any],
) -> None:
    result = full_pass(config)
    assert result["thresholds_passed"] and all(result["checks"].values())
    assert (
        result["actual_admission"] is False
        and result["fresh_global_admission"] is False
    )
    assert "authenticated source" in result["scope"]


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "missing_layout",
        "duplicate_layout",
        "missing_audit",
        "duplicate_audit",
        "accuracy",
        "exact",
        "coverage_other",
        "compression",
        "recall",
        "menus",
        "context",
        "work",
        "audit",
        "own_clock",
        "audit_clock",
    ],
)
def test_full_failures_and_boundaries(config: dict[str, Any], change: str) -> None:
    rows, layouts, audit = full_fixture(config)
    seconds = 900.0
    native_seconds = 900.0
    target = next(
        r
        for r in rows
        if r["representation"] == definition.CANDIDATE and r["iteration"] == 4096
    )
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows.append(rows[-1])
    elif change == "missing_layout":
        layouts.pop()
    elif change == "duplicate_layout":
        layouts.append(layouts[-1])
    elif change == "missing_audit":
        audit.pop()
    elif change == "duplicate_audit":
        audit.append(audit[-1])
    elif change == "accuracy":
        target["exploitability_pot"] = math.nextafter(0.005, 1)
    elif change == "exact":
        next(
            r for r in rows if r["representation"] == "exact" and r["iteration"] == 4096
        )["exploitability_pot"] = math.nextafter(0.001, 1)
    elif change == "coverage_other":
        next(
            r
            for r in rows
            if r["representation"] == "texture_b8" and r["iteration"] == 4096
        )["coverage"] = math.nextafter(0.95, 0)
    elif change == "compression":
        next(d for d in layouts if d["representation"] == definition.CANDIDATE)[
            "information_sets"
        ] = 751
    elif change == "recall":
        layouts[0]["recall_violations"] = 1
    elif change == "menus":
        layouts[0]["menus_compatible"] = False
    elif change == "context":
        audit[0]["context_sha256"] = "wrong"
    elif change == "work":
        target["total_node_work"] -= 1
    elif change == "audit":
        audit[0]["value_error_chips"] = math.nextafter(1e-9, 1)
    elif change == "own_clock":
        seconds = math.nextafter(900.0, math.inf)
    else:
        native_seconds = math.nextafter(900.0, math.inf)
    r = assess_full(
        rows,
        layouts,
        audit,
        config,
        elapsed_seconds=seconds,
        audit_seconds=native_seconds,
    )
    assert not r["thresholds_passed"] and not r["actual_admission"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("iteration", True),
        ("total_node_work", True),
        ("coverage", True),
        ("coverage", 1.1),
        ("exploitability_pot", float("nan")),
        ("exploitability_pot", float("inf")),
        ("exploitability_pot", -1),
    ],
)
def test_invalid_full_types_and_numbers(
    config: dict[str, Any], key: str, value: Any
) -> None:
    rows, d, a = full_fixture(config)
    rows[0][key] = value
    with pytest.raises(ValueError):
        assess_full(rows, d, a, config, elapsed_seconds=1, audit_seconds=1)


def test_sampled_boundary_and_primary_readout_not_selected_after_outcomes(
    config: dict[str, Any],
) -> None:
    rows, audit = sampled_fixture(config)
    r = assess_sampled(
        rows, audit, full_pass(config), config, elapsed_seconds=7200, audit_seconds=900
    )
    assert (
        r["thresholds_passed"]
        and not r["actual_admission"]
        and not r["fresh_global_admission"]
    )
    # Current/uniform synthetic errors are deliberately much worse: only LINEAR
    # is primary, although every readout/average coverage/audit remains required.
    assert all(x["synthetic_fixture"] is True for x in rows + audit)
    for x in rows:
        if x["readout"] == "linear" and x["representation"] == definition.CANDIDATE:
            x["exploitability_pot"] = 0.011
        elif x["readout"] == "current":
            x["exploitability_pot"] = 0.0
    assert not assess_sampled(
        rows, audit, full_pass(config), config, elapsed_seconds=1, audit_seconds=1
    )["thresholds_passed"]


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "missing_audit",
        "duplicate_audit",
        "full_missing",
        "full_failed",
        "full_stage",
        "full_contract",
        "context",
        "method",
        "batch_bool",
        "warm_zero",
        "warm_wrong",
        "cut_work",
        "overshoot",
        "readout_work",
        "layout",
        "recall",
        "menus",
        "coverage_uniform",
        "median",
        "worst",
        "audit",
        "own_clock",
        "audit_clock",
    ],
)
def test_sampled_complete_contract_failures(
    config: dict[str, Any], change: str
) -> None:
    rows, audit = sampled_fixture(config)
    full = full_pass(config)
    seconds = 7200.0
    native_seconds = 900.0
    target = next(
        r
        for r in rows
        if r["representation"] == definition.CANDIDATE
        and r["work_checkpoint"] == 10000000
        and r["readout"] == "linear"
    )
    if change == "missing":
        rows.remove(target)
    elif change == "duplicate":
        rows.append(target)
    elif change == "missing_audit":
        audit.pop()
    elif change == "duplicate_audit":
        audit.append(audit[-1])
    elif change == "full_missing":
        full = {}
    elif change == "full_failed":
        full["thresholds_passed"] = False
    elif change == "full_stage":
        full["stage"] = "sampled"
    elif change == "full_contract":
        full["contract_sha256"] = "wrong"
    elif change == "context":
        target["context_sha256"] = "wrong"
    elif change == "method":
        target["regret_mode"] = "clipped"
    elif change == "batch_bool":
        target["batch_size"] = True
    elif change == "warm_zero":
        target["initialization_work"] = 0
    elif change == "warm_wrong":
        target["initialization_work"] = 3999
    elif change == "cut_work":
        target["total_node_work"] = 9999999
    elif change == "overshoot":
        target["previous_node_work"] = 10000000
    elif change == "readout_work":
        target["total_node_work"] += 1
        target["last_iteration_work"] += 1
    elif change == "layout":
        target["information_sets"] = 749
    elif change == "recall":
        target["recall_violations"] = 1
    elif change == "menus":
        target["menus_compatible"] = False
    elif change == "coverage_uniform":
        next(
            r
            for r in rows
            if r["readout"] == "uniform" and r["work_checkpoint"] == 10000000
        )["coverage"] = math.nextafter(0.95, 0)
    elif change == "median":
        for r in rows:
            if r["representation"] == definition.CANDIDATE and r["readout"] == "linear":
                r["exploitability_pot"] = math.nextafter(0.01, 1)
    elif change == "worst":
        target["exploitability_pot"] = math.nextafter(0.025, 1)
    elif change == "audit":
        audit[0]["exploitability_error_chips"] = math.nextafter(1e-9, 1)
    elif change == "own_clock":
        seconds = math.nextafter(7200.0, math.inf)
    else:
        native_seconds = math.nextafter(900.0, math.inf)
    if change == "warm_zero":
        with pytest.raises(ValueError):
            assess_sampled(
                rows,
                audit,
                full,
                config,
                elapsed_seconds=seconds,
                audit_seconds=native_seconds,
            )
    else:
        assert not assess_sampled(
            rows,
            audit,
            full,
            config,
            elapsed_seconds=seconds,
            audit_seconds=native_seconds,
        )["thresholds_passed"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("seed", True),
        ("work_checkpoint", True),
        ("initialization_work", True),
        ("coverage", float("nan")),
        ("coverage", -1),
        ("total_node_work", 1.2),
        ("menus_compatible", 1),
    ],
)
def test_invalid_sampled_types(config: dict[str, Any], key: str, value: Any) -> None:
    r, a = sampled_fixture(config)
    r[0][key] = value
    with pytest.raises(ValueError):
        assess_sampled(
            r, a, full_pass(config), config, elapsed_seconds=1, audit_seconds=1
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("mass_intervals", 16),
        ("packed_bits", 60),
        ("feature_streets", [4, 5]),
        ("semantics", "actual own filtered"),
    ],
)
def test_definition_changes_are_not_silently_accepted(
    config: dict[str, Any], field: str, value: Any
) -> None:
    c = copy.deepcopy(config)
    c[field] = value
    with pytest.raises(ValueError):
        definition.validate(c)


def test_bound_input_tamper_rejected(
    config: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(definition, "digest", lambda path: "wrong")
    with pytest.raises(ArithmeticError):
        definition.check_inputs(ROOT, config)
    with pytest.raises(ArithmeticError):
        definition.contract(ROOT)
