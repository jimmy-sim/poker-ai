"""Complete real profiling on SOFTWARE fixtures; no actual poker cost measurements."""

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import batch_cost_inputs as inputs
from poker_ai.evaluation import batch_cost_run as run
from poker_ai.evaluation.batch_cost_fixture import SCOPE, exercise, job
from poker_ai.evaluation.batch_cost_report import write_report
from poker_ai.evaluation.batch_cost_validation import gather
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def complete() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    original = json.loads((ROOT / config["source_profile"]).read_text())
    selected = [
        next(r for r in original["rows"] if r["index"] == i and r["repetition"] == 0)
        for i in config["selected_source_indices"]
    ]
    return exercise(config, selected, Deadline(180))


def test_actual_all48_instrumented_controls_and_call_counts(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    saved, selected = complete
    rows = gather(saved["batch"], selected, saved["config"])
    assert rows == saved["rows"] and saved["scope"] == SCOPE
    assert len(rows) == 48 and sum(r["stats"] is not None for r in rows) == 24
    for row in rows:
        if row["mode"] == "instrumented":
            assert (
                row["call_accounting"]["recursive_visit_calls"]
                == row["endpoint"]["incremental_visits"]
            )
            assert (
                row["call_accounting"]["external_calls"]
                == row["endpoint"]["sampled_traversals"]
            )


def test_actual_ledger_corruption_is_detected(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    saved, selected = complete
    changed = copy.deepcopy(saved["batch"])
    event = next(
        e
        for e in changed["workers"][0]["messages"]
        if e["kind"] == "cell" and e["row"]["mode"] == "instrumented"
    )
    f = next(
        f
        for f in event["row"]["stats"]["functions"]
        if f["file"] == "src/poker_ai/training/mccfr.py" and f["name"] == "visit"
    )
    f["total_calls"] += 1
    with pytest.raises(ArithmeticError, match="call counts"):
        gather(changed, selected, saved["config"])


def test_numeric_report_roundtrip_and_scope(
    complete: tuple[dict[str, Any], list[dict[str, Any]]], tmp_path: Path
) -> None:
    saved, _ = complete
    a = write_report(saved, tmp_path / "a", plots=False)
    b = write_report(saved, tmp_path / "b", plots=False)
    assert a["numerical_sha256"] == b["numerical_sha256"]
    assert a["endpoints"] == 48 and a["instrumented_profiles"] == 24
    assert "SOFTWARE FIXTURE" in (tmp_path / "a/tables.md").read_text()


def test_full_runner_serialization_and_offline_base_reader(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("matplotlib")
    saved, selected = complete
    config = copy.deepcopy(saved["config"])
    config["prefix_runtime"] = runtime_environment()
    config["source_profile"] = "EXPLICIT_SOURCE_PROFILE.json"
    (tmp_path / config["source_profile"]).write_text(json.dumps(dict(scope=SCOPE)))
    marker = tmp_path / "EXPLICIT_SOURCE.py"
    marker.write_text("# explicit software source fixture\n")
    source = dict(
        dirty=False, git_commit="f" * 40, sha256={marker.name: digest(marker)}
    )
    h = sha(source["sha256"])
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(
        inputs, "prerequisites", lambda root: ({"scope": SCOPE}, selected)
    )
    ci = dict(
        checked_commit=source["git_commit"],
        source_sha256=h,
        run_id=123,
        jobs=inputs.JOBS,
    )
    local = dict(source_sha256=h, checks=inputs.LOCAL)
    persist(tmp_path / inputs.CHECKED, inputs.record_checks(tmp_path, ci, local))
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/training-isolation.json").write_text(
        json.dumps(dict(future_comparison={}))
    )
    monkeypatch.setattr(run, "job", job)
    path = tmp_path / "attempt/profile.json"
    result = run.run(tmp_path, path)
    assert result["status"] == "completed_cost_profile_no_strength"
    assert (
        result["scope"] == SCOPE and result["short_prefix_training_attempted"] is True
    )
    assert (
        result["completed_endpoints"] == 48
        and result["long_learning_performed"] is False
    )
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("reader training forbidden"),
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("reader native forbidden")
        ),
    ):
        replayed = run.replay(tmp_path, path)
    report = write_report(replayed, tmp_path / "offline", plots=False)
    assert report["numerical_sha256"] == result["report"]["numerical_sha256"]
    assert len(result["report"]["figures"]) == 2
    assert all(
        (path.parent / "report" / name).stat().st_size > 1000
        for name in result["report"]["figures"]
    )
    with pytest.raises(FileExistsError):
        run.run(tmp_path, path)


def test_real_cost_prerequisites_are_reader_only() -> None:
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(Reference, "__init__", side_effect=AssertionError("no native")),
    ):
        original, selected = inputs.prerequisites(ROOT)
    assert len(selected) == 24 and all(r["path"]["seed"] == 20261301 for r in selected)
    assert original["forecast"]["guarded_own_seconds"] == 7201.492438541833
