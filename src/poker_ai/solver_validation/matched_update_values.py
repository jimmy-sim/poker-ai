"""Native fixed-opponent scalars using only saved OWN policies and OWN replies."""

import math
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.finite import FloatArray
from poker_ai.solver_validation.averaging_history import FIXED_FIELDS
from poker_ai.solver_validation.matched_array_reference import ScalarReference

Cache = dict[tuple[str, int], tuple[str, float, float]]


def fixed(
    peer: dict[str, Any],
    candidate: FloatArray,
    opponent: FloatArray,
    own_reply: Reply,
    reference: ScalarReference,
    cache: Cache,
) -> dict[str, Any]:
    tree, target = reference.tree, peer["target"]
    if type(target) is not int or target not in (0, 1) or own_reply.target != target:
        raise ValueError("native fixed target/reply owner changed")
    tree.validate_policy(candidate)
    tree.validate_policy(opponent)
    before = array_sha(candidate), array_sha(opponent)
    if before != (peer["own_policy_sha256"], peer["opponent_policy_sha256"]):
        raise ArithmeticError("native fixed own/opponent policy bits changed")
    mixed = np.where((tree.owners == target)[:, None], candidate, opponent)
    sign = 1 if target == 0 else -1
    baseline = sign * reference.value(mixed)
    reply = own_reply.apply(tree, mixed)
    fingerprint = array_sha(reply)
    if fingerprint != peer["reply_sha256"]:
        raise ArithmeticError("native fixed OWN reply differs from source")
    key = peer["opponent_profile_id"], target
    if key not in cache:
        cache[key] = (
            fingerprint,
            reference.response_value(mixed, target),
            sign * reference.value(reply),
        )
    elif cache[key][0] != fingerprint:
        raise ArithmeticError("native fixed cache changed opponent/reply context")
    _, root, achieved = cache[key]
    result = dict(
        **{k: peer[k] for k in FIXED_FIELDS},
        baseline_value_chips=baseline,
        restricted_reply_value_chips=root,
        achieved_reply_value_chips=achieved,
        gain_chips=root - baseline,
    )
    errors = [
        abs(result[k] - peer[k])
        for k in (
            "baseline_value_chips",
            "restricted_reply_value_chips",
            "achieved_reply_value_chips",
            "gain_chips",
        )
    ]
    if any(not math.isfinite(e) for e in errors) or before != (
        array_sha(candidate),
        array_sha(opponent),
    ):
        raise ArithmeticError("nonfinite/mutated native fixed comparison")
    return dict(**result, maximum_error_chips=max(errors))
