"""Retain toy B4 path evidence and reject tampered own replay."""

import json
from pathlib import Path

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.evaluation.river_strength_capture import capture_path, replay_path
from poker_ai.evaluation.river_strength_learning import SEEDS, PathSpec
from poker_ai.postflop.river_study import Deadline

BINDING = "a" * 64


def test_toy_capture_replays_and_retains_all_readouts(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    folder = tmp_path / "own"
    path = PathSpec(0, "FICTIONAL", SEEDS[0], "coarse")
    saved = capture_path(scoring, path, folder, BINDING, (80, 240), Deadline(10))
    assert saved["status"] == "completed"
    assert len(saved["captures"]) == 6
    assert replay_path(scoring, folder) == saved
    assert [r["metadata"]["readout"] for r in saved["captures"]] == [
        "current",
        "uniform_average",
        "linear_average",
    ] * 2
    with pytest.raises(FileExistsError):
        capture_path(scoring, path, folder, BINDING, (80,), Deadline(10))


def test_toy_replay_rejects_changed_snapshot_and_missing_readout(
    tmp_path: Path,
) -> None:
    scoring = software_context(0).scoring["coarse"]
    folder = tmp_path / "own"
    path = PathSpec(0, "FICTIONAL", SEEDS[0], "coarse")
    capture_path(scoring, path, folder, BINDING, (80,), Deadline(10))
    summary_path = folder / "summary.json"
    saved = json.loads(summary_path.read_bytes())
    removed = saved["captures"].pop()
    summary_path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError, match="missing fixed readout"):
        replay_path(scoring, folder)
    summary_path.write_text(
        json.dumps({**saved, "captures": [*saved["captures"], removed]})
    )
    artifact = folder / removed["file"]
    artifact.write_bytes(artifact.read_bytes() + b"changed")
    with pytest.raises(ArithmeticError, match="snapshot bytes/hash"):
        replay_path(scoring, folder)


def test_timeout_keeps_failure_event(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    folder = tmp_path / "timeout"
    path = PathSpec(0, "FICTIONAL", SEEDS[0], "coarse")
    with pytest.raises(TimeoutError):
        capture_path(scoring, path, folder, BINDING, (80,), Deadline(0))
    events = [
        json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()
    ]
    assert events[0]["kind"] == "started"
    assert events[-1]["kind"] == "failed_retained"
    assert not (folder / "summary.json").exists()


def test_toy_replay_rejects_changed_average_mass(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    folder = tmp_path / "own"
    path = PathSpec(0, "FICTIONAL", SEEDS[0], "coarse")
    capture_path(scoring, path, folder, BINDING, (80,), Deadline(10))
    mass = folder / "80-linear-mass.json.gz"
    mass.write_bytes(mass.read_bytes() + b"changed")
    with pytest.raises(ArithmeticError, match="cumulative mass bytes"):
        replay_path(scoring, folder)
