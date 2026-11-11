"""Saved-profile loss accounting and common-opponent crosses; never learn."""

import itertools
import json
import math
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.reply_trace import trace_losses


def verify_trace(
    summary: dict[str, Any],
    detail: dict[str, Any],
    source: dict[str, Any],
    owners: list[int],
    menus: list[int],
    mapping: list[int],
    streets: list[str],
    tolerance: float,
) -> float:
    """Check ALL rows and audited roots, not only the selected display examples.

    Losses use saved prefix reach and optimal own-reply suffixes. They sum to
    unilateral BR gain against this profile's fixed opposite seat. Differences
    across profiles change that opponent; use the separate cross panel for a
    common-opponent target-policy comparison.
    """
    json.dumps((summary, detail), allow_nan=False)
    if not (len(owners) == len(menus) == len(mapping) == len(streets)):
        raise ArithmeticError("complete exact-row descriptions required")
    if any(
        [r["target"] for r in data["responses"]] != [0, 1] for data in (summary, detail)
    ):
        raise ArithmeticError("both ordered responding seats required")
    roots = {
        "exact_exploitability_chips": "exact_exploitability_chips",
        "restricted_exploitability_chips": "within_partition_gain_chips",
        "extra_information_chips": "extra_information_gap_chips",
        "saved_value_player_zero_chips": "value_player_zero_chips",
    }
    errors = [
        abs(float(summary[a]) - float(source["metrics"][b])) for a, b in roots.items()
    ]
    for response, full, prior in zip(
        summary["responses"], detail["responses"], source["responses"], strict=True
    ):
        target = response["target"]
        if type(target) is not int or prior["target"] != target:
            raise ArithmeticError("responding-seat identity changed")
        rows = full["infos"]
        if [r["exact_info"] for r in rows] != [
            i for i, o in enumerate(owners) if o == target
        ]:
            raise ArithmeticError("missing/duplicate/out-of-order owned decision row")
        for row in rows:
            info = row["exact_info"]
            if (
                type(info) is not int
                or row["abstract_info"] != mapping[info]
                or row["loss_chips"] < -tolerance
                or row["counterfactual_mass"] < 0
                or row["saved_reach_mass"] < 0
                or len(row["conditional_values_chips"]) != menus[info]
            ):
                raise ArithmeticError("invalid decision-row identity/support/menu/loss")
        for name, previous in (
            ("baseline_value_chips", "baseline_value_chips"),
            ("exact_reply_value_chips", "exact_reply_value_chips"),
            ("restricted_reply_value_chips", "restricted_reply_value_chips"),
            ("within_partition_gain_chips", "within_partition_gain_chips"),
            ("extra_information_value_chips", "extra_information_gap_chips"),
        ):
            errors.append(abs(float(response[name]) - float(prior[previous])))
        exact_gain = float(response["exact_gain_chips"])
        errors.extend(
            (
                abs(
                    exact_gain
                    - response["exact_reply_value_chips"]
                    + response["baseline_value_chips"]
                ),
                abs(
                    response["within_partition_gain_chips"]
                    - response["restricted_reply_value_chips"]
                    + response["baseline_value_chips"]
                ),
                abs(
                    response["extra_information_value_chips"]
                    - response["exact_reply_value_chips"]
                    + response["restricted_reply_value_chips"]
                ),
                abs(math.fsum(r["loss_chips"] for r in rows) - exact_gain),
                abs(response["loss_sum_chips"] - exact_gain),
                abs(response["accounting_error_chips"]),
            )
        )
        expected_streets = {streets[r["exact_info"]] for r in rows}
        if set(response["street_losses_chips"]) != expected_streets:
            raise ArithmeticError("street inventory changed")
        for street in expected_streets:
            value = math.fsum(
                r["loss_chips"] for r in rows if streets[r["exact_info"]] == street
            )
            errors.append(abs(value - response["street_losses_chips"][street]))
        for group in response["top_groups"]:
            value = math.fsum(
                r["loss_chips"]
                for r in rows
                if r["abstract_info"] == group["abstract_info"]
            )
            errors.append(abs(value - group["loss_contribution_chips"]))
        for field, previous in (
            ("exact_reply_profile", "exact"),
            ("restricted_reply_profile", "restricted"),
        ):
            if sha(full[field]) != source["reply_sha256"][target][previous]:
                raise ArithmeticError("saved own-reply fingerprint changed")
    errors.append(
        abs(
            math.fsum(r["exact_gain_chips"] for r in summary["responses"]) / 2
            - summary["exact_exploitability_chips"]
        )
    )
    maximum = max(float(e) for e in errors)
    if any(not math.isfinite(e) or e > tolerance for e in errors):
        raise ArithmeticError("row/street/group/root accounting changed")
    return maximum


def cross_policies(
    tree: ArrayTree,
    policies: dict[str, FloatArray],
    sources: dict[str, dict[str, Any]],
    identity: dict[str, Any],
    tolerance: float,
) -> list[dict[str, Any]]:
    """All target/opponent combinations at one frozen game/seed coordinate.

    Replies are our own fine-information DP, not imported reference strategies.
    Diagonal unilateral gains need NOT be zero; they reproduce source gains.
    """
    arms = tuple(policies)
    if len(arms) != 4 or set(sources) != set(arms):
        raise ArithmeticError("four complete saved candidate/opponent arms required")
    before = {arm: array_sha(p) for arm, p in policies.items()}
    replies: dict[tuple[str, int], Reply] = {}
    for arm, target in itertools.product(arms, (0, 1)):
        trace = trace_losses(tree, policies[arm], target, tolerance=tolerance)
        owned = np.flatnonzero(tree.owners == target)
        replies[arm, target] = Reply(
            target, trace.value, tuple(int(trace.profile[i].argmax()) for i in owned)
        )
        if (
            sha(pack_policy(tree, trace.profile))
            != sources[arm]["reply_sha256"][target]["exact"]
        ):
            raise ArithmeticError("cross opponent reply differs from audited source")
    rows = []
    for candidate, opponent, target in itertools.product(arms, arms, (0, 1)):
        measured = fixed_match(
            tree,
            policies[candidate],
            policies[opponent],
            replies[opponent, target],
            tolerance,
        )
        row = dict(
            **identity,
            candidate=candidate,
            opponent=opponent,
            target=target,
            candidate_id=sources[candidate]["id"],
            opponent_id=sources[opponent]["id"],
            candidate_fine_policy_sha256=before[candidate],
            opponent_fine_policy_sha256=before[opponent],
            target_ev_chips=measured["baseline_value_chips"],
            best_reply_value_chips=measured["restricted_reply_value_chips"],
            achieved_reply_value_chips=measured["achieved_reply_value_chips"],
            unilateral_gain_chips=measured["gain_chips"],
            independently_audited_diagonal=candidate == opponent,
            independent_new_cross_audit=False,
        )
        if candidate == opponent:
            old = sources[candidate]["responses"][target]
            for key, value in (
                ("target_ev_chips", old["baseline_value_chips"]),
                ("best_reply_value_chips", old["exact_reply_value_chips"]),
                (
                    "unilateral_gain_chips",
                    old["exact_reply_value_chips"] - old["baseline_value_chips"],
                ),
            ):
                if abs(row[key] - value) > tolerance:
                    raise ArithmeticError("cross diagonal differs from audited source")
        rows.append(row)
    validate_cross(rows, arms, tolerance)
    if before != {arm: array_sha(p) for arm, p in policies.items()}:
        raise ArithmeticError("cross analysis mutated a saved policy")
    return rows


def validate_cross(
    rows: list[dict[str, Any]], arms: tuple[str, ...], tolerance: float
) -> None:
    json.dumps(rows, allow_nan=False)
    keys = [(r["candidate"], r["opponent"], r["target"]) for r in rows]
    if (
        len(keys) != 32
        or len(set(keys)) != 32
        or set(keys) != set(itertools.product(arms, arms, (0, 1)))
    ):
        raise ArithmeticError("complete32-condition common-opponent grid required")
    lookup = dict(zip(keys, rows, strict=True))
    for (candidate, opponent, target), row in lookup.items():
        if type(target) is not int:
            raise ArithmeticError("typed cross target required")
        reverse = lookup[opponent, candidate, 1 - target]
        errors = [
            abs(row["target_ev_chips"] + reverse["target_ev_chips"]),
            abs(row["best_reply_value_chips"] - row["achieved_reply_value_chips"]),
            abs(
                row["best_reply_value_chips"]
                - row["target_ev_chips"]
                - row["unilateral_gain_chips"]
            ),
        ]
        for other in arms:
            peer = lookup[other, opponent, target]
            errors.append(
                abs(row["best_reply_value_chips"] - peer["best_reply_value_chips"])
            )
            if (
                row["candidate_fine_policy_sha256"]
                == peer["candidate_fine_policy_sha256"]
            ):
                errors.append(abs(row["target_ev_chips"] - peer["target_ev_chips"]))
        if row["unilateral_gain_chips"] < -tolerance or any(
            e > tolerance for e in errors
        ):
            raise ArithmeticError("common-opponent EV/reply/accounting identity failed")
