"""Source-bound cost-only protocol; the failed learning gate stays unadmitted."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.frozen_batch_protocol import read_profile
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/batch-overhead.json"
CONFIG_SHA = "2b8e24ae2e808dc468b1090795651c0eb5bba6e30a6310aa718da975267bb9a3"
ENTRIES = ("scripts/profile_batch_overhead.py", "scripts/report_batch_overhead.py")
CHECKED = "results/batch-overhead/code-checks.json"
FORMAT = "poker-ai-frozen-batch-function-cost-v1"
LOCAL = dict.fromkeys(
    ("base_311", "base_312", "all_extras_311", "all_extras_312", "slow_integrations"),
    "passed",
)
JOBS = {"Python 3.11": "success", "Python 3.12": "success"}


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("fixed batch cost protocol changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if any(digest(root / p) != h for p, h in config["input_sha256"].items()):
        raise ArithmeticError("batch cost prerequisite changed")
    return config


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def binding(root: Path) -> tuple[dict[str, Any], str]:
    current = source(root)
    if current["dirty"] is not False:
        raise ValueError("publish checked batch cost source first")
    return current, sha(current["sha256"])


def prerequisites(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = config_inputs(root)
    original = read_profile(root, root / config["source_profile"])
    if original["forecast"]["decision"] != "exceeds_cap_stop_before_long_learning":
        raise ArithmeticError("retain original failed forecast before cost diagnosis")
    rows = [
        next(
            r for r in original["rows"] if r["index"] == index and r["repetition"] == 0
        )
        for index in config["selected_source_indices"]
    ]
    if (
        len(rows) != 24
        or any(r["path"]["seed"] != 20261301 for r in rows)
        or {r["path"]["batch_size"] for r in rows} != {1, 4, 16}
    ):
        raise ArithmeticError("fixed first-seed cost selection incomplete")
    return original, rows


def record_checks(
    root: Path, ci: dict[str, Any], local: dict[str, Any]
) -> dict[str, Any]:
    config_inputs(root)
    current, h = binding(root)
    if (
        ci["checked_commit"] != current["git_commit"]
        or ci["source_sha256"] != h
        or local["source_sha256"] != h
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
        or not same(ci["jobs"], JOBS)
        or not same(local["checks"], LOCAL)
    ):
        raise ArithmeticError("observed cost code checks do not bind current source")
    return dict(
        format=FORMAT + "-checked-source",
        status="checked_cost_profile_only",
        source=current,
        source_sha256=h,
        checked_commit=current["git_commit"],
        ci_run=ci["run_id"],
        ci_jobs=ci["jobs"],
        local_checks=local["checks"],
        scope="fixed24-path48-endpoint cost profile only, not long learning admission",
    )


def require_checks(root: Path, *, clean: bool = True) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / CHECKED).read_text())
    check_source(root, saved["source"])
    current = source(root)
    if (
        saved["format"] != FORMAT + "-checked-source"
        or saved["status"] != "checked_cost_profile_only"
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
        raise ArithmeticError("batch cost source gate missing/changed")
    return saved


def duration(value: Any) -> bool:
    return number(value, nonnegative=True)
