"""Reconstruct every intervention from original OWN windows, then rescore it."""

import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.window_fallback_compute import evaluate_window, fixed_targets
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs, windows
from poker_ai.evaluation.window_fallback_validation import grid
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline

SCORE_FIELDS = ("metrics", "responses", "reply_sha256", "maximum_accounting_error")
UNIT_FIELDS = {
    "eligible_uniform_reach_fraction",
    "maximum_own_reach_at_eligible_histories",
    "eligible_river_uniform_reach_fraction",
    "maximum_own_reach_at_eligible_river_histories",
}


def compare_support(
    actual: list[dict[str, Any]], saved: list[dict[str, Any]], tolerance: float
) -> float:
    if len(actual) != 2 or len(saved) != 2:
        raise ArithmeticError("fallback replay support inventory changed")
    maximum = 0.0
    for a, b in zip(actual, saved, strict=True):
        if set(a) != set(b) or any(
            not same(a[k], b[k]) for k in a.keys() - UNIT_FIELDS
        ):
            raise ArithmeticError("fallback support counts/targets changed")
        for k in UNIT_FIELDS:
            if a[k] is None:
                if b[k] is not None:
                    raise ArithmeticError("fallback empty reach changed")
            elif not number(b[k]) or abs(a[k] - b[k]) > tolerance:
                raise ArithmeticError("fallback support unitless replay failed")
            else:
                maximum = max(maximum, abs(a[k] - b[k]))
    return float(maximum)


def replay_archives(
    data: FallbackInputs, path: Path, saved: dict[str, Any], deadline: Deadline
) -> dict[str, Any]:
    started = time.perf_counter()
    grid(saved, data)
    stream = read_archive(
        archive_path(path, saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    )
    maximum = unitless = full_error = full_realization = 0.0
    count = full_count = 0
    fixed = []
    for window in windows(data, deadline):
        deadline.check()
        expected, panel = evaluate_window(
            window, data.config, saved["source_sha256"], deadline
        )
        for evaluation in expected:
            row, blob = next(stream)
            detail = decode(blob, window.context, row)
            policy = unpack_policy(window.context.partition, detail["policy"])
            if policy.tobytes() != evaluation.policy.tobytes():
                raise ArithmeticError(
                    "fallback policy does not reconstruct from its exact mask"
                )
            metadata = evaluation.metadata
            if any(
                not same(row[k], metadata[k])
                for k in metadata.keys()
                - set(SCORE_FIELDS)
                - {"support", "maximum_realization_change"}
            ):
                raise ArithmeticError(
                    "fallback mask/source/unchanged-row metadata changed"
                )
            error = compare(
                {k: metadata[k] for k in SCORE_FIELDS},
                {k: row[k] for k in SCORE_FIELDS},
            )
            if error > data.config["tolerance_chips"]:
                raise ArithmeticError("fallback own score/reply replay failed")
            maximum = max(maximum, error)
            unitless = max(
                unitless,
                compare_support(
                    metadata["support"],
                    row["support"],
                    data.config["tolerance_unitless"],
                ),
            )
            change = abs(
                metadata["maximum_realization_change"]
                - row["maximum_realization_change"]
            )
            if change > data.config["tolerance_unitless"]:
                raise ArithmeticError("fallback realization unitless replay failed")
            unitless = max(unitless, change)
        peer = saved["panels"][window.index]
        if any(
            not same(panel[k], peer[k])
            for k in (
                "index",
                "case",
                "source_profile_id",
                "source_window_id",
                "window_variant",
            )
        ):
            raise ArithmeticError("fallback panel identity changed")
        error = compare(
            {k: v for k, v in panel.items() if k != "maximum_realization_change"},
            {k: v for k, v in peer.items() if k != "maximum_realization_change"},
        )
        if error > data.config["tolerance_chips"]:
            raise ArithmeticError("fallback panel/control accounting replay failed")
        maximum = max(maximum, error)
        change = abs(
            panel["maximum_realization_change"] - peer["maximum_realization_change"]
        )
        if change > data.config["tolerance_unitless"]:
            raise ArithmeticError("fallback panel unitless replay failed")
        unitless = max(unitless, change)
        matches, identity_error = fixed_targets(window, expected, data, deadline)
        fixed.extend(matches)
        maximum = max(maximum, identity_error)
        count += 1
        if window.source.case["traversal"] == "full":
            full_count += 1
            full_error = max(full_error, panel["full_control_error_chips"])
            full_realization = max(
                full_realization, panel["maximum_realization_change"]
            )
    if next(stream, None) is not None or count != 128 or full_count != 32:
        raise ArithmeticError("fallback replay profile/window inventory changed")
    error = compare(fixed, saved["fixed_matches"])
    if error > data.config["tolerance_chips"]:
        raise ArithmeticError("fallback fixed-target replay failed")
    maximum = max(maximum, error)
    deadline.check()
    return dict(
        status="all_window_fallback_profiles_and_targets_replayed",
        new_postflop_training_performed=False,
        source_windows=count,
        profiles=512,
        raw_window_controls=count,
        full_windows=full_count,
        additivity_panels=count,
        fixed_target_conditions=len(fixed),
        maximum_error_chips=maximum,
        maximum_error_unitless=unitless,
        maximum_full_control_error_chips=full_error,
        maximum_full_realization_change=full_realization,
        seconds=time.perf_counter() - started,
    )
