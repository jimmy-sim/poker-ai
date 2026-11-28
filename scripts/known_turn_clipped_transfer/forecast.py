"""Conservative one-time admission from twelve fixed candidate profiles."""

import math
from typing import Any

from known_turn_clipped_transfer.plan import MAX_RSS, PROFILE_WORK, paths

FINAL_WORK = 40_000_000
PROFILE_CAP = 900
OWN_CAP = 7_200


def forecast(record: dict[str, Any]) -> dict[str, Any]:
    """Use the slowest repeat per game, summed on fixed dry/wet workers."""
    specs = paths()
    count = len(specs)
    assignments = [list(range(0, count * 3, 2)), list(range(1, count * 3, 2))]
    if (
        record.get("status") != "completed"
        or record.get("worker_count") != 2
        or record.get("assignments") != assignments
        or type(record.get("seconds")) not in (int, float)
        or not 0 < record["seconds"] < PROFILE_CAP
    ):
        raise ArithmeticError("complete capped fixed-partition profile required")
    rows: list[dict[str, Any]] = []
    for worker in record["workers"]:
        done = [message for message in worker["messages"] if message["kind"] == "done"]
        if len(done) != 1 or worker["exitcode"] != 0:
            raise ArithmeticError("profile worker incomplete")
        rows.extend(done[0]["summary"]["summaries"])
    if len(rows) != count * 3 or {row["index"] for row in rows} != set(
        range(count * 3)
    ):
        raise ArithmeticError("twelve fixed profile paths missing or repeated")
    by_path: list[list[dict[str, Any]]] = [[] for _ in specs]
    for row in rows:
        index = row["index"]
        spec = specs[index % count]
        if (
            row["repeat"] != index // count
            or row["path"]
            != dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
            or row["captures"] != 2
            or type(row["final_work"]) is not int
            or row["final_work"] < PROFILE_WORK
            or type(row["whole_path_seconds"]) not in (int, float)
            or not math.isfinite(row["whole_path_seconds"])
            or row["whole_path_seconds"] <= 0
            or type(row["worker_peak_rss_bytes"]) is not int
            or not 0 < row["worker_peak_rss_bytes"] < MAX_RSS
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
        sum(item["maximum_seconds"] for item in maxima[::2]),
        sum(item["maximum_seconds"] for item in maxima[1::2]),
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
