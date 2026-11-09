"""Fictional native receipts test schema only; no solver execution is implied."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation import frozen_batches as native

ROOT = Path(__file__).resolve().parents[1]
METRICS = (
    "exact_exploitability_chips",
    "within_partition_gain_chips",
    "extra_information_gap_chips",
    "river_only_gain_exact_prefix_chips",
    "value_player_zero_chips",
)


def fictional(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    rows = []
    identities = [
        (i, w, t)
        for i in range(72)
        for w in ("linear", "uniform")
        for t in config["work_labels"]
    ]
    identities += [
        (i, "linear", t) for i in range(72, 88) for t in config["work_labels"]
    ]
    for i, w, t in identities:
        rows.append(
            dict(
                id=f"FICTIONAL_{i}_{w}_{t}",
                path_index=i,
                work_label=t,
                receipt=dict(policy_sha256="a" * 64),
                reply_sha256=[{"exact": "b" * 64}] * 2,
                metrics={k: 0.0 for k in METRICS},
                responses=[
                    dict(
                        target=j,
                        baseline_value_chips=0.0,
                        exact_reply_value_chips=0.0,
                        restricted_reply_value_chips=0.0,
                        river_before_value_chips=0.0,
                    )
                    for j in (0, 1)
                ],
            )
        )
    own = dict(
        scope="FICTIONAL_SCHEMA_ONLY_NO_NATIVE_RUN",
        rows=rows,
        config=config,
        details_sha256="c" * 64,
    )
    path = tmp_path / "fictional-own.json"
    path.write_text(json.dumps(own))
    source = {"dirty": False, "sha256": {"FICTIONAL_SCHEMA_ONLY": "f" * 64}}
    saved = dict(
        format=native.FORMAT,
        status="completed",
        failure=None,
        source=source,
        source_sha256=sha(source["sha256"]),
        own_sha256=digest(path),
        details_sha256="c" * 64,
        reference=config["native_reference"],
        license=dict(
            sha256=config["native_reference"]["license_sha256"],
            installed_license_files=["FICTIONAL_SCHEMA_ONLY"],
        ),
        reference_actions_exported=False,
        training_performed=False,
        seconds=1.0,
        own_replay=dict(
            status="all_batch_profiles_and_raw_observations_replayed",
            profiles=480,
            fresh_profiles=432,
            reused_full_profiles=48,
            mass_reconstructions=432,
            current_observations=216,
            maximum_error_chips=0.0,
            maximum_error_unitless=0.0,
            new_postflop_training_performed=False,
            seconds=0.1,
        ),
        batch=dict(
            status="completed",
            failure=None,
            assignments=partition(88, 3),
            workers=[],
            seconds=0.2,
        ),
    )
    for slot, assigned in enumerate(saved["batch"]["assignments"]):
        events = []
        for row in rows:
            if row["path_index"] not in assigned:
                continue
            events.append(
                dict(
                    kind="cell",
                    id=row["id"],
                    path_index=row["path_index"],
                    work_label=row["work_label"],
                    policy_sha256=row["receipt"]["policy_sha256"],
                    own_reply_sha256=row["reply_sha256"],
                    native_metrics=row["metrics"],
                    maximum_error_chips=0.0,
                    responses=[
                        dict(
                            target=j,
                            exact_root_chips=0.0,
                            restricted_root_chips=0.0,
                            achieved_exact_chips=0.0,
                            achieved_restricted_chips=0.0,
                            achieved_river_before_chips=0.0,
                        )
                        for j in (0, 1)
                    ],
                )
            )
        events.append(
            dict(
                kind="done",
                summary=dict(
                    paths=len(assigned), profiles=len(events), maximum_error_chips=0.0
                ),
            )
        )
        saved["batch"]["workers"].append(dict(slot=slot, exitcode=0, messages=events))
    return saved, own, path


def test_complete_fictional480_grid_checks_only_contract(tmp_path: Path) -> None:
    saved, own, path = fictional(tmp_path)
    result = native.validate(saved, own, path)
    assert result["profiles"] == 480
    assert result["maximum_error_chips"] == 0
    assert own["scope"] == "FICTIONAL_SCHEMA_ONLY_NO_NATIVE_RUN"


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "duplicate",
        "path",
        "bool_path",
        "work_label",
        "policy",
        "reply_hash",
        "target",
        "metric_nan",
        "root_inf",
        "wrong_root",
        "error_summary",
        "exit",
        "done",
        "partial",
        "deadline",
        "negative_seconds",
        "elapsed",
        "own_hash",
        "source_hash",
        "license",
        "reference",
        "export",
        "training",
        "replay_grid",
    ],
)
def test_native_failure_receipts_never_become_complete(
    damage: str, tmp_path: Path
) -> None:
    saved, own, path = fictional(tmp_path)
    event = saved["batch"]["workers"][0]["messages"][0]
    if damage == "missing":
        saved["batch"]["workers"][0]["messages"].pop(0)
    elif damage == "duplicate":
        saved["batch"]["workers"][0]["messages"][1] = copy.deepcopy(event)
    elif damage == "path":
        event["path_index"] = 1
    elif damage == "bool_path":
        event["path_index"] = False
    elif damage == "work_label":
        event["work_label"] = 1
    elif damage == "policy":
        event["policy_sha256"] = "d" * 64
    elif damage == "reply_hash":
        event["own_reply_sha256"] = [{}] * 2
    elif damage == "target":
        event["responses"][0]["target"] = 1
    elif damage == "metric_nan":
        event["native_metrics"] = dict(
            event["native_metrics"], value_player_zero_chips=float("nan")
        )
    elif damage == "root_inf":
        event["responses"][0]["achieved_exact_chips"] = float("inf")
    elif damage == "wrong_root":
        event["responses"][0]["exact_root_chips"] = 0.1
        event["maximum_error_chips"] = 0.1
    elif damage == "error_summary":
        event["maximum_error_chips"] = 1e-14
    elif damage == "exit":
        saved["batch"]["workers"][0]["exitcode"] = 1
    elif damage == "done":
        saved["batch"]["workers"][0]["messages"].pop()
    elif damage == "partial":
        saved["status"] = "incomplete"
    elif damage == "deadline":
        saved["seconds"] = 900.0
    elif damage == "negative_seconds":
        saved["seconds"] = -1.0
    elif damage == "elapsed":
        saved["own_replay"]["seconds"] = 5.0
    elif damage == "own_hash":
        saved["own_sha256"] = "d" * 64
    elif damage == "source_hash":
        saved["source_sha256"] = "d" * 64
    elif damage == "license":
        saved["license"]["sha256"] = "d" * 64
    elif damage == "reference":
        saved["reference"] = dict(saved["reference"], version="wrong")
    elif damage == "export":
        saved["reference_actions_exported"] = True
    elif damage == "training":
        saved["training_performed"] = True
    elif damage == "replay_grid":
        saved["own_replay"]["profiles"] = 479
    with pytest.raises((ArithmeticError, KeyError)):
        native.validate(saved, own, path)


@pytest.mark.slow
def test_real_native_adapter_on_existing_own_poker_profiles_only() -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.postflop.controlled_checkpoints import pack_policy
    from poker_ai.postflop.learning_training import score_data
    from poker_ai.solver_validation.controlled_pipeline import (
        compare_one,
        license_record,
        references,
    )

    config = inputs.config_inputs(ROOT)
    data = inputs.prerequisites(ROOT)
    assert (
        license_record(config)["sha256"] == config["native_reference"]["license_sha256"]
    )
    refs = references(data.base.contexts)
    for game in config["spot_files"]:
        source = next(
            p
            for p in data.base.policies
            if p.case["spot_file"] == game
            and p.case["representation"] == "texture_range_q8_b8"
            and p.case["traversal"] == "external"
        )
        context = data.base.context(source.case)
        score = context.score(source.policy)
        detail = dict(
            policy=pack_policy(context.partition, source.policy),
            **score_data(context, score),
            replies=[
                {k: pack_policy(context.exact, v) for k, v in r.items()}
                for r in score.replies
            ],
        )
        row = dict(
            id="ACTUAL_OLD_OWN_PROFILE_NOT_NEW_TRAINING",
            path_index=0,
            work_label=10000000,
            receipt=source.row["receipt"],
            metrics=detail["metrics"],
            responses=detail["responses"],
            reply_sha256=detail["reply_sha256"],
        )
        result = dict(
            id=row["id"],
            path_index=0,
            work_label=10000000,
            policy_sha256=row["receipt"]["policy_sha256"],
            own_reply_sha256=row["reply_sha256"],
            **compare_one(context, refs[game, "texture_range_q8_b8"], detail),
        )
        assert native.error(result, row) <= 1e-9
