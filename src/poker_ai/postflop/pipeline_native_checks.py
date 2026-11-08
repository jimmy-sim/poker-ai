"""Native-receipt arithmetic validation only; no native runtime import."""

import math
from typing import Any

from poker_ai.postflop import pipeline_cost as own
from poker_ai.postflop.cell_process import THREAD_ENV, partition
from poker_ai.postflop.parallel_profile import finite, same


def validate_native(
    native: dict[str, Any],
    saved: dict[str, Any],
    profiles: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> None:
    batches = native["batches"]
    if len(batches) != 3 or not same([b["repeat"] for b in batches], [0, 1, 2]):
        raise ArithmeticError("native pipeline repeat grid incomplete")
    expected = partition(16, 3)
    tolerance = saved["config"]["tolerance_chips"]
    count = 0
    for batch in batches:
        if (
            batch["status"] != "completed"
            or batch["failure"] is not None
            or not same(batch["worker_count"], 3)
            or not same(batch["assignments"], expected)
            or len(batch["workers"]) != 3
            or not all(
                finite(batch[k], positive=(k == "seconds"))
                for k in (
                    "seconds",
                    "parent_cpu_seconds",
                    "reaped_children_cpu_seconds",
                )
            )
        ):
            raise ArithmeticError("native pipeline batch incomplete")
        pids = []
        for slot, worker in enumerate(batch["workers"]):
            events = worker["messages"]
            if (
                not same(worker["slot"], slot)
                or not same(worker["exitcode"], 0)
                or type(worker["pid"]) is not int
                or worker["pid"] <= 0
                or [e["kind"] for e in events]
                != ["started", "prepared"] + ["cell"] * len(expected[slot]) + ["done"]
                or not same(events[0]["pid"], worker["pid"])
                or not same(events[0]["thread_environment"], THREAD_ENV)
                or not finite(events[1]["seconds"])
                or not finite(events[-1]["seconds"], positive=True)
                or not finite(events[-1]["cpu_seconds"])
                or events[-1]["seconds"] > batch["seconds"] + 1e-6
                or not same(events[-1]["summary"], dict(cells=len(expected[slot])))
            ):
                raise ArithmeticError("native worker identity/setup/events changed")
            pids.append(worker["pid"])
            measured = events[1]["seconds"]
            for index, event in zip(expected[slot], events[2:-1], strict=True):
                row = event["row"]
                if (
                    not same(event["index"], index)
                    or not same(row["index"], index)
                    or not same(row["case"], {k: cases[index][k] for k in own.CASE})
                    or set(row["native_metrics"]) != set(own.METRICS)
                    or not all(
                        type(v) in (int, float) and math.isfinite(v)
                        for v in row["native_metrics"].values()
                    )
                    or not finite(row["seconds"], positive=True)
                    or not finite(row["cpu_seconds"])
                    or not finite(row["maximum_error_chips"])
                    or row["maximum_error_chips"] > tolerance
                    or len(row["responses"]) != 2
                ):
                    raise ArithmeticError("native scalar/timer/profile mismatch")
                errors = [
                    abs(row["native_metrics"][k] - profiles[index]["metrics"][k])
                    for k in own.METRICS
                ]
                for target, response in enumerate(row["responses"]):
                    own_reply = profiles[index]["responses"][target]
                    if not same(response["target"], target):
                        raise ArithmeticError("native target order changed")
                    names = {
                        "exact_root_chips": "exact_reply_value_chips",
                        "restricted_root_chips": "restricted_reply_value_chips",
                        "achieved_exact_chips": "exact_reply_value_chips",
                        "achieved_restricted_chips": "restricted_reply_value_chips",
                        "achieved_river_before_chips": "river_before_value_chips",
                    }
                    for native_key, own_key in names.items():
                        value = response[native_key]
                        if type(value) not in (int, float) or not math.isfinite(value):
                            raise ArithmeticError("nonfinite native reply")
                        errors.append(abs(value - own_reply[own_key]))
                if (
                    max(errors) > tolerance
                    or abs(row["maximum_error_chips"] - max(errors)) > 1e-15
                ):
                    raise ArithmeticError(
                        "native error receipt/achieved replies disagree"
                    )
                roots = row["responses"]
                derived = dict(
                    exact_exploitability_chips=sum(r["exact_root_chips"] for r in roots)
                    / 2,
                    within_partition_gain_chips=sum(
                        r["restricted_root_chips"] for r in roots
                    )
                    / 2,
                    extra_information_gap_chips=sum(
                        r["exact_root_chips"] - r["restricted_root_chips"]
                        for r in roots
                    )
                    / 2,
                    river_only_gain_exact_prefix_chips=sum(
                        r["exact_root_chips"] - r["achieved_river_before_chips"]
                        for r in roots
                    )
                    / 2,
                )
                if any(
                    abs(row["native_metrics"][k] - v) > tolerance
                    for k, v in derived.items()
                ):
                    raise ArithmeticError("native root aggregation changed")
                measured += row["seconds"]
                count += 1
            if measured > events[-1]["seconds"] + 1e-6:
                raise ArithmeticError("native worker omitted measured costs")
        if len(set(pids)) != 3:
            raise ArithmeticError("native worker PID duplicated")
    if (
        count != 48
        or not finite(native["seconds"], positive=True)
        or math.fsum(b["seconds"] for b in batches) > native["seconds"] + 1e-6
        or native["seconds"] > saved["config"]["native_calibration_maximum_seconds"]
        or not finite(native["parent_cpu_seconds"])
        or not finite(native["reaped_children_cpu_seconds"])
        or native["reaped_children_cpu_seconds"] + 0.05
        < math.fsum(b["reaped_children_cpu_seconds"] for b in batches)
        or native["parent_cpu_seconds"] + 1e-6
        < math.fsum(b["parent_cpu_seconds"] for b in batches)
    ):
        raise ArithmeticError("native total time/case count/CPU mismatch")
