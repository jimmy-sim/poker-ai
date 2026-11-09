"""Archived state/work gate, source binding and retained failures, no poker learning."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import batch_reduction_inputs as inputs
from poker_ai.evaluation import batch_reduction_run as runner
from poker_ai.evaluation.batch_reduction_validation import gather, grid
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import digest
from poker_ai.reproducibility import runtime_environment

ROOT = Path(__file__).resolve().parents[1]


def rows() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    original = json.loads(
        (ROOT / "results/frozen-pass-batches/profile.json").read_text()
    )
    peers = [r for r in original["rows"] if r["repetition"] == 0]
    return original["config"], peers, original["rows"]


def test_prospective_grid_source_pins_and_retained_failed_forecast() -> None:
    c = inputs.config_inputs(ROOT)
    config, peers, points = rows()
    result = grid(points, peers, 3, config)
    assert (
        result is not None
        and result["decision"] == "exceeds_cap_stop_before_long_learning"
    )
    assert c["maximum_own_seconds"] == 7200 and c["seeds"] == [
        20261301,
        20261302,
        20261303,
    ]
    assert grid(peers, peers, 1, config) is None


@pytest.mark.parametrize("field", inputs.IDENTITY)
def test_every_archived_state_work_identity_is_checked(field: str) -> None:
    c, p, r = rows()
    r = copy.deepcopy(r)
    r[0][field] = None
    with pytest.raises(ArithmeticError):
        grid(r, p, 3, c)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "extra",
        "nan",
        "negative",
        "projection",
        "bool_index",
        "bool_rep",
        "extra_field",
    ],
)
def test_raw_row_schema_and_complete_grid(change: str) -> None:
    c, p, r = rows()
    r = copy.deepcopy(r)
    if change == "missing":
        r.pop()
    elif change == "duplicate":
        r[-1] = r[0]
    elif change == "extra":
        r.append(r[0])
    elif change == "nan":
        r[0]["incremental_seconds"] = float("nan")
    elif change == "negative":
        r[0]["cpu_seconds"] = -1
    elif change == "projection":
        r[0]["projected_training_seconds"] += 1
    elif change == "bool_index":
        r[0]["index"] = False
    elif change == "bool_rep":
        r[0]["repetition"] = False
    else:
        r[0]["unexpected"] = 1
    with pytest.raises(ArithmeticError):
        grid(r, p, 3, c)


def batch_fixture() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    c, p, _ = rows()
    assignments = partition(72, 3)
    workers = []
    for slot, indices in enumerate(assignments):
        messages = []
        for i in indices:
            messages.append(
                dict(kind="prepared", phase="prefix_started", index=i, repetition=0)
            )
            row = {k: v for k, v in p[i].items() if k != "index"}
            messages.append(dict(kind="cell", index=i, row=row))
        messages.append(
            dict(kind="done", summary=dict(paths=len(indices), rows=len(indices)))
        )
        workers.append(dict(slot=slot, exitcode=0, messages=messages))
    return (
        c,
        p,
        dict(
            status="completed", failure=None, assignments=assignments, workers=workers
        ),
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing_start",
        "wrong_start",
        "missing_done",
        "wrong_done",
        "wrong_slot",
        "wrong_assignment",
        "exit",
        "status",
    ],
)
def test_worker_partial_and_identity_receipts_rejected(change: str) -> None:
    c, p, b = batch_fixture()
    assert len(gather(b, p, 1, c)) == 72
    if change == "missing_start":
        b["workers"][0]["messages"].pop(0)
    elif change == "wrong_start":
        b["workers"][0]["messages"][0]["index"] = False
    elif change == "missing_done":
        b["workers"][0]["messages"].pop()
    elif change == "wrong_done":
        b["workers"][0]["messages"][-1]["summary"]["rows"] = 1
    elif change == "wrong_slot":
        b["workers"][0]["slot"] = False
    elif change == "wrong_assignment":
        b["assignments"][0].pop()
    elif change == "exit":
        b["workers"][0]["exitcode"] = 1
    else:
        b["status"] = "incomplete"
    with pytest.raises(ArithmeticError):
        gather(b, p, 1, c)


def source_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    marker = tmp_path / "EXPLICIT_SOURCE.py"
    marker.write_text("# software fixture\n")
    s = dict(dirty=False, git_commit="e" * 40, sha256={marker.name: digest(marker)})
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(s))
    c = inputs.config_inputs(ROOT)
    monkeypatch.setattr(inputs, "config_inputs", lambda root: c)
    ci = dict(
        checked_commit=s["git_commit"],
        source_sha256=sha(s["sha256"]),
        run_id=123,
        jobs=inputs.JOBS,
    )
    local = dict(source_sha256=sha(s["sha256"]), checks=inputs.LOCAL)
    saved = inputs.record_checks(tmp_path, ci, local)
    persist(tmp_path / inputs.CHECKS, saved)
    return saved


def test_source_check_and_dirty_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved = source_gate(tmp_path, monkeypatch)
    assert inputs.require_checks(tmp_path) == saved
    (tmp_path / "EXPLICIT_SOURCE.py").write_text("# changed\n")
    with pytest.raises(ArithmeticError):
        inputs.require_checks(tmp_path)


def test_failure_before_prefix_retained_and_no_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_gate(tmp_path, monkeypatch)
    base = json.loads((ROOT / "configs/frozen-pass-batches.json").read_text())
    base["prefix_runtime"] = runtime_environment()
    (tmp_path / "configs").mkdir()
    persist(tmp_path / "configs/frozen-pass-batches.json", base)

    def fail(root: Path) -> Any:
        raise ArithmeticError("injected before prefix")

    monkeypatch.setattr(inputs, "prerequisites", fail)
    path = tmp_path / "attempt.json"
    with pytest.raises(ArithmeticError, match="injected"):
        runner.run(tmp_path, path, "correctness")
    saved = json.loads(path.read_text())
    assert (
        saved["status"] == "incomplete"
        and saved["short_prefix_training_attempted"] is False
        and saved["completed_endpoints"] == 0
    )
    with pytest.raises(FileExistsError):
        runner.run(tmp_path, path, "correctness")


def test_failure_after_start_retains_attempted_partial_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_gate(tmp_path, monkeypatch)
    base = json.loads((ROOT / "configs/frozen-pass-batches.json").read_text())
    base["prefix_runtime"] = runtime_environment()
    persist(tmp_path / "configs/frozen-pass-batches.json", base)
    _, peers, _ = rows()
    monkeypatch.setattr(inputs, "prerequisites", lambda root: ({"config": base}, peers))
    persist(tmp_path / "configs/training-isolation.json", dict(future_comparison={}))

    def fail(*args: Any) -> None:
        record = args[-1]
        record.update(
            status="incomplete",
            workers=[
                dict(
                    messages=[
                        dict(
                            kind="prepared",
                            phase="prefix_started",
                            index=0,
                            repetition=0,
                        ),
                        dict(
                            kind="cell",
                            index=0,
                            row={"scope": "EXPLICIT_SYNTHETIC_PARTIAL_EVENT"},
                        ),
                    ]
                )
            ],
        )
        raise TimeoutError("injected after prefix start")

    monkeypatch.setattr(runner, "run_batch", fail)
    path = tmp_path / "partial.json"
    with pytest.raises(TimeoutError, match="injected"):
        runner.run(tmp_path, path, "correctness")
    saved = json.loads(path.read_text())
    assert (
        saved["status"] == "incomplete"
        and saved["short_prefix_training_attempted"] is True
        and saved["completed_endpoints"] == 1
    )
    assert (
        saved["batch"]["workers"][0]["messages"][1]["row"]["scope"]
        == "EXPLICIT_SYNTHETIC_PARTIAL_EVENT"
    )


@pytest.mark.parametrize("field", ["checked_commit", "source_sha256", "jobs", "run_id"])
def test_source_gate_needs_exact_observed_jobs_and_commit(
    field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved = source_gate(tmp_path, monkeypatch)
    ci = dict(
        checked_commit=saved["checked_commit"],
        source_sha256=saved["source_sha256"],
        jobs=inputs.JOBS,
        run_id=123,
    )
    local = dict(source_sha256=saved["source_sha256"], checks=inputs.LOCAL)
    ci[field] = None
    with pytest.raises(ArithmeticError):
        inputs.record_checks(tmp_path, ci, local)
