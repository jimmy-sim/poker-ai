"""Histogram k-means and one-dimensional earth-mover k-medians.

For distributions on equally spaced equity grid points, W1 is the sum of absolute
CDF differences times grid spacing. A coordinatewise median CDF remains monotone,
so it gives a valid W1 cluster representative. Euclidean histogram k-means uses
arithmetic means. Neither construction certifies strategic abstraction error.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.random import Generator
from numpy.typing import NDArray

from poker_ai.toy.tree import FloatArray

Metric = Literal["euclidean", "earth_mover"]


def validate_histograms(values: FloatArray) -> None:
    if (
        values.ndim != 3
        or values.shape[0] == 0
        or values.shape[1] == 0
        or values.shape[2] < 2
        or not np.all(np.isfinite(values))
        or np.any(values < 0)
        or not np.allclose(values.sum(axis=-1), 1, atol=1e-12, rtol=0)
    ):
        raise ValueError("need normalized finite histogram blocks [N,streets,bins]")


def earth_mover(first: FloatArray, second: FloatArray) -> FloatArray:
    """W1 on equity grid [0,1], with broadcastable leading dimensions."""
    if first.shape[-1] < 2 or first.shape[-1] != second.shape[-1]:
        raise ValueError("matching equity grids need at least two points")
    difference = np.abs(np.cumsum(first, axis=-1) - np.cumsum(second, axis=-1))
    return np.asarray(
        difference[..., :-1].sum(axis=-1) / (first.shape[-1] - 1), dtype=np.float64
    )


def distances(values: FloatArray, centers: FloatArray, metric: Metric) -> FloatArray:
    if values.shape[1:] != centers.shape[1:]:
        raise ValueError("histogram feature shapes disagree")
    if metric == "euclidean":
        result = ((values[:, None] - centers[None, :]) ** 2).mean(axis=(-2, -1))
    elif metric == "earth_mover":
        result = earth_mover(values[:, None], centers[None, :]).mean(axis=-1)
    else:
        raise ValueError("unknown clustering metric")
    return np.asarray(result, dtype=np.float64)


@dataclass(frozen=True)
class ClusterModel:
    centers: FloatArray
    equity_centers: FloatArray
    metric: Metric
    iterations: int
    occupied: int

    def assign(self, histograms: FloatArray) -> NDArray[np.int64]:
        validate_histograms(histograms)
        return np.asarray(
            distances(histograms, self.centers, self.metric).argmin(axis=1),
            dtype=np.int64,
        )


def fit_clusters(
    histograms: FloatArray,
    equities: FloatArray,
    *,
    clusters: int,
    metric: Metric,
    rng: Generator,
    max_iterations: int = 100,
) -> ClusterModel:
    """Lloyd clustering with seeded distance-weighted initialization.

    Empty clusters retain their previous center. Report occupied count explicitly;
    identical features cannot populate artificially distinct buckets. There is
    no claim that a single initialization finds a globally optimal clustering.
    """
    validate_histograms(histograms)
    size = len(histograms)
    if (
        type(clusters) is not int
        or not 1 <= clusters <= size
        or type(max_iterations) is not int
        or max_iterations < 1
        or equities.shape != (size,)
        or not np.all(np.isfinite(equities))
        or np.any(equities < 0)
        or np.any(equities > 1)
        or metric not in ("euclidean", "earth_mover")
    ):
        raise ValueError("invalid clustering settings or equity measurements")
    chosen = [int(rng.integers(size))]
    for _ in range(1, clusters):
        nearest = distances(histograms, histograms[chosen], metric).min(axis=1)
        weights = nearest if metric == "euclidean" else nearest**2
        total = float(weights.sum())
        if total > 0:
            chosen.append(int(rng.choice(size, p=weights / total)))
        else:
            chosen.append(next(i for i in range(size) if i not in chosen))
    centers = histograms[chosen].copy()
    equity_centers = equities[chosen].copy()
    labels = np.full(size, -1, dtype=np.int64)
    for _iteration in range(1, max_iterations + 1):
        new_labels = distances(histograms, centers, metric).argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for cluster in range(clusters):
            members = histograms[labels == cluster]
            if not len(members):
                continue
            if metric == "euclidean":
                centers[cluster] = members.mean(axis=0)
            else:
                cdf = np.median(np.cumsum(members, axis=-1), axis=0)
                centers[cluster] = np.diff(cdf, axis=-1, prepend=0)
            equity_centers[cluster] = equities[labels == cluster].mean()
    # Assignment is recomputed for returned centers, including when iteration
    # budget ended immediately after an update.
    final_labels = distances(histograms, centers, metric).argmin(axis=1)
    for cluster in range(clusters):
        if np.any(final_labels == cluster):
            equity_centers[cluster] = equities[final_labels == cluster].mean()
    validate_histograms(centers)
    return ClusterModel(
        centers, equity_centers, metric, _iteration, len(set(final_labels.tolist()))
    )
