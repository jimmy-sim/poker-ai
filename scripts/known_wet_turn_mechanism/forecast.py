"""Strict fixed two-worker conservative compute admission."""

import math
from typing import Any

from known_wet_turn_mechanism.plan import paths

PROFILE_WORK = 1_000_000
FINAL_WORK = 10_000_000
PROFILE_CAP = 900
OWN_CAP = 7_200
OVERHEAD = 600


def forecast(record: dict[str, Any]) -> dict[str, Any]:
    """Take each path's worst of three full-path time extrapolations.

    `T` is the larger fixed worker load; one control and one candidate run
    concurrently. Strict admission is `2*(2*T+600)<7200` seconds.
    """
    if (
        record.get("status") != "completed"
        or record.get("worker_count") != 2
        or record.get("assignments") != [[0, 2, 4], [1, 3, 5]]
        or type(record.get("seconds")) not in (int, float)
        or not 0 < record["seconds"] < PROFILE_CAP
    ):
        raise ArithmeticError("complete capped two-worker profile required")
    rows = []
    for worker in record["workers"]:
        done = [message for message in worker["messages"] if message["kind"] == "done"]
        if len(done) != 1 or worker["exitcode"] != 0:
            raise ArithmeticError("profile worker incomplete")
        rows.extend(done[0]["summary"]["summaries"])
    if len(rows) != 6 or {row["index"] for row in rows} != set(range(6)):
        raise ArithmeticError("profile path/repeat grid incomplete")
    by_path: list[list[dict[str, Any]]] = [[], []]
    specs = paths()
    for row in rows:
        index = row["index"]
        spec = specs[index % 2]
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm, seed=spec.seed)
        if (
            row["repeat"] != index // 2
            or row["path"] != expected
            or row["captures"] != 2
            or type(row["final_work"]) is not int
            or row["final_work"] < PROFILE_WORK
            or type(row["whole_path_seconds"]) not in (int, float)
            or not math.isfinite(row["whole_path_seconds"])
            or row["whole_path_seconds"] <= 0
            or type(row["worker_peak_rss_bytes"]) is not int
            or row["worker_peak_rss_bytes"] <= 0
        ):
            raise ArithmeticError("profile path source/work/timing changed")
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
    sums = [maxima[0]["maximum_seconds"], maxima[1]["maximum_seconds"]]
    t = max(sums)
    bound = 2 * (2 * t + OVERHEAD)
    return dict(
        status="admitted" if bound < OWN_CAP else "rejected",
        profile_seconds=record["seconds"],
        profile_work_by_arm={spec.arm: PROFILE_WORK for spec in specs},
        final_work=FINAL_WORK,
        per_path_maxima=maxima,
        fixed_worker_sums_seconds=sums,
        T_seconds=t,
        strict_bound_seconds=bound,
        whole_own_cap_seconds=OWN_CAP,
        rule="2*(2*T+600)<7200",
    )
