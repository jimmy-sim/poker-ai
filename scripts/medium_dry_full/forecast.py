"""Data-only conservative six-path 1m-to-10m admission."""

import math
from typing import Any

from medium_dry_full.gate import PROFILE_WORK, WORK, paths


def forecast(record: dict[str, Any]) -> dict[str, Any]:
    """Sum each deterministic spot's slowest scaled repeat for serial work."""
    if (
        record.get("status") != "completed"
        or record.get("worker_count") != 1
        or record.get("assignments") != [list(range(6))]
        or type(record.get("seconds")) not in (int, float)
        or not 0 < record["seconds"] < 900
    ):
        raise ArithmeticError("complete capped six-path profile required")
    workers = record["workers"]
    if len(workers) != 1:
        raise ArithmeticError("one serial profile worker required")
    worker = workers[0]
    done = [message for message in worker["messages"] if message["kind"] == "done"]
    if len(done) != 1 or worker["exitcode"] != 0:
        raise ArithmeticError("incomplete serial profile worker")
    rows = done[0]["summary"]["summaries"]
    if len(rows) != 6 or {row["index"] for row in rows} != set(range(6)):
        raise ArithmeticError("missing profile index")
    maxima: list[dict[str, Any]] = []
    for path_index, game, arm in paths():
        repeats = [row for row in rows if row["index"] % 2 == path_index]
        if len(repeats) != 3 or {row["repeat"] for row in repeats} != {0, 1, 2}:
            raise ArithmeticError("missing spot repeat")
        estimates = []
        for row in repeats:
            if (
                row["path"] != dict(index=path_index, game=game, arm=arm)
                or row["captures"] != 2
                or type(row["final_work"]) is not int
                or row["final_work"] < PROFILE_WORK
                or type(row["whole_path_seconds"]) not in (int, float)
                or not math.isfinite(row["whole_path_seconds"])
                or row["whole_path_seconds"] <= 0
            ):
                raise ArithmeticError("invalid whole-path profile row")
            estimates.append(row["whole_path_seconds"] * WORK[-1] / row["final_work"])
        maxima.append(
            dict(
                index=path_index,
                repeat_estimates_seconds=estimates,
                maximum_seconds=max(estimates),
            )
        )
    t = math.fsum(row["maximum_seconds"] for row in maxima)
    bound = 2 * (2 * t + 600)
    return dict(
        status="admitted" if bound < 7200 else "rejected",
        profile_seconds=record["seconds"],
        profile_work=PROFILE_WORK,
        final_work=WORK[-1],
        per_path_maxima=maxima,
        serial_sum_seconds=t,
        T_seconds=t,
        strict_bound_seconds=bound,
        whole_own_cap_seconds=7200,
        rule="2*(2*T+600)<7200",
    )
