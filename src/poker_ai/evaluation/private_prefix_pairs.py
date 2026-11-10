"""Complete paired metrics against unchanged B1 and IID fixed-work baselines."""

import math
from typing import Any

from poker_ai.evaluation.private_prefix_design import READOUTS, Design, index_rows
from poker_ai.postflop.parallel_profile import same

KINDS = ("B1", "IID")
CASE_FIELDS = (
    "spot_file",
    "representation",
    "regret_rule",
    "seed",
    "regret_weight",
    "average_weight",
    "traversal",
    "bridge",
)


def metric_difference(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, float]:
    if (
        set(baseline) != set(candidate)
        or not baseline
        or any(
            type(v) not in (int, float) or not math.isfinite(v)
            for row in (baseline, candidate)
            for v in row.values()
        )
    ):
        raise ArithmeticError("paired scalar metric names/finite units changed")
    result = {k: float(baseline[k] - candidate[k]) for k in sorted(baseline)}
    if any(not math.isfinite(v) for v in result.values()):
        raise ArithmeticError("paired scalar difference overflow")
    return result


def self_pairs(
    design: Design, rows: list[dict[str, Any]], baselines: dict[Any, Any]
) -> list[dict[str, Any]]:
    actual = index_rows(rows, ("path_index", "work_label", "readout"))
    expected = {(i, t, r) for i in range(48) for t in design.labels for r in READOUTS}
    if set(actual) != expected or set(baselines) != {
        (k, *key) for k in KINDS for key in expected
    }:
        raise ArithmeticError("all864 B1/IID self contrasts required")
    result = []
    # A reused B1 endpoint must remain the same saved policy across both B4/B16
    # comparisons, never a separately selected favorable baseline.
    B1: dict[Any, Any] = {}
    for kind in KINDS:
        for key in sorted(expected):
            candidate, baseline = actual[key], baselines[kind, *key]
            index, label, readout = key
            if (
                any(
                    not same(candidate["case"][k], baseline["case"][k])
                    for k in CASE_FIELDS
                )
                or not same(baseline["work_label"], label)
                or baseline["readout"] != readout
                or not same(
                    baseline["batch_size"],
                    1 if kind == "B1" else candidate["batch_size"],
                )
                or type(baseline["total_work"]) is not int
                or baseline["total_work"] < label
                or type(candidate["total_work"]) is not int
                or candidate["total_work"] < label
            ):
                raise ArithmeticError("paired fixed-work baseline coordinate changed")
            if kind == "B1":
                identity = (index % 24, label, readout)
                binding = (
                    baseline["id"],
                    baseline["receipt"]["policy_sha256"],
                    baseline["total_work"],
                    baseline["iteration"],
                )
                if identity in B1 and not same(B1[identity], binding):
                    raise ArithmeticError(
                        "shared B1 baseline changed across batch comparisons"
                    )
                B1[identity] = binding
            result.append(
                dict(
                    baseline_kind=kind,
                    path_index=index,
                    work_label=label,
                    readout=readout,
                    candidate_id=candidate["id"],
                    baseline_id=baseline["id"],
                    candidate_policy_sha256=candidate["receipt"]["policy_sha256"],
                    baseline_policy_sha256=baseline["receipt"]["policy_sha256"],
                    candidate_total_work=candidate["total_work"],
                    baseline_total_work=baseline["total_work"],
                    candidate_iteration=candidate["iteration"],
                    baseline_iteration=baseline["iteration"],
                    baseline_minus_candidate_chips=metric_difference(
                        baseline["metrics"], candidate["metrics"]
                    ),
                )
            )
    return result


def fixed_pairs(
    rows: list[dict[str, Any]], baselines: dict[Any, Any]
) -> list[dict[str, Any]]:
    actual = index_rows(rows, ("own_snapshot_id", "opponent_profile_id", "target"))
    expected = {(kind, *key) for kind in KINDS for key in actual}
    if len(actual) != 1152 or set(baselines) != expected:
        raise ArithmeticError("all2304 fixed B1/IID contrasts required")
    result = []
    for kind in KINDS:
        for key, candidate in sorted(actual.items()):
            baseline = baselines[kind, *key]
            if (
                type(candidate["target"]) is not int
                or candidate["target"] not in (0, 1)
                or any(
                    not same(candidate[k], baseline[k])
                    for k in (
                        "target",
                        "opponent_profile_id",
                        "opponent_policy_sha256",
                        "reply_sha256",
                        "work_label",
                    )
                )
                or any(
                    not same(candidate["case"][k], baseline["case"][k])
                    for k in CASE_FIELDS
                )
            ):
                raise ArithmeticError(
                    "fixed baseline changed opponent/seat/root context"
                )
            fields = (
                "baseline_value_chips",
                "restricted_reply_value_chips",
                "achieved_reply_value_chips",
                "gain_chips",
            )
            differences = metric_difference(
                {k: baseline[k] for k in fields}, {k: candidate[k] for k in fields}
            )
            if (
                abs(differences["restricted_reply_value_chips"]) > 1e-9
                or abs(differences["achieved_reply_value_chips"]) > 1e-9
                or abs(differences["baseline_value_chips"] + differences["gain_chips"])
                > 1e-9
            ):
                raise ArithmeticError(
                    "paired fixed root/achieved EV/gain sign identity failed"
                )
            result.append(
                dict(
                    baseline_kind=kind,
                    candidate_id=key[0],
                    opponent_profile_id=key[1],
                    target=key[2],
                    baseline_id=baseline["own_snapshot_id"],
                    baseline_minus_candidate_ev_chips=differences[
                        "baseline_value_chips"
                    ],
                    baseline_minus_candidate_gain_chips=differences["gain_chips"],
                )
            )
    return result
