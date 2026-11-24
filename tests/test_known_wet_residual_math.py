"""Fictional residual ranking and published-input guard regressions."""

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_wet_residual.analysis import capture, parent_cases, verify_case  # noqa: E402
from known_wet_residual.gate import contract  # noqa: E402
from known_wet_residual.math import rank_street, street_summary  # noqa: E402
from known_wet_turn_mechanism.plan import CANDIDATE, CONTROL, LABELS, READOUTS  # noqa: E402


def identities() -> list[dict[str, Any]]:
    return [dict(street="TURN" if i < 12 else "RIVER", seat=i % 2) for i in range(24)]


def test_published_saved_policy_grid_and_forecast() -> None:
    plan = contract(ROOT)
    rows = parent_cases(ROOT)
    assert len(rows) == 12
    assert set(rows) == {
        (arm, work, readout)
        for arm in (CONTROL, CANDIDATE)
        for work in LABELS
        for readout in READOUTS
    }
    assert (
        2 * plan["parent_report_wall_seconds"] + 120
        == plan["forecast_bound_seconds"]
        < plan["hard_cap_seconds"]
    )


def test_rank_street_uses_final_gain_then_exact_index() -> None:
    gain = np.asarray([0.05] * 12 + [0.01] * 12, dtype=np.float64)
    gain[2] = 0.5
    gain[14] = 0.2
    turn = rank_street(gain, identities(), "TURN")
    river = rank_street(gain, identities(), "RIVER")
    assert turn == [2, 0, 1, 3, 4, 5, 6, 7, 8, 9]
    assert river == [14, 12, 13, 15, 16, 17, 18, 19, 20, 21]
    assert (
        street_summary(gain, identities(), turn, "TURN")["concentration"]
        == "concentrated"
    )
    assert (
        street_summary(gain, identities(), river, "RIVER")["concentration"]
        == "concentrated"
    )
    with pytest.raises(ArithmeticError, match="selection"):
        street_summary(gain, identities(), turn[:-1] + [turn[0]], "TURN")


def test_reject_bad_gain_and_missing_capture() -> None:
    gain = np.ones(24, dtype=np.float64)
    gain[0] = -0.01
    with pytest.raises(ArithmeticError, match="negative"):
        rank_street(gain, identities(), "TURN")
    gain[0] = float("nan")
    with pytest.raises(ArithmeticError, match="nonfinite"):
        rank_street(gain, identities(), "TURN")
    row = dict(metadata=dict(work_label=100000, readout="linear_average"))
    assert capture(dict(captures=[row]), 100000, "linear_average") is row
    with pytest.raises(ArithmeticError, match="missing"):
        capture(dict(captures=[row]), 1000000, "linear_average")
    with pytest.raises(ArithmeticError, match="duplicate"):
        capture(dict(captures=[row, row]), 100000, "linear_average")


def test_fictional_trace_reconciles_saved_score_and_streets() -> None:
    gain = np.asarray([0.1] * 12 + [0.2] * 12, dtype=np.float64)
    selected = {
        street: rank_street(gain, identities(), street) for street in ("TURN", "RIVER")
    }
    traces = [
        SimpleNamespace(saved_reach_mass=np.ones(24, dtype=np.float64))
        for _ in range(2)
    ]
    score = float(gain.sum())
    detail: dict[str, Any] = dict(contribution=gain, traces=traces)
    published: dict[str, Any] = dict(
        policy_sha256="fictional",
        actual_node_work=100000,
        exploitability_chips=score,
        turn_contribution_chips=1.2,
        river_contribution_chips=2.4,
        whole_coverage=1.0,
        post_initial_river_coverage=1.0,
        worker_peak_rss_bytes=1000,
        whole_path_seconds=1.0,
        native_maximum_error_chips=0.0,
    )
    saved: dict[str, Any] = dict(
        receipt=dict(policy_sha256="fictional"),
        metadata=dict(total_work=100000),
        score=dict(metrics=dict(exact_exploitability_chips=score)),
    )
    checked = verify_case(detail, selected, identities(), published, saved)
    assert checked["positive_saved_prefix_rows"] == {"TURN": 12, "RIVER": 12}
    assert checked["street"]["TURN"]["total_chips"] == pytest.approx(1.2)
    published["river_contribution_chips"] = 2.3
    with pytest.raises(ArithmeticError, match="street gain"):
        verify_case(detail, selected, identities(), published, saved)
