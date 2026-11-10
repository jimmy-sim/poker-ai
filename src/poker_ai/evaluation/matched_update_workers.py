"""Check fixed partitions and raw worker completion records."""

from typing import Any

from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.parallel_profile import same


def complete(batch: dict[str, Any], summary_fields: dict[str, int]) -> None:
    assignments = partition(24, 3)
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or type(batch["worker_count"]) is not int
        or batch["worker_count"] != 3
        or not same(batch["assignments"], assignments)
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("incomplete/different matched worker partition")
    for slot, worker in enumerate(batch["workers"]):
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            type(worker["slot"]) is not int
            or worker["slot"] != slot
            or type(worker["exitcode"]) is not int
            or worker["exitcode"] != 0
            or len(done) != 1
            or any(e["kind"] == "error" for e in worker["messages"])
            or any(
                e["kind"] == "cell"
                and (type(e["index"]) is not int or e["index"] not in assignments[slot])
                for e in worker["messages"]
            )
        ):
            raise ArithmeticError(
                "matched worker did not complete its assigned contexts"
            )
        summary = done[0]["summary"]
        if any(not same(summary[k], v) for k, v in summary_fields.items()):
            raise ArithmeticError("matched worker completion count changed")
