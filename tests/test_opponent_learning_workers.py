"""Actual tiny spawned paths and complete/failing worker aggregation, no poker."""

import copy
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.evaluation.opponent_learning_design import COST, TOY, TOY_WORK, Design
from poker_ai.evaluation.opponent_learning_gate import source
from poker_ai.evaluation.opponent_learning_workers import gather, training
from poker_ai.postflop.cell_process import partition, run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def spawned(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    # This is a unit run on the current source, not published proof/admission.
    scratch = tmp_path_factory.mktemp("opponent-worker-paths")
    deadline = Deadline(180)
    contexts = [software_context(0), software_context(1)]
    batch: dict[str, Any] = {}
    run_batch(
        30,
        3,
        training,
        dict(
            root=str(ROOT),
            source_sha256=sha(source(ROOT)["sha256"]),
            scope=TOY,
            scratch=str(scratch),
            deadline_started=deadline.started,
            context_sha256=[
                {
                    k: tree_digest(c.tree(k))
                    for k in ("coarse", "mixed0", "mixed1", "fine")
                }
                for c in contexts
            ],
        ),
        deadline,
        batch,
    )
    return batch


def test_same_three_process_path_captures_complete_tiny_grid(
    spawned: dict[str, Any],
) -> None:
    results = gather(spawned, Design(TOY, TOY_WORK))
    assert len(results) == 30
    assert sum(len(r["captures"]) for r in results) == 324
    assert sum(len(r["masses"]) for r in results) == 216
    assert len({r["warm"]["path_index"] for r in results}) == 30
    assert all(w["exitcode"] == 0 for w in spawned["workers"])


@pytest.mark.parametrize(
    "change",
    ["failure", "exit", "assignment", "missing", "warm", "phase", "bool_index"],
)
def test_failed_or_changed_worker_grid_is_not_complete(
    spawned: dict[str, Any], change: str
) -> None:
    bad = copy.deepcopy(spawned)
    worker = bad["workers"][0]
    if change == "failure":
        bad["failure"] = {"type": "fixture"}
    elif change == "exit":
        worker["exitcode"] = False
    elif change == "assignment":
        bad["assignments"][0] = [0]
    else:
        event = next(
            e
            for e in worker["messages"]
            if e["kind"] == "cell" and e["phase"] == "warm"
        )
        if change == "missing":
            worker["messages"].remove(event)
        elif change == "warm":
            event["row"]["path_index"] = False
        elif change == "phase":
            event["phase"] = "unregistered"
        else:
            event["index"] = False
    with pytest.raises(ArithmeticError):
        gather(bad, Design(TOY, TOY_WORK))


def test_cost_scope_and_changed_source_stop_before_a_trainer(tmp_path: Path) -> None:
    binding = sha(source(ROOT)["sha256"])
    for scope, source_hash in ((COST, binding), (TOY, "b" * 64)):
        with pytest.raises((ValueError, ArithmeticError)):
            training(
                0,
                partition(30, 3)[0],
                dict(root=str(ROOT), scope=scope, source_sha256=source_hash),
                lambda e: None,
            )
    assert list(tmp_path.iterdir()) == []
