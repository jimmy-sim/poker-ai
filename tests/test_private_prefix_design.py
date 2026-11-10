"""Independent full-grid identities and typed work/lineage rejection."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.private_prefix_design import Design, inventory


def config() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "configs/private-prefix-stratification.json"
        ).read_text()
    )
    return result


def design() -> Design:
    return Design.build(config(), mode="toy", toy_labels=(10, 20, 30))


def records() -> tuple[Design, dict[str, Any]]:
    """Fabricated metadata fixture only: every label crosses the same warm pass."""
    d = design()
    manifest = d.manifest()
    result: dict[str, Any] = dict(
        scope=d.scope,
        manifest=manifest,
        source_sha256="0" * 64,
        captures=[],
        masses=[],
        rows=[],
    )
    for name in ("captures", "masses"):
        for expected in manifest[name]:
            row = dict(
                expected,
                source_sha256="0" * 64,
                guard_sha256="0" * 64,
                current_sha256="0" * 64,
                prefix_plan_sha256="0" * 64,
                iteration=1,
                previous_work=0,
                total_work=100,
                last_iteration_visits=100,
                initialization_visits=100,
                sampled_traversals=0,
                overshoot=100 - expected["work_label"],
                previous_capture_guard_sha256=None,
                current_movement=None,
                prefix_setup_seconds=0.0,
                initialization_seconds=0.0,
                file="EXPLICIT_METADATA_ONLY",
                metadata_sha256="0" * 64,
                receipt={"sha256": "0" * 64, "policy_sha256": "0" * 64},
            )
            result[name].append(row)
    result["rows"] = [
        dict(
            r,
            capture_sha256=r["receipt"]["sha256"],
            capture_metadata_sha256=r["metadata_sha256"],
        )
        for r in result["captures"]
    ]
    return d, result


def test_complete_grid_and_both_books_are_shared_not_extra_training_paths() -> None:
    d, saved = records()
    assert len(d.paths) == 48
    assert {p["seed"] for p in d.paths} == {20261301, 20261302, 20261303}
    assert len(saved["captures"]) == 432 and len(saved["masses"]) == 288
    assert {r["original_iid_path_index"] for r in saved["captures"]} == set(
        range(24, 72)
    )
    inventory(d, saved, scored=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("seeds", [20261301] * 3),
        ("seeds", [True, 20261302, 20261303]),
        ("new_batch_sizes", [4]),
        ("work_labels", [1, 2, 3]),
        ("regret_rules", ["signed", "signed"]),
    ],
)
def test_config_grid_is_exact_not_just_equal_length(field: str, value: Any) -> None:
    c = config()
    c[field] = value
    with pytest.raises(ValueError, match="grid changed"):
        Design.build(c, mode="real")


@pytest.mark.parametrize("labels", [(10, 10, 20), (30, 20, 10), (True, 20, 30)])
def test_toy_labels_and_scope_must_be_explicit(labels: Any) -> None:
    with pytest.raises(ValueError):
        Design.build(config(), mode="toy", toy_labels=labels)
    with pytest.raises(ValueError):
        Design.build(config(), mode="real", toy_labels=(10, 20, 30))


@pytest.mark.parametrize("kind", ["captures", "masses", "rows"])
@pytest.mark.parametrize("damage", ["missing", "duplicate", "extra"])
def test_missing_duplicate_and_extra_rows_fail(kind: str, damage: str) -> None:
    d, saved = records()
    if damage == "missing":
        saved[kind].pop()
    elif damage == "duplicate":
        saved[kind].append(copy.deepcopy(saved[kind][0]))
    else:
        extra = copy.deepcopy(saved[kind][0])
        extra["id"] = "extra"
        saved[kind].append(extra)
    with pytest.raises(ArithmeticError):
        inventory(d, saved, scored=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("iteration", True),
        ("sampled_traversals", 1),
        ("previous_work", 10),
        ("total_work", 99),
        ("last_iteration_visits", 99),
        ("initialization_visits", 0),
        ("overshoot", 0),
        ("guard_sha256", "bad"),
        ("source_sha256", "1" * 64),
        ("prefix_setup_seconds", True),
        ("initialization_seconds", float("nan")),
        ("batch_size", 16),
        ("readout", "linear_average"),
        ("current_movement", {"l1": 1.0}),
    ],
)
def test_typed_coordinates_state_work_timing_and_shared_trajectory(
    field: str, value: Any
) -> None:
    d, saved = records()
    saved["captures"][0][field] = value
    with pytest.raises(ArithmeticError):
        inventory(d, saved, scored=False)


def test_scoring_cannot_change_policy_or_capture_lineage() -> None:
    d, saved = records()
    saved["rows"][0] = copy.deepcopy(saved["rows"][0])
    saved["rows"][0]["receipt"]["policy_sha256"] = "1" * 64
    with pytest.raises(ArithmeticError, match="lineage"):
        inventory(d, saved, scored=True)


def test_scope_and_manifest_prevent_toy_or_old_data_masquerading_as_real() -> None:
    d, saved = records()
    saved["scope"] = "KNOWN_HOLDEM_PRIVATE_PREFIX_DIAGNOSTIC_NOT_GLOBAL_ADMISSION"
    with pytest.raises(ArithmeticError, match="scope"):
        inventory(d, saved, scored=False)
    assert Design.build(config(), mode="old").prefix() == "old-iid"
    assert d.prefix() == "toy-stratified"
