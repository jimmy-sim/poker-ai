"""Reconstruct all saved-current scores and fixed targets with OWN arithmetic."""

import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_cells import policies
from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.batch_current_validation import grid
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def replay_archives(
    path: Path, saved: dict[str, Any], sources: inputs.Sources, deadline: Deadline
) -> dict[str, Any]:
    started = time.perf_counter()
    grid(saved["rows"], saved["fixed_matches"], sources, saved["source_sha256"])
    maximum = 0.0
    count = 0
    actual_fixed = []
    final = sources.own["config"]["work_labels"][-1]
    for row, blob in read_archive(
        archive_path(path, saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    ):
        deadline.check()
        context = sources.data.base.context(row["case"])
        error, detail = replay_detail(context, row, blob, 1e-9)
        maximum = max(maximum, error)
        count += 1
        if row["work_label"] == final:
            policy = unpack_policy(context.partition, detail["policy"])
            actual_fixed.extend(matches(sources, row, policy, saved["source_sha256"]))
    for row, blob in policies(sources, "average"):
        if row["path_index"] >= 72 or row["work_label"] != final:
            continue
        deadline.check()
        context = sources.data.base.context(row["case"])
        policy = unpack_policy(context.partition, decode(blob, context, row)["policy"])
        actual_fixed.extend(matches(sources, row, policy, saved["source_sha256"]))
    actual_fixed.sort(
        key=lambda r: (r["own_snapshot_id"], r["opponent_profile_id"], r["target"])
    )
    maximum = max(maximum, compare(actual_fixed, saved["fixed_matches"]))
    if count != 216 or len(actual_fixed) != 1728 or maximum > 1e-9:
        raise ArithmeticError("saved current/fixed arithmetic replay failed")
    return dict(
        status="all216currents_and1728fixed_targets_replayed",
        current_profiles=count,
        fixed_targets=len(actual_fixed),
        maximum_error_chips=maximum,
        seconds=time.perf_counter() - started,
        training_performed=False,
        reference_constructed=False,
    )
