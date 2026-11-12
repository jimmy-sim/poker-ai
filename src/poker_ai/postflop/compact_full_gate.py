"""Source-bound prerequisites and fixed conservative no-trajectory forecast."""

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop.compact_full_clock import measurement
from poker_ai.postflop.compact_full_context import contexts, metrics
from poker_ai.postflop.compact_full_run import replay, runtime
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.public_range_definition import check_inputs, contract
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.postflop.river_study import digest

ROOT_FOLDER = "results/compact-full-control"


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
        raise ArithmeticError("prerequisite path/bytes changed")
    return path


def checks(root: Path, path: Path) -> dict[str, Any]:
    """Validate archived execution receipts, not a bare 'tests passed' boolean."""
    saved: dict[str, Any] = json.loads(path.read_text())
    fingerprint = artifacts.source(root, clean=False)["fingerprint"]
    required = {
        (role, minor)
        for role in ("base", "optional", "hosted")
        for minor in ("311", "312")
    }
    rows = saved["checks"]
    ids = [(r["role"], r["minor"]) for r in rows]
    if (
        len(ids) != len(set(ids))
        or set(ids) != required
        or saved["source_fingerprint"] != fingerprint
    ):
        raise ArithmeticError(
            "source-bound local/optional/hosted check cohort incomplete"
        )
    commits = {r["checked_commit"] for r in rows}
    if len(commits) != 1:
        raise ArithmeticError("checks must cover the same exact source commit")
    commit = next(iter(commits))
    current = artifacts.source(root, clean=False)
    artifacts.commit_sources(root, commit, current["sha256"])
    for row in rows:
        log = checked_path(root, row["log"]).read_text(encoding="utf-8-sig")
        if (
            row["status"] != "passed"
            or row["source_fingerprint"] != fingerprint
            or row["python"] != ("3.11.17" if row["minor"] == "311" else "3.12.15")
            or "passed" not in log
            or row["checked_commit"] not in log
        ):
            raise ArithmeticError("check execution log/source/runtime receipt mismatch")
        if row["role"] == "hosted" and (
            row["conclusion"] != "success"
            or row["head_sha"] != row["checked_commit"]
            or type(row["job_id"]) is not int
            or type(row["run_id"]) is not int
        ):
            raise ArithmeticError("hosted job is not successful on the tested source")
    return saved


def layout(
    root: Path, output: Path, repetition: int, started: float, check_path: Path
) -> dict[str, Any]:
    """Complete no-training structural/metric/JSON round trip, three fixed repeats."""
    if type(repetition) is not int or repetition not in (0, 1, 2):
        raise ValueError("fixed structural repetition 0,1,2 required")
    saved: dict[str, Any] = dict(
        format="compact-full-layout-cost-v1",
        status="running",
        failure=None,
        repetition=repetition,
        source=artifacts.source(root, clean=True),
        runtime=runtime(),
        rows=[],
        archive_directory=output.stem + "-layouts",
        poker_training_performed=False,
        actual_admission=False,
        fresh_global_admission=False,
    )
    try:
        artifacts.atomic(output, saved)
        checks(root, check_path)
        saved["checks"] = bound(root, check_path)
        for context in contexts(root, software=False):
            if time.perf_counter() - started >= 900:
                raise TimeoutError("structural complete-command cap")
            tree = context.scoring.partition
            policy = tree.normalize(tree.legal)
            zeros = np.zeros_like(policy)
            before = metrics(context, policy, zeros)
            raw = dict(policy=policy.tolist(), sums=zeros.tolist())
            blob = canonical(raw)
            archive = output.parent / saved["archive_directory"]
            receipt = artifacts.write_snapshot(
                archive / f"{len(saved['rows']):04d}.json.gz", raw
            )
            restored = artifacts.load_snapshot(archive, receipt)
            after = metrics(
                context,
                np.asarray(restored["policy"], dtype=np.float64),
                np.asarray(restored["sums"], dtype=np.float64),
            )
            if canonical(before) != canonical(after):
                raise ArithmeticError("nontraining policy round trip changed metrics")
            saved["rows"].append(
                dict(
                    **context.binding,
                    **context.diagnostics,
                    metrics=before,
                    snapshot=receipt,
                    serialized_bytes=len(blob),
                )
            )
            artifacts.atomic(output, saved)
        saved["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        saved["seconds"] = time.perf_counter() - started
        saved["peak_process_rss_bytes"] = peak_rss_bytes()
        artifacts.atomic(output, saved)
    return saved


def replay_layout(root: Path, path: Path) -> None:
    saved = json.loads(path.read_text())
    if saved["archive_directory"] != path.stem + "-layouts":
        raise ArithmeticError("structural archive directory changed")
    rows = saved["rows"]
    count = 0
    for index, context in enumerate(contexts(root, software=False)):
        row = rows[index]
        raw = artifacts.load_snapshot(
            path.parent / saved["archive_directory"], row["snapshot"]
        )
        tree = context.scoring.partition
        policy = tree.normalize(tree.legal)
        zeros = np.zeros_like(policy)
        expected = dict(policy=policy.tolist(), sums=zeros.tolist())
        if canonical(expected) != canonical(raw):
            raise ArithmeticError(
                "structural cost used a nonuniform/nonzero-training table"
            )
        actual = dict(
            **context.binding,
            **context.diagnostics,
            metrics=metrics(context, policy, zeros),
            serialized_bytes=len(canonical(raw)),
            snapshot=row["snapshot"],
        )
        if canonical(actual) != canonical(row):
            raise ArithmeticError("structural layout/metric/archive replay mismatch")
        count += 1
    if count != len(rows):
        raise ArithmeticError("structural replay omitted rows")


def conservative_bounds(
    h: float, a: float, s: float, t: float, n: float
) -> tuple[float, float]:
    if any(
        type(v) not in (int, float) or not math.isfinite(v) or v < 0
        for v in (h, a, s, t, n)
    ):
        raise ValueError("finite nonnegative forecast durations required")
    return 4 * (1.2 * h + s + t), 4 * (1.2 * a + s + n)


def forecast(root: Path, check_path: Path) -> dict[str, Any]:
    from poker_ai.postflop.range_admission import replay as old_replay
    from poker_ai.postflop.range_admission_report import checked_audit
    from poker_ai.solver_validation.compact_full import validate

    checks(root, check_path)
    base = root / ROOT_FOLDER
    own_path = base / "software/own.json"
    native_path = base / "software/native.json"
    own = json.loads(own_path.read_text())
    native = json.loads(native_path.read_text())
    if own["software_only"] is not True or own["checks"] != bound(root, check_path):
        raise ArithmeticError("tiny software proof required")
    replay(root, own_path)
    validate(own, native, digest(own_path))
    t = measurement(own_path, "software-own")["seconds"]
    n = measurement(native_path, "software-native")["seconds"]
    costs = []
    inputs = [check_path, own_path, native_path]
    for repetition in (0, 1, 2):
        path = base / f"cost/{repetition}.json"
        cost = json.loads(path.read_text())
        expected = {
            (s, r)
            for s in contract(root)["spot_files"]
            for r in contract(root)["representations"]
        }
        ids = [(r["spot_file"], r["representation"]) for r in cost["rows"]]
        artifacts.check_source(root, cost["source"])
        if (
            cost["status"] != "completed"
            or cost["failure"] is not None
            or cost["repetition"] != repetition
            or cost["poker_training_performed"] is not False
            or len(ids) != len(set(ids))
            or set(ids) != expected
            or cost["checks"] != bound(root, check_path)
        ):
            raise ArithmeticError(
                "three complete source-bound structural repeats required"
            )
        costs.append(measurement(path, "layout")["seconds"])
        replay_layout(root, path)
        inputs.append(path)
    historical_own = root / "results/range-mass-admission/study.json"
    historical_native = root / "results/range-mass-admission/independent.json"
    previous, _, _ = old_replay(root, historical_own)
    old_native = json.loads(historical_native.read_text())
    checked_audit(historical_own, previous, old_native)
    h, a = previous["seconds"], old_native["seconds"]
    s = max(costs)
    own_bound, native_bound = conservative_bounds(h, a, s, t, n)
    inputs += [historical_own, historical_native]
    return dict(
        format="compact-full-forecast-v1",
        status="completed",
        source=artifacts.source(root, clean=True),
        runtime=runtime(),
        inputs=[bound(root, p) for p in inputs],
        historical_own_seconds=h,
        historical_native_seconds=a,
        maximum_structural_seconds=s,
        tiny_own_seconds=t,
        tiny_native_seconds=n,
        profile_ratio=1.2,
        safety_factor=4,
        own_forecast_seconds=own_bound,
        native_forecast_seconds=native_bound,
        within_fixed_caps=own_bound < 900 and native_bound < 900,
        actual_admission=False,
        fresh_global_admission=False,
        limitation=(
            "engineering safety margin, not a statistical bound; no new training prefix"
        ),
    )


def admission(root: Path, check_path: Path) -> dict[str, Any]:
    forecast_path = root / ROOT_FOLDER / "forecast.json"
    saved = json.loads(forecast_path.read_text())
    measurement(forecast_path, "forecast")
    actual = forecast(root, check_path)
    before = {k: v for k, v in saved.items() if k not in {"complete_command", "source"}}
    after = {k: v for k, v in actual.items() if k != "source"}
    if (
        canonical(before) != canonical(after)
        or saved["source"]["fingerprint"] != actual["source"]["fingerprint"]
    ):
        raise ArithmeticError("forecast raw inputs/arithmetic changed")
    paths = [forecast_path, check_path] + [
        checked_path(root, x) for x in saved["inputs"]
    ]
    for path in paths:
        artifacts.published(root, path)
    return dict(
        format="compact-full-admission-v1",
        status="completed",
        source=artifacts.source(root, clean=True),
        runtime=runtime(),
        inputs=[bound(root, p) for p in paths],
        full_trajectory_admitted=saved["within_fixed_caps"],
        actual_admission=False,
        fresh_global_admission=False,
        scope=(
            "permission for frozen full-control study only, "
            "not an accuracy or sampled admission"
        ),
    )


def require_admission(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    measurement(path, "admit")
    artifacts.check_source(root, saved["source"])
    if (
        saved["format"] != "compact-full-admission-v1"
        or saved["status"] != "completed"
        or saved["full_trajectory_admitted"] is not True
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
    ):
        raise ArithmeticError("full-control trajectory not admitted")
    for item in saved["inputs"]:
        checked_path(root, item)
    artifacts.published(root, path)
    check_path = root / ROOT_FOLDER / "checks.json"
    actual = admission(root, check_path)
    before = {k: v for k, v in saved.items() if k not in {"complete_command", "source"}}
    after = {k: v for k, v in actual.items() if k != "source"}
    if canonical(before) != canonical(after):
        raise ArithmeticError(
            "published admission no longer follows from checked inputs"
        )
    check_inputs(root, contract(root))
    return bound(root, path)
