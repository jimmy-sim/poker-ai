"""Fixed OWN opponents and exact seat signs; no learned/reference strategy edits."""

from typing import Any

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.batch_current_inputs import Sources
from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.finite import FloatArray
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same

VALUES = (
    "baseline_value_chips",
    "restricted_reply_value_chips",
    "achieved_reply_value_chips",
    "gain_chips",
)


def matches(
    sources: Sources, row: dict[str, Any], policy: FloatArray, binding: str
) -> list[dict[str, Any]]:
    case = row["case"]
    context = sources.data.base.context(case)
    tree = context.partition
    before = array_sha(policy)
    if before != row["receipt"]["policy_sha256"]:
        raise ArithmeticError("candidate differs from bound source policy")
    opponents = [
        p
        for p in full_sources(sources.data)
        if all(p.case[k] == case[k] for k in ("spot_file", "representation"))
    ]
    if len(opponents) != 4:
        raise ArithmeticError("exact four original full controls required")
    result = []
    for opponent in opponents:
        fingerprint = array_sha(opponent.policy)
        if fingerprint != opponent.row["receipt"]["policy_sha256"]:
            raise ArithmeticError("original full opponent changed")
        for target in (0, 1):
            reply = sources.data.replies[opponent.identifier, target]
            record = fixed_match(tree, policy, opponent.policy, reply)
            result.append(
                dict(
                    **record,
                    path_index=row["path_index"],
                    case=case,
                    batch_size=row["batch_size"],
                    work_label=row["work_label"],
                    own_snapshot_id=row["id"],
                    own_source_profile_id=row.get("source_current_id", row["id"]),
                    own_variant=row.get("variant", case["average_weight"] + "_average"),
                    opponent_profile_id=opponent.identifier,
                    own_policy_sha256=before,
                    opponent_policy_sha256=fingerprint,
                    reply_sha256=array_sha(reply.apply(tree, opponent.policy)),
                    source_sha256=binding,
                )
            )
        if array_sha(opponent.policy) != fingerprint:
            raise ArithmeticError("diagnosis mutated original opponent")
    if array_sha(policy) != before:
        raise ArithmeticError("diagnosis mutated saved candidate")
    return result


def paired_fixed(current: dict[str, Any], average: dict[str, Any]) -> dict[str, float]:
    """Positive gain gap means CURRENT loses more to the same own best response."""
    for k in (
        "target",
        "opponent_profile_id",
        "opponent_policy_sha256",
        "reply_sha256",
        "path_index",
        "work_label",
    ):
        if not same(current[k], average[k]):
            raise ArithmeticError("paired fixed comparison changes opponent or target")
    if any(not number(r[k]) for r in (current, average) for k in VALUES):
        raise ArithmeticError("nonfinite paired fixed values")
    if (
        abs(
            current["restricted_reply_value_chips"]
            - average["restricted_reply_value_chips"]
        )
        > 1e-9
    ):
        raise ArithmeticError("fixed opponent reply root changed")
    ev = current["baseline_value_chips"] - average["baseline_value_chips"]
    gain = current["gain_chips"] - average["gain_chips"]
    if abs(ev + gain) > 1e-9:
        raise ArithmeticError("unilateral EV/gain sign identity failed")
    return dict(
        current_minus_average_ev_chips=ev, current_minus_average_gain_chips=gain
    )
