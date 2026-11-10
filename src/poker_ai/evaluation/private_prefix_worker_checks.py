"""Check every raw completion against the fixed three spawned partitions."""

from typing import Any

from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.parallel_profile import same


def complete(batch: dict[str, Any], size: int) -> list[dict[str, Any]]:
    assignments = partition(size, 3)
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], assignments)
        or not same(batch["worker_count"], 3)
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("complete fixed three-worker partition required")
    cells = []
    for slot, worker in enumerate(batch["workers"]):
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            not same(worker["slot"], slot)
            or not same(worker["exitcode"], 0)
            or len(done) != 1
            or any(e["kind"] == "error" for e in worker["messages"])
            or not same(done[0]["summary"]["paths"], len(assignments[slot]))
        ):
            raise ArithmeticError("worker did not complete all assigned paths")
        for event in worker["messages"]:
            if event["kind"] != "cell":
                continue
            if (
                type(event["index"]) is not int
                or event["index"] not in assignments[slot]
            ):
                raise ArithmeticError("worker cell outside assigned partition")
            cells.append(event)
    return cells


def partial_cells(batch: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for worker in batch.get("workers", []):
        result.extend(e for e in worker["messages"] if e["kind"] == "cell")
    return result
