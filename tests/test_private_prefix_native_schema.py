"""Synthetic schema fixtures only: no native construction or solver agreement."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.private_prefix_design import REAL
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.averaging_history import FIXED_FIELDS
from poker_ai.solver_validation.private_prefix import FORMAT, gather, validate


def records(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Deliberately impossible zero-hash policies, valid for schema tests only.

    They cannot pass the archive/source/publication gates of a real command.
    Setup flags below are data under test, not claims that a solver ran.
    """
    source = {"sha256": {"EXPLICIT_SCHEMA_ONLY": "0" * 64}}
    own: dict[str, Any] = dict(
        scope=REAL,
        source=source,
        source_sha256=sha(source["sha256"]),
        details_sha256="0" * 64,
        config={"reference": dict(name="OpenSpiel", version="2.0.2")},
        rows=[],
        fixed_matches=[],
    )
    events = []
    for i in range(432):
        row = dict(
            id=f"EXPLICIT_SCHEMA_{i:03d}",
            path_index=i // 9,
            work_label=100000,
            receipt={"policy_sha256": "0" * 64},
            reply_sha256=[{}, {}],
            metrics={"value_player_zero_chips": 0.0},
            responses=[
                dict(
                    exact_reply_value_chips=0.0,
                    restricted_reply_value_chips=0.0,
                    river_before_value_chips=0.0,
                )
                for _ in range(2)
            ],
        )
        own["rows"].append(row)
        result = dict(
            id=row["id"],
            path_index=row["path_index"],
            work_label=row["work_label"],
            policy_sha256="0" * 64,
            own_reply_sha256=[{}, {}],
            native_metrics=copy.deepcopy(row["metrics"]),
            responses=[
                dict(
                    target=t,
                    exact_root_chips=0.0,
                    restricted_root_chips=0.0,
                    achieved_exact_chips=0.0,
                    achieved_restricted_chips=0.0,
                    achieved_river_before_chips=0.0,
                )
                for t in (0, 1)
            ],
            maximum_error_chips=0.0,
        )
        events.append(
            dict(kind="cell", phase="self", index=row["path_index"], result=result)
        )
        if i % 9 >= 3:
            continue
        for opponent in range(4):
            for target in (0, 1):
                fixed = dict(
                    target=target,
                    own_snapshot_id=row["id"],
                    own_source_profile_id=row["id"],
                    own_variant="current",
                    opponent_profile_id=f"EXPLICIT_OPP_{opponent}",
                    own_policy_sha256="0" * 64,
                    opponent_policy_sha256="0" * 64,
                    reply_sha256="0" * 64,
                    baseline_value_chips=0.0,
                    restricted_reply_value_chips=0.0,
                    achieved_reply_value_chips=0.0,
                    gain_chips=0.0,
                )
                own["fixed_matches"].append(fixed)
                native_fixed = dict(
                    **{k: fixed[k] for k in FIXED_FIELDS},
                    baseline_value_chips=0.0,
                    restricted_reply_value_chips=0.0,
                    achieved_reply_value_chips=0.0,
                    gain_chips=0.0,
                    maximum_error_chips=0.0,
                )
                events.append(
                    dict(
                        kind="cell",
                        phase="fixed",
                        index=row["path_index"],
                        result=native_fixed,
                    )
                )
    path.write_text(json.dumps(own, sort_keys=True))
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="completed_native_comparison_only",
        failure=None,
        scope=REAL,
        source=source,
        source_sha256=own["source_sha256"],
        own_sha256=digest(path),
        details_sha256="0" * 64,
        publication={"own_sha256": digest(path)},
        reference=own["config"]["reference"],
        license={
            "sha256": (
                "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
            ),
            "installed_license_files": ["EXPLICIT_SCHEMA_ONLY"],
        },
        reference_setup_started=True,
        reference_setup_completed=True,
        training_performed=False,
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        long_run_admitted=False,
        seconds=0.1,
        maximum_error_chips=0.0,
        events=events,
    )
    gather(saved)
    return own, saved


def test_complete_schema_ids_and_raw_event_accounting(tmp_path: Path) -> None:
    own, native = records(tmp_path / "own.json")
    result = validate(native, own, tmp_path / "own.json")
    assert result["profiles"] == 432 and result["fixed_targets"] == 1152
    assert result["maximum_error_chips"] == 0
    assert result["long_run_admitted"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "missing_self",
        "duplicate_self",
        "missing_fixed",
        "duplicate_fixed",
        "wrong_event_route",
        "bool_count",
        "export",
        "trained",
        "admitted",
        "scope",
        "own_hash",
        "reference",
        "license",
        "partial",
        "elapsed",
        "nonfinite",
        "root",
        "reply_hash",
        "max_error",
    ],
)
def test_native_schema_rejects_incomplete_changed_or_unsafe_claims(
    tmp_path: Path, damage: str
) -> None:
    own, native = records(tmp_path / "own.json")
    if damage in ("missing_self", "missing_fixed", "duplicate_self", "duplicate_fixed"):
        phase = "self" if damage.endswith("self") else "fixed"
        index = next(i for i, e in enumerate(native["events"]) if e["phase"] == phase)
        if damage.startswith("missing"):
            native["events"].pop(index)
        else:
            native["events"].append(copy.deepcopy(native["events"][index]))
        gather(native)
    elif damage == "wrong_event_route":
        native["events"][0]["index"] = True
    elif damage == "bool_count":
        native["completed_profiles"] = True
    elif damage == "export":
        native["reference_actions_exported"] = True
    elif damage == "trained":
        native["training_performed"] = True
    elif damage == "admitted":
        native["long_run_admitted"] = True
    elif damage == "scope":
        native["scope"] = "EXPLICIT_FAKE_SCOPE"
    elif damage == "own_hash":
        native["own_sha256"] = "1" * 64
    elif damage == "reference":
        native["reference"] = dict(name="commercial", version="1")
    elif damage == "license":
        native["license"]["sha256"] = "1" * 64
    elif damage == "partial":
        native["status"] = "failed"
    elif damage == "elapsed":
        native["seconds"] = 900
    elif damage == "nonfinite":
        native["events"][0]["result"]["native_metrics"]["value_player_zero_chips"] = (
            float("nan")
        )
    elif damage == "root":
        native["events"][0]["result"]["responses"][0]["exact_root_chips"] = 1.0
    elif damage == "reply_hash":
        native["events"][0]["result"]["own_reply_sha256"] = [{"bad": "1"}, {}]
    elif damage == "max_error":
        native["maximum_error_chips"] = 1.0
    with pytest.raises((ArithmeticError, ValueError)):
        validate(native, own, tmp_path / "own.json")
