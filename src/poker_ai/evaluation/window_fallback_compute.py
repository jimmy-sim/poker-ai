"""Score every declared own fallback fill; never update a learner."""

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.controlled_reply_inputs import modes
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs, Window
from poker_ai.evaluation.window_fallback_math import (
    LABELS,
    MASKS,
    fill_rows,
    full_equivalence,
    panel_identity,
)
from poker_ai.finite import FloatArray
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def mask_sha(mask: Any) -> str:
    return hashlib.sha256(np.asarray(mask, dtype=np.uint8).tobytes()).hexdigest()


@dataclass(frozen=True)
class Evaluation:
    metadata: dict[str, Any]
    policy: FloatArray


def evaluate_window(
    window: Window,
    config: dict[str, Any],
    binding: str,
    deadline: Deadline,
) -> tuple[list[Evaluation], dict[str, Any]]:
    """Four own profiles form one complete seat-fill panel, including no-ops."""
    context, tree = window.context, window.context.partition
    results = []
    scores = {}
    full_error = 0.0
    control_error = 0.0
    for order, (label, targets) in enumerate(zip(LABELS, MASKS, strict=True)):
        deadline.check()
        filled = fill_rows(
            tree,
            window.policy,
            window.mass,
            window.source.policy,
            targets,
            window.river,
        )
        scored = score_data(
            context, context.score(filled.policy, tolerance=config["tolerance_chips"])
        )
        scores[label] = scored
        if order == 0:
            control_error = compare(scored, {k: window.row[k] for k in scored})
            if (
                control_error > config["tolerance_chips"]
                or array_sha(filled.policy) != window.row["receipt"]["policy_sha256"]
            ):
                raise ArithmeticError("raw window control changed its own policy/score")
        if window.source.case["traversal"] == "full":
            full_error = max(
                full_error,
                full_equivalence(
                    filled,
                    scores["raw"],
                    scored,
                    config["tolerance_chips"],
                    config["tolerance_unitless"],
                ),
            )
        metadata = dict(
            id=f"window-{window.index:03d}-{label}",
            index=window.index,
            order=order,
            case=window.source.case,
            source_case_index=window.index // 2,
            source_profile_id=window.source.identifier,
            source_window_id=window.row["id"],
            window_variant=window.row["variant"],
            source_window_policy_sha256=window.row["receipt"]["policy_sha256"],
            whole_policy_sha256=array_sha(window.source.policy),
            window_mass_sha256=array_sha(window.mass),
            window_definition=window.row["window"],
            upstream_iteration=window.row["iteration"],
            upstream_work=window.row["total_work"],
            source_sha256=binding,
            fill_label=label,
            fill_targets=list(targets),
            eligible_sha256=mask_sha(filled.eligible),
            changed_sha256=mask_sha(filled.changed),
            support=filled.support,
            maximum_realization_change=filled.maximum_realization_change,
            **scored,
        )
        results.append(Evaluation(metadata, filled.policy))
    panel = dict(
        index=window.index,
        case=window.source.case,
        source_profile_id=window.source.identifier,
        source_window_id=window.row["id"],
        window_variant=window.row["variant"],
        raw_control_error_chips=control_error,
        full_control_error_chips=full_error
        if window.source.case["traversal"] == "full"
        else None,
        maximum_realization_change=max(
            r.metadata["maximum_realization_change"] for r in results
        ),
        **panel_identity(scores, config["tolerance_chips"]),
    )
    return results, panel


def fixed_targets(
    window: Window,
    results: list[Evaluation],
    data: FallbackInputs,
    deadline: Deadline,
) -> tuple[list[dict[str, Any]], float]:
    """Keep all old whole-average opponents fixed; fill only our responding rows."""
    if len(results) != 4 or [r.metadata["fill_label"] for r in results] != list(LABELS):
        raise ArithmeticError("incomplete window fill profiles for fixed matches")
    tree = window.context.partition
    mode_order = {mode: i for i, mode in enumerate(modes(data.config))}
    opponents = sorted(
        (p for p in data.history.base.policies if p.group == window.source.group),
        key=lambda p: mode_order[p.mode],
    )
    if len(opponents) != 4:
        raise ArithmeticError("window fixed-opponent source grid incomplete")
    baseline = {}
    controls = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in data.saved["fixed_matches"]
    }
    matches = []
    maximum = 0.0
    for evaluation in (results[0], results[3]):
        row, policy = evaluation.metadata, evaluation.policy
        for opponent in opponents:
            deadline.check()
            for target in (0, 1):
                # Target-row replacement makes a both-fill identical to target-only.
                if row["fill_label"] == "fill_both":
                    only = results[target + 1].policy
                    if (
                        policy[tree.owners == target].tobytes()
                        != only[tree.owners == target].tobytes()
                    ):
                        raise ArithmeticError(
                            "fixed target fill differs from target-only rows"
                        )
                response = fixed_match(
                    tree,
                    policy,
                    opponent.policy,
                    data.history.replies[opponent.identifier, target],
                    data.config["tolerance_chips"],
                )
                key = opponent.identifier, target
                if row["fill_label"] == "raw":
                    peer = controls[window.row["id"], opponent.identifier, target]
                    control_error = compare(response, {k: peer[k] for k in response})
                    if control_error > data.config["tolerance_chips"]:
                        raise ArithmeticError(
                            "raw window fixed-opponent control changed"
                        )
                    maximum = max(maximum, control_error)
                    baseline[key] = response
                raw = baseline[key]
                delta_gain = response["gain_chips"] - raw["gain_chips"]
                delta_ev = (
                    response["baseline_value_chips"] - raw["baseline_value_chips"]
                )
                error = max(
                    abs(delta_gain + delta_ev),
                    abs(
                        response["restricted_reply_value_chips"]
                        - raw["restricted_reply_value_chips"]
                    ),
                )
                if window.source.case["traversal"] == "full":
                    error = max(error, abs(delta_gain), abs(delta_ev))
                if error > data.config["tolerance_chips"]:
                    raise ArithmeticError(
                        "window fixed-root/EV/full-control identity failed"
                    )
                maximum = max(maximum, error)
                matches.append(
                    dict(
                        index=window.index,
                        case=window.source.case,
                        source_window_id=window.row["id"],
                        window_variant=window.row["variant"],
                        fill_label=row["fill_label"],
                        own_snapshot_id=row["id"],
                        own_source_profile_id=window.source.identifier,
                        own_variant=window.row["variant"] + "/" + row["fill_label"],
                        own_policy_sha256=array_sha(policy),
                        opponent_profile_id=opponent.identifier,
                        opponent_case=opponent.case,
                        opponent_policy_sha256=array_sha(opponent.policy),
                        reply_sha256=opponent.row["reply_sha256"][target]["restricted"],
                        gain_difference_chips=delta_gain,
                        ev_difference_chips=delta_ev,
                        **response,
                    )
                )
    return matches, maximum
