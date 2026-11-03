"""Reach-weighted comparison metrics; no strategy generation or training inputs."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from poker_ai.toy.tree import FloatArray


def normalized_weights(weights: FloatArray, count: int) -> FloatArray:
    if (
        weights.shape != (count,)
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
        or not float(weights.sum()) > 0
    ):
        raise ValueError("reach weights need finite nonnegative positive total mass")
    return np.asarray(weights / weights.sum(), dtype=np.float64)


def validate_probabilities(probabilities: FloatArray, legal: NDArray[np.bool_]) -> None:
    if (
        probabilities.ndim != 2
        or probabilities.shape != legal.shape
        or legal.dtype != np.bool_
        or np.any(legal.sum(axis=1) == 0)
        or not np.all(np.isfinite(probabilities))
        or np.any(probabilities < 0)
        or np.any(probabilities[~legal] != 0)
        or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-12, rtol=0)
    ):
        raise ValueError("normalized legal action probabilities required")


def action_frequency_gap(
    first: FloatArray, second: FloatArray, reach: FloatArray, legal: NDArray[np.bool_]
) -> float:
    """Mean action-probability absolute difference, weighted by declared reach.

    Divide each node's L1 by its OWN legal action count, excluding padded columns;
    then average node MAEs with normalized reach weights. Units are probability
    points (multiply by 100 for percentage points), not L1 or total variation.
    Zero-reach groups are undefined and rejected, rather than labeled zero gap.
    """
    validate_probabilities(first, legal)
    validate_probabilities(second, legal)
    weights = normalized_weights(reach, len(first))
    per_node = np.abs(first - second).sum(axis=1) / legal.sum(axis=1)
    return float(weights @ per_node)


def range_frequencies(
    probabilities: FloatArray, reach: FloatArray, legal: NDArray[np.bool_]
) -> FloatArray:
    """Reach-weighted action frequencies after consistent action-column alignment."""
    validate_probabilities(probabilities, legal)
    return np.asarray(
        normalized_weights(reach, len(probabilities)) @ probabilities, dtype=np.float64
    )


@dataclass(frozen=True, slots=True)
class EVGap:
    signed: float
    mean_absolute: float


def ev_gap(first: FloatArray, second: FloatArray, weights: FloatArray) -> EVGap:
    """Weighted EV(first)-EV(second), in the supplied common chip units.

    Positive signed gap favors first against the SAME fixed opponent. Absolute
    gap does not indicate who is stronger. No sampling confidence is implied.
    """
    if (
        first.ndim != 1
        or first.shape != second.shape
        or not np.all(np.isfinite(first))
        or not np.all(np.isfinite(second))
    ):
        raise ValueError("finite aligned value vectors required")
    probabilities = normalized_weights(weights, len(first))
    delta = first - second
    return EVGap(float(probabilities @ delta), float(probabilities @ np.abs(delta)))
