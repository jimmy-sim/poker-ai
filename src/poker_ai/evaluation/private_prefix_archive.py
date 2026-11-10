"""Full-grid source/work/lineage/raw-mass replay without constructing a learner."""

from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_math import coverage, movement, window_mass
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.private_prefix_design import Design, index_rows, inventory
from poker_ai.finite import FloatArray
from poker_ai.postflop.cached_nodes import cache_nodes
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive, sha
from poker_ai.postflop.learning_training import replay_snapshot
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.private_prefix import PrefixPlan
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline

ContextFor = Callable[[int], ScoringContext]
FixedFor = Callable[[dict[str, Any], FloatArray, str], list[dict[str, Any]]]


def fixed_inventory(design: Design, saved: dict[str, Any]) -> None:
    rows = saved["fixed_matches"]
    actual = index_rows(rows, ("own_snapshot_id", "opponent_profile_id", "target"))
    final = {r["id"]: r for r in saved["rows"] if r["work_label"] == design.labels[-1]}
    if len(final) != 144 or len(actual) != 1152:
        raise ArithmeticError("complete private-prefix final fixed inventory required")
    peer_sets: dict[tuple[str, str], set[str]] = {}
    for identifier, own in final.items():
        selected = [r for r in rows if r["own_snapshot_id"] == identifier]
        peers = {r["opponent_profile_id"] for r in selected}
        if len(selected) != 8 or len(peers) != 4:
            raise ArithmeticError("four unchanged opponents and both seats required")
        key = own["case"]["spot_file"], own["case"]["representation"]
        if key in peer_sets and peer_sets[key] != peers:
            raise ArithmeticError("fixed opponent inventory changed across candidates")
        peer_sets[key] = peers
        for peer in peers:
            pair = [r for r in selected if r["opponent_profile_id"] == peer]
            if {r["target"] for r in pair} != {0, 1} or any(
                type(r["target"]) is not int for r in pair
            ):
                raise ArithmeticError("fixed target seat must be integer0/1")
        for row in selected:
            if (
                row["source_sha256"] != saved["source_sha256"]
                or row["own_policy_sha256"] != own["receipt"]["policy_sha256"]
                or row["own_variant"] != own["readout"]
                or any(
                    not same(row[k], own[k])
                    for k in ("case", "batch_size", "path_index", "work_label")
                )
            ):
                raise ArithmeticError("fixed candidate source/case/readout changed")


def replay(
    path: Path,
    saved: dict[str, Any],
    design: Design,
    context_for: ContextFor,
    fixed_for: FixedFor,
    deadline: Deadline,
) -> dict[str, Any]:
    contexts = {i: context_for(i) for i in range(48)}
    context_for = contexts.__getitem__
    inventory(design, saved, scored=True)
    fixed_inventory(design, saved)
    captures = {}
    for row, blob in read_archive(
        path.with_name(saved["captures_file"]),
        saved["captures_sha256"],
        saved["captures"],
    ):
        deadline.check()
        context = context_for(row["path_index"])
        policy = unpack_policy(context.partition, decode(blob, context, row)["policy"])
        captures[row["path_index"], row["work_label"], row["readout"]] = (row, policy)
    # Reconstruct the static chance plan independently of any trainer; cache by
    # exact context object, not a mutable input label from the archive.
    plans, warms = {}, {}
    currents = {}
    unitless = maximum = 0.0
    for index in range(48):
        context = context_for(index)
        tree = context.partition
        key = id(tree)
        if key not in plans:
            plans[key] = sha(asdict(PrefixPlan.build(cache_nodes(tree)[0])))
        previous_policy: FloatArray | None = None
        previous_row = None
        previous_guard = None
        for label in design.labels:
            row, policy = captures[index, label, "current"]
            if row["prefix_plan_sha256"] != plans[key] or row[
                "current_sha256"
            ] != array_sha(policy):
                raise ArithmeticError(
                    "private-prefix plan/current export differs from game"
                )
            if row["initialization_visits"] != 2 * len(tree.player):
                raise ArithmeticError("private-prefix exact warm work changed")
            same_crossing = (
                previous_row is not None
                and row["iteration"] == previous_row["iteration"]
            )
            if same_crossing:
                assert previous_row is not None
                if (
                    not same(row["current_movement"], previous_row["current_movement"])
                    or row["previous_capture_guard_sha256"]
                    != previous_row["previous_capture_guard_sha256"]
                ):
                    raise ArithmeticError("shared crossing movement metadata changed")
            else:
                if row["previous_capture_guard_sha256"] != previous_guard:
                    raise ArithmeticError("movement predecessor guard changed")
                actual = (
                    movement(tree, previous_policy, policy)
                    if previous_policy is not None
                    else None
                )
                if (actual is None) != (row["current_movement"] is None):
                    raise ArithmeticError("current movement warm predecessor changed")
                if actual is not None:
                    unitless = max(unitless, compare(actual, row["current_movement"]))
                previous_policy = policy
                previous_guard = row["guard_sha256"]
            previous_row = row
            currents[index, label] = row
    masses = {}
    for row, blob in read_archive(
        path.with_name(saved["masses_file"]), saved["masses_sha256"], saved["masses"]
    ):
        deadline.check()
        context = context_for(row["path_index"])
        mass = decode_mass(blob, context.partition, row)
        masses[row["path_index"], row["work_label"], row["readout"]] = mass
    expected_fixed = index_rows(
        saved["fixed_matches"], ("own_snapshot_id", "opponent_profile_id", "target")
    )
    observed_fixed = set()
    for row, blob in read_archive(
        path.with_name(saved["details_file"]), saved["details_sha256"], saved["rows"]
    ):
        deadline.check()
        index, label, readout = row["path_index"], row["work_label"], row["readout"]
        context = context_for(index)
        tree = context.partition
        captured, policy = captures[index, label, readout]
        stored = unpack_policy(tree, decode(blob, context, row)["policy"])
        if policy.tobytes() != stored.tobytes():
            raise ArithmeticError(
                "private-prefix scored archive changed captured policy"
            )
        maximum = max(maximum, replay_snapshot(context, row, blob, 1e-9))
        if readout != "current":
            mass = masses[index, label, readout.removesuffix("_average")]
            if tree.normalize(mass).tobytes() != policy.tobytes():
                raise ArithmeticError(
                    "private-prefix average no longer reconstructs from raw mass"
                )
            key = id(tree)
            if key not in warms:
                warms[key] = warm_mass(tree)
            first = np.unique(context.exact_to_partition, return_index=True)[1]
            river = (context.river_masks[0] | context.river_masks[1])[first]
            support = dict(
                whole=coverage(tree, mass, river),
                post_warm=coverage(tree, window_mass(tree, warms[key], mass), river),
            )
            unitless = max(unitless, compare(support, row["coverage"]))
        elif row["coverage"] is not None:
            raise ArithmeticError("current policy cannot claim average mass coverage")
        if label == design.labels[-1]:
            for record in fixed_for(row, policy, saved["source_sha256"]):
                k = (
                    record["own_snapshot_id"],
                    record["opponent_profile_id"],
                    record["target"],
                )
                if k not in expected_fixed or k in observed_fixed:
                    raise ArithmeticError("fixed replay identity changed or duplicated")
                observed_fixed.add(k)
                maximum = max(maximum, compare(record, expected_fixed[k]))
    if observed_fixed != set(expected_fixed) or maximum > 1e-9 or unitless > 1e-12:
        raise ArithmeticError("complete private-prefix archive/fixed replay failed")
    return dict(
        captures=432,
        profiles=432,
        masses=288,
        fixed_targets=1152,
        maximum_error_chips=maximum,
        maximum_error_unitless=unitless,
        learner_constructed=False,
        reference_constructed=False,
    )
