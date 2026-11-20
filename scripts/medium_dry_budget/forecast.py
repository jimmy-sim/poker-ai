"""Conservative fixed 18-path 1m-to-100m work admission, data only."""

import math
from typing import Any

from medium_dry_budget.gate import PROFILE_WORK, WORK, paths


def forecast(record: dict[str, Any]) -> dict[str, Any]:
    """Take each path's slowest complete repeat before fixed-worker summing."""
    if (
        record.get("status") != "completed"
        or record.get("worker_count") != 3
        or record.get("assignments") != [list(range(i, 18, 3)) for i in range(3)]
        or type(record.get("seconds")) not in (int, float)
        or not 0 < record["seconds"] < 900
    ):
        raise ArithmeticError("complete capped 18-path profile required")
    rows: list[dict[str, Any]] = []
    for worker in record["workers"]:
        done = [m for m in worker["messages"] if m["kind"] == "done"]
        if len(done) != 1 or worker["exitcode"] != 0:
            raise ArithmeticError("incomplete profile worker")
        rows.extend(done[0]["summary"]["summaries"])
    if len(rows) != 18 or {row["index"] for row in rows} != set(range(18)):
        raise ArithmeticError("missing profile index")
    maxima: list[dict[str, Any]] = []
    for path_index, seed, arm in paths():
        repeats = [row for row in rows if row["index"] % 6 == path_index]
        if len(repeats) != 3 or {row["repeat"] for row in repeats} != {0, 1, 2}:
            raise ArithmeticError("missing path repeat")
        estimates = []
        for row in repeats:
            expected = dict(
                index=path_index, game="new_medium_dry_oop", seed=seed, arm=arm
            )
            if (
                row["path"] != expected
                or row["captures"] != 3
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
    sums = [
        math.fsum(maxima[i]["maximum_seconds"] for i in range(slot, 6, 3))
        for slot in range(3)
    ]
    t = max(sums)
    bound = 2 * (2 * t + 600)
    return dict(
        status="admitted" if bound < 7200 else "rejected",
        profile_seconds=record["seconds"],
        profile_work=PROFILE_WORK,
        final_work=WORK[-1],
        per_path_maxima=maxima,
        fixed_worker_sums_seconds=sums,
        T_seconds=t,
        strict_bound_seconds=bound,
        whole_own_cap_seconds=7200,
        rule="2*(2*T+600)<7200",
    )
