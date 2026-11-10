"""Replay capture/scored lineage, raw books and every fixed target without training."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.matched_update_records import (
    inventory,
    lineage,
    paired_fixed,
    paired_self,
)
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline

ContextFor = Callable[[int], ScoringContext]
FixedFor = Callable[[dict[str, Any], FloatArray], list[dict[str, Any]]]


def reused(
    sources: inputs.Sources,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ids = {p["reused_profile_id"] for p in sources.manifest["self_pairs"]}
    profiles = [r for r in sources.archived.own["rows"] if r["id"] in ids]
    profiles += [r for r in sources.scored_currents.values() if r["id"] in ids]
    fixed = [r for r in sources.fixed if r["own_snapshot_id"] in ids]
    if len(profiles) != 144 or len(fixed) != 1152:
        raise ArithmeticError("all already-audited right endpoints/targets required")
    return profiles, fixed


def replay_archives(
    path: Path,
    saved: dict[str, Any],
    manifest: dict[str, Any],
    expected: list[dict[str, Any]],
    context_for: ContextFor,
    fixed_for: FixedFor,
    right: list[dict[str, Any]],
    right_fixed: list[dict[str, Any]],
    deadline: Deadline,
) -> dict[str, Any]:
    inventory(saved, manifest, expected)
    captures = {r["id"]: r for r in saved["captures"]}
    if len(saved["rows"]) != 144 or {r["id"] for r in saved["rows"]} != set(captures):
        raise ArithmeticError("scored profile inventory differs from captures")
    policies = {}
    for row, blob in read_archive(
        archive_path(path, saved["captures_file"]),
        saved["captures_sha256"],
        saved["captures"],
    ):
        deadline.check()
        context = context_for(row["path_index"])
        policies[row["id"]] = unpack_policy(
            context.partition, decode(blob, context, row)["policy"]
        )
    maximum = 0.0
    actual_fixed = []
    for row, blob in read_archive(
        archive_path(path, saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    ):
        deadline.check()
        context = context_for(row["path_index"])
        lineage(row, captures[row["id"]])
        error, detail = replay_detail(context, row, blob, 1e-9)
        policy = unpack_policy(context.partition, detail["policy"])
        if array_sha(policy) != array_sha(policies[row["id"]]):
            raise ArithmeticError("scored archive changed captured policy bits")
        maximum = max(maximum, error)
        actual_fixed.extend(fixed_for(row, policy))
    for row, blob in read_archive(
        archive_path(path, saved["masses_file"]),
        saved["masses_sha256"],
        saved["masses"],
    ):
        deadline.check()
        context = context_for(row["path_index"])
        mass = decode_mass(blob, context.partition, row)
        policy = policies[row["target_id"] + "-" + row["readout"] + "_average"]
        if array_sha(context.partition.normalize(mass)) != array_sha(policy):
            raise ArithmeticError("raw ledger does not reproduce captured average bits")

    def key(r: dict[str, Any]) -> tuple[Any, ...]:
        return r["own_snapshot_id"], r["opponent_profile_id"], r["target"]

    maximum = max(
        maximum, compare(sorted(actual_fixed, key=key), saved["fixed_matches"])
    )
    actual_self = paired_self(manifest, saved["rows"], right)
    actual_pairs = paired_fixed(manifest, actual_fixed, right_fixed)
    maximum = max(
        maximum,
        compare(actual_self, saved["self_pairs"]),
        compare(actual_pairs, saved["fixed_pairs"]),
    )
    if maximum > 1e-9:
        raise ArithmeticError("matched archive/fixed/paired replay changed")
    deadline.check()
    return dict(
        status="all144captures144scored96ledgers1152fixed_replayed",
        profiles=144,
        captures=144,
        raw_ledgers=96,
        fixed_targets=1152,
        self_pairs=144,
        fixed_pairs=1152,
        source_work_crossings=len(expected),
        maximum_error_chips=maximum,
        training_performed=False,
        reference_constructed=False,
    )


def replay_real(
    path: Path, saved: dict[str, Any], sources: inputs.Sources, deadline: Deadline
) -> dict[str, Any]:
    right, fixed = reused(sources)
    expected = [
        sources.original(i, w) for i in range(24) for w in (100000, 1000000, 10000000)
    ]
    return replay_archives(
        path,
        saved,
        sources.manifest,
        expected,
        sources.context,
        lambda row, policy: matches(
            sources.archived, row, policy, saved["source_sha256"]
        ),
        right,
        fixed,
        deadline,
    )
