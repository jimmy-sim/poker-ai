"""Fixed own trajectory selection and a historical-cost gate, no new learning."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation import controlled_reply_io
from poker_ai.evaluation.controlled_reply_inputs import Inputs, identity
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

CONFIG = "configs/averaging-history.json"
ENTRIES = (
    "scripts/check_averaging_history.py",
    "scripts/study_averaging_history.py",
    "scripts/audit_averaging_history.py",
    "scripts/report_averaging_history.py",
)


def validate_config(config: dict[str, Any]) -> None:
    fixed = dict(
        schema_version=1,
        status="preregistered_diagnostic_trajectory_replay_no_new_learning_rule",
        source_report="results/controlled-learning/own.json",
        source_archive="results/controlled-learning/own-profiles.jsonl.gz",
        selection_config="configs/controlled-reply-diagnosis.json",
        source_axis="work",
        source_target=10000000,
        regret_weight="linear",
        spot_files=[
            "configs/learning-spots/dev_low_oop.json",
            "configs/learning-spots/dev_medium_oop.json",
        ],
        representations=["exact", "texture_range_q8_b8"],
        traversals=["full", "external"],
        seeds=[20261301, 20261302, 20261303],
        regret_rules=["signed", "clipped"],
        average_weights=["uniform", "linear"],
        bridge="common",
        current_work_labels=[100000, 1000000, 5000000, 9000000, 10000000],
        original_average_replay_labels=[100000, 1000000, 10000000],
        suffix_windows=[[5000000, 10000000], [9000000, 10000000]],
        expected_cells=64,
        expected_original_average_checks=192,
        expected_current_profiles=320,
        expected_suffix_profiles=128,
        expected_whole_average_profiles=64,
        expected_self_profiles=512,
        cumulative_mass_work_labels=[5000000, 9000000, 10000000],
        expected_cumulative_mass_records=192,
        fixed_opponent_own_variants=[
            "whole_average",
            "current_final",
            "suffix_5m_10m",
            "suffix_9m_10m",
        ],
        expected_fixed_opponent_target_conditions=2048,
        worker_count=3,
        start_method="spawn",
        maximum_own_seconds=7200,
        maximum_native_seconds=900,
        correctness_receipt="results/averaging-history/correctness.json",
        admission_receipt="results/averaging-history/admission.json",
        tolerance_chips=1e-9,
        tolerance_unitless=1e-12,
    )
    pins = {
        "configs/training-isolation.json",
        "configs/controlled-learning-comparison.json",
        "results/controlled-learning/own.json",
        "results/controlled-learning/own-profiles.jsonl.gz",
        "results/controlled-learning/native.json",
        "configs/controlled-reply-diagnosis.json",
        "results/controlled-replies/own.json",
        "results/controlled-replies/own-traces.jsonl.gz",
        "results/controlled-replies/native.json",
    }
    if (
        any(not same(config[k], v) for k, v in fixed.items())
        or set(config["input_sha256"]) != pins
    ):
        raise ArithmeticError("averaging-history selection/budget changed")
    for key, expected_forecast in dict(
        observation_allowance_multiplier=2.0,
        fixed_overhead_allowance_seconds=600.0,
        guard_multiplier=2.0,
    ).items():
        if not same(config["forecast"][key], expected_forecast):
            raise ArithmeticError("averaging-history forecast rule changed")
    for key, expected_reference in dict(
        name="OpenSpiel",
        version="2.0.2",
        license="Apache-2.0",
        license_sha256="cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    ).items():
        if not same(config["native_reference"][key], expected_reference):
            raise ArithmeticError("averaging-history reference pin changed")
    if any(
        config["prefix_runtime"][k] != v
        for k, v in {"python": "3.11.17", "numpy": "2.4.6"}.items()
    ):
        raise ArithmeticError("averaging-history prefix runtime changed")


def inputs(root: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    validate_config(config)
    if any(digest(root / p) != value for p, value in config["input_sha256"].items()):
        raise ArithmeticError("averaging-history input hash changed")
    return config


@dataclass(frozen=True)
class HistoryInputs:
    config: dict[str, Any]
    base: Inputs
    prefixes: dict[tuple[str, int], dict[str, Any]]
    replies: dict[tuple[str, int], Reply]


def load(root: Path) -> HistoryInputs:
    """Read archived native checks as prerequisites; construct no native solver.

    Only OWN policies, rules, seeds and arrays are used by the trajectory worker.
    Archived native scalar validation supplies no learning targets or strategies.
    """
    from poker_ai.solver_validation.controlled_replies import validate

    config = inputs(root)
    path = root / "results/controlled-replies/own.json"
    saved, base = controlled_reply_io.read_saved(root, path)
    audit = json.loads((path.parent / "native.json").read_text())
    check_source(root, audit["source"])
    validate(audit, saved, path, base)
    replies = {}
    for record in controlled_reply_io.trace_records(path, saved, base):
        s = record["summary"]
        replies[s["profile_id"], s["target"]] = Reply(
            s["target"],
            s["restricted_reply_value_chips"],
            tuple(r[5] for r in record["rows"]),
        )
    selected = {p.identifier: p for p in base.policies}
    prefixes = {}
    for row, blob in read_archive(
        root / config["source_archive"],
        base.original["details_sha256"],
        base.original["rows"],
    ):
        identifier = identity(row["case"])
        if identifier not in selected or not same(
            row["case"], selected[identifier].case
        ):
            continue
        labels = [
            t
            for t in config["original_average_replay_labels"]
            if ["work", t] in row["labels"]
        ]
        if labels:
            decode(blob, base.context(row["case"]), row)
        for threshold in labels:
            if (identifier, threshold) in prefixes:
                raise ArithmeticError("duplicate original history prefix")
            prefixes[identifier, threshold] = row
    if (
        len(prefixes) != 192
        or len(replies) != 128
        or set(prefixes)
        != {
            (p.identifier, t)
            for p in base.policies
            for t in config["original_average_replay_labels"]
        }
    ):
        raise ArithmeticError("averaging-history prerequisites incomplete")
    return HistoryInputs(config, base, prefixes, replies)


def forecast(data: HistoryInputs) -> dict[str, Any]:
    """Fixed formula over the complete historical selection; no trial training."""
    durations = {}
    for worker in data.base.original["batch"]["workers"]:
        for event in worker["messages"]:
            if event.get("phase") != "trained":
                continue
            if (
                type(event["index"]) is not int
                or event["index"] in durations
                or not number(event["seconds"], nonnegative=True)
                or event["seconds"] <= 0
            ):
                raise ArithmeticError("invalid/duplicate original cell duration")
            durations[event["index"]] = event["seconds"]
    rows = []
    sums = []
    for slot, indices in enumerate(partition(64, 3)):
        chosen = []
        for index in indices:
            source = data.base.policies[index]
            if source.row["index"] not in durations:
                raise ArithmeticError("original selected cell duration missing")
            seconds = durations[source.row["index"]]
            chosen.append(seconds)
            rows.append(
                dict(
                    index=index,
                    slot=slot,
                    source_id=source.identifier,
                    original_index=source.row["index"],
                    seconds=seconds,
                )
            )
        sums.append(math.fsum(chosen))
    rule = data.config["forecast"]
    seconds = rule["guard_multiplier"] * (
        rule["observation_allowance_multiplier"] * max(sums)
        + rule["fixed_overhead_allowance_seconds"]
    )
    return dict(
        source_cells=64,
        historical_cell_rows=sorted(rows, key=lambda r: r["index"]),
        partition_original_seconds=sums,
        guarded_own_seconds=seconds,
        cap_seconds=data.config["maximum_own_seconds"],
        decision="fits_requires_checked_admission"
        if seconds < data.config["maximum_own_seconds"]
        else "exceeds_cap_stop_before_replay",
        new_postflop_training_performed=False,
        interpretation=(
            "planning forecast, not measured new runtime or a timing guarantee"
        ),
    )
