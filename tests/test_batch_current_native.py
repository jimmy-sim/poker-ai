"""Fictional native receipt schema; this does not claim independent solver runs."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation import batch_currents as native

ROOT = Path(__file__).resolve().parents[1]
METRICS = (
    "value_player_zero_chips",
    "exact_exploitability_chips",
    "within_partition_gain_chips",
    "extra_information_gap_chips",
    "river_only_gain_exact_prefix_chips",
)


def fictional(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    config = inputs.config_inputs(ROOT)
    rows: list[dict[str, Any]] = []
    fixed: list[dict[str, Any]] = []
    for i in range(72):
        for t in (100000, 1000000, 10000000):
            rows.append(
                dict(
                    id=f"FICTIONAL_CURRENT_{i}_{t}",
                    path_index=i,
                    work_label=t,
                    receipt=dict(policy_sha256="a" * 64),
                    reply_sha256=[dict(exact="b" * 64)] * 2,
                    metrics={k: 0.0 for k in METRICS},
                    responses=[
                        dict(
                            target=k,
                            exact_reply_value_chips=0.0,
                            restricted_reply_value_chips=0.0,
                            river_before_value_chips=0.0,
                        )
                        for k in (0, 1)
                    ],
                )
            )
        for kind in ("current", "uniform_average", "linear_average"):
            identifier = (
                f"FICTIONAL_CURRENT_{i}_10000000"
                if kind == "current"
                else f"FICTIONAL_{kind}_{i}"
            )
            for control in range(4):
                for target in (0, 1):
                    fixed.append(
                        dict(
                            target=target,
                            own_snapshot_id=identifier,
                            own_source_profile_id=identifier,
                            own_variant=kind,
                            opponent_profile_id=f"FICTIONAL_CONTROL_{control}",
                            own_policy_sha256="a" * 64,
                            opponent_policy_sha256="b" * 64,
                            reply_sha256="c" * 64,
                            path_index=i,
                            baseline_value_chips=0.0,
                            restricted_reply_value_chips=0.0,
                            achieved_reply_value_chips=0.0,
                            gain_chips=0.0,
                        )
                    )
    own: dict[str, Any] = dict(
        scope="FICTIONAL_SCHEMA_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        rows=rows,
        fixed_matches=fixed,
        details_sha256="d" * 64,
        reference=config["native_reference"],
    )
    path = tmp_path / "fictional-own.json"
    path.write_text(json.dumps(own))
    workers: list[dict[str, Any]] = []
    assignments = partition(72, 3)
    for slot, assigned in enumerate(assignments):
        messages: list[dict[str, Any]] = [
            dict(kind="prepared", phase="reference_setup_started"),
            dict(kind="prepared", phase="reference_setup_completed"),
        ]
        for r in rows:
            if r["path_index"] not in assigned:
                continue
            result: dict[str, Any] = dict(
                id=r["id"],
                path_index=r["path_index"],
                work_label=r["work_label"],
                policy_sha256=r["receipt"]["policy_sha256"],
                own_reply_sha256=r["reply_sha256"],
                native_metrics=r["metrics"],
                responses=[
                    dict(
                        target=k,
                        exact_root_chips=0.0,
                        restricted_root_chips=0.0,
                        achieved_exact_chips=0.0,
                        achieved_restricted_chips=0.0,
                        achieved_river_before_chips=0.0,
                    )
                    for k in (0, 1)
                ],
                maximum_error_chips=0.0,
            )
            messages.append(
                dict(kind="cell", phase="self", index=r["path_index"], result=result)
            )
        for r in fixed:
            if r["path_index"] not in assigned:
                continue
            messages.append(
                dict(
                    kind="cell",
                    phase="fixed",
                    index=r["path_index"],
                    result=dict(r, maximum_error_chips=0.0),
                )
            )
        messages.append(
            dict(
                kind="done",
                summary=dict(
                    paths=24,
                    current_profiles=72,
                    fixed_targets=576,
                    cached_opponent_targets=32,
                    maximum_error_chips=0.0,
                ),
            )
        )
        workers.append(dict(slot=slot, exitcode=0, messages=messages))
    source = dict(dirty=False, sha256={"FICTIONAL_SOURCE_ONLY": "a" * 64})
    saved: dict[str, Any] = dict(
        format=native.FORMAT,
        status="completed",
        failure=None,
        source=source,
        source_sha256=sha(source["sha256"]),
        own_sha256=digest(path),
        details_sha256=own["details_sha256"],
        reference=own["reference"],
        license=dict(
            sha256=own["reference"]["license_sha256"],
            installed_license_files=["FICTIONAL_NOT_INSTALLED"],
        ),
        training_performed=False,
        reference_actions_exported=False,
        reference_setup_started=True,
        reference_setup_completed_workers=3,
        seconds=1.0,
        own_replay=dict(
            status="all216currents_and1728fixed_targets_replayed",
            current_profiles=216,
            fixed_targets=1728,
            maximum_error_chips=0.0,
            seconds=0.1,
            training_performed=False,
            reference_constructed=False,
        ),
        batch=dict(
            status="completed",
            failure=None,
            assignments=assignments,
            workers=workers,
            seconds=0.8,
        ),
    )
    return saved, own, path


def test_complete_fictional216self_and1728fixed_schema(tmp_path: Path) -> None:
    saved, own, path = fictional(tmp_path)
    result = native.validate(saved, own, path)
    assert result["current_profiles"] == 216 and result["fixed_targets"] == 1728
    assert (
        result["unique_opponent_targets"] == 32
        and result["worker_cached_root_evaluations"] == 96
    )


@pytest.mark.parametrize(
    "damage",
    [
        "missing_self",
        "duplicate_fixed",
        "fixed_target",
        "fixed_policy",
        "fixed_nonfinite",
        "self_nonfinite",
        "setup_missing",
        "setup_flag",
        "setup_count",
        "partial",
        "own_hash",
        "reply_hash",
        "count",
        "cache_count",
        "training",
        "export",
        "elapsed",
    ],
)
def test_partial_corrupt_or_wrong_source_is_not_complete(
    damage: str, tmp_path: Path
) -> None:
    saved, own, path = fictional(tmp_path)
    worker = saved["batch"]["workers"][0]
    messages = worker["messages"]
    self_event = next(e for e in messages if e.get("phase") == "self")
    fixed_event = next(e for e in messages if e.get("phase") == "fixed")
    if damage == "missing_self":
        messages.remove(self_event)
    elif damage == "duplicate_fixed":
        messages.append(copy.deepcopy(fixed_event))
    elif damage == "fixed_target":
        fixed_event["result"]["target"] = 1
    elif damage == "fixed_policy":
        fixed_event["result"]["own_policy_sha256"] = "f" * 64
    elif damage == "fixed_nonfinite":
        fixed_event["result"]["gain_chips"] = float("nan")
    elif damage == "self_nonfinite":
        self_event["result"]["native_metrics"] = {k: float("nan") for k in METRICS}
    elif damage == "setup_missing":
        messages.pop(0)
    elif damage == "setup_flag":
        saved["reference_setup_started"] = False
    elif damage == "setup_count":
        saved["reference_setup_completed_workers"] = True
    elif damage == "partial":
        saved["batch"]["status"] = "incomplete"
    elif damage == "own_hash":
        saved["own_sha256"] = "f" * 64
    elif damage == "reply_hash":
        self_event["result"]["own_reply_sha256"] = [dict(exact="f" * 64)] * 2
    elif damage == "count":
        messages[-1]["summary"]["fixed_targets"] = 1
    elif damage == "cache_count":
        messages[-1]["summary"]["cached_opponent_targets"] = 31
    elif damage == "training":
        saved["training_performed"] = True
    elif damage == "export":
        saved["reference_actions_exported"] = True
    else:
        saved["seconds"] = 900.0
    with pytest.raises((ArithmeticError, KeyError)):
        native.validate(saved, own, path)


@pytest.mark.slow
def test_real_native_job_on_one_preexisting_own_control_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.evaluation.averaging_history_inputs import load
    from poker_ai.evaluation.batch_current_math import matches
    from poker_ai.evaluation.frozen_batch_validation import full_sources
    from poker_ai.evaluation.reduced_study_training import save
    from poker_ai.postflop.learning_artifacts import write_archive
    from poker_ai.postflop.river_study import Deadline
    from poker_ai.solver_validation.controlled_pipeline import license_record

    data = load(ROOT)
    control = full_sources(data)[0]
    context = data.base.context(control.case)
    sources = inputs.Sources(
        tmp_path / "EXPLICIT_SOURCE.json",
        dict(config=data.config),
        data,
        dict(scope="EXISTING_OWN_CONTROL_ADAPTER_TEST"),
    )
    scratch = tmp_path / "scratch"
    deadline = Deadline(180)
    metadata = dict(
        id="EXPLICIT_PREEXISTING_OWN_CONTROL",
        path_index=0,
        case=control.case,
        batch_size=1,
        work_label=10000000,
        variant="current",
    )
    row = save(context, control.policy, metadata, scratch, lambda e: None, deadline)
    fixed = matches(sources, row, control.policy, "a" * 64)
    archive = tmp_path / "profiles.jsonl.gz"
    h = write_archive(archive, scratch, [row])
    own = dict(
        scope="EXISTING_OWN_CONTROL_ONLY_NOT_NEW_DIAGNOSIS",
        rows=[row],
        fixed_matches=fixed,
        details_file=archive.name,
        details_sha256=h,
    )
    monkeypatch.setattr(inputs, "load", lambda root: sources)
    monkeypatch.setattr(native, "policies", lambda *a: iter(()))
    assert (
        license_record(
            dict(native_reference=inputs.config_inputs(ROOT)["native_reference"])
        )["sha256"]
        == inputs.config_inputs(ROOT)["native_reference"]["license_sha256"]
    )
    events: list[dict[str, Any]] = []
    result = native.job(
        0,
        [0],
        dict(
            root=str(ROOT),
            own=own,
            own_path=str(tmp_path / "own.json"),
            remaining_seconds=180,
        ),
        events.append,
    )
    assert (
        result["current_profiles"] == 1
        and result["fixed_targets"] == 8
        and result["cached_opponent_targets"] == 8
    )
    assert result["maximum_error_chips"] <= 1e-9
    assert [e["phase"] for e in events if e["kind"] == "prepared"] == [
        "reference_setup_started",
        "reference_setup_completed",
    ]
