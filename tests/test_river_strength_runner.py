"""Stage ordering and toy worker execution without new Hold'em training."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "river_strength_runner", ROOT / "scripts/study_river_strength.py"
)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
SPEC.loader.exec_module(runner)


def test_profile_worker_uses_fixed_fresh_path_and_replays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        runner, "context", lambda root, game, arm: software_context(0).scoring["coarse"]
    )
    events: list[dict[str, Any]] = []
    payload = dict(
        root=str(ROOT),
        output=str(tmp_path),
        labels=(80,),
        stage="profile",
        deadline=Deadline(10),
        fingerprint="a" * 64,
    )
    summary = runner._worker(0, [0], payload, events.append)
    assert summary["slot"] == 0 and len(summary["summaries"]) == 1
    assert summary["summaries"][0]["captures"] == 3
    assert [event["phase"] for event in events] == ["started", "completed"]
    assert (tmp_path / "repeat0/path00/summary.json").is_file()
    with pytest.raises(FileExistsError):
        runner._worker(0, [0], payload, events.append)


def test_proof_gate_precedes_output_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "clean_revision", lambda root: "0" * 40)
    monkeypatch.setattr(runner, "source_fingerprint", lambda root: "a" * 64)

    def unavailable(*args: object) -> None:
        raise ArithmeticError("source qualification missing")

    monkeypatch.setattr(runner, "require_archive", unavailable)
    output = tmp_path / "proof"
    with pytest.raises(ArithmeticError, match="source qualification missing"):
        runner.run_stage("proof", ROOT, output)
    assert not output.exists()


def test_toy_proof_runs_after_mock_qualification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "clean_revision", lambda root: "0" * 40)
    monkeypatch.setattr(runner, "source_fingerprint", lambda root: "a" * 64)
    monkeypatch.setattr(runner, "require_archive", lambda *args: {})
    output = tmp_path / "proof"
    runner.run_stage("proof", ROOT, output)
    assert (output / "toy/summary.json").is_file()
    assert (output / "result.json").is_file()
    assert not (output / "failure.json").exists()
