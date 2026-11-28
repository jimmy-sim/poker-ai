"""Independent synthetic checks for frozen row accounting and labels."""

import numpy as np
import pytest
from known_mixture_residual_map.math import summarize


def test_turn_concentration_and_deterministic_ranking() -> None:
    gains = np.array([0.6, 0.2, 0.0, 0.2], dtype=np.float64)
    result = summarize(gains, ("TURN", "TURN", "RIVER", "RIVER"), 1.0)
    assert result["street_label"] == "turn-dominant"
    assert result["streets"]["TURN"]["top_five_indices"] == [0, 1]
    assert result["streets"]["RIVER"]["top_five_indices"] == [3, 2]
    assert result["streets"]["RIVER"]["positive_rows"] == 1


@pytest.mark.parametrize(
    ("gains", "score"),
    [
        ([0.5, -0.1], 0.4),
        ([0.5, 0.5], 0.9),
        ([float("nan"), 1.0], 1.0),
    ],
)
def test_reject_bad_row_accounting(gains: list[float], score: float) -> None:
    with pytest.raises(ArithmeticError):
        summarize(np.array(gains), ("TURN", "RIVER"), score)


def test_split_and_distributed_labels() -> None:
    gains = np.ones(60, dtype=np.float64)
    result = summarize(gains, ("TURN",) * 30 + ("RIVER",) * 30, 60.0)
    assert result["street_label"] == "split"
    assert result["streets"]["TURN"]["concentration"] == "distributed"
    assert result["streets"]["RIVER"]["concentration"] == "distributed"
