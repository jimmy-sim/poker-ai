"""Observed code checks and published saved-data admission, never learning."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.batch_current_checks import checked_tree
from poker_ai.evaluation.frozen_batch_protocol import JOBS as JOBS
from poker_ai.evaluation.frozen_batch_protocol import LOCAL as LOCAL
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest


def record_checks(
    root: Path, ci: dict[str, Any], local: dict[str, Any]
) -> dict[str, Any]:
    inputs.config_inputs(root)
    current, h = inputs.binding(root)
    if (
        ci["source_sha256"] != h
        or local["source_sha256"] != h
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
        or not same(ci["jobs"], JOBS)
        or not same(local["checks"], LOCAL)
    ):
        raise ArithmeticError("observed saved-current checks do not bind exact source")
    tested = checked_tree(root, ci["checked_commit"], current["sha256"])
    return dict(
        format=inputs.FORMAT + "-checks",
        status="checked_code_not_scoring_admission",
        source=tested,
        working_tree_commit=current["git_commit"],
        source_sha256=h,
        checked_commit=ci["checked_commit"],
        ci_run=ci["run_id"],
        ci_jobs=ci["jobs"],
        local_checks=local["checks"],
    )


def require_checks(root: Path, *, clean: bool = True) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / inputs.CHECKS).read_text())
    check_source(root, saved["source"])
    current = inputs.source(root)
    if (
        saved["format"] != inputs.FORMAT + "-checks"
        or saved["status"] != "checked_code_not_scoring_admission"
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["checked_commit"] != saved["source"]["git_commit"]
        or type(saved["ci_run"]) is not int
        or saved["ci_run"] <= 0
        or not same(saved["ci_jobs"], JOBS)
        or not same(saved["local_checks"], LOCAL)
        or (
            clean
            and (
                current["dirty"] is not False
                or not same(current["sha256"], saved["source"]["sha256"])
            )
        )
    ):
        raise ArithmeticError("saved-current code gate changed")
    return saved


def expected_admission(root: Path, *, clean: bool = True) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    checked = require_checks(root, clean=clean)
    sources = inputs.load(root)
    hashes = inputs.source_hashes(root, sources)
    hashes[inputs.CONFIG] = digest(root / inputs.CONFIG)
    hashes[inputs.CHECKS] = digest(root / inputs.CHECKS)
    return dict(
        format=inputs.FORMAT + "-admission",
        status="admitted_saved_data_diagnosis_only",
        source_sha256=checked["source_sha256"],
        input_sha256=hashes,
        checked_commit=checked["checked_commit"],
        ci_run=checked["ci_run"],
        current_profiles=216,
        fixed_targets=1728,
        maximum_own_seconds=config["maximum_own_seconds"],
        maximum_native_seconds=config["maximum_native_seconds"],
        scope="no training,policy edits,selected/default/fresh/global admission",
    )


def record_admission(root: Path) -> dict[str, Any]:
    return expected_admission(root)


def require_admission(root: Path, *, clean: bool = True) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / inputs.ADMITTED).read_text())
    if not same(saved, expected_admission(root, clean=clean)):
        raise ArithmeticError("saved-current admission changed")
    return saved
