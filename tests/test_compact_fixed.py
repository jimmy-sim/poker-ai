"""Frozen-policy mathematics; unit fixtures never admit a real diagnostic."""

import copy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation import compact_fixed_inputs as inputs
from poker_ai.evaluation import compact_sampled_inputs as old_inputs
from poker_ai.evaluation.compact_fixed_clock import schedule
from poker_ai.evaluation.compact_fixed_software import (
    analytical_fixture as native_fixture,
)
from poker_ai.evaluation.compact_fixed_software import (
    coarse_context as context,
)
from poker_ai.postflop.compact_fixed import (
    MIXTURES,
    detail,
    fixed_identities,
    mix,
    native_check,
    replay_detail,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("target", [0, 1])
def test_all_four_mixtures_preserve_rows_and_fixed_roots(target: int) -> None:
    c = context(target)
    s = np.array([[0.5, 0.5]])
    f = np.array([[0.0, 1.0]])
    before = s.tobytes(), f.tobytes()
    rows = []
    for mode in MIXTURES:
        p = mix(c, s, f, mode)
        for owner in (0, 1):
            expected = s if mode[owner] == "S" else f
            np.testing.assert_array_equal(
                p[c.scoring.partition.owners == owner],
                expected[c.scoring.partition.owners == owner],
            )
        r = detail(
            c,
            p,
            dict(spot_file="fixture", representation="coarse", seed=17, mixture=mode),
        )
        replay_detail(c, p, r)
        rows.append(r)
    conditions = fixed_identities(rows)
    assert len(conditions) == 4
    selected = [r for r in conditions if r["target"] == target]
    assert all(
        r["own_S_to_F_gain_chips"] == 0.25 and r["information_gap_chips"] == 1
        for r in selected
    )
    assert max(r["maximum_error_chips"] for r in conditions) == 0
    assert (s.tobytes(), f.tobytes()) == before


@pytest.mark.parametrize(
    "mutation",
    ["missing", "duplicate", "exact_root", "limited_root", "information", "within"],
)
def test_fixed_opponent_invariants_fail_closed(mutation: str) -> None:
    c = context()
    s = np.array([[0.5, 0.5]])
    f = np.array([[0.0, 1.0]])
    rows = [
        detail(
            c,
            mix(c, s, f, m),
            dict(spot_file="fixture", representation="coarse", seed=17, mixture=m),
        )
        for m in MIXTURES
    ]
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    else:
        key = {
            "exact_root": "exact_reply_value_chips",
            "limited_root": "restricted_reply_value_chips",
            "information": "extra_information_gap_chips",
            "within": "within_partition_gain_chips",
        }[mutation]
        rows[0]["responses"][0][key] += 1
    with pytest.raises(ArithmeticError):
        fixed_identities(rows)


@pytest.mark.parametrize("bad", [True, -1, 1e-8, float("nan")])
def test_fixed_tolerance_cannot_be_relaxed(bad: Any) -> None:
    with pytest.raises(ValueError):
        fixed_identities([], bad)
    with pytest.raises(ValueError):
        native_check({}, {}, bad)


def test_detail_corruption_is_not_replayed() -> None:
    c = context()
    p = np.array([[0.5, 0.5]])
    r = detail(
        c, p, dict(spot_file="fixture", representation="coarse", seed=17, mixture="SS")
    )
    r["metrics"]["extra_information_gap_chips"] += 0.1
    with pytest.raises(ArithmeticError):
        replay_detail(c, p, r)
    with pytest.raises(ValueError):
        mix(c, p, p, "unknown")
    with pytest.raises((ValueError, ArithmeticError)):
        mix(c, np.array([[1.0, 1.0]]), p, "SS")


def test_hand_computed_native_fixture() -> None:
    own, native = native_fixture()
    assert native_check(own, native) == 0
    assert native["native_metrics"]["extra_information_gap_chips"] == 0.5


@pytest.mark.parametrize(
    "mutation",
    ["root", "achieved", "value", "error", "bool", "missing", "extra", "target"],
)
def test_native_fields_are_recomputed(mutation: str) -> None:
    own, native = native_fixture()
    if mutation == "root":
        native["responses"][0]["restricted_root_chips"] += 0.1
    elif mutation == "achieved":
        native["responses"][0]["achieved_exact_chips"] += 0.1
    elif mutation == "value":
        native["native_metrics"]["value_player_zero_chips"] += 1
    elif mutation == "error":
        native["maximum_error_chips"] = 0.1
    elif mutation == "bool":
        native["maximum_error_chips"] = False
    elif mutation == "missing":
        native["responses"].pop()
    elif mutation == "target":
        native["responses"][0]["target"] = 1
    else:
        native["extra"] = 0
    with pytest.raises((ArithmeticError, ValueError)):
        native_check(own, native)


def test_deadline_reserves_all_downstream_caps() -> None:
    now = datetime(2026, 11, 12, 16, 40, tzinfo=UTC)
    schedule("own", "2026-11-12T18:00:00Z", now)
    with pytest.raises(TimeoutError):
        schedule("own", "2026-11-12T18:00:00Z", now + timedelta(seconds=1))
    with pytest.raises(ValueError):
        schedule("own", "2026-11-12T18:00:00", now)


def test_frozen_inventory_and_caps() -> None:
    design = inputs.config(ROOT)
    assert (
        design["source_profiles"] == 48
        and design["logical_profiles"] == 144
        and design["target_conditions"] == 288
    )
    assert len(inputs.expected(ROOT, True)) == len(inputs.expected(ROOT, False)) == 144
    assert design["maximum_own_seconds"] == design["maximum_native_seconds"] == 900


def test_two_player_kuhn_fixed_roots_with_zero_support() -> None:
    c = next(iter(old_inputs.game_contexts(ROOT, "software").values()))
    tree = c.scoring.partition
    s = tree.normalize(tree.legal)
    f = np.zeros_like(s)
    f[:, 0] = 1
    rows = [
        detail(
            c,
            mix(c, s, f, mode),
            dict(
                spot_file=c.spot_file,
                representation=c.representation,
                seed=17,
                mixture=mode,
            ),
        )
        for mode in MIXTURES
    ]
    records = fixed_identities(rows)
    assert len(records) == 4 and max(r["maximum_error_chips"] for r in records) < 1e-12
