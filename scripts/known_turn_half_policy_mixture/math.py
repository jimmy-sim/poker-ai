"""Pure exact-row arithmetic and frozen strength decision; no saved-policy I/O."""

import math
from typing import Any

import numpy as np

from known_turn_half_policy_mixture.plan import GAMES
from poker_ai.finite import FloatArray


def half_mix(
    control: FloatArray, candidate: FloatArray, legal: FloatArray
) -> FloatArray:
    """Average legal action probabilities per exact row with fixed 50:50 weights."""
    if (
        control.shape != candidate.shape
        or control.shape != legal.shape
        or len(control) != 8340
    ):
        raise ArithmeticError("half-mixture exact row grid changed")
    if not np.all(np.isfinite(control)) or not np.all(np.isfinite(candidate)):
        raise ArithmeticError("nonfinite parent probabilities")
    if np.any(control < 0) or np.any(candidate < 0):
        raise ArithmeticError("negative parent probability")
    if np.any(control[legal == 0] != 0) or np.any(candidate[legal == 0] != 0):
        raise ArithmeticError("parent uses illegal action")
    if np.any(np.abs(control.sum(axis=1) - 1) > 1e-12) or np.any(
        np.abs(candidate.sum(axis=1) - 1) > 1e-12
    ):
        raise ArithmeticError("parent row does not sum to one")
    mixed: FloatArray = 0.5 * control + 0.5 * candidate
    if np.any(np.abs(mixed.sum(axis=1) - 1) > 1e-12):
        raise ArithmeticError("mixed row does not sum to one")
    return mixed


def decision(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the immutable four-game q8-comparator thresholds in initial pots."""
    if len(rows) != 4 or [r["game"] for r in rows] != list(GAMES):
        raise ArithmeticError("four fixed games required")
    values = [r["mixed_fraction_initial_pot"] for r in rows]
    diffs = [r["mixed_minus_control_fraction_initial_pot"] for r in rows]
    if any(not math.isfinite(v) or v < -1e-9 for v in values) or any(
        not math.isfinite(d) for d in diffs
    ):
        raise ArithmeticError("nonfinite/negative exploitability result")
    improving = [i for i, delta in enumerate(diffs) if delta <= -0.001]
    positive = (
        all(value <= 0.01 and value <= 0.025 for value in values)
        and len(improving) >= 3
        and any("dry" in GAMES[i] for i in improving)
        and any("wet" in GAMES[i] for i in improving)
        and all(delta <= 0.001 for delta in diffs)
    )
    negative = any(value > 0.01 or value > 0.025 for value in values) or any(
        delta > 0.001 for delta in diffs
    )
    return {
        "classification": "positive"
        if positive
        else "negative"
        if negative
        else "inconclusive",
        "improved_games": [GAMES[i] for i in improving],
    }
