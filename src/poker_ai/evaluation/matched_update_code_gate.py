"""Observed exact-source local/hosted gates; no study admission by themselves."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.batch_current_checks import checked_tree
from poker_ai.evaluation.matched_update_run import source
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source

CHECKS = "results/matched-update-pipeline/code-checks.json"
REQUIRED_LOCAL = (
    "base311",
    "base312",
    "optional311",
    "optional312",
    "focused_slow311",
    "focused_slow312",
)
JOBS = {"Python 3.11": "success", "Python 3.12": "success"}


def record(root: Path, ci: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    inputs.config_inputs(root)
    current = source(root)
    binding = sha(current["sha256"])
    if (
        current["dirty"] is not False
        or ci["source_sha256"] != binding
        or local["source_sha256"] != binding
        or set(local["results"]) != set(REQUIRED_LOCAL)
        or any(
            local["results"][k]["status"] != "passed"
            or type(local["results"][k]["tests_passed"]) is not int
            or local["results"][k]["tests_passed"] <= 0
            for k in REQUIRED_LOCAL
        )
        or not same(ci["jobs"], JOBS)
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
    ):
        raise ArithmeticError("incomplete/different-source observed code checks")
    tested = checked_tree(root, ci["checked_commit"], current["sha256"])
    return dict(
        status="tested_software_not_real_study_admission",
        source=tested,
        source_sha256=binding,
        ci=ci,
        local=local,
    )


def require(root: Path, *, clean: bool) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / CHECKS).read_text())
    check_source(root, saved["source"])
    if (
        saved["status"] != "tested_software_not_real_study_admission"
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["ci"]["source_sha256"] != saved["source_sha256"]
        or saved["local"]["source_sha256"] != saved["source_sha256"]
        or not same(saved["ci"]["jobs"], JOBS)
        or type(saved["ci"]["run_id"]) is not int
        or saved["ci"]["run_id"] <= 0
        or set(saved["local"]["results"]) != set(REQUIRED_LOCAL)
        or any(
            saved["local"]["results"][k]["status"] != "passed"
            or type(saved["local"]["results"][k]["tests_passed"]) is not int
            or saved["local"]["results"][k]["tests_passed"] <= 0
            for k in REQUIRED_LOCAL
        )
    ):
        raise ArithmeticError("complete source code gate changed")
    checked_tree(root, saved["ci"]["checked_commit"], saved["source"]["sha256"])
    current = source(root)
    if not same(current["sha256"], saved["source"]["sha256"]) or (
        clean and current["dirty"] is not False
    ):
        raise ArithmeticError("current pipeline source differs from checked source")
    return saved
