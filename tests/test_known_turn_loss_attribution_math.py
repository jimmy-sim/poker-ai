"""Fictional additive attribution, ranking and decision assumptions."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_loss_attribution.analysis import observe, saved_capture  # noqa: E402
from known_turn_loss_attribution.math import rank_rows, summarize  # noqa: E402


def test_signed_mass_ties_and_fixed_known_rows() -> None:
    control = np.array(
        [0.25, 0.125, 0.375, 0, 0.5, 0.125, 0, 0.25, 0.125, 0, 0.25], dtype=float
    )
    candidate = np.array(
        [0.5, 0, 0.25, 0, 0.625, 0.125, 0, 0.125, 0.25, 0, 0.125], dtype=float
    )
    result = summarize(control, candidate, list(range(11)), [0, 1])
    assert result["top_ten_by_delta"][0] == 0
    assert result["top_ten_by_delta"][1:3] == [4, 8]
    assert result["positive_worsening_chips"] == pytest.approx(0.5)
    assert result["negative_offset_chips"] == pytest.approx(0.5)
    assert result["net_change_chips"] == pytest.approx(0)
    assert result["top_ten_positive_share"] == pytest.approx(1)
    assert result["known_positive_share"] == pytest.approx(0.5)
    assert result["location"] == "concentrated"
    assert result["known_row_role"] == "dominant"
    assert result["positive_row_count"] == 3
    assert result["negative_row_count"] == 4
    json.dumps(result, allow_nan=False)


def test_distributed_and_zero_positive_mass() -> None:
    control = np.zeros(24, dtype=float)
    candidate = np.ones(24, dtype=float)
    result = summarize(control, candidate, list(range(24)), [0])
    assert result["top_ten_by_delta"] == list(range(10))
    assert result["location"] == "distributed"
    assert result["known_row_role"] == "nondominant"
    assert result["top_ten_positive_share"] == pytest.approx(10 / 24)
    none = summarize(candidate, control, list(range(24)), [0])
    assert none["location"] == none["known_row_role"] == "none"
    assert none["positive_worsening_chips"] == 0
    assert none["negative_offset_chips"] == 24


def test_reject_unaligned_or_invalid_contributions() -> None:
    good = np.zeros(12, dtype=float)
    with pytest.raises(ArithmeticError, match="aligned"):
        summarize(good, good[:-1], list(range(11)), [0])
    with pytest.raises(ArithmeticError, match="aligned"):
        summarize(good, good, [0, 0], [0])
    with pytest.raises(ArithmeticError, match="aligned"):
        summarize(good, good, [0, 1], [2])
    bad = good.copy()
    bad[0] = float("nan")
    with pytest.raises(ArithmeticError, match="aligned"):
        summarize(good, bad, [0, 1], [0])
    with pytest.raises(ArithmeticError, match="ranking"):
        rank_rows(bad, [0, 1])


def test_fictional_saved_observation_and_capture() -> None:
    row = {"metadata": {"work_label": 10_000_000, "readout": "linear_average"}}
    assert saved_capture({"captures": [row]}) is row
    with pytest.raises(ArithmeticError, match="missing"):
        saved_capture({"captures": []})
    with pytest.raises(ArithmeticError, match="duplicate"):
        saved_capture({"captures": [row, row]})
    detail = {
        "expanded": np.array([[0.25, 0.75]]),
        "traces": [
            SimpleNamespace(
                counterfactual_mass=np.array([0.2]),
                saved_reach_mass=np.array([0.1]),
                conditional_values=np.array([[-2.0, 4.0]]),
                losses=np.array([0.6]),
            )
        ],
    }
    got = observe(
        detail, {"exact_info": 0, "seat": 0, "legal_actions": ["fold", "call"]}
    )
    assert got["saved_probabilities"] == [0.25, 0.75]
    assert got["counterfactual_reach"] == 0.2
    assert got["saved_prefix_reach"] == 0.1
    assert got["alternative_action_values_chips"] == [-2.0, 4.0]
    assert got["additive_contribution_chips"] == 0.3
