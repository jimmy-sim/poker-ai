"""Fresh-process boundaries and negative gates, never a training admission."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import compact_opponent_admission as gates
from poker_ai.evaluation.compact_opponent_workers import _training
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def test_fresh_training_imports_and_runtime_forbid_reference_backends() -> None:
    code = """
import sys
from poker_ai.evaluation.compact_opponent_workers import training
from poker_ai.evaluation.compact_opponent_guard import isolated,runtime
runtime(worker=True)
with isolated(worker=True):
    names=('pyspiel','open_spiel.python.policy',
           'poker_ai.solver_validation.reference')
    for name in names:
        try: __import__(name)
        except AssertionError: pass
        else: raise AssertionError('reference import was allowed')
runtime(worker=True)
print('fresh worker imports reference-free; all3 import attempts rejected')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "all3 import attempts rejected" in result.stdout


def test_read_only_parent_blocks_solver_construction() -> None:
    # Isolated subprocess: other optional tests may already have imported pyspiel.
    code = """
from poker_ai.evaluation.compact_opponent_guard import isolated
with isolated(worker=False):
    from poker_ai.solver_validation.reference import Reference
    from poker_ai.solver_validation.matched_array_reference import ScalarReference
    from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
    for constructor in (Reference,ScalarReference,ReducedDispatchBatchTrainer):
        try: constructor(None)
        except AssertionError: pass
        else: raise AssertionError('read-only parent constructed a solver')
print('all3 solver constructors rejected')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "all3 solver constructors rejected" in result.stdout


@pytest.mark.parametrize(
    "payload", [{}, {"saved_policy": []}, {"reference_strategy": []}]
)
def test_training_worker_rejects_nonstructural_payload_before_source_or_initialization(
    payload: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="only structural"):
        _training(0, list(range(0, 30, 3)), payload, lambda e: None)


def test_all_three_own_costs_are_required_before_any_native_cost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = tmp_path / gates.FOLDER / "cost/0"
    folder.mkdir(parents=True)
    # Explicit schema fixture, not measured/public evidence.
    from poker_ai.evaluation.opponent_learning_design import COST, WORK, Design

    saved = dict(
        scope=COST,
        repetition=0,
        config={"UNIT": True},
        poker_training_performed=False,
        actual_poker_training_work=0,
        manifest=Design(COST, WORK).manifest(),
    )
    (folder / "own.json").write_text(json.dumps(saved))
    monkeypatch.setattr(gates, "measurement", lambda *a: {"UNIT": True})
    monkeypatch.setattr(gates, "contract", lambda *a: {"UNIT": True})
    publications = []

    def publication(*args: Any) -> dict[str, Any]:
        publications.append(args[1])
        return {}

    monkeypatch.setattr(gates, "publication", publication)
    with pytest.raises(FileNotFoundError):
        gates.all_own_costs_published(tmp_path)
    assert publications == [folder / "own.json"]


@pytest.mark.parametrize(
    "change", ["none", "missing", "hash", "commit", "ref", "scope", "extra"]
)
def test_each_pre_native_cost_witness_field_is_checked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    common = dict(
        own_commit="UNIT_COMMIT",
        upstream_commit="UNIT_UPSTREAM",
        locally_recorded_upstream="refs/remotes/origin/UNIT_BRANCH",
    )
    witnesses = []
    for repetition in (0, 1, 2):
        path = tmp_path / gates.FOLDER / f"cost/{repetition}/own.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"UNIT_ONLY_NOT_AN_ARCHIVE": true}')
        witnesses.append(
            dict(
                common,
                own_sha256=digest(path),
                source_sha256="a" * 64,
                scope="UNIT_PUBLICATION_ONLY",
                published_input_sha256={str(path): digest(path)},
            )
        )

    def publication(root: Path, path: Path, own: dict[str, Any]) -> dict[str, Any]:
        return dict(
            common,
            own_sha256=digest(path),
            source_sha256="a" * 64,
            scope="UNIT_PUBLICATION_ONLY",
            published_input_sha256={str(path): digest(path)},
        )

    monkeypatch.setattr(gates, "publication", publication)
    native = dict(
        source_sha256="a" * 64,
        publication=common,
        all_own_cost_publications_before_native=witnesses,
    )
    if change == "none":
        gates.validate_cost_publications(tmp_path, native)
        return
    if change == "missing":
        witnesses.pop()
    elif change == "hash":
        witnesses[0]["published_input_sha256"] = {}
    elif change == "commit":
        witnesses[0]["own_commit"] = "OTHER"
    elif change == "ref":
        witnesses[0]["locally_recorded_upstream"] = "OTHER"
    elif change == "scope":
        witnesses[0]["scope"] = "CLAIMED_INDEPENDENT_REVIEW"
    else:
        witnesses[0]["unexpected_reference_actions"] = []
    with pytest.raises(ArithmeticError):
        gates.validate_cost_publications(tmp_path, native)
