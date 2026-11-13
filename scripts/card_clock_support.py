"""Own-process boundary observations; no machine-wide process or power data."""

import math
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from profile_compact_replay import atomic

COUNTERS = (
    "ru_maxrss",
    "ru_minflt",
    "ru_majflt",
    "ru_nswap",
    "ru_inblock",
    "ru_oublock",
    "ru_nvcsw",
    "ru_nivcsw",
)
CPU = ("ru_utime", "ru_stime")
CLOCKS = ("perf_seconds", "utc_seconds", "process_cpu_seconds", "thread_cpu_seconds")


def usage(which: int) -> dict[str, Any]:
    raw = resource.getrusage(which)
    return {name: getattr(raw, name) for name in (*COUNTERS, *CPU)}


def snapshot() -> dict[str, Any]:
    return dict(
        pid=os.getpid(),
        platform=sys.platform,
        rss_unit="bytes"
        if sys.platform == "darwin"
        else "KiB"
        if sys.platform.startswith("linux")
        else "platform_native_uninterpreted",
        perf_seconds=time.perf_counter(),
        utc_seconds=time.time(),
        process_cpu_seconds=time.process_time(),
        thread_cpu_seconds=time.thread_time(),
        self_usage=usage(resource.RUSAGE_SELF),
        reaped_child_usage=usage(resource.RUSAGE_CHILDREN),
    )


def valid(row: dict[str, Any]) -> None:
    if (
        set(row)
        != {"pid", "platform", "rss_unit", *CLOCKS, "self_usage", "reaped_child_usage"}
        or type(row["pid"]) is not int
        or row["pid"] <= 0
        or not isinstance(row["platform"], str)
    ):
        raise ArithmeticError("complete own-process clock snapshot required")
    expected = (
        "bytes"
        if row["platform"] == "darwin"
        else "KiB"
        if row["platform"].startswith("linux")
        else "platform_native_uninterpreted"
    )
    if row["rss_unit"] != expected:
        raise ArithmeticError("RSS units must follow actual producer platform")
    if any(
        type(row[k]) not in (int, float) or not math.isfinite(row[k]) or row[k] < 0
        for k in CLOCKS
    ):
        raise ArithmeticError("finite nonnegative raw clocks required")
    for kind in ("self_usage", "reaped_child_usage"):
        values = row[kind]
        if (
            set(values) != set((*COUNTERS, *CPU))
            or any(type(values[k]) is not int or values[k] < 0 for k in COUNTERS)
            or any(
                type(values[k]) not in (int, float)
                or not math.isfinite(values[k])
                or values[k] < 0
                for k in CPU
            )
        ):
            raise ArithmeticError("complete nonnegative OS resource snapshot required")


def interval(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    valid(before)
    valid(after)
    if any(before[k] != after[k] for k in ("pid", "platform", "rss_unit")):
        raise ArithmeticError("one producer process and resource units per interval")
    clocks = {k: after[k] - before[k] for k in CLOCKS}
    if any(clocks[k] < 0 for k in CLOCKS if k != "utc_seconds"):
        raise ArithmeticError("monotonic active and elapsed clocks required")
    values = {}
    for kind in ("self_usage", "reaped_child_usage"):
        a, b = before[kind], after[kind]
        delta = {k: b[k] - a[k] for k in (*CPU, *COUNTERS) if k != "ru_maxrss"}
        if any(v < 0 for v in delta.values()):
            raise ArithmeticError("cumulative OS counters must not decrease")
        values[kind] = dict(
            delta=delta,
            peak_rss_before=a["ru_maxrss"],
            peak_rss_after=b["ru_maxrss"],
            rss_unit=before["rss_unit"],
            peak_is_cumulative_not_interval_allocation=True,
        )
    return dict(
        clocks=clocks,
        resources=values,
        scope=(
            "nearby non-atomic boundary calls; CPU is not a wall interval; "
            "UTC is observational; OS-zero counters may be unsupported"
        ),
    )


def record(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return dict(before=before, after=after, interval=interval(before, after))


def check_record(saved: dict[str, Any]) -> None:
    if set(saved) != {"before", "after", "interval"} or saved["interval"] != interval(
        saved["before"], saved["after"]
    ):
        raise ArithmeticError("resource interval differs from raw boundary snapshots")


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Any
) -> dict[str, Any]:
    """Unchanged numerical worker/summary; separate instrumentation sidecar."""
    from compact_cached.native import independent
    from trace_card_audit import CONFIG_SHA, preflight

    root = Path(payload["root"])
    folder = Path(os.environ["POKER_CARD_CLOCK_DIR"])
    if not folder.resolve().is_relative_to(root.resolve() / "results/runs"):
        raise ArithmeticError(
            "worker instrumentation must stay inside fresh run folder"
        )
    path = folder / f"worker-{slot}.json"
    if path.exists() or path.is_symlink():
        raise FileExistsError("retain previous worker telemetry")
    before = snapshot()
    saved: dict[str, Any] = dict(
        status="running",
        slot=slot,
        indices=indices,
        config_sha256=CONFIG_SHA,
        before=before,
        scope=(
            "instrumented wrapper; unchanged original numeric worker/summary, "
            "no card hooks installed"
        ),
    )
    atomic(path, saved)
    try:
        _, source = preflight(root, clean=False)
        import numpy

        import poker_ai

        saved["runtime"] = dict(
            python=sys.version.split()[0],
            numpy=numpy.__version__,
            module_is_under_checked_source_root=Path(poker_ai.__file__)
            .resolve()
            .is_relative_to(root.resolve() / "src"),
        )
        saved["source"] = source
        atomic(path, saved)
        result = independent(slot, indices, payload, send)
        saved.update(
            numeric_summary=result, phase="numeric_finished_after_source_pending"
        )
        atomic(path, saved)
        _, after_source = preflight(root, clean=False)
        if source["sha256"] != after_source["sha256"]:
            raise ArithmeticError("effective worker instrumentation source changed")
        saved.update(
            status="complete_worker_resource_trace",
            numeric_summary=result,
            observation=record(before, snapshot()),
        )
        atomic(path, saved)
        return result
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
            after_failure=snapshot(),
        )
        atomic(path, saved)
        raise
