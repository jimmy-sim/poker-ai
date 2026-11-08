"""Fixed-profile within-partition accounting with explicit target-chip signs."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.reply_trace import LossTrace, trace_losses


def value(tree: ArrayTree, policy: FloatArray) -> float:
    tree.validate_policy(policy)
    return float(tree.values(tree.edges(policy))[0])


def crossed_policy(
    tree: ArrayTree, first: FloatArray, second: FloatArray
) -> FloatArray:
    """Player zero takes A's rows and player one B's; never assume symmetric roles."""
    tree.validate_policy(first)
    tree.validate_policy(second)
    result = np.where((tree.owners == 0)[:, None], first, second)
    tree.validate_policy(result)
    return result


@dataclass(frozen=True)
class Reply:
    target: int
    root: float
    choices: tuple[int, ...]  # Owned information rows in ascending index order.

    def apply(self, tree: ArrayTree, baseline: FloatArray) -> FloatArray:
        tree.validate_policy(baseline)
        owned = np.flatnonzero(tree.owners == self.target)
        if (
            type(self.target) is not int
            or self.target not in (0, 1)
            or len(owned) != len(self.choices)
        ):
            raise ValueError("reply owner/information inventory changed")
        if any(
            type(a) is not int or not 0 <= a < len(tree.actions[int(i)])
            for i, a in zip(owned, self.choices, strict=True)
        ):
            raise ValueError("reply contains an invalid legal column")
        policy = baseline.copy()
        policy[owned] = 0
        if len(owned):
            policy[owned, np.asarray(self.choices, dtype=np.int64)] = 1
        tree.validate_policy(policy)
        return policy


def require_tolerance(tolerance: float) -> None:
    if (
        type(tolerance) not in (int, float)
        or not math.isfinite(tolerance)
        or not 0 < tolerance <= 1e-9
    ):
        raise ValueError("invalid within-reply chip tolerance")


def trace(
    tree: ArrayTree,
    policy: FloatArray,
    target: int,
    streets: tuple[str, ...],
    tolerance: float,
) -> tuple[LossTrace, Reply, dict[str, Any]]:
    require_tolerance(tolerance)
    if type(target) is not int or target not in (0, 1):
        raise ValueError("target must be seat zero or one")
    if len(streets) != len(tree.keys) or set(streets) - {"TURN", "RIVER"}:
        raise ValueError("trace needs a public turn/river label per information row")
    result = trace_losses(tree, policy, target, tolerance=tolerance)
    owned = np.flatnonzero(tree.owners == target)
    reply = Reply(
        target, result.value, tuple(int(result.profile[i].argmax()) for i in owned)
    )
    if reply.apply(tree, policy).tobytes() != result.profile.tobytes():
        raise ArithmeticError("compact own reply changes its profile")
    street_losses = {
        street: math.fsum(
            float(result.losses[i]) for i in owned if streets[int(i)] == street
        )
        for street in ("TURN", "RIVER")
    }
    error = max(
        result.accounting_error, abs(math.fsum(street_losses.values()) - result.gain)
    )
    if error > tolerance:
        raise ArithmeticError("within street losses do not telescope to root gain")
    return (
        result,
        reply,
        dict(
            target=target,
            baseline_value_chips=(1 if target == 0 else -1) * value(tree, policy),
            restricted_reply_value_chips=result.value,
            gain_chips=result.gain,
            row_loss_sum_chips=math.fsum(float(result.losses[i]) for i in owned),
            street_losses_chips=street_losses,
            accounting_error_chips=error,
            owned_rows=len(owned),
        ),
    )


def cross(
    tree: ArrayTree,
    first: FloatArray,
    second: FloatArray,
    reply_to_second: Reply,
    reply_to_first: Reply,
    *,
    tolerance: float,
) -> dict[str, Any]:
    require_tolerance(tolerance)
    if (reply_to_second.target, reply_to_first.target) != (0, 1):
        raise ValueError("cross requires seat-zero reply to B, seat-one reply to A")
    mixed = crossed_policy(tree, first, second)
    baseline = value(tree, mixed)
    responses = []
    for target, reply in enumerate((reply_to_second, reply_to_first)):
        sign = 1 if target == 0 else -1
        achieved = sign * value(tree, reply.apply(tree, mixed))
        gain = reply.root - sign * baseline
        if (
            not math.isfinite(achieved)
            or not math.isfinite(gain)
            or gain < -tolerance
            or abs(achieved - reply.root) > tolerance
        ):
            raise ArithmeticError("crossed own reply/root ordering changed")
        responses.append(
            dict(
                target=target,
                baseline_value_chips=sign * baseline,
                restricted_reply_value_chips=reply.root,
                achieved_reply_value_chips=achieved,
                gain_chips=gain,
            )
        )
    return dict(
        value_player_zero_chips=baseline,
        responses=responses,
        within_partition_gain_chips=math.fsum(r["gain_chips"] for r in responses) / 2,
    )
