"""Read-only own profile/mass/current audits; never invoke a learner or native API."""

import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import decode_mass
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_math import coverage, movement, window_mass
from poker_ai.evaluation.averaging_history_replay import archive_path, compare_coverage
from poker_ai.evaluation.frozen_batch_validation import grid
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_training import expected_pass
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_training import replay_snapshot
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def warm_mass(tree: ArrayTree) -> FloatArray:
    """Original two simultaneous uniform t1 expected averages, no random draws."""
    uniform = tree.normalize(tree.legal)
    mass = np.zeros_like(tree.legal)
    lookup = {k: i for i, k in enumerate(tree.keys)}
    for target in (0, 1):
        for key, values in expected_pass(tree, uniform, target).averages.items():
            mass[lookup[key], : len(values)] += values
    return mass


def raw_grid(saved: dict[str, Any]) -> None:
    for name, weights, prefix in (
        ("masses", ("uniform", "linear"), "mass"),
        ("currents", ("linear",), "current"),
    ):
        rows = saved[name]
        expected = {
            (i, w, t)
            for i in range(72)
            for w in weights
            for t in saved["config"]["work_labels"]
        }
        found = []
        profiles = {
            (r["path_index"], r["case"]["average_weight"], r["work_label"]): r
            for r in saved["rows"]
            if r["path_index"] < 72
        }
        for row in rows:
            key = row["path_index"], row["case"]["average_weight"], row["work_label"]
            peer = profiles[key]
            identifier = (
                f"mass-{key[0]:03d}-{key[1]}-{key[2]}"
                if prefix == "mass"
                else f"current-{key[0]:03d}-{key[2]}"
            )
            if row["id"] != identifier or any(
                not same(row[k], peer[k])
                for k in ("case", "batch_size", "guard_sha256", "source_sha256")
            ):
                raise ArithmeticError("raw batch observation binding changed")
            found.append(key)
        if (
            len(found) != len(expected)
            or len(set(found)) != len(expected)
            or set(found) != expected
        ):
            raise ArithmeticError("raw batch observations missing/duplicate")
        if found != sorted(found):
            raise ArithmeticError("raw batch observation order must be canonical")


def replay_archives(
    path: Path,
    saved: dict[str, Any],
    data: HistoryInputs,
    deadline: Deadline,
) -> dict[str, Any]:
    started = time.perf_counter()
    grid(saved["rows"], data, saved["config"], saved["source_sha256"])
    raw_grid(saved)
    current_summary = {}
    previous: FloatArray | None = None
    last_index = -1
    maximum = unitless = 0.0
    for row, blob in read_archive(
        archive_path(path, saved["current_details_file"]),
        saved["current_details_sha256"],
        saved["currents"],
    ):
        deadline.check()
        index = row["path_index"]
        context = data.base.context(row["case"])
        if index != last_index:
            previous = None
        policy = unpack_policy(context.partition, decode(blob, context, row)["policy"])
        changes = (
            movement(context.partition, previous, policy)
            if previous is not None
            else None
        )
        if row["receipt"]["policy_sha256"] != row["current_sha256"] or (
            changes is None
        ) != (row["current_movement"] is None):
            raise ArithmeticError("raw current observation/movement changed")
        if changes is not None:
            error = compare(changes, row["current_movement"])
            unitless = max(unitless, error)
            if error > 1e-12:
                raise ArithmeticError("batch current movement replay failed")
        current_summary[index, row["work_label"]] = (row["current_sha256"], changes)
        previous, last_index = policy, index
    mass_stream = iter(
        read_archive(
            archive_path(path, saved["mass_details_file"]),
            saved["mass_details_sha256"],
            saved["masses"],
        )
    )
    warm_by_context = {}
    reconstructed = 0
    for row, blob in read_archive(
        archive_path(path, saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    ):
        deadline.check()
        context = data.base.context(row["case"])
        maximum = max(maximum, replay_snapshot(context, row, blob, 1e-9))
        if row["path_index"] >= 72:
            continue
        mass_row, mass_blob = next(mass_stream)
        if any(
            not same(row[k], mass_row[k])
            for k in (
                "path_index",
                "case",
                "batch_size",
                "work_label",
                "guard_sha256",
                "source_sha256",
            )
        ):
            raise ArithmeticError("batch mass/profile ordering changed")
        mass = decode_mass(mass_blob, context.partition, mass_row)
        policy = unpack_policy(context.partition, decode(blob, context, row)["policy"])
        if context.partition.normalize(mass).tobytes() != policy.tobytes():
            raise ArithmeticError("batch average no longer reconstructs from raw mass")
        key = row["case"]["spot_file"], row["case"]["representation"]
        if key not in warm_by_context:
            warm_by_context[key] = warm_mass(context.partition)
        first = np.unique(context.exact_to_partition, return_index=True)[1]
        river = (context.river_masks[0] | context.river_masks[1])[first]
        actual = dict(
            whole=coverage(context.partition, mass, river),
            post_warm=coverage(
                context.partition,
                window_mass(context.partition, warm_by_context[key], mass),
                river,
            ),
        )
        for name in actual:
            unitless = max(
                unitless, compare_coverage(actual[name], row["coverage"][name], 1e-12)
            )
        current, changes = current_summary[row["path_index"], row["work_label"]]
        if row["current_sha256"] != current or (changes is None) != (
            row["current_movement"] is None
        ):
            raise ArithmeticError("dual-book current observations differ")
        if changes is not None:
            error = compare(changes, row["current_movement"])
            if error > 1e-12:
                raise ArithmeticError("dual-book current movement changed")
            unitless = max(unitless, error)
        reconstructed += 1
    if (
        next(mass_stream, None) is not None
        or reconstructed != 432
        or len(current_summary) != 216
    ):
        raise ArithmeticError("unreplayed batch observations")
    deadline.check()
    return dict(
        status="all_batch_profiles_and_raw_observations_replayed",
        profiles=480,
        fresh_profiles=432,
        reused_full_profiles=48,
        mass_reconstructions=432,
        current_observations=216,
        maximum_error_chips=maximum,
        maximum_error_unitless=unitless,
        new_postflop_training_performed=False,
        seconds=time.perf_counter() - started,
    )
