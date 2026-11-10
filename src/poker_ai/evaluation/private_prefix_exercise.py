"""Generic complete own capture/scoring/archive/replay exercise, no admission.

The explicit fixture caller supplies one nonuniform Kuhn game. Real workers must
be separately gated; this function accepts no file path or alternate learner
factory from a command line. It is an IO primitive, not authority to train poker.
"""

from pathlib import Path
from typing import Any

from poker_ai.evaluation.private_prefix_archive import ContextFor, FixedFor, replay
from poker_ai.evaluation.private_prefix_capture import collect
from poker_ai.evaluation.private_prefix_design import Design, inventory
from poker_ai.evaluation.private_prefix_io import archive, gather
from poker_ai.evaluation.reduced_study_training import save
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline


def exercise(
    path: Path,
    saved: dict[str, Any],
    design: Design,
    context_for: ContextFor,
    fixed_for: FixedFor,
    scratch: Path,
    deadline: Deadline,
) -> None:
    def retain(event: dict[str, Any]) -> None:
        saved["events"].append(event)

    for index in range(48):
        deadline.check()
        retain(dict(kind="cell", phase="training_started", index=index))
        result = collect(
            context_for(index),
            design,
            index,
            scratch,
            saved["source_sha256"],
            retain,
            deadline,
        )
        retain(dict(kind="cell", phase="trained", index=index, result=result))
        gather(saved)
        persist(path, saved)
    inventory(design, saved, scored=False)
    archive(path, saved, scratch, "captures", "captures")
    archive(path, saved, scratch, "masses", "masses")
    # Every capture is complete before the first new policy score.
    for captured, blob in read_archive(
        path.with_name(saved["captures_file"]),
        saved["captures_sha256"],
        saved["captures"],
    ):
        deadline.check()
        context = context_for(captured["path_index"])
        policy = unpack_policy(
            context.partition, decode(blob, context, captured)["policy"]
        )
        metadata = {
            k: v
            for k, v in captured.items()
            if k not in {"file", "receipt", "metadata_sha256", "seconds", "cpu_seconds"}
        }
        metadata.update(
            capture_sha256=captured["receipt"]["sha256"],
            capture_metadata_sha256=captured["metadata_sha256"],
        )
        scored = save(context, policy, metadata, scratch, retain, deadline)
        if scored["work_label"] == design.labels[-1]:
            for row in fixed_for(scored, policy, saved["source_sha256"]):
                retain(
                    dict(
                        kind="cell", phase="fixed", index=scored["path_index"], row=row
                    )
                )
    gather(saved)
    inventory(design, saved, scored=True)
    archive(path, saved, scratch, "rows", "profiles")
    saved["own_replay"] = replay(path, saved, design, context_for, fixed_for, deadline)
