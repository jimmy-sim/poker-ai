"""Read-only parallel replay of every own saved checkpoint; never train."""

import time
from pathlib import Path
from typing import Any

from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.learning_artifacts import read_archive
from poker_ai.postflop.learning_protocol import read_own
from poker_ai.postflop.learning_training import replay_snapshot
from poker_ai.postflop.river_study import Deadline


def replay_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root, path = Path(payload["root"]), Path(payload["own_path"])
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(root, payload["comparison"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    saved, count, maximum = payload["own"], 0, 0.0
    for row, blob in read_archive(
        path.with_name(saved["details_file"]), saved["details_sha256"], saved["rows"]
    ):
        deadline.check()
        if row["index"] not in indices:
            continue
        context = contexts[row["case"]["spot_file"], row["case"]["representation"]]
        error = replay_snapshot(context, row, blob, 1e-9)
        maximum = max(maximum, error)
        count += 1
        send(
            dict(
                kind="cell", index=row["index"], id=row["id"], maximum_error_chips=error
            )
        )
    return dict(cells=len(indices), snapshots=count, maximum_error_chips=maximum)


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved, comparison = read_own(root, path)
    batch: dict[str, Any] = {}
    run_batch(
        140,
        3,
        replay_job,
        dict(
            root=str(root),
            own_path=str(path),
            own=saved,
            comparison=comparison,
            remaining_seconds=3600,
        ),
        Deadline(3600),
        batch,
    )
    events = [e for w in batch["workers"] for e in w["messages"] if e["kind"] == "cell"]
    if sorted(e["id"] for e in events) != sorted(r["id"] for r in saved["rows"]):
        raise ArithmeticError("own replay checkpoint inventory changed")
    return dict(
        status="all_own_controlled_checkpoints_replayed",
        snapshots=len(events),
        logical_checkpoints=sum(len(r["labels"]) for r in saved["rows"]),
        maximum_error_chips=max(e["maximum_error_chips"] for e in events),
        seconds=batch["seconds"],
    )
