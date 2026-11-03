"""Equity feature contracts, suit symmetry and analytical transport geometry."""

import itertools

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.clustering import earth_mover, fit_clusters
from poker_ai.abstraction.potential import (
    FeatureConfig,
    canonical_cards,
    deterministic_potential,
    grid_histogram,
)
from poker_ai.cards import parse_card


def cards(text: str) -> tuple[int, ...]:
    return tuple(map(parse_card, text.split()))


def test_suit_canonicalization_has_169_preflop_classes() -> None:
    classes = {
        canonical_cards(tuple(pair), ())
        for pair in itertools.combinations(range(52), 2)
    }
    assert len(classes) == 169
    assert canonical_cards(cards("As Kh"), cards("Qs Jh Td")) == canonical_cards(
        cards("Ad Kc"), cards("Qd Jc Th")
    )


def test_river_has_no_artificial_future_uncertainty_and_handles_ties() -> None:
    config = FeatureConfig(current_samples=8, runouts=2, opponent_samples=2)
    tied = deterministic_potential(cards("2d 3h"), cards("Tc Jc Qc Kc Ac"), config)
    assert tied.equity == 0.5 and tied.board_lengths == (5,)
    np.testing.assert_array_equal(tied.histograms, [[0, 0, 0, 0, 1, 0, 0, 0, 0]])
    nuts = deterministic_potential(cards("As Ks"), cards("Qs Js Ts 2d 3d"), config)
    assert nuts.equity == 1
    np.testing.assert_array_equal(nuts.histograms, [[0, 0, 0, 0, 0, 0, 0, 0, 1]])


def test_potential_covers_every_future_street_and_is_suit_invariant() -> None:
    config = FeatureConfig(current_samples=8, runouts=2, opponent_samples=2)
    first = deterministic_potential(cards("As Kh"), cards("Qs Jh Td"), config)
    second = deterministic_potential(cards("Ad Kc"), cards("Qd Jc Th"), config)
    assert first.board_lengths == (3, 4, 5)
    assert first.equity == second.equity
    np.testing.assert_array_equal(first.histograms, second.histograms)
    np.testing.assert_allclose(first.histograms.sum(axis=1), 1)
    pre = deterministic_potential(cards("As Kh"), (), config)
    assert pre.board_lengths == (0, 3, 4, 5)


def test_transport_distinguishes_equal_mean_and_respects_equity_units() -> None:
    middle = np.array([0.0, 1.0, 0.0])
    polarized = np.array([0.5, 0, 0.5])
    grid = np.linspace(0, 1, 3)
    assert middle @ grid == polarized @ grid == 0.5
    assert earth_mover(middle, polarized) == pytest.approx(0.5)
    assert earth_mover(np.array([1.0, 0, 0]), np.array([0.0, 0, 1])) == pytest.approx(1)
    assert earth_mover(middle, middle) == 0


@pytest.mark.parametrize("metric", ["euclidean", "earth_mover"])
def test_clustering_recovers_two_separated_groups_reproducibly(metric: str) -> None:
    from typing import cast

    from poker_ai.abstraction.clustering import Metric

    histograms = np.array([[[1.0, 0, 0]], [[1.0, 0, 0]], [[0.0, 0, 1]], [[0.0, 0, 1]]])
    equity = np.array([0.0, 0, 1, 1])
    a = fit_clusters(
        histograms,
        equity,
        clusters=2,
        metric=cast(Metric, metric),
        rng=Generator(PCG64(9)),
    )
    b = fit_clusters(
        histograms,
        equity,
        clusters=2,
        metric=cast(Metric, metric),
        rng=Generator(PCG64(9)),
    )
    labels = a.assign(histograms)
    assert labels[0] == labels[1] and labels[2] == labels[3] and labels[0] != labels[2]
    np.testing.assert_array_equal(a.centers, b.centers)
    np.testing.assert_allclose(a.equity_centers[labels], equity)
    assert a.occupied == 2


def test_invalid_cards_and_histogram_values_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_cards(cards("As As"), ())
    with pytest.raises(ValueError):
        grid_histogram(np.array([1.1]), 9)
    with pytest.raises(ValueError):
        FeatureConfig(bins=1)


def test_w1_median_and_euclidean_mean_have_distinct_analytical_centers() -> None:
    values = np.array([[[1.0, 0, 0]], [[0.0, 1, 0]], [[0.0, 0, 1]]])
    equity = np.array([0.0, 0.5, 1])
    median = fit_clusters(
        values, equity, clusters=1, metric="earth_mover", rng=Generator(PCG64(3))
    )
    mean = fit_clusters(
        values, equity, clusters=1, metric="euclidean", rng=Generator(PCG64(3))
    )
    np.testing.assert_allclose(median.centers, [[[0, 1, 0]]])
    np.testing.assert_allclose(mean.centers, [[[1 / 3, 1 / 3, 1 / 3]]])
