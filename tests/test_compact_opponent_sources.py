"""Complete source/old-cost loader integration, no new learning or native use."""

from pathlib import Path

import numpy as np
import pytest

from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.evaluation.compact_opponent_sources import load, standins
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow


def test_complete_sealed_real_sources_and_all180_explicit_cost_projections() -> None:
    # Software integration of historical data only. This is NOT a fixed cost
    # repetition, new trajectory, forecast, admission or strength measurement.
    with isolated(worker=False):
        deadline = Deadline(900)
        sources = load(ROOT, deadline)
        assert len(sources.original_boundaries) == 36
        assert len(sources.opponents) == 16
        assert {r["path_index"] % 5 for r in sources.original_boundaries} == {0, 4}
        data = standins(ROOT, sources, deadline)
        assert len(data.members) == 180
        for coordinate in range(6):
            for weight in ("uniform", "linear"):
                books = [
                    data.members[coordinate, "coarse", work, weight].values
                    for work in (100_000, 1_000_000, 10_000_000)
                ]
                assert all(
                    np.all(b >= a) for a, b in zip(books, books[1:], strict=False)
                )
        assert all(
            m.identity["learned_compact_values"] is False for m in data.members.values()
        )
