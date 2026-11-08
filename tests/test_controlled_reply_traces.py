"""Compact trace tampering and unit-specific replay checks on an explicit toy."""

import copy
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.controlled_reply_inputs import (
    SourcePolicy,
    config_inputs,
    expected,
    modes,
)
from poker_ai.evaluation.controlled_reply_traces import (
    compare_record,
    make_record,
    validate_record,
)
from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import sha

ROOT = Path(__file__).resolve().parents[1]


def asymmetric() -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, 1, -2, -2, 1, -2, -2]),
        np.array([0, 1, -1, -1, 1, -1, -1]),
        ("player-zero", "player-one-hidden-action"),
        ((0, 1),) * 2,
        np.array([0, 1]),
        np.ones((2, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        np.array([0, 0, 3, -1, 0, -2, 2], dtype=np.float64),
        (np.array([0]), np.array([1, 4])),
    )


def policy(p0: float, p1: float) -> np.ndarray[Any, np.dtype[np.float64]]:
    return np.array([[p0, 1 - p0], [p1, 1 - p1]])


@pytest.fixture
def source() -> tuple[SourcePolicy, ScoringContext]:
    tree = asymmetric()
    saved = policy(0.8, 0.3)
    context = ScoringContext(
        tree, tree, np.arange(2), (np.zeros(2, dtype=np.bool_), np.array([False, True]))
    )
    a, b = saved.copy(), saved.copy()
    a[0], b[1] = (0, 1), (0, 1)
    case = dict(
        spot_file="EXPLICIT_SOFTWARE_FIXTURE",
        representation="exact",
        traversal="full",
        seed=None,
        regret_rule="signed",
        average_weight="linear",
        regret_weight="linear",
        bridge="common",
    )
    row = dict(
        id="toy-source",
        iteration=10,
        total_work=140,
        receipt=dict(
            policy_sha256=hashlib.sha256(
                np.asarray(saved, dtype="<f8").tobytes()
            ).hexdigest()
        ),
        responses=[
            dict(
                baseline_value_chips=0.32,
                restricted_reply_value_chips=0.8,
                within_partition_gain_chips=0.48,
            ),
            dict(
                baseline_value_chips=-0.32,
                restricted_reply_value_chips=0.4,
                within_partition_gain_chips=0.72,
            ),
        ],
        reply_sha256=[
            dict(restricted=sha(pack_policy(tree, a))),
            dict(restricted=sha(pack_policy(tree, b))),
        ],
    )
    saved.flags.writeable = False
    return SourcePolicy(case, row, saved), context


@pytest.mark.parametrize("target", [0, 1])
def test_compact_trace_roundtrip_all_owned_rows_and_source_reply(
    source: tuple[Any, ...], target: int
) -> None:
    original, context = source
    summary, record, reply = make_record(
        original, context, target, ("TURN", "RIVER"), 1e-9
    )
    assert summary["owned_rows"] == 1
    assert summary["gain_chips"] == pytest.approx(0.48 if target == 0 else 0.72)
    restored = validate_record(
        copy.deepcopy(record), original, context, ("TURN", "RIVER"), 1e-9
    )
    assert restored == reply
    assert compare_record(record, copy.deepcopy(record), 1e-9, 1e-12) == 0


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "duplicate",
        "bool_info",
        "reply",
        "q",
        "mass",
        "loss",
        "source",
        "street",
        "root",
        "bool_count",
        "nan",
        "target",
    ],
)
def test_trace_rejects_changed_rows_roots_menus_or_source(
    source: tuple[Any, ...], mode: str
) -> None:
    original, context = source
    _, record, _ = make_record(original, context, 0, ("TURN", "RIVER"), 1e-9)
    row, summary = record["rows"][0], record["summary"]
    if mode == "missing":
        record["rows"].clear()
    elif mode == "duplicate":
        record["rows"].append(copy.deepcopy(row))
    elif mode == "bool_info":
        row[0] = False
    elif mode == "reply":
        row[5] = 0
    elif mode == "q":
        row[4][0] += 1
    elif mode == "mass":
        row[3] = -1.0
    elif mode == "loss":
        row[1] += 1
    elif mode == "source":
        summary["source_policy_sha256"] = "0" * 64
    elif mode == "street":
        summary["street_losses_chips"]["TURN"] += 1
    elif mode == "root":
        summary["restricted_reply_value_chips"] += 1
    elif mode == "bool_count":
        summary["owned_rows"] = True
    elif mode == "nan":
        row[4][0] = float("nan")
    else:
        summary["target"] = False
    with pytest.raises(ArithmeticError):
        validate_record(record, original, context, ("TURN", "RIVER"), 1e-9)


def test_unitless_mass_replay_does_not_inherit_chip_tolerance(
    source: tuple[Any, ...],
) -> None:
    original, context = source
    _, a, _ = make_record(original, context, 0, ("TURN", "RIVER"), 1e-9)
    b = copy.deepcopy(a)
    b["rows"][0][2] += 2e-11
    with pytest.raises(ArithmeticError, match="support"):
        compare_record(a, b, 1e-9, 1e-12)


def test_complete_prespecified_selection_has_all_modes_and_no_seed_replication() -> (
    None
):
    config = config_inputs(ROOT)
    identities = expected(config)
    assert len(identities) == 64
    assert modes(config) == [
        ("signed", "uniform"),
        ("signed", "linear"),
        ("clipped", "uniform"),
        ("clipped", "linear"),
    ]
    assert sum('"seed": null' in item for item in identities) == 16


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_target", 10000000.0),
        ("maximum_own_seconds", True),
        ("expected_source_profiles", 63),
        ("regret_weight", "uniform"),
        ("seeds", [20261301]),
        ("average_weights", ["linear"]),
        ("representations", ["exact"]),
        ("tolerance_unitless", 1e-9),
    ],
)
def test_protocol_does_not_accept_a_smaller_or_changed_study(
    key: str, value: Any
) -> None:
    from poker_ai.evaluation.controlled_reply_inputs import validate_config

    config = copy.deepcopy(config_inputs(ROOT))
    config[key] = value
    with pytest.raises(ArithmeticError):
        validate_config(config)


@pytest.mark.parametrize("key", ["name", "version", "license", "license_sha256"])
def test_reference_pins_are_checked_without_loading_the_optional_solver(
    key: str,
) -> None:
    from poker_ai.evaluation.controlled_reply_inputs import validate_config

    config = copy.deepcopy(config_inputs(ROOT))
    config["native_reference"][key] = "changed"
    with pytest.raises(ArithmeticError):
        validate_config(config)
