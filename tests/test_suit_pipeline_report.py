"""Actual saved-report integrity and execution isolation; no new experiments."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import report_suit_pipeline as report
import suit_candidates_support as kernel
from compact_suit import admission, cli, native, workers
from compact_suit.normalization import Normalization

ROOT = Path(__file__).resolve().parents[1]


def blocked(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("saved report must not execute a numerical experiment")


def block_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    for module, name in (
        (admission, "build_game"),
        (admission, "kernel_geometry"),
        (cli, "read"),
        (cli, "training"),
        (native, "independent"),
        (workers, "training"),
        (kernel, "BASE"),
        (kernel, "ALL"),
        (kernel, "reduced_cards"),
        (Normalization, "installed"),
    ):
        monkeypatch.setattr(module, name, blocked)


def test_saved_cost_report_with_all_execution_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    block_execution(monkeypatch)
    summary = report.gather(ROOT)
    assert summary["compute_forecast_pass"] is False
    assert summary["study_admission_claimed"] is False
    assert summary["new_training_performed"] is False
    assert len(summary["measured_costs"]) == 6
    assert summary["forecast"]["strict_own_pass"] is True
    assert summary["forecast"]["strict_native_pass"] is False
    assert summary["forecast"]["N"] == max(
        row["complete_seconds"]
        for row in summary["measured_costs"]
        if row["mode"] == "native"
    )
    report.show(summary)
    output = capsys.readouterr().out
    assert "912.542s / 900s: FAIL" in output
    assert "zero new training" in output


def test_changed_sealed_archive_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = report.digest

    def damaged(path: Path) -> str:
        if path == ROOT / report.FOLDER / "cost/1/own-captures.jsonl.gz":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(report, "digest", damaged)
    block_execution(monkeypatch)
    with pytest.raises(ArithmeticError, match="forecast input changed"):
        report.gather(ROOT)


def test_boolean_complete_time_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = Path.read_text
    path = ROOT / report.FOLDER / "forecast.json"

    def damaged(member: Path, *args: Any, **kwargs: Any) -> str:
        text = original(member, *args, **kwargs)
        if member == path:
            saved = json.loads(text)
            saved["complete_command"]["seconds"] = True
            return json.dumps(saved)
        return text

    monkeypatch.setattr(Path, "read_text", damaged)
    block_execution(monkeypatch)
    with pytest.raises(ArithmeticError, match="complete-command measurement"):
        report.gather(ROOT)


def test_existing_report_preserved(tmp_path: Path) -> None:
    marker = tmp_path / "keep.txt"
    marker.write_text("existing report")
    with pytest.raises(FileExistsError):
        report.render(ROOT, tmp_path)
    assert marker.read_text() == "existing report"
