"""Replay all OWN strategy/mass archives and fixed-opponent target matches."""

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_math import (
    coverage,
    fixed_match,
    movement,
    window_mass,
)
from poker_ai.evaluation.averaging_history_validation import grid
from poker_ai.evaluation.controlled_reply_inputs import modes
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def archive_path(path: Path, name: Any) -> Path:
    if not isinstance(name, str) or Path(name).name != name or name in ("", ".", ".."):
        raise ArithmeticError("history archive must be a bound filename")
    return path.with_name(name)


def compare_coverage(
    actual: dict[str, Any], saved: dict[str, Any], tolerance: float
) -> float:
    if set(actual) != set(saved) or set(saved) != {"all", "river"}:
        raise ArithmeticError("window coverage regions changed")
    maximum = 0.0
    for label in ("all", "river"):
        a, b = actual[label], saved[label]
        if set(a) != set(b) or any(
            not same(a[k], b[k]) for k in ("rows", "positive_rows")
        ):
            raise ArithmeticError("window support row counts changed")
        for key in ("row_fraction", "uniform_reach_fraction"):
            if a[key] is None:
                if b[key] is not None:
                    raise ArithmeticError("zero-support coverage changed")
            elif (
                not number(b[key], nonnegative=True)
                or b[key] > 1
                or abs(a[key] - b[key]) > tolerance
            ):
                raise ArithmeticError("window unitless coverage changed")
            else:
                maximum = max(maximum, abs(a[key] - b[key]))
    return maximum


def replay_archives(
    root: Path,
    path: Path,
    saved: dict[str, Any],
    data: HistoryInputs,
    deadline: Deadline,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retained boundaries reconstruct suffix/whole policies without new training.

    Every source profile is rescored independently with the OWN scorer. Native
    comparison belongs to a separate validation runner and supplies no strategy.
    Keep one case's dense arrays at a time, not the whole padded archive in RAM.
    """
    started = time.perf_counter()
    grid(saved["rows"], saved["masses"], data, saved["source_sha256"])
    stream = read_archive(
        archive_path(path, saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    )
    mass_stream = read_archive(
        archive_path(path, saved["mass_details_file"]),
        saved["mass_details_sha256"],
        saved["masses"],
    )
    controls = {
        (r["own_profile_id"], r["opponent_profile_id"], r["target"]): r
        for c in json.loads((root / "results/controlled-replies/own.json").read_text())[
            "crosses"
        ]
        for r in c["responses"]
    }
    if len(controls) != 512:
        raise ArithmeticError("original fixed-opponent control inventory incomplete")
    maximum, unitless, identity_error = 0.0, 0.0, 0.0
    count, mass_count, suffix_count, whole_count = 0, 0, 0, 0
    matches = []
    order = {mode: i for i, mode in enumerate(modes(data.config))}
    for index, source in enumerate(data.base.policies):
        deadline.check()
        context = data.base.context(source.case)
        tree = context.partition
        first = np.unique(context.exact_to_partition, return_index=True)[1]
        river = (context.river_masks[0] | context.river_masks[1])[first]
        boundaries: dict[int, tuple[dict[str, Any], FloatArray]] = {}
        for expected_order, label in enumerate(
            data.config["cumulative_mass_work_labels"]
        ):
            row, blob = next(mass_stream)
            if not same(
                [row["index"], row["order"], row["work_label"]],
                [index, expected_order, label],
            ):
                raise ArithmeticError("cumulative history boundary stream changed")
            boundaries[label] = row, decode_mass(blob, tree, row)
            mass_count += 1
        previous: FloatArray | None = None
        final_variants: dict[str, tuple[dict[str, Any], FloatArray]] = {}
        for expected_order in range(8):
            deadline.check()
            row, blob = next(stream)
            if not same([row["index"], row["order"]], [index, expected_order]):
                raise ArithmeticError("history policy stream changed")
            detail = decode(blob, context, row)
            policy = unpack_policy(tree, detail["policy"])
            actual_score = score_data(
                context, context.score(policy, tolerance=data.config["tolerance_chips"])
            )
            error = compare(actual_score, {key: row[key] for key in actual_score})
            if error > data.config["tolerance_chips"]:
                raise ArithmeticError("history own score/reply replay changed")
            maximum = max(maximum, error)
            count += 1
            if row["kind"] == "current":
                changes = (
                    movement(tree, previous, policy) if previous is not None else None
                )
                error = compare(changes, row["current_movement"])
                if error > data.config["tolerance_unitless"]:
                    raise ArithmeticError("current unitless movement replay changed")
                unitless = max(unitless, error)
                previous = policy
                if row["work_label"] in boundaries:
                    mass_row = boundaries[row["work_label"]][0]
                    if any(
                        not same(row[k], mass_row[k])
                        for k in (
                            "case",
                            "source_profile_id",
                            "iteration",
                            "total_work",
                            "previous_work",
                            "last_iteration_visits",
                            "state_sha256",
                            "learning_path_sha256",
                        )
                    ):
                        raise ArithmeticError(
                            "raw mass and current state/work bindings differ"
                        )
                if row["work_label"] == data.config["source_target"]:
                    final_variants["current_final"] = row, policy
                continue
            end_row, end = boundaries[data.config["source_target"]]
            if row["kind"] == "whole_average":
                weights = end
                whole_count += 1
                if array_sha(policy) != source.row["receipt"]["policy_sha256"]:
                    raise ArithmeticError("whole source average fingerprint changed")
            else:
                left, right = data.config["suffix_windows"][expected_order - 6]
                begin_row, begin = boundaries[left]
                weights = window_mass(tree, begin, end)
                window = dict(
                    left_label=left,
                    right_label=right,
                    left_iteration=begin_row["iteration"],
                    left_work=begin_row["total_work"],
                    left_state_sha256=begin_row["state_sha256"],
                    left_mass_sha256=begin_row["receipt"]["mass_sha256"],
                    right_mass_sha256=end_row["receipt"]["mass_sha256"],
                    increment_mass_sha256=array_sha(weights),
                )
                if not same(window, row["window"]):
                    raise ArithmeticError("suffix boundary/time/mass binding changed")
                suffix_count += 1
            if tree.normalize(weights).tobytes() != policy.tobytes():
                raise ArithmeticError(
                    "archived cumulative masses do not reconstruct average"
                )
            unitless = max(
                unitless,
                compare_coverage(
                    coverage(tree, weights, river),
                    row["coverage"],
                    data.config["tolerance_unitless"],
                ),
            )
            final_variants[row["variant"]] = row, policy
        opponents = sorted(
            (p for p in data.base.policies if p.group == source.group),
            key=lambda p: order[p.mode],
        )
        if len(opponents) != 4 or set(final_variants) != set(
            data.config["fixed_opponent_own_variants"]
        ):
            raise ArithmeticError(
                "history fixed-opponent source/variant grid incomplete"
            )
        case_matches = {}
        for variant in data.config["fixed_opponent_own_variants"]:
            row, policy = final_variants[variant]
            for opponent in opponents:
                deadline.check()
                for target in (0, 1):
                    response = fixed_match(
                        tree,
                        policy,
                        opponent.policy,
                        data.replies[opponent.identifier, target],
                        data.config["tolerance_chips"],
                    )
                    record = dict(
                        index=index,
                        case=source.case,
                        own_source_profile_id=source.identifier,
                        own_snapshot_id=row["id"],
                        own_variant=variant,
                        own_policy_sha256=row["receipt"]["policy_sha256"],
                        opponent_profile_id=opponent.identifier,
                        opponent_case=opponent.case,
                        opponent_policy_sha256=opponent.row["receipt"]["policy_sha256"],
                        reply_sha256=opponent.row["reply_sha256"][target]["restricted"],
                        **response,
                    )
                    if variant == "whole_average":
                        peer = controls[source.identifier, opponent.identifier, target]
                        error = compare(response, {key: peer[key] for key in response})
                        if error > data.config["tolerance_chips"]:
                            raise ArithmeticError(
                                "whole fixed-opponent control changed"
                            )
                        identity_error = max(identity_error, error)
                    case_matches[variant, opponent.identifier, target] = record
                    matches.append(record)
        for variant in data.config["fixed_opponent_own_variants"]:
            for opponent in opponents:
                for target in (0, 1):
                    own = case_matches[variant, opponent.identifier, target]
                    whole = case_matches["whole_average", opponent.identifier, target]
                    identity_error = max(
                        identity_error,
                        abs(
                            own["restricted_reply_value_chips"]
                            - whole["restricted_reply_value_chips"]
                        ),
                        abs(
                            own["gain_chips"]
                            - whole["gain_chips"]
                            + own["baseline_value_chips"]
                            - whole["baseline_value_chips"]
                        ),
                    )
    if next(stream, None) is not None or next(mass_stream, None) is not None:
        raise ArithmeticError("history archive has extra profile/boundary records")
    if (count, mass_count, suffix_count, whole_count, len(matches)) != (
        512,
        192,
        128,
        64,
        2048,
    ):
        raise ArithmeticError("history replay or fixed-opponent inventory incomplete")
    if identity_error > data.config["tolerance_chips"]:
        raise ArithmeticError("history fixed-opponent gain/EV identity changed")
    deadline.check()
    return dict(
        status="all_averaging_history_profiles_and_windows_replayed",
        source_cases=64,
        profiles=count,
        cumulative_boundaries=mass_count,
        suffix_reconstructions=suffix_count,
        whole_reconstructions=whole_count,
        identical_current_pairs=160,
        fixed_opponent_target_conditions=len(matches),
        maximum_error_chips=maximum,
        maximum_error_unitless=unitless,
        maximum_fixed_identity_error_chips=identity_error,
        seconds=time.perf_counter() - started,
        new_postflop_training_performed=False,
    ), matches
