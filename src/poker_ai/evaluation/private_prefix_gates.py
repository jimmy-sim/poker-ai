"""Observed exact-source software checks; these alone never admit real training."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.batch_current_checks import checked_tree
from poker_ai.evaluation.private_prefix_sources import FOLDER, contract, source
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

CHECKS = FOLDER + "pipeline-code-checks.json"
LOCAL = (
    "base311",
    "base312",
    "optional311",
    "optional312",
    "focused_slow311",
    "focused_slow312",
)
JOBS = {"Python 3.11": "success", "Python 3.12": "success"}


def record(root: Path, ci: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    contract(root)
    current = source(root)
    binding = sha(current["sha256"])
    if (
        current["dirty"] is not False
        or ci["source_sha256"] != binding
        or local["source_sha256"] != binding
        or not same(ci["jobs"], JOBS)
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
        or set(local["results"]) != set(LOCAL)
    ):
        raise ArithmeticError(
            "complete observed current-source software checks required"
        )
    for row in local["results"].values():
        if (
            row["status"] != "passed"
            or type(row["tests_passed"]) is not int
            or row["tests_passed"] <= 0
            or digest(root / row["log"]) != row["log_sha256"]
        ):
            raise ArithmeticError("local source-check log/status changed")
    tested = checked_tree(root, ci["checked_commit"], current["sha256"])
    return dict(
        status="tested_private_prefix_pipeline_not_training_admission",
        source=tested,
        source_sha256=binding,
        ci=ci,
        local=local,
        long_run_admitted=False,
    )


def require(root: Path, *, clean: bool) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / CHECKS).read_text())
    check_source(root, saved["source"])
    if (
        saved["status"] != "tested_private_prefix_pipeline_not_training_admission"
        or saved["long_run_admitted"] is not False
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["ci"]["source_sha256"] != saved["source_sha256"]
        or saved["local"]["source_sha256"] != saved["source_sha256"]
        or not same(saved["ci"]["jobs"], JOBS)
        or type(saved["ci"]["run_id"]) is not int
        or saved["ci"]["run_id"] <= 0
        or set(saved["local"]["results"]) != set(LOCAL)
    ):
        raise ArithmeticError("private-prefix software check receipt changed")
    for row in saved["local"]["results"].values():
        if (
            row["status"] != "passed"
            or type(row["tests_passed"]) is not int
            or row["tests_passed"] <= 0
            or digest(root / row["log"]) != row["log_sha256"]
        ):
            raise ArithmeticError("private-prefix local check evidence changed")
    checked_tree(root, saved["ci"]["checked_commit"], saved["source"]["sha256"])
    current = source(root)
    if not same(current["sha256"], saved["source"]["sha256"]) or (
        clean and current["dirty"] is not False
    ):
        raise ArithmeticError(
            "current complete pipeline inventory differs from checked source"
        )
    return saved
