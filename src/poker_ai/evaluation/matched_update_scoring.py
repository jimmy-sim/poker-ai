"""Score immutable captures only after the complete original-trajectory barrier."""

from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.matched_update_capture import barrier, collect
from poker_ai.evaluation.matched_update_records import lineage, metadata
from poker_ai.evaluation.reduced_study_training import save
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.river_study import Deadline

REAL_SCOPE = "KNOWN_HOLDEM_MATCHED_UPDATE_DIAGNOSIS_NOT_GLOBAL_ADMISSION"


def score_capture(
    context: ScoringContext,
    row: dict[str, Any],
    blob: bytes,
    scratch: Path,
    send: Send,
    deadline: Deadline,
) -> tuple[dict[str, Any], Any]:
    policy = unpack_policy(context.partition, decode(blob, context, row)["policy"])
    meta = dict(
        **metadata(row),
        capture_sha256=row["receipt"]["sha256"],
        capture_metadata_sha256=row["metadata_sha256"],
        coordinate_axis="iteration",
        work_label=None,
    )
    scored = save(context, policy, meta, scratch, send, deadline)
    lineage(scored, row)
    return scored, policy


def training_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    sources = inputs.load(Path(payload["root"]))
    send(dict(kind="prepared", phase="own_sources_loaded"))
    counts = dict(paths=0, captures=0, masses=0, checkpoints=0, capture_events=0)
    for index in indices:
        deadline.check()
        send(dict(kind="cell", phase="training_started", index=index))
        result = collect(
            sources.context(index),
            sources.paths[index],
            index,
            sources.targets(index),
            [sources.original(index, w) for w in (100000, 1000000, 10000000)],
            Path(payload["scratch"]),
            payload["binding"],
            REAL_SCOPE,
            send,
            deadline,
        )
        for key in counts:
            counts[key] += 1 if key == "paths" else result[key]
        send(dict(kind="cell", phase="trained", index=index, row=result))
    return counts


def scoring_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    sources = inputs.load(Path(payload["root"]))
    expected = [
        sources.original(i, w) for i in range(24) for w in (100000, 1000000, 10000000)
    ]
    # Every worker independently checks the parent-wide barrier before scoring.
    barrier(payload["checkpoints"], expected)
    counts = dict(paths=len(indices), profiles=0, fixed_targets=0)
    path, saved = Path(payload["own_path"]), payload["own"]
    for row, blob in read_archive(
        archive_path(path, saved["captures_file"]),
        saved["captures_sha256"],
        saved["captures"],
    ):
        deadline.check()
        if row["path_index"] not in indices:
            continue
        context = sources.context(row["path_index"])
        scored, policy = score_capture(
            context, row, blob, Path(payload["scratch"]), send, deadline
        )
        counts["profiles"] += 1
        for record in matches(sources.archived, scored, policy, payload["binding"]):
            send(dict(kind="cell", phase="fixed", index=row["path_index"], row=record))
            counts["fixed_targets"] += 1
    return counts
