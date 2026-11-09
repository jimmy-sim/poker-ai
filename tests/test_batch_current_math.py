"""Independent signed EV/gain differences and exact self-zero sanity checks."""

import copy
from typing import Any

import pytest

from poker_ai.evaluation.batch_current_math import paired_fixed


def point(ev: float) -> dict[str, Any]:
    return dict(
        target=0,
        opponent_profile_id="explicit_own_control",
        opponent_policy_sha256="a" * 64,
        reply_sha256="b" * 64,
        path_index=0,
        work_label=10000000,
        baseline_value_chips=ev,
        restricted_reply_value_chips=3.0,
        achieved_reply_value_chips=3.0,
        gain_chips=3.0 - ev,
    )


def test_self_comparison_is_exactly_zero_and_gain_has_opposite_ev_sign() -> None:
    a = point(1.0)
    b = point(2.0)
    assert paired_fixed(a, a) == dict(
        current_minus_average_ev_chips=0.0, current_minus_average_gain_chips=0.0
    )
    assert paired_fixed(a, b) == dict(
        current_minus_average_ev_chips=-1.0, current_minus_average_gain_chips=1.0
    )
    assert paired_fixed(b, a) == dict(
        current_minus_average_ev_chips=1.0, current_minus_average_gain_chips=-1.0
    )
    a["target"] = b["target"] = 1
    assert paired_fixed(a, b)["current_minus_average_ev_chips"] == -1.0


@pytest.mark.parametrize(
    "field",
    [
        "target",
        "opponent_profile_id",
        "opponent_policy_sha256",
        "reply_sha256",
        "path_index",
        "work_label",
    ],
)
def test_different_fixed_opponent_or_target_cannot_be_paired(field: str) -> None:
    a = point(1.0)
    b = point(2.0)
    b[field] = None
    with pytest.raises(ArithmeticError):
        paired_fixed(a, b)


@pytest.mark.parametrize(
    "field",
    [
        "baseline_value_chips",
        "restricted_reply_value_chips",
        "achieved_reply_value_chips",
        "gain_chips",
    ],
)
def test_nonfinite_and_changed_roots_rejected(field: str) -> None:
    a = point(1.0)
    b = point(2.0)
    b[field] = float("nan")
    with pytest.raises(ArithmeticError):
        paired_fixed(a, b)
    a = point(1.0)
    b = point(2.0)
    b["restricted_reply_value_chips"] += 1
    with pytest.raises(ArithmeticError):
        paired_fixed(a, b)


def test_inputs_not_mutated() -> None:
    a, b = point(1.0), point(2.0)
    old = copy.deepcopy((a, b))
    paired_fixed(a, b)
    assert (a, b) == old
