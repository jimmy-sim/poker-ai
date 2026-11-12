"""Ownership-only saved mixtures and independently checked gain identities."""

import math
from typing import Any

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.controlled_checkpoints import pack_policy, unpack_policy
from poker_ai.postflop.learning_artifacts import canonical

MIXTURES = ("SS", "SF", "FS", "FF")
METRICS = (
    "value_player_zero_chips",
    "exact_exploitability_chips",
    "within_partition_gain_chips",
    "extra_information_gap_chips",
    "river_only_gain_exact_prefix_chips",
)


def mix(
    context: Context, sampled: FloatArray, full: FloatArray, name: str
) -> FloatArray:
    if name not in MIXTURES:
        raise ValueError("all and only declared SS/SF/FS/FF mixtures")
    tree = context.scoring.partition
    tree.validate_policy(sampled)
    tree.validate_policy(full)
    if np.any((tree.owners != 0) & (tree.owners != 1)):
        raise ValueError("two valid owners required")
    chosen = np.where(
        tree.owners[:, None] == 0,
        sampled if name[0] == "S" else full,
        sampled if name[1] == "S" else full,
    )
    tree.validate_policy(chosen)
    for target in (0, 1):
        expected = sampled if name[target] == "S" else full
        if not np.array_equal(
            chosen[tree.owners == target], expected[tree.owners == target]
        ):
            raise ArithmeticError("mixture changed source row probabilities")
    chosen.flags.writeable = False
    return chosen


def detail(
    context: Context, policy: FloatArray, identity: dict[str, Any]
) -> dict[str, Any]:
    before = policy.tobytes()
    score = context.scoring.score(policy)
    result = dict(
        **identity,
        binding=context.binding,
        policy=pack_policy(context.scoring.partition, policy),
        metrics=score.metrics,
        responses=score.responses,
        maximum_accounting_error_chips=score.maximum_accounting_error,
        replies=[
            {name: pack_policy(context.scoring.exact, p) for name, p in replies.items()}
            for replies in score.replies
        ],
    )
    if before != policy.tobytes():
        raise ArithmeticError("own analysis mutated source policy")
    return result


def replay_detail(
    context: Context, expected: FloatArray, saved: dict[str, Any]
) -> None:
    policy = unpack_policy(context.scoring.partition, saved["policy"])
    if not np.array_equal(policy, expected):
        raise ArithmeticError("saved mixture differs from original source rows")
    identity = {k: saved[k] for k in ("spot_file", "representation", "seed", "mixture")}
    if canonical(saved) != canonical(detail(context, expected, identity)):
        raise ArithmeticError("own reply/scalar/raw-policy replay changed")


def fixed_identities(
    rows: list[dict[str, Any]], tolerance: float = 1e-9
) -> list[dict[str, Any]]:
    if type(tolerance) not in (int, float) or not 0 < tolerance <= 1e-9:
        raise ValueError("fixed numerical tolerance required")
    keys = [
        tuple(r[k] for k in ("spot_file", "representation", "seed", "mixture"))
        for r in rows
    ]
    if len(keys) != len(set(keys)):
        raise ArithmeticError("duplicate fixed-opponent recipe")
    lookup = dict(zip(keys, rows, strict=True))
    groups = {key[:3] for key in keys}
    result = []
    for group in sorted(groups):
        if any((*group, m) not in lookup for m in MIXTURES):
            raise ArithmeticError("incomplete four-way ownership grid")
        for target in (0, 1):
            for opponent in ("S", "F"):
                s = "S" + opponent if target == 0 else opponent + "S"
                f = "F" + opponent if target == 0 else opponent + "F"
                a = lookup[*group, s]["responses"][target]
                b = lookup[*group, f]["responses"][target]
                if a["target"] != target or b["target"] != target:
                    raise ArithmeticError("response target changed")
                gain = b["baseline_value_chips"] - a["baseline_value_chips"]
                errors = [
                    abs(a[k] - b[k])
                    for k in (
                        "exact_reply_value_chips",
                        "restricted_reply_value_chips",
                        "extra_information_gap_chips",
                    )
                ]
                errors.extend(
                    (
                        abs(
                            a["within_partition_gain_chips"]
                            - b["within_partition_gain_chips"]
                            - gain
                        ),
                        abs(
                            (a["exact_reply_value_chips"] - a["baseline_value_chips"])
                            - (b["exact_reply_value_chips"] - b["baseline_value_chips"])
                            - gain
                        ),
                    )
                )
                if any(not math.isfinite(e) or e > tolerance for e in errors):
                    raise ArithmeticError(
                        "fixed opponent roots/information/EV identity failed"
                    )
                result.append(
                    dict(
                        spot_file=group[0],
                        representation=group[1],
                        seed=group[2],
                        target=target,
                        opponent_source=opponent,
                        own_S_to_F_gain_chips=gain,
                        information_gap_chips=a["extra_information_gap_chips"],
                        maximum_error_chips=max(errors),
                    )
                )
    return result


def native_check(
    own: dict[str, Any], native: dict[str, Any], tolerance: float = 1e-9
) -> float:
    """Recompute every reported error/metric from raw native scalars; no solver."""
    if type(tolerance) not in (int, float) or not 0 < tolerance <= 1e-9:
        raise ValueError("fixed numerical tolerance required")
    if set(native) != {"native_metrics", "responses", "maximum_error_chips"}:
        raise ArithmeticError("native schema changed")
    if type(native["maximum_error_chips"]) not in (int, float) or not math.isfinite(
        native["maximum_error_chips"]
    ):
        raise ValueError("numeric native error required")
    responses = native["responses"]
    value = native["native_metrics"]["value_player_zero_chips"]
    if (
        len(responses) != 2
        or any(type(r["target"]) is not int for r in responses)
        or [r["target"] for r in responses] != [0, 1]
    ):
        raise ArithmeticError("both native response targets required")
    fields = (
        "exact_root_chips",
        "restricted_root_chips",
        "achieved_exact_chips",
        "achieved_restricted_chips",
        "achieved_river_before_chips",
    )
    if set(native["native_metrics"]) != set(METRICS) or any(
        set(r) != {"target", *fields} for r in responses
    ):
        raise ArithmeticError("native scalar schema changed")
    if any(
        type(x) not in (int, float) or not math.isfinite(x)
        for x in [value, *[r[k] for r in responses for k in fields]]
    ):
        raise ValueError("finite numeric native scalars required")
    metrics = dict(
        value_player_zero_chips=value,
        exact_exploitability_chips=math.fsum(r["exact_root_chips"] for r in responses)
        / 2,
        within_partition_gain_chips=math.fsum(
            r["restricted_root_chips"] for r in responses
        )
        / 2,
        extra_information_gap_chips=math.fsum(
            r["exact_root_chips"] - r["restricted_root_chips"] for r in responses
        )
        / 2,
        river_only_gain_exact_prefix_chips=math.fsum(
            r["exact_root_chips"] - r["achieved_river_before_chips"] for r in responses
        )
        / 2,
    )
    errors = [abs(metrics[k] - own["metrics"][k]) for k in METRICS]
    names = dict(
        exact_root_chips="exact_reply_value_chips",
        restricted_root_chips="restricted_reply_value_chips",
        achieved_exact_chips="exact_reply_value_chips",
        achieved_restricted_chips="restricted_reply_value_chips",
        achieved_river_before_chips="river_before_value_chips",
    )
    errors.extend(
        abs(row[k] - own["responses"][i][v])
        for i, row in enumerate(responses)
        for k, v in names.items()
    )
    maximum = max(errors)
    if (
        canonical(metrics) != canonical(native["native_metrics"])
        or maximum != native["maximum_error_chips"]
        or maximum > tolerance
        or not math.isfinite(maximum)
    ):
        raise ArithmeticError("native raw-scalar/metric/derived-error agreement failed")
    for row in responses:
        if (
            row["exact_root_chips"] < row["restricted_root_chips"] - tolerance
            or abs(row["exact_root_chips"] - row["achieved_exact_chips"]) > tolerance
            or abs(row["restricted_root_chips"] - row["achieved_restricted_chips"])
            > tolerance
        ):
            raise ArithmeticError("native root/achieved reply ordering mismatch")
    return float(maximum)
