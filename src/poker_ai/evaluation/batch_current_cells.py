"""Rescore saved currents and fixed opponents in isolated workers, never train."""

from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.reduced_study_training import save
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.river_study import Deadline


def policies(sources: inputs.Sources, kind: str) -> Any:
    current = kind == "current"
    key = "current_details" if current else "details"
    rows = sources.own["currents" if current else "rows"]
    yield from read_archive(
        archive_path(sources.own_path, sources.own[key + "_file"]),
        sources.own[key + "_sha256"],
        rows,
    )


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    root = Path(payload["root"])
    sources = inputs.load(root)
    return evaluate_paths(indices, payload, send, sources, deadline)


def evaluate_paths(
    indices: list[int],
    payload: dict[str, Any],
    send: Send,
    sources: inputs.Sources,
    deadline: Deadline,
) -> dict[str, Any]:
    final = sources.own["config"]["work_labels"][-1]
    peers = {
        (r["path_index"], r["work_label"]): r
        for r in sources.own["rows"]
        if r["path_index"] < 72 and r["case"]["average_weight"] == "linear"
    }
    self_count = fixed_count = candidate_count = 0
    for kind in ("current", "average"):
        for row, blob in policies(sources, kind):
            deadline.check()
            index = row["path_index"]
            if index not in indices or (
                kind == "average" and (index >= 72 or row["work_label"] != final)
            ):
                continue
            context = sources.data.base.context(row["case"])
            policy = unpack_policy(
                context.partition, decode(blob, context, row)["policy"]
            )
            candidate = row
            if kind == "current":
                peer = peers[index, row["work_label"]]
                metadata = dict(
                    id=row["id"],
                    path_index=index,
                    case=row["case"],
                    batch_size=row["batch_size"],
                    work_label=row["work_label"],
                    variant="current",
                    origin="saved_current_rescored_no_training",
                    source_current_id=row["id"],
                    source_current_policy_sha256=row["receipt"]["policy_sha256"],
                    source_guard_sha256=row["guard_sha256"],
                    source_study_sha256=sources.own["source_sha256"],
                    source_sha256=payload["binding"],
                    iteration=peer["iteration"],
                    total_work=peer["total_work"],
                )
                candidate = save(
                    context, policy, metadata, Path(payload["scratch"]), send, deadline
                )
                if (
                    candidate["receipt"]["policy_sha256"]
                    != row["receipt"]["policy_sha256"]
                ):
                    raise ArithmeticError("rescoring changed current policy bytes")
                self_count += 1
            if row["work_label"] == final:
                for record in matches(sources, candidate, policy, payload["binding"]):
                    send(dict(kind="cell", phase="fixed", index=index, row=record))
                    fixed_count += 1
                candidate_count += 1
    return dict(
        paths=len(indices),
        self_profiles=self_count,
        fixed_targets=fixed_count,
        final_candidates=candidate_count,
    )
