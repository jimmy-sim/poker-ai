"""Complete 24-path/48-endpoint cost grids, exact source states and call ledgers."""

from typing import Any

from poker_ai.evaluation import batch_cost_stats
from poker_ai.evaluation.batch_cost_inputs import duration
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.parallel_profile import same


def validate_row(
    row: dict[str, Any], source: dict[str, Any], config: dict[str, Any], index: int
) -> None:
    if set(row) != {
        "index",
        "source_index",
        "mode",
        "endpoint",
        "whole_measure_seconds",
        "stats",
        "call_accounting",
    }:
        raise ArithmeticError("cost row fields changed")
    if (
        not same(row["index"], index)
        or not same(row["source_index"], source["index"])
        or row["mode"] not in config["modes"]
        or not duration(row["whole_measure_seconds"])
    ):
        raise ArithmeticError("cost row identity/duration changed")
    endpoint = row["endpoint"]
    if set(endpoint) != set(config["expected_endpoint_fields"]) | {
        "repetition",
        "setup_and_warm_seconds",
        "incremental_seconds",
        "cpu_seconds",
    } or not same(endpoint["repetition"], 0):
        raise ArithmeticError("cost endpoint fields/repetition changed")
    if any(
        not same(endpoint[k], source[k]) for k in config["expected_endpoint_fields"]
    ):
        raise ArithmeticError("cost endpoint differs from original state/work/source")
    if "projected_training_seconds" in endpoint:
        raise ArithmeticError(
            "instrumented extrapolation must not become a planning forecast"
        )
    for k in ("setup_and_warm_seconds", "incremental_seconds", "cpu_seconds"):
        if not duration(endpoint[k]):
            raise ArithmeticError("invalid cost endpoint duration")
    if (
        endpoint["setup_and_warm_seconds"] + endpoint["incremental_seconds"]
        > row["whole_measure_seconds"] + 1e-9
    ):
        raise ArithmeticError("cost endpoint elapsed accounting changed")
    if row["mode"] == "plain":
        if row["stats"] is not None or row["call_accounting"] is not None:
            raise ArithmeticError("plain control cannot claim function profiling")
    else:
        stats = row["stats"]
        batch_cost_stats.validate(stats)
        if (
            not same(
                row["call_accounting"],
                batch_cost_stats.call_accounting(stats, endpoint),
            )
            or stats["total_self_seconds"] > row["whole_measure_seconds"] + 1e-9
        ):
            raise ArithmeticError("profiler work/elapsed accounting changed")


def grid(
    rows: list[dict[str, Any]], selected: list[dict[str, Any]], config: dict[str, Any]
) -> None:
    if len(selected) != 24 or len(rows) != 48:
        raise ArithmeticError("cost endpoint grid incomplete")
    found = []
    checks = 0
    for row in rows:
        index = row["index"]
        if type(index) is not int or not 0 <= index < 24:
            raise ArithmeticError("cost selected index changed")
        validate_row(row, selected[index], config, index)
        found.append((index, row["mode"]))
        checks += len(row["endpoint"]["prefix_checks"])
    expected = {(i, m) for i in range(24) for m in config["modes"]}
    if set(found) != expected or len(set(found)) != 48 or checks != 32:
        raise ArithmeticError("cost modes/prefix checks missing/duplicate")


def gather(
    batch: dict[str, Any], selected: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(24, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("cost worker grid incomplete")
    rows = []
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("cost worker failed")
        events = [e for e in worker["messages"] if e["kind"] == "cell"]
        starts = [
            (e["index"], e["mode"])
            for e in worker["messages"]
            if e["kind"] == "prepared" and e.get("phase") == "measurement_started"
        ]
        if len(starts) != 2 * len(assigned) or set(starts) != {
            (i, m) for i in assigned for m in config["modes"]
        }:
            raise ArithmeticError("cost measurement-start inventory missing/duplicate")
        for event in events:
            if (
                type(event["index"]) is not int
                or event["index"] not in assigned
                or not same(event["row"]["index"], event["index"])
            ):
                raise ArithmeticError("cost row assignment changed")
            rows.append(event["row"])
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if len(done) != 1 or not same(
            done[0]["summary"],
            dict(
                paths=len(assigned),
                endpoints=2 * len(assigned),
                function_profiles=len(assigned),
            ),
        ):
            raise ArithmeticError("cost worker completion missing/changed")
    rows.sort(key=lambda r: (r["index"], config["modes"].index(r["mode"])))
    grid(rows, selected, config)
    return rows
