"""Compact all-owned-row traces, bound to previously audited own policies."""

import math
from typing import Any

import numpy as np

from poker_ai.evaluation import controlled_reply_math as math_reply
from poker_ai.evaluation.controlled_reply_inputs import SourcePolicy
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.policy_swaps import street_mask

COLUMNS = (
    "info",
    "loss_chips",
    "counterfactual_mass",
    "saved_reach_mass",
    "conditional_values_chips",
    "reply_column",
)


def public_streets(context: ScoringContext) -> tuple[str, ...]:
    if not isinstance(context.exact, MatrixTree) or not isinstance(
        context.partition, MatrixTree
    ):
        raise ValueError("public poker street labels require matrix sources")
    turn = street_mask(context.exact, context.partition)
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    return tuple("TURN" if turn[i] else "RIVER" for i in first)


def partition_sha(context: ScoringContext) -> str:
    tree = context.partition
    return sha(
        dict(
            keys=list(tree.keys),
            owners=tree.owners.tolist(),
            actions=[list(a) for a in tree.actions],
        )
    )


def make_record(
    source: SourcePolicy,
    context: ScoringContext,
    target: int,
    streets: tuple[str, ...],
    tolerance: float,
) -> tuple[dict[str, Any], dict[str, Any], math_reply.Reply]:
    tree = context.partition
    result, reply, summary = math_reply.trace(
        tree, source.policy, target, streets, tolerance
    )
    previous = source.row["responses"][target]
    if (
        max(
            abs(summary["baseline_value_chips"] - previous["baseline_value_chips"]),
            abs(reply.root - previous["restricted_reply_value_chips"]),
            abs(result.gain - previous["within_partition_gain_chips"]),
        )
        > tolerance
    ):
        raise ArithmeticError("restricted trace disagrees with audited source roots")
    reply_hash = sha(pack_policy(context.exact, context.expand(result.profile)))
    if reply_hash != source.row["reply_sha256"][target]["restricted"]:
        raise ArithmeticError("restricted own reply fingerprint differs from source")
    summary.update(
        profile_id=source.identifier,
        case=source.case,
        source_snapshot_id=source.row["id"],
        source_policy_sha256=source.row["receipt"]["policy_sha256"],
        partition_sha256=partition_sha(context),
        reply_sha256=reply_hash,
        source_iteration=source.row["iteration"],
        source_work=source.row["total_work"],
    )
    owned = np.flatnonzero(tree.owners == target)
    rows = [
        [
            int(i),
            float(result.losses[i]),
            float(result.counterfactual_mass[i]),
            float(result.saved_reach_mass[i]),
            result.conditional_values[i, : len(tree.actions[int(i)])].tolist(),
            choice,
        ]
        for i, choice in zip(owned, reply.choices, strict=True)
    ]
    record = dict(summary=summary, rows=rows)
    validate_record(record, source, context, streets, tolerance)
    return summary, record, reply


def validate_record(
    record: dict[str, Any],
    source: SourcePolicy,
    context: ScoringContext,
    streets: tuple[str, ...],
    tolerance: float,
) -> math_reply.Reply:
    math_reply.require_tolerance(tolerance)
    if set(record) != {"summary", "rows"}:
        raise ArithmeticError("within trace envelope changed")
    summary, rows, tree = record["summary"], record["rows"], context.partition
    target = summary["target"]
    if type(target) is not int or target not in (0, 1):
        raise ArithmeticError("within trace target changed")
    fixed = dict(
        profile_id=source.identifier,
        case=source.case,
        source_snapshot_id=source.row["id"],
        source_policy_sha256=source.row["receipt"]["policy_sha256"],
        partition_sha256=partition_sha(context),
        reply_sha256=source.row["reply_sha256"][target]["restricted"],
        source_iteration=source.row["iteration"],
        source_work=source.row["total_work"],
    )
    if any(not same(summary[k], value) for k, value in fixed.items()):
        raise ArithmeticError("within trace source/menus/identity changed")
    owned = [int(i) for i in np.flatnonzero(tree.owners == target)]
    if (
        not isinstance(rows, list)
        or type(summary["owned_rows"]) is not int
        or summary["owned_rows"] != len(owned)
        or len(rows) != len(owned)
    ):
        raise ArithmeticError("within trace row inventory changed")
    previous = source.row["responses"][target]
    expected = dict(
        baseline_value_chips=previous["baseline_value_chips"],
        restricted_reply_value_chips=previous["restricted_reply_value_chips"],
        gain_chips=previous["within_partition_gain_chips"],
    )
    if any(
        not number(summary[k]) or abs(summary[k] - v) > tolerance
        for k, v in expected.items()
    ):
        raise ArithmeticError("within trace root values changed")
    choices, losses = [], []
    totals: dict[str, list[float]] = {street: [] for street in ("TURN", "RIVER")}
    for info, row in zip(owned, rows, strict=True):
        if (
            not isinstance(row, list)
            or len(row) != len(COLUMNS)
            or type(row[0]) is not int
            or row[0] != info
        ):
            raise ArithmeticError("within trace owned row order/identity changed")
        _, loss, cf, reach, q, choice = row
        if (
            not number(loss)
            or loss < -tolerance
            or not number(cf, nonnegative=True)
            or not number(reach, nonnegative=True)
            or not isinstance(q, list)
            or len(q) != len(tree.actions[info])
            or any(not number(v) for v in q)
            or type(choice) is not int
            or not 0 <= choice < len(q)
        ):
            raise ArithmeticError("invalid within trace numbers/actions")
        local = max(q) - math.fsum(
            float(p) * v for p, v in zip(source.policy[info, : len(q)], q, strict=True)
        )
        if abs(loss - reach * local) > tolerance:
            raise ArithmeticError("within trace local loss identity changed")
        choices.append(choice)
        losses.append(loss)
        totals[streets[info]].append(loss)
    actual = math.fsum(losses)
    if (
        not number(summary["row_loss_sum_chips"])
        or abs(actual - summary["row_loss_sum_chips"]) > tolerance
        or abs(actual - summary["gain_chips"]) > tolerance
        or set(summary["street_losses_chips"]) != {"TURN", "RIVER"}
        or any(
            not number(summary["street_losses_chips"][street])
            or abs(math.fsum(values) - summary["street_losses_chips"][street])
            > tolerance
            for street, values in totals.items()
        )
        or not number(summary["accounting_error_chips"], nonnegative=True)
        or summary["accounting_error_chips"] > tolerance
    ):
        raise ArithmeticError("within trace row/street/root accounting changed")
    reply = math_reply.Reply(
        target, summary["restricted_reply_value_chips"], tuple(choices)
    )
    restored = reply.apply(tree, source.policy)
    if (
        sha(pack_policy(context.exact, context.expand(restored)))
        != summary["reply_sha256"]
    ):
        raise ArithmeticError("compact own reply does not restore source fingerprint")
    return reply


def compare_record(
    actual: dict[str, Any], saved: dict[str, Any], chip: float, unitless: float
) -> float:
    """Compare full records; mass/support tolerances never inherit chip units."""
    from poker_ai.postflop.range_reply import compare

    maximum = compare(actual["summary"], saved["summary"])
    if maximum > chip or len(actual["rows"]) != len(saved["rows"]):
        raise ArithmeticError("within trace summary/count replay changed")
    for a, b in zip(actual["rows"], saved["rows"], strict=True):
        if not same([a[0], a[5]], [b[0], b[5]]):
            raise ArithmeticError("within trace replay info/reply changed")
        error = max(compare(a[1], b[1]), compare(a[4], b[4]))
        if error > chip or compare([a[2], a[3]], [b[2], b[3]]) > unitless:
            raise ArithmeticError("within trace values/support replay changed")
        maximum = max(maximum, error)
    return maximum
