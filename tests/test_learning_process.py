"""Real spawned orchestration on explicitly synthetic toy worlds, not Hold'em."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.postflop import (
    controlled_profile,
    learning_protocol,
    node_profile,
    pipeline_cost,
)
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import read_archive, write_archive
from poker_ai.postflop.learning_training import own_job, validate_grid
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint
from poker_ai.postflop.training_isolation import sentinel_tree

ROOT = Path(__file__).resolve().parents[1]


def synthetic_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Child-local toy context injection; production own_job/counters are unchanged."""
    tree = sentinel_tree()
    empty = np.zeros(len(tree.keys), dtype=np.bool_)
    context = ScoringContext(tree, tree, np.arange(len(tree.keys)), (empty, empty))
    contexts = {
        (c["spot_file"], c["representation"]): context for c in payload["cells"]
    }
    previous = pipeline_cost.contexts
    pipeline_cost.contexts = lambda root, comparison: contexts
    try:
        return own_job(slot, indices, payload, send)
    finally:
        pipeline_cost.contexts = previous


def test_all_original_cell_identities_spawn_with_toy_data_and_stream_840_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT))
    _, comparison, cells = learning_protocol.inputs(ROOT)
    tree = sentinel_tree()
    prefixes = {}
    for cell in cells:
        solver = node_profile.trainer(
            tree, cell, "nodes" if cell["traversal"] == "external" else "parent"
        )
        if cell["bridge"] != "cold_target_history_mass":
            solver.initialize_exact()
        while solver.iteration < 4:
            solver.step()
        prefixes[controlled_profile.identity(cell)] = dict(
            iterations=4,
            state_sha256=fingerprint(solver),
            total_visits=solver.nodes_visited,
            initialization_visits=solver.initialization_visits,
        )
    batch: dict[str, Any] = {}
    labels = dict(work=[150, 300, 500], iteration=[2, 4, 8])
    run_batch(
        140,
        3,
        synthetic_job,
        dict(
            root=str(ROOT),
            comparison=comparison,
            cells=cells,
            remaining_seconds=120,
            scratch=str(tmp_path),
            labels=labels,
            source_sha256="a" * 64,
            prefixes=prefixes,
            tolerance=1e-9,
        ),
        Deadline(120),
        batch,
    )
    rows = validate_grid(batch, cells, labels)
    assert sum(len(r["labels"]) for r in rows) == 840
    assert len({r["index"] for r in rows}) == 140
    assert all(w["exitcode"] == 0 for w in batch["workers"])
    archive = tmp_path / "explicit-synthetic-toy-archive.jsonl.gz"
    sha = write_archive(archive, tmp_path, rows)
    assert sum(1 for _ in read_archive(archive, sha, rows)) == len(rows)
