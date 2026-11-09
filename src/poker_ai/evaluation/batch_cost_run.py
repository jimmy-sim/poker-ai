"""Checked-source cost profiling and offline replay with complete failure retention."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_cost_inputs as inputs
from poker_ai.evaluation.batch_cost_profile import job
from poker_ai.evaluation.batch_cost_report import write_report
from poker_ai.evaluation.batch_cost_validation import gather
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment


def fresh(path: Path) -> None:
    if path.exists() or path.with_suffix(".tmp").exists():
        raise FileExistsError("retain complete/partial cost attempt")


def run(root: Path, output: Path) -> dict[str, Any]:
    fresh(output)
    if (output.parent / "report").exists():
        raise FileExistsError("retain previous cost report")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    checked = inputs.require_checks(root)
    env = runtime_environment()
    if any(env[k] != config["prefix_runtime"][k] for k in ("python", "numpy")):
        raise ArithmeticError("cost profiling requires archived original runtime")
    deadline = Deadline(900)
    deadline.started = started
    saved: dict[str, Any] = dict(
        format=inputs.FORMAT,
        scope=config["status"],
        status="running",
        failure=None,
        config=config,
        source=current,
        source_sha256=binding,
        code_checks=checked,
        environment=env,
        source_profile_sha256=digest(root / config["source_profile"]),
        batch={},
        rows=[],
        report=None,
        seconds=0.0,
        prefix_training_requested=True,
        short_prefix_training_attempted=False,
        completed_endpoints=0,
        long_learning_performed=False,
        strength_scores_measured=False,
        optimizer_introduced=False,
        reference_constructed=False,
        new_policy_archive=False,
    )
    persist(output, saved)
    try:
        before = time.perf_counter()
        _, selected = inputs.prerequisites(root)
        saved["input_replay_seconds"] = time.perf_counter() - before
        comparison = json.loads((root / "configs/training-isolation.json").read_text())[
            "future_comparison"
        ]
        run_batch(
            24,
            3,
            job,
            dict(
                root=str(root),
                selected=selected,
                comparison=comparison,
                config=config,
                remaining_seconds=900 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        saved["rows"] = gather(saved["batch"], selected, config)
        deadline.check()
        saved["report"] = write_report(saved, output.parent / "report")
        deadline.check()
        saved["status"] = "completed_cost_profile_no_strength"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        workers = saved["batch"].get("workers", [])
        saved["short_prefix_training_attempted"] = any(
            e.get("phase") == "measurement_started"
            for w in workers
            for e in w["messages"]
        )
        saved["completed_endpoints"] = sum(
            e["kind"] == "cell" for w in workers for e in w["messages"]
        )
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - children.children_user
            - children.children_system
        )
        persist(output, saved)
    return saved


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = inputs.config_inputs(root)
    check_source(root, saved["source"])
    if (
        saved["format"] != inputs.FORMAT
        or saved["status"] != "completed_cost_profile_no_strength"
        or saved["failure"] is not None
        or saved["scope"] != config["status"]
        or not same(saved["config"], config)
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["source_profile_sha256"] != digest(root / config["source_profile"])
        or saved["prefix_training_requested"] is not True
        or saved["short_prefix_training_attempted"] is not True
        or not same(saved["completed_endpoints"], 48)
        or any(
            saved[k] is not False
            for k in (
                "long_learning_performed",
                "strength_scores_measured",
                "optimizer_introduced",
                "reference_constructed",
                "new_policy_archive",
            )
        )
        or not inputs.duration(saved["seconds"])
        or saved["seconds"] >= 900
    ):
        raise ArithmeticError("incomplete/changed cost profile receipt")
    checked = inputs.require_checks(root, clean=False)
    if (
        not same(saved["code_checks"], checked)
        or saved["source_sha256"] != checked["source_sha256"]
    ):
        raise ArithmeticError("cost profile checked source changed")
    _, selected = inputs.prerequisites(root)
    rows = gather(saved["batch"], selected, config)
    if not same(rows, saved["rows"]):
        raise ArithmeticError("cost archived rows differ from worker evidence")
    report = saved["report"]
    expected = dict(
        paths=24,
        endpoints=48,
        instrumented_profiles=24,
        function_rows=sum(
            len(r["stats"]["functions"]) for r in rows if r["stats"] is not None
        ),
        caller_rows=sum(
            len(r["stats"]["callers"]) for r in rows if r["stats"] is not None
        ),
    )
    if (
        any(not same(report[k], v) for k, v in expected.items())
        or set(report["numerical_sha256"])
        != {"cases.csv", "functions.csv", "callers.csv", "tables.md"}
        or report["figures"] != ["function-self.png", "mean-direct-callees.png"]
        or any(
            not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdef" for c in h)
            for h in report["numerical_sha256"].values()
        )
    ):
        raise ArithmeticError("cost report inventory changed")
    if (
        not inputs.duration(saved["batch"]["seconds"])
        or not inputs.duration(saved["input_replay_seconds"])
        or saved["batch"]["seconds"] + saved["input_replay_seconds"]
        > saved["seconds"] + 1e-9
    ):
        raise ArithmeticError("cost stage elapsed accounting changed")
    return saved
