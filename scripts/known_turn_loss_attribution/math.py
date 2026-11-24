"""Additive, noncausal decomposition of two saved-policy score differences."""

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray


def rank_rows(values: NDArray[np.float64], indices: list[int]) -> list[int]:
    """Sort descending value, ascending exact row index on ties."""
    if len(indices) != len(set(indices)) or not np.all(np.isfinite(values)):
        raise ArithmeticError("invalid exact-row ranking input")
    return sorted(indices, key=lambda i: (-float(values[i]), i))


def summarize(
    control: NDArray[np.float64],
    candidate: NDArray[np.float64],
    indices: list[int],
    known: list[int],
) -> dict[str, Any]:
    """Partition exact-row change into positive worsening and offset chips.

    This is a numerical decomposition across each arm's own saved opponent
    and optimized reply continuation, not a causal action intervention.
    """
    if (
        control.shape != candidate.shape
        or control.ndim != 1
        or not indices
        or len(indices) != len(set(indices))
        or not set(known) <= set(indices)
        or any(i < 0 or i >= len(control) for i in indices)
        or not np.all(np.isfinite(control))
        or not np.all(np.isfinite(candidate))
        or float(control.min(initial=0)) < -1e-12
        or float(candidate.min(initial=0)) < -1e-12
    ):
        raise ArithmeticError("invalid aligned row contributions")
    delta = candidate - control
    ranked = rank_rows(delta, indices)
    absolute = rank_rows(candidate, indices)
    positive = math.fsum(max(float(delta[i]), 0.0) for i in indices)
    offset = math.fsum(max(-float(delta[i]), 0.0) for i in indices)
    net = math.fsum(float(delta[i]) for i in indices)
    top = ranked[:10]
    top_positive = math.fsum(max(float(delta[i]), 0.0) for i in top)
    known_positive = math.fsum(max(float(delta[i]), 0.0) for i in known)
    return {
        "row_count": len(indices),
        "positive_row_count": sum(bool(delta[i] > 0) for i in indices),
        "negative_row_count": sum(bool(delta[i] < 0) for i in indices),
        "positive_worsening_chips": positive,
        "negative_offset_chips": offset,
        "net_change_chips": net,
        "top_ten_by_delta": top,
        "top_ten_by_candidate_gain": absolute[:10],
        "top_ten_positive_share": None if positive == 0 else top_positive / positive,
        "known_positive_share": None if positive == 0 else known_positive / positive,
        "location": "none"
        if positive == 0
        else "concentrated"
        if top_positive / positive >= 0.5
        else "distributed",
        "known_row_role": "none"
        if positive == 0
        else "dominant"
        if known_positive / positive >= 0.5
        else "nondominant",
    }
