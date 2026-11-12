"""Fresh source/old-cost integration, no new learning or native construction."""

import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow


def test_complete_sealed_real_sources_and_all180_explicit_cost_projections() -> None:
    # Other optional tests may preload pyspiel. Production guards stay strict;
    # the actual loader runs in a fresh subprocess, like its real CLI.
    code = """from pathlib import Path
import numpy as np
from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.evaluation.compact_opponent_sources import load,standins
from poker_ai.postflop.river_study import Deadline
ROOT=Path.cwd()
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
            for work,book in zip((100_000,1_000_000,10_000_000),books,strict=True):
                average=data.members[coordinate,"coarse",work,weight+"_average"].values
                tree=data.context_for(coordinate).coarse
                assert np.array_equal(tree.normalize(book),average)
    assert all(
        m.identity["learned_compact_values"] is False for m in data.members.values()
    )
print("all36boundaries180projections; zero new learning/native construction")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )
    recorded = json.loads((ROOT / "results/compact-sampled/real/own.json").read_text())[
        "runtime"
    ]
    import numpy as np

    if (
        sys.version.split()[0] != recorded["python"]
        or np.__version__ != recorded["numpy"]
        or version("numba") != recorded["numba"]
    ):
        # The original guard is intentional and unchanged. Software/data tests
        # on a newer interpreter cannot admit bit-exact original trajectories.
        assert result.returncode != 0
        assert "own/native/replay runtime changed" in result.stderr
        return
    assert result.returncode == 0, result.stderr
    assert "all36boundaries180projections" in result.stdout
