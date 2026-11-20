"""Focused checks for the declared saved-policy diagnostic grid and ranking."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from river_generalization_diagnosis.analysis import (  # noqa: E402
    LABELS,
    SEEDS,
    cases,
    ordered_top,
)


def test_declared_grid_has_exact_saved_paths_and_work() -> None:
    grid = cases()
    assert len(grid) == 12
    assert [item.index for item in grid] == list(range(12))
    for seed_index, seed in enumerate(SEEDS):
        candidate = [
            item
            for item in grid
            if item.seed == seed and item.arm == "q8_turn_exact_river"
        ]
        control = [
            item
            for item in grid
            if item.seed == seed and item.arm == "texture_range_q8_b8"
        ]
        assert [(item.work, item.path_index) for item in candidate] == [
            (work, 7 + 2 * seed_index) for work in LABELS
        ]
        assert [(item.work, item.path_index) for item in control] == [
            (LABELS[-1], 6 + 2 * seed_index)
        ]


def test_rank_excludes_unsupported_rows_and_breaks_ties_by_index() -> None:
    values = np.array([0.0, 0.25, 0.5, 0.25, 0.5])
    support = np.array([1.0, 1.0, 0.0, 1.0, 2.0])
    assert ordered_top(values, support, 5) == [4, 1, 3]


def test_rank_rejects_nonfinite_loss() -> None:
    with pytest.raises(ValueError, match="invalid ranked"):
        ordered_top(np.array([np.nan]), np.array([1.0]), 1)
