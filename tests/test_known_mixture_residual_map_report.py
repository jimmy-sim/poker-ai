"""Synthetic report schema and historical measurement-source pin checks."""

from known_mixture_residual_map.report import MEASUREMENT_SOURCE, negative_mixture


def test_nested_published_classification_is_required() -> None:
    assert negative_mixture({"classification": {"classification": "negative"}})
    assert not negative_mixture({"classification": "negative"})
    assert not negative_mixture({"classification": {"classification": "positive"}})


def test_historical_measurement_source_is_explicit() -> None:
    assert MEASUREMENT_SOURCE == (
        "4eba834da858694d40ac1ce87fddb68bd47efb43f5dabcb4db6f29b223d9f57c"
    )
