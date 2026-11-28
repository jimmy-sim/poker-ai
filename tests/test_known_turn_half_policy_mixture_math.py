"""Fictional probability and fixed-decision checks; no saved poker policy read."""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_half_policy_mixture.math import decision, half_mix  # noqa: E402
from known_turn_half_policy_mixture.plan import GAMES  # noqa: E402


def fictional_rows() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build 8,340 entirely fictional two-action exact information rows."""
    legal = np.ones((8340, 2), dtype=np.float64)
    control = np.tile(np.array([0.2, 0.8]), (8340, 1))
    candidate = np.tile(np.array([0.6, 0.4]), (8340, 1))
    return control, candidate, legal


def test_half_mixture_is_exact_rowwise_arithmetic() -> None:
    control, candidate, legal = fictional_rows()
    mixed = half_mix(control, candidate, legal)
    assert np.allclose(mixed[:, 0], 0.4, rtol=0, atol=1e-15)
    assert np.allclose(mixed[:, 1], 0.6, rtol=0, atol=1e-15)
    assert np.allclose(mixed.sum(axis=1), 1, rtol=0, atol=1e-15)


@pytest.mark.parametrize(
    "change", ["nonfinite", "negative", "rowsum", "illegal", "shape"]
)
def test_half_mixture_rejects_invalid_parent(change: str) -> None:
    control, candidate, legal = fictional_rows()
    if change == "nonfinite":
        candidate[4, 0] = np.nan
    elif change == "negative":
        candidate[4] = [-0.1, 1.1]
    elif change == "rowsum":
        candidate[4] = [0.5, 0.4]
    elif change == "illegal":
        legal[4, 0] = 0
    else:
        candidate = candidate[:-1]
    with pytest.raises(ArithmeticError):
        half_mix(control, candidate, legal)


def test_fixed_four_game_decision() -> None:
    rows = [
        {
            "game": game,
            "mixed_fraction_initial_pot": 0.009,
            "mixed_minus_control_fraction_initial_pot": -0.002,
        }
        for game in GAMES
    ]
    assert decision(rows)["classification"] == "positive"
    rows[0]["mixed_fraction_initial_pot"] = 0.01001
    assert decision(rows)["classification"] == "negative"
    rows[0]["mixed_fraction_initial_pot"] = 0.009
    rows[0]["mixed_minus_control_fraction_initial_pot"] = 0
    rows[1]["mixed_minus_control_fraction_initial_pot"] = 0
    assert decision(rows)["classification"] == "inconclusive"
