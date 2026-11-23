"""Data-only conservative eight-path full/full compute admission."""

import math
from typing import Any

from turn_exact_transfer.learning import paths

PROFILE_WORK = 1_000_000
FINAL_WORK = 10_000_000
PROFILE_CAP = 900
OWN_CAP = 7_200
OVERHEAD = 600


def forecast(record: dict[str, Any]) -> dict[str, Any]:
    """Take the worst of three whole-path extrapolations per fixed worker.

    Every profile time includes context, initialization, capture, scoring and
    replay. Scaling the complete observed interval by 10m/actual work is
    deliberately conservative; no phase is subtracted or repeat selected for
    speed. Admission requires strict `2*(2*T+600)<7200` seconds.
    """
    if (
        record.get("status") != "completed"
        or record.get("worker_count") != 3
        or record.get("assignments") != [list(range(i, 24, 3)) for i in range(3)]
        or type(record.get("seconds")) not in (int, float)
        or not 0 < record["seconds"] < PROFILE_CAP
    ):
        raise ArithmeticError("complete capped three-worker profile required")
    rows = []
    for worker in record["workers"]:
        done = [message for message in worker["messages"] if message["kind"] == "done"]
        if len(done) != 1 or worker["exitcode"] != 0:
            raise ArithmeticError("profile worker incomplete")
        rows.extend(done[0]["summary"]["summaries"])
    if len(rows) != 24 or {row["index"] for row in rows} != set(range(24)):
        raise ArithmeticError("profile path/repeat grid incomplete")
    by_path: list[list[dict[str, Any]]] = [[] for _ in range(8)]
    for row in rows:
        index = row["index"]
        spec = paths()[index % 8]
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm, seed=spec.seed)
        if (
            row["repeat"] != index // 8
            or row["path"] != expected
            or row["captures"] != 2
            or type(row["final_work"]) is not int
            or row["final_work"] < PROFILE_WORK
            or type(row["whole_path_seconds"]) not in (int, float)
            or not math.isfinite(row["whole_path_seconds"])
            or row["whole_path_seconds"] <= 0
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
    sums = [
        math.fsum(maxima[i]["maximum_seconds"] for i in range(slot, 8, 3))
        for slot in range(3)
    ]
    t = max(sums)
    conservative = 2 * (2 * t + OVERHEAD)
    return dict(
        status="admitted" if conservative < OWN_CAP else "rejected",
        profile_seconds=record["seconds"],
        profile_work_by_arm={spec.arm: PROFILE_WORK for spec in paths()},
        final_work=FINAL_WORK,
        per_path_maxima=maxima,
        fixed_worker_sums_seconds=sums,
        T_seconds=t,
        strict_bound_seconds=conservative,
        whole_own_cap_seconds=OWN_CAP,
        rule="2*(2*T+600)<7200",
    )
