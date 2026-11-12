"""Persisted admission regression; all prerequisites are synthetic, no training."""

import json
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import compact_opponent_admission as gates
from poker_ai.evaluation import compact_opponent_cli as cli
from poker_ai.evaluation.opponent_learning_design import COST
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest


@pytest.mark.parametrize(
    "change", ["none", "missing_seal", "wrong_seal", "legacy", "cap", "source", "input"]
)
def test_cli_written_permit_roundtrips_without_losing_required_seals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    # Gate prerequisites/identity/timings are UNIT ONLY. The actual permit
    # builder, CLI persistence and permit reader run; no game/worker/reference.
    source = dict(
        git_commit="UNIT_ONLY_NOT_A_COMMIT",
        dirty=False,
        git_status=[],
        sha256={"unit_only.py": "a" * 64},
    )
    binding = sha(source["sha256"])
    folder = tmp_path / gates.FOLDER
    folder.mkdir(parents=True)
    (tmp_path / gates.CHECKS).write_text("UNIT ONLY NOT ACTUAL CHECKS")
    historical = tmp_path / "old-input.txt"
    historical.write_text("UNIT ONLY historical data")
    routine = {"routine-input.txt": "b" * 64}
    seals = {"old-input.txt": digest(historical)}
    timing = [
        dict(scope=COST, repetition=i, complete_command=dict(seconds=1))
        for i in range(3)
    ]
    forecast = gates.forecast({"T": 1}, timing, timing)
    (folder / "forecast.json").write_text(
        json.dumps(
            dict(
                status="complete_fixed_cost_forecast",
                failure=None,
                source_sha256=binding,
                forecast=forecast,
                verified_input_sha256=seals,
            )
        )
    )
    monkeypatch.setattr(cli, "source", lambda r: source)
    monkeypatch.setattr(
        cli, "contract", lambda r: {"unit_only": True, "study_id": "UNIT_ONLY"}
    )
    monkeypatch.setattr(cli, "input_pins", lambda r: routine)
    monkeypatch.setattr(
        gates,
        "require_checks",
        lambda r: dict(
            source_sha256=binding,
            ci=dict(checked_commit="UNIT_ONLY_NOT_A_COMMIT", run_id=1),
        ),
    )
    monkeypatch.setattr(gates, "published", lambda *a: None)
    monkeypatch.setattr(gates, "committed", lambda *a: None)
    monkeypatch.setattr(gates, "measurement", lambda *a: {"unit_only": True})
    monkeypatch.setattr(gates, "sealed_costs", lambda r: (forecast, seals))
    monkeypatch.setenv("POKER_COMPACT_OPPONENT_STARTED", repr(time.perf_counter()))

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("synthetic admission reached a worker")

    monkeypatch.setattr(cli, "run_batch", forbidden)
    assert cli.child_main(tmp_path, ["admit", "--_child"]) == 0
    path = tmp_path / gates.ADMISSION
    saved = json.loads(path.read_text())
    if change == "none":
        checked = gates.require_admission(tmp_path, binding)
        assert checked["input_sha256"] == routine
        assert checked["permit_input_sha256"] == {
            **seals,
            gates.FOLDER + "forecast.json": digest(folder / "forecast.json"),
            gates.CHECKS: digest(tmp_path / gates.CHECKS),
        }
        assert checked["poker_training_performed"] is False
        assert checked["reference_constructed"] is False
        return
    if change == "missing_seal":
        del saved["permit_input_sha256"]["old-input.txt"]
    elif change == "wrong_seal":
        saved["permit_input_sha256"]["old-input.txt"] = "0" * 64
    elif change == "legacy":
        saved.pop("permit_input_sha256", None)
    elif change == "cap":
        saved["maximum_own_seconds"] += 1
    elif change == "source":
        saved["source_sha256"] = "0" * 64
    else:
        historical.write_text("changed historical input")
    path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        gates.require_admission(tmp_path, binding)
