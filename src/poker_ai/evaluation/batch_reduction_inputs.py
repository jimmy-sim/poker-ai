"""Fixed reduction-only inputs and checked-source gate; old failures are frozen."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation import frozen_batch_inputs as old
from poker_ai.evaluation.batch_cost_run import replay as replay_cost
from poker_ai.evaluation.frozen_batch_protocol import JOBS as JOBS
from poker_ai.evaluation.frozen_batch_protocol import LOCAL as LOCAL
from poker_ai.evaluation.frozen_batch_protocol import read_profile
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/batch-reduction.json"
CONFIG_SHA = "937f2f9721ccc8ebacc7cfdc56e9e718b8bb9e30dcfb653b33b1c55c4a8b6e7f"
FOLDER = "results/batch-reduction/"
CHECKS = FOLDER + "code-checks.json"
CORRECTNESS = FOLDER + "correctness.json"
PROFILE = FOLDER + "profile.json"
FORMAT = "poker-ai-batch-array-reductions-v1"
IDENTITY = (
    "path",
    "initialization_visits",
    "incremental_visits",
    "total_work",
    "previous_work",
    "last_iteration_visits",
    "iteration",
    "sampled_traversals",
    "overshoot",
    "guard_sha256",
    "readout_sha256",
    "prefix_checks",
)


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("fixed reduction protocol changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if any(digest(root / p) != h for p, h in config["input_sha256"].items()):
        raise ArithmeticError("frozen reduction input changed")
    base = old.config_inputs(root)
    for key in (
        "batch_sizes",
        "seeds",
        "representations",
        "regret_rules",
        "regret_weight",
        "worker_count",
        "start_method",
        "maximum_own_seconds",
        "maximum_native_seconds",
    ):
        if not same(config[key], base[key]):
            raise ArithmeticError("reduction changed original grid or caps")
    return config


def source(root: Path) -> dict[str, Any]:
    return source_provenance(
        root, root / CONFIG, entrypoints=("scripts/validate_batch_reduction.py",)
    )


def binding(root: Path) -> tuple[dict[str, Any], str]:
    current = source(root)
    if current["dirty"] is not False:
        raise ValueError("publish checked reduction source first")
    return current, sha(current["sha256"])


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
        raise ArithmeticError("reduction code checks do not bind current source")
    return dict(
        format=FORMAT + "-checks",
        status="checked_short_prefixes_only",
        source=current,
        source_sha256=h,
        checked_commit=current["git_commit"],
        ci_run=ci["run_id"],
        ci_jobs=ci["jobs"],
        local_checks=local["checks"],
        scope="not long learning admission",
    )


def require_checks(root: Path, *, clean: bool = True) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / CHECKS).read_text())
    check_source(root, saved["source"])
    current = source(root)
    if (
        saved["format"] != FORMAT + "-checks"
        or saved["status"] != "checked_short_prefixes_only"
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
        raise ArithmeticError("reduction checked source changed")
    return saved


def prerequisites(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = config_inputs(root)
    saved = read_profile(root, root / config["source_forecast"])
    replay_cost(root, root / config["source_cost_profile"])
    if saved["forecast"]["decision"] != "exceeds_cap_stop_before_long_learning":
        raise ArithmeticError("original failed forecast must remain failed")
    rows = [
        next(r for r in saved["rows"] if r["index"] == i and r["repetition"] == 0)
        for i in range(72)
    ]
    return saved, rows
