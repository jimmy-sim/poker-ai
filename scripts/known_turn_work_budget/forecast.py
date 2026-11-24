"""Strict fixed two-worker admission from all twelve published profile paths."""

import math
from typing import Any

from known_turn_work_budget.plan import MAX_RSS, PROFILE_WORK, paths

FINAL_WORK = 40_000_000
PROFILE_CAP = 900
OWN_CAP = 7_200


def forecast(record: dict[str, Any]) -> dict[str, Any]:
    """Use each path's slowest of three complete 1m whole-path extrapolations.

    Worker 0 has wet/dry controls; worker 1 has wet/dry candidates. T is
    the larger sum of the two path maxima within one worker. The strict
    2*(2*T+600)<7200 bound includes a safety factor and fixed overhead.
    """
    if (
        record.get("status") != "completed"
        or record.get("worker_count") != 2
        or record.get("assignments") != [[0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11]]
        or type(record.get("seconds")) not in (int, float)
        or not 0 < record["seconds"] < PROFILE_CAP
    ):
        raise ArithmeticError("complete capped fixed-partition profile required")
    rows = []
    for worker in record["workers"]:
        done = [message for message in worker["messages"] if message["kind"] == "done"]
        if len(done) != 1 or worker["exitcode"] != 0:
            raise ArithmeticError("profile worker incomplete")
        rows.extend(done[0]["summary"]["summaries"])
    if len(rows) != 12 or {row["index"] for row in rows} != set(range(12)):
        raise ArithmeticError("twelve fixed profile paths missing or repeated")
    by_path: list[list[dict[str, Any]]] = [[], [], [], []]
    specs = paths()
    for row in rows:
        index = row["index"]
        spec = specs[index % 4]
        if (
            row["repeat"] != index // 4
            or row["path"]
            != dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
            or row["captures"] != 2
            or type(row["final_work"]) is not int
            or row["final_work"] < PROFILE_WORK
            or type(row["whole_path_seconds"]) not in (int, float)
            or not math.isfinite(row["whole_path_seconds"])
            or row["whole_path_seconds"] <= 0
            or type(row["worker_peak_rss_bytes"]) is not int
            or not 0 < row["worker_peak_rss_bytes"] <= MAX_RSS
        ):
            raise ArithmeticError("profile path work/source/time/memory changed")
        by_path[spec.index].append(row)
    maxima = []
    for index, repeats in enumerate(by_path):
        if len(repeats) != 3 or {row["repeat"] for row in repeats} != {0, 1, 2}:
            raise ArithmeticError("three complete repeats per path required")
        estimates = [
            row["whole_path_seconds"] * FINAL_WORK / row["final_work"]
            for row in repeats
        ]
        maxima.append(
            dict(
                index=index,
                repeat_estimates_seconds=estimates,
                maximum_seconds=max(estimates),
            )
        )
    worker_sums = [
        maxima[0]["maximum_seconds"] + maxima[2]["maximum_seconds"],
        maxima[1]["maximum_seconds"] + maxima[3]["maximum_seconds"],
    ]
    t = max(worker_sums)
    bound = 2 * (2 * t + 600)
    return dict(
        status="admitted" if bound < OWN_CAP else "rejected",
        profile_seconds=record["seconds"],
        final_work=FINAL_WORK,
        per_path_maxima=maxima,
        fixed_worker_sums_seconds=worker_sums,
        T_seconds=t,
        strict_bound_seconds=bound,
        whole_own_cap_seconds=OWN_CAP,
        rule="2*(2*T+600)<7200",
    )
