"""Checked source, complete proof/cost evidence and fixed sampled admission."""

import json
import math
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_sampled_cost as cost
from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.evaluation import compact_sampled_own as own
from poker_ai.evaluation.compact_sampled_clock import measurement
from poker_ai.evaluation.compact_sampled_prior import verify
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.compact_full_run import check_runtime, runtime
from poker_ai.postflop.compact_sampled_native_checks import validate
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.river_study import digest


def bound(root: Path, path: Path) -> dict[str, Any]:
    return dict(
        file=str(path.resolve().relative_to(root.resolve())), sha256=digest(path)
    )


def checked_path(root: Path, item: dict[str, Any]) -> Path:
    path = root / str(item["file"])
    if (
        not path.resolve().is_relative_to(root.resolve())
        or path.is_symlink()
        or digest(path) != item["sha256"]
    ):
        raise ArithmeticError("sampled prerequisite path/bytes changed")
    return path


def require_checks(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    current = inputs.source(root, clean=False)
    rows = saved["checks"]
    ids = [(r["role"], r["minor"]) for r in rows]
    expected = {(r, v) for r in ("base", "optional", "hosted") for v in ("311", "312")}
    if (
        len(ids) != 6
        or len(set(ids)) != 6
        or set(ids) != expected
        or saved["source_fingerprint"] != current["fingerprint"]
    ):
        raise ArithmeticError(
            "complete source-bound base/optional/hosted cohort required"
        )
    commits = {r["checked_commit"] for r in rows}
    if len(commits) != 1:
        raise ArithmeticError("all check roles must bind the same source commit")
    files.commit_sources(root, next(iter(commits)), current["sha256"])
    for row in rows:
        log = checked_path(root, row["log"]).read_text(encoding="utf-8-sig")
        if (
            row["status"] != "passed"
            or row["source_fingerprint"] != current["fingerprint"]
            or row["python"] != ("3.11.17" if row["minor"] == "311" else "3.12.15")
            or row["checked_commit"] not in log
            or "passed" not in log
        ):
            raise ArithmeticError("source check log/head/runtime mismatch")
        if row["role"] == "hosted" and (
            row["conclusion"] != "success"
            or row["head_sha"] != row["checked_commit"]
            or type(row["job_id"]) is not int
            or type(row["run_id"]) is not int
        ):
            raise ArithmeticError("successful exact-head hosted jobs required")
    return bound(root, path)


def timing_paths(root: Path) -> dict[str, Any]:
    """ALL24 historical complete B4 paths; max per game for each new10m path."""
    from poker_ai.evaluation.frozen_batch_inputs import paths

    config = inputs.protocol(root)
    path = root / "results/reduced-batch-study/own.json"
    original = json.loads(path.read_text())
    if (
        original["status"] != "completed_own_native_pending"
        or original["failure"] is not None
    ):
        raise ArithmeticError("completed historical B4 timing evidence required")
    # Authenticate all old named dependencies, allowing only added source files.
    files.commit_sources(
        root, original["source"]["git_commit"], original["source"]["sha256"]
    )
    cases = paths(original["config"])
    rows = []
    for batch in original["batches"]:
        if batch["status"] != "completed" or batch["failure"] is not None:
            raise ArithmeticError("historical worker batch incomplete")
        for worker in batch["workers"]:
            if worker["exitcode"] != 0:
                raise ArithmeticError("historical worker failed")
            for event in worker["messages"]:
                if (
                    event.get("kind") == "cell"
                    and event.get("phase") == "trained"
                    and 24 <= event.get("index", -1) < 48
                ):
                    rows.append(dict(event, case=cases[event["index"]]))
    if len(rows) != 24 or {r["index"] for r in rows} != set(range(24, 48)):
        raise ArithmeticError("all24 historical B4 cases required")
    for row in rows:
        if (
            row["case"]["batch_size"] != 4
            or type(row["work"]) is not int
            or row["work"] < 10_000_000
            or type(row["seconds"]) not in (int, float)
            or not math.isfinite(row["seconds"])
            or row["seconds"] <= 0
            or not 0 <= row["initialization_seconds"] <= row["seconds"]
        ):
            raise ArithmeticError("historical timing omitted full work/setup")
    estimates = []
    for case in inputs.cases(root, "real"):
        group = [r for r in rows if r["case"]["spot_file"] == case["spot_file"]]
        if len(group) != 12:
            raise ArithmeticError("all12 complete historical timings per game required")
        estimates.append(max(r["seconds"] for r in group))
    assignments = partition(36, config["worker_count"])
    workers = [math.fsum(estimates[i] for i in group) for group in assignments]
    return dict(
        historical_paths=rows,
        path_seconds=estimates,
        assignments=assignments,
        worker_seconds=workers,
        T=max(workers),
        full_work_charged=True,
        source_file=str(path.relative_to(root)),
        source_sha256=digest(path),
    )


def checked_native(
    root: Path, path: Path, own_path: Path, original: dict[str, Any], operation: str
) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    inputs.check_source(root, saved["source"])
    measurement(path, operation)
    validate(original, saved, digest(own_path))
    return saved


def forecast(root: Path, check_path: Path, *, deep: bool = True) -> dict[str, Any]:
    require_checks(root, check_path)
    prior = verify(root)
    folder = root / inputs.FOLDER
    toy_own_path = folder / "software/own.json"
    toy_native_path = folder / "software/native.json"
    toy = json.loads(toy_own_path.read_text())
    if toy["scope"] != "software" or toy["checks"] != bound(root, check_path):
        raise ArithmeticError("complete sampled tiny proof required")
    own.replay(root, toy_own_path)
    checked_native(root, toy_native_path, toy_own_path, toy, "software-native")
    p = max(
        measurement(toy_own_path, "software-own")["seconds"],
        measurement(toy_native_path, "software-native")["seconds"],
    )
    paths = [check_path, toy_own_path, toy_native_path]
    own_times = []
    native_times = []
    for repetition in (0, 1, 2):
        own_path = folder / f"cost/own-{repetition}.json"
        native_path = folder / f"cost/native-{repetition}.json"
        saved = json.loads(own_path.read_text())
        if (
            saved["scope"] != "cost"
            or type(saved["repetition"]) is not int
            or saved["repetition"] != repetition
            or saved["status"] != "completed"
            or saved["failure"] is not None
            or saved["sampled_training_performed"] is not False
            or saved["learner_constructed"] is not False
            or saved["checks"] != bound(root, check_path)
            or len(saved["points"]) != 108
            or len(saved["rows"]) != 324
        ):
            raise ArithmeticError(
                "all three complete no-training own/native costs required"
            )
        inputs.check_source(root, saved["source"])
        if deep:
            cost.replay(root, own_path)
        checked_native(root, native_path, own_path, saved, "cost-native")
        own_times.append(measurement(own_path, "cost-own")["seconds"])
        native_times.append(measurement(native_path, "cost-native")["seconds"])
        paths.extend((own_path, native_path))
    historical = timing_paths(root)
    t = historical["T"]
    o = max(own_times)
    n = max(native_times)
    factor = inputs.protocol(root)["forecast_safety_factor"]
    own_bound = factor * (t + o + p)
    native_bound = factor * (n + o + p)
    return dict(
        format="compact-sampled-forecast-v1",
        status="completed",
        failure=None,
        source=inputs.source(root),
        runtime=runtime(),
        inputs=[bound(root, p) for p in paths],
        prior_full=prior,
        training=historical,
        maximum_own_cost_seconds=o,
        maximum_native_cost_seconds=n,
        maximum_tiny_seconds=p,
        safety_factor=factor,
        own_forecast_seconds=own_bound,
        native_forecast_seconds=native_bound,
        within_fixed_caps=own_bound < 7200 and native_bound < 900,
        actual_admission=False,
        fresh_global_admission=False,
        limitation=(
            "Fixed engineering margin, not statistical confidence; "
            "no new training prefix"
        ),
    )


def seals(root: Path) -> list[dict[str, Any]]:
    folder = root / inputs.FOLDER
    paths = {
        folder / "checks.json",
        folder / "forecast.json",
        folder / "forecast-child.json",
    }
    for name in ("checks", "software", "cost"):
        paths.update(p for p in (folder / name).rglob("*") if p.is_file())
    previous = json.loads((root / "results/compact-full-control/own.json").read_text())
    paths.update(root / name for name in previous["source"]["sha256"])
    paths.update(root / name for name in inputs.protocol(root)["input_sha256"])
    paths.update(
        root / "results/compact-full-control/snapshots" / row["snapshot"]["file"]
        for row in previous["rows"]
    )
    for name in ("own-child.json", "native-child.json", "result-child.json"):
        paths.add(root / "results/compact-full-control" / name)
    if any(p.is_symlink() or p.name.endswith(".tmp") for p in paths):
        raise ArithmeticError("partial/symlink proof inputs cannot supply admission")
    return [bound(root, p) for p in sorted(paths)]


def admit(root: Path, check_path: Path) -> dict[str, Any]:
    folder = root / inputs.FOLDER
    path = folder / "forecast.json"
    saved = json.loads(path.read_text())
    measurement(path, "forecast")
    actual = forecast(root, check_path, deep=False)
    before = {k: v for k, v in saved.items() if k not in {"source", "complete_command"}}
    after = {k: v for k, v in actual.items() if k != "source"}
    if (
        canonical(before) != canonical(after)
        or saved["source"]["fingerprint"] != actual["source"]["fingerprint"]
    ):
        raise ArithmeticError(
            "forecast no longer derives from pinned evidence/arithmetic"
        )
    leaves = seals(root)
    for item in leaves:
        path = checked_path(root, item)
        if not str(path.relative_to(root)).startswith("src/"):
            files.published(root, path)
    return dict(
        format="compact-sampled-admission-v1",
        status="completed",
        failure=None,
        source=inputs.source(root),
        runtime=runtime(),
        inputs=leaves,
        sampled_trajectory_admitted=actual["within_fixed_caps"],
        own_forecast_seconds=actual["own_forecast_seconds"],
        native_forecast_seconds=actual["native_forecast_seconds"],
        actual_admission=False,
        fresh_global_admission=False,
        scope=(
            "Frozen known-game sampled study permission only, "
            "not accuracy/default/global admission"
        ),
    )


def require_admission(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    measurement(path, "admit")
    inputs.check_source(root, saved["source"])
    check_runtime(saved["runtime"], real=True)
    if (
        saved["format"] != "compact-sampled-admission-v1"
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["sampled_trajectory_admitted"] is not True
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
    ):
        raise ArithmeticError("published sampled study is not admitted")
    for item in saved["inputs"]:
        checked_path(root, item)
    actual = admit(root, root / inputs.FOLDER / "checks.json")
    for key in (
        "inputs",
        "sampled_trajectory_admitted",
        "own_forecast_seconds",
        "native_forecast_seconds",
    ):
        if canonical(saved[key]) != canonical(actual[key]):
            raise ArithmeticError("admission source/input/forecast seal changed")
    files.published(root, path)
    return bound(root, path)


def worker_admission(root: Path, path: Path, expected: str) -> None:
    if digest(path) != expected:
        raise ArithmeticError("worker permit bytes changed")
    saved = json.loads(path.read_text())
    measurement(path, "admit")
    inputs.check_source(root, saved["source"])
    if saved["sampled_trajectory_admitted"] is not True:
        raise ArithmeticError("worker has no sampled trajectory permit")
    for item in saved["inputs"]:
        checked_path(root, item)
    files.published(root, path)
