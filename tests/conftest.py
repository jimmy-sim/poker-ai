"""Reproducible property checks under the committed dependency lockfile."""

from collections.abc import Callable

import numpy as np
import pytest
from hypothesis import settings
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction, Kind, fit_quantizer
from poker_ai.abstraction.potential import FeatureConfig, Potential

settings.register_profile(
    "reproducible", derandomize=True, max_examples=200, deadline=None
)
settings.load_profile("reproducible")


def _tiny_card_model(kind: Kind) -> CardAbstraction:
    models = {}
    for length in (0, 3, 4, 5):
        lengths = (length,) + tuple(t for t in (3, 4, 5) if t > length)
        features = [
            Potential(equity, lengths, np.tile(row, (len(lengths), 1)))
            for equity, row in ((0.0, [1.0, 0, 0]), (1.0, [0.0, 0, 1]))
        ]
        models[length] = fit_quantizer(
            features, kind=kind, buckets=2, rng=Generator(PCG64(31))
        )
    return CardAbstraction(
        models, FeatureConfig(bins=3, current_samples=4, runouts=1, opponent_samples=2)
    )


@pytest.fixture
def card_model_factory() -> Callable[[Kind], CardAbstraction]:
    return _tiny_card_model
