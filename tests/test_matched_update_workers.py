"""Raw worker completion must agree with fixed assignments and whole inventories."""

from typing import Any

import pytest

from poker_ai.evaluation.matched_update_workers import complete
from poker_ai.postflop.cell_process import partition


def fixture() -> dict[str, Any]:
    return dict(
        status="completed",
        failure=None,
        worker_count=3,
        assignments=partition(24, 3),
        workers=[
            dict(
                slot=i,
                exitcode=0,
                messages=[
                    dict(kind="cell", index=i, phase="EXPLICIT_TEST"),
                    dict(
                        kind="done",
                        summary=dict(paths=8, profiles=48, fixed_targets=384),
                    ),
                ],
            )
            for i in range(3)
        ],
    )


def test_complete_raw_fixed_partition() -> None:
    complete(fixture(), dict(paths=8, profiles=48, fixed_targets=384))


@pytest.mark.parametrize(
    "kind",
    [
        "status",
        "failure",
        "assignments",
        "worker_count",
        "slot",
        "exit",
        "missing_done",
        "duplicate_done",
        "bool_count",
        "cross_partition",
        "error",
    ],
)
def test_partial_or_corrupt_worker_cannot_supply_complete_receipt(kind: str) -> None:
    value = fixture()
    worker = value["workers"][0]
    if kind == "status":
        value["status"] = "incomplete"
    elif kind == "failure":
        value["failure"] = dict(type="TimeoutError")
    elif kind == "assignments":
        value["assignments"][0].pop()
    elif kind == "worker_count":
        value["worker_count"] = True
    elif kind == "slot":
        worker["slot"] = True
    elif kind == "exit":
        worker["exitcode"] = 1
    elif kind == "missing_done":
        worker["messages"].pop()
    elif kind == "duplicate_done":
        worker["messages"].append(worker["messages"][-1])
    elif kind == "bool_count":
        worker["messages"][-1]["summary"]["paths"] = True
    elif kind == "cross_partition":
        worker["messages"][0]["index"] = 1
    else:
        worker["messages"].append(dict(kind="error", reason="injected"))
    with pytest.raises(ArithmeticError):
        complete(value, dict(paths=8, profiles=48, fixed_targets=384))


def test_fixed_event_rows_sort_by_policy_before_opponent_and_seat() -> None:
    from poker_ai.evaluation.matched_update_run import gather

    rows = [
        dict(
            path_index=0,
            work_label=None,
            own_snapshot_id=policy,
            opponent_profile_id=opponent,
            target=seat,
        )
        for policy in ("prefix-000-B4-current", "prefix-000-B4-linear_average")
        for opponent in ("EXPLICIT_A", "EXPLICIT_B")
        for seat in (0, 1)
    ]
    saved = dict(
        batches=[
            dict(
                assignments=[[0], [1], [2]],
                workers=[
                    dict(
                        slot=0,
                        messages=[
                            dict(kind="cell", phase="fixed", index=0, row=r)
                            for r in rows
                        ],
                    )
                ],
            )
        ]
    )
    gather(saved)
    assert saved["fixed_matches"] == sorted(
        rows,
        key=lambda r: (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]),
    )
