"""Exact old state/work controls and complete raw short-prefix worker receipts."""

from typing import Any

from poker_ai.evaluation import batch_reduction_inputs as inputs
from poker_ai.evaluation.frozen_batch_profile import forecast
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same


def grid(
    rows: list[dict[str, Any]],
    peers: list[dict[str, Any]],
    repeats: int,
    original_config: dict[str, Any],
) -> dict[str, Any] | None:
    if (
        type(repeats) is not int
        or repeats not in (1, 3)
        or len(peers) != 72
        or len(rows) != 72 * repeats
    ):
        raise ArithmeticError("incomplete reduction prefix grid")
    found = []
    for row in rows:
        i, r = row["index"], row["repetition"]
        if (
            type(i) is not int
            or not 0 <= i < 72
            or type(r) is not int
            or r not in range(repeats)
            or set(row) != set(peers[i])
        ):
            raise ArithmeticError("reduction row identity/schema changed")
        if any(not same(row[k], peers[i][k]) for k in inputs.IDENTITY):
            raise ArithmeticError("reduction differs from archived state/work")
        for key in (
            "setup_and_warm_seconds",
            "incremental_seconds",
            "cpu_seconds",
            "projected_training_seconds",
        ):
            if not number(row[key], nonnegative=True) or row[key] <= 0:
                raise ArithmeticError("invalid reduction time")
        initial = row["initialization_visits"]
        expected = (
            row["setup_and_warm_seconds"]
            + row["incremental_seconds"]
            * (10000000 - initial)
            / row["incremental_visits"]
        )
        if abs(row["projected_training_seconds"] - expected) > 1e-9:
            raise ArithmeticError("reduction projection changed")
        found.append((i, r))
    if len(set(found)) != 72 * repeats:
        raise ArithmeticError("duplicate reduction prefix")
    return forecast(rows, original_config) if repeats == 3 else None


def gather(
    batch: dict[str, Any],
    peers: list[dict[str, Any]],
    repeats: int,
    original_config: dict[str, Any],
) -> list[dict[str, Any]]:
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(72, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("incomplete reduction worker batch")
    rows = []
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("reduction worker failed")
        starts = []
        completed = []
        for e in worker["messages"]:
            if e["kind"] == "prepared" and e.get("phase") == "prefix_started":
                starts.append((e["index"], e["repetition"]))
            if e["kind"] == "cell":
                if type(e["index"]) is not int or e["index"] not in assigned:
                    raise ArithmeticError("reduction path assigned incorrectly")
                row = dict(index=e["index"], **e["row"])
                rows.append(row)
                completed.append((e["index"], row["repetition"]))
        expected = [(i, r) for i in assigned for r in range(repeats)]
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            not same(starts, expected)
            or not same(completed, expected)
            or len(done) != 1
            or not same(
                done[0]["summary"],
                dict(paths=len(assigned), rows=repeats * len(assigned)),
            )
        ):
            raise ArithmeticError("reduction completion/start inventory changed")
    rows.sort(key=lambda r: (r["index"], r["repetition"]))
    grid(rows, peers, repeats, original_config)
    return rows
