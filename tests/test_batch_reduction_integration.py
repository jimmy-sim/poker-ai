"""Real tiny-game processes and serialized gates; explicitly not Hold'em outcomes."""

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import batch_reduction_inputs as inputs
from poker_ai.evaluation import batch_reduction_run as runner
from poker_ai.evaluation.batch_reduction_fixture import SCOPE, exercise, job, prepare
from poker_ai.evaluation.batch_reduction_report import write_report
from poker_ai.evaluation.batch_reduction_validation import gather, grid
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def complete() -> tuple[
    dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]
]:
    base = json.loads((ROOT / "configs/frozen-pass-batches.json").read_text())
    deadline = Deadline(240)
    config, peers = prepare(base, deadline)
    correct = exercise(config, peers, 1, deadline)
    timing = exercise(config, peers, 3, deadline)
    return config, peers, correct, timing


def test_real_three_process_all72_and216_old_state_identities(
    complete: tuple[
        dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]
    ],
) -> None:
    config, peers, correct, timing = complete
    assert correct["scope"] == timing["scope"] == SCOPE
    assert len(gather(correct["batch"], peers, 1, config)) == 72
    assert len(gather(timing["batch"], peers, 3, config)) == 216
    result = grid(timing["rows"], peers, 3, config)
    assert result is not None and result["repeated_B1_readout_prefix_checks"] == 144
    assert sum(len(r["prefix_checks"]) for r in correct["rows"]) == 48


def test_real_changed_worker_state_stops_complete_receipt(
    complete: tuple[
        dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]
    ],
) -> None:
    config, peers, correct, _ = complete
    changed = copy.deepcopy(correct["batch"])
    e = next(e for e in changed["workers"][0]["messages"] if e["kind"] == "cell")
    e["row"]["guard_sha256"] = "0" * 64
    with pytest.raises(ArithmeticError, match="archived"):
        gather(changed, peers, 1, config)


def test_real_full_runner_two_stages_offline_and_report_roundtrip(
    complete: tuple[
        dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]
    ],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, peers, _, _ = complete
    config = copy.deepcopy(inputs.config_inputs(ROOT))
    config["status"] = SCOPE
    marker = tmp_path / "EXPLICIT_SOURCE.py"
    marker.write_text("# explicit software fixture\n")
    source = dict(
        dirty=False, git_commit="c" * 40, sha256={marker.name: digest(marker)}
    )
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(inputs, "prerequisites", lambda root: ({"config": base}, peers))
    h = sha(source["sha256"])
    ci = dict(
        checked_commit=source["git_commit"],
        source_sha256=h,
        run_id=123,
        jobs=inputs.JOBS,
    )
    local = dict(source_sha256=h, checks=inputs.LOCAL)
    persist(tmp_path / inputs.CHECKS, inputs.record_checks(tmp_path, ci, local))
    base = copy.deepcopy(base)
    base["prefix_runtime"] = runtime_environment()
    persist(tmp_path / "configs/frozen-pass-batches.json", base)
    persist(tmp_path / "configs/training-isolation.json", dict(future_comparison={}))
    monkeypatch.setattr(runner, "job", job)
    correct = runner.run(tmp_path, tmp_path / inputs.CORRECTNESS, "correctness")
    assert correct["completed_endpoints"] == 72 and correct["scope"] == SCOPE
    profile = runner.run(tmp_path, tmp_path / inputs.PROFILE, "profile")
    assert (
        profile["completed_endpoints"] == 216
        and profile["short_prefix_training_attempted"] is True
    )
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("reader learner forbidden"),
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("reader native forbidden")
        ),
    ):
        saved = runner.replay(tmp_path, tmp_path / inputs.PROFILE)
    a = write_report(saved, tmp_path / "a")
    b = write_report(saved, tmp_path / "b")
    assert a == b and saved == profile
    assert json.loads((tmp_path / "a/summary.json").read_text())["scope"] == SCOPE
    changed = copy.deepcopy(profile)
    changed["forecast"]["guarded_own_seconds"] += 1
    persist(tmp_path / "changed.json", changed)
    with pytest.raises(ArithmeticError, match="forecast"):
        runner.replay(tmp_path, tmp_path / "changed.json")
