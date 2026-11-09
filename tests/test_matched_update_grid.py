"""Complete explicit metadata fixtures and actual immutable source coverage."""

import copy
import itertools
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_grid as grid
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.solver_validation.reference import Reference

ROOT = Path(__file__).resolve().parents[1]


def fixture() -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    config = json.loads((ROOT / grid.CONFIG).read_text())
    currents, averages, fixed = [], [], []
    contexts = itertools.product(
        config["spot_files"],
        config["representations"],
        config["regret_rules"],
        config["seeds"],
    )
    for index, values in enumerate(contexts):
        case = dict(
            zip(grid.FIELDS, values, strict=True),
            traversal="external",
            regret_weight="linear",
            bridge="common",
            average_weight="linear",
        )
        for batch, offset in ((1, 0), (4, 24), (16, 48)):
            for work in config["original_work_labels"]:
                row = dict(
                    id=f"EXPLICIT_CURRENT_{index}_{batch}_{work}",
                    variant="current",
                    case=copy.deepcopy(case),
                    path_index=index + offset,
                    batch_size=batch,
                    work_label=work,
                    iteration=1000 // batch,
                    total_work=work + batch,
                    receipt=dict(policy_sha256="a" * 64),
                    metrics="EXPLICIT_NO_STRENGTH_VALUES_USED",
                )
                currents.append(row)
                for weight in ("uniform", "linear"):
                    average = copy.deepcopy(row)
                    average.pop("variant")
                    average["case"]["average_weight"] = weight
                    average["id"] = f"EXPLICIT_AVERAGE_{index}_{batch}_{work}_{weight}"
                    averages.append(average)
    for row in [*currents, *averages]:
        if row["work_label"] == config["final_work_label"]:
            for opponent, seat in itertools.product(range(4), (0, 1)):
                fixed.append(
                    dict(
                        own_snapshot_id=row["id"],
                        opponent_profile_id=f"EXPLICIT_FIXED_{opponent}",
                        target=seat,
                    )
                )
    return config, currents, averages, fixed


def test_complete_metadata_grid_retains_every_context_and_readout() -> None:
    config, current, average, fixed = fixture()
    actual = grid.build_grid(config, current, average, fixed)
    assert len(actual["iteration_targets"]) == 48
    assert len(actual["self_pairs"]) == 144
    assert len({p["planned_prefix_id"] for p in actual["self_pairs"]}) == 144
    assert {p["readout"] for p in actual["self_pairs"]} == set(grid.READOUTS)
    assert {t["target_iteration"] for t in actual["iteration_targets"]} == {250, 62}
    assert actual["new_fixed_targets_planned"] == 1152
    assert actual["reused_fixed_targets"] == 1152
    assert actual["long_run_admitted"] is False
    # Change/remove every fictional strength value: target selection is identical.
    other = copy.deepcopy(current)
    for row in other:
        row.pop("metrics")
    assert grid.build_grid(config, other, average, fixed) == actual


@pytest.mark.parametrize(
    "kind",
    ["current_missing", "current_duplicate", "average_missing", "average_duplicate"],
)
def test_incomplete_or_duplicate_source_inventory_rejected(kind: str) -> None:
    config, current, average, fixed = fixture()
    rows = current if kind.startswith("current") else average
    if kind.endswith("missing"):
        rows.pop()
    else:
        rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(ArithmeticError):
        grid.build_grid(config, current, average, fixed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("batch_size", True),
        ("batch_size", 2),
        ("path_index", True),
        ("path_index", 50),
        ("work_label", True),
        ("total_work", True),
        ("total_work", 0),
        ("iteration", True),
        ("iteration", 0),
    ],
)
def test_bad_count_coordinate_identity_rejected(field: str, value: Any) -> None:
    config, current, average, fixed = fixture()
    current[0][field] = value
    with pytest.raises(ArithmeticError):
        grid.build_grid(config, current, average, fixed)


def test_target_beyond_source_endpoint_cannot_extend_budget() -> None:
    config, current, average, fixed = fixture()
    right = next(
        r for r in current if r["path_index"] == 24 and r["work_label"] == 10000000
    )
    right["iteration"] = 1001
    with pytest.raises(ArithmeticError, match="do not extend"):
        grid.build_grid(config, current, average, fixed)


def test_same_path_readouts_must_have_identical_update_and_work() -> None:
    config, current, average, fixed = fixture()
    row = next(
        r for r in average if r["path_index"] == 24 and r["work_label"] == 10000000
    )
    row["total_work"] += 1
    with pytest.raises(ArithmeticError, match="readouts disagree"):
        grid.build_grid(config, current, average, fixed)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "seat", "opponent"])
def test_fixed_opponent_grid_cannot_change_or_lose_targets(kind: str) -> None:
    config, current, average, fixed = fixture()
    selected = next(
        r for r in current if r["path_index"] == 24 and r["work_label"] == 10000000
    )
    row = next(r for r in fixed if r["own_snapshot_id"] == selected["id"])
    if kind == "missing":
        fixed.remove(row)
    elif kind == "duplicate":
        fixed.append(copy.deepcopy(row))
    elif kind == "seat":
        row["target"] = True
    else:
        row["opponent_profile_id"] = "EXPLICIT_OTHER"
    with pytest.raises(ArithmeticError):
        grid.build_grid(config, current, average, fixed)


def test_changed_prospective_config_rejected_before_any_input_load(
    tmp_path: Path,
) -> None:
    path = tmp_path / grid.CONFIG
    path.parent.mkdir(parents=True)
    config = json.loads((ROOT / grid.CONFIG).read_text())
    config["seeds"] = [7]
    path.write_text(json.dumps(config))
    with pytest.raises(ArithmeticError, match="config changed"):
        grid.config_inputs(tmp_path)


def test_actual_source_manifest_without_learner_or_reference_construction() -> None:
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(Reference, "__init__", side_effect=AssertionError("no reference")),
    ):
        saved = grid.manifest(ROOT)
    assert saved["status"] == "prospective_grid_only_no_training_admission"
    assert len(saved["input_sha256"]) == 9
    assert len(saved["self_pairs"]) == 144
    assert saved["new_strength_scores"] is False
    assert saved["long_run_admitted"] is False
    for target in saved["iteration_targets"]:
        assert target["target_iteration"] <= target["baseline_original_final_iteration"]
        assert target["baseline_original_final_work"] >= 10000000


def test_published_prospective_targets_recompute_from_verified_source() -> None:
    from poker_ai.postflop.pipeline_report import check_source

    saved = json.loads((ROOT / "results/matched-update-batches/plan.json").read_text())
    check_source(ROOT, saved["source"])
    actual = grid.manifest(ROOT)
    for key in (
        "input_sha256",
        "iteration_targets",
        "self_pairs",
        "new_profiles_planned",
        "reused_profiles",
        "new_fixed_targets_planned",
        "reused_fixed_targets",
    ):
        assert actual[key] == saved[key]
    assert saved["source"]["dirty"] is False
    assert saved["new_strength_scores"] is False and saved["long_run_admitted"] is False
