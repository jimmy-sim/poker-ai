"""Kernel receipts reject stale/partial/admission-spoofed outputs and retain IO."""

import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import private_prefix_correctness as checks
from poker_ai.postflop.river_study import digest


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = tmp_path / "test-source.py"
    source.write_text("# Explicit receipt fixture, not a scientific source gate.\n")
    monkeypatch.setattr(checks, "contract", lambda _: {"scope": "UNIT_RECEIPT_FIXTURE"})
    monkeypatch.setattr(
        checks,
        "source_provenance",
        lambda *args, **kwargs: {
            "dirty": False,
            "sha256": {"test-source.py": digest(source)},
        },
    )
    return tmp_path / "receipt.json"


def test_actual_kernel_rows_replay_and_refuse_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = fixture(tmp_path, monkeypatch)
    saved = checks.run(tmp_path, path)
    assert len(saved["math"]) == 12 and len(saved["trajectories"]) == 120
    assert checks.replay(tmp_path, path) == saved
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        checks.run(tmp_path, path)
    assert original == path.read_bytes()


def test_midcheck_failure_keeps_prior_rows_and_cannot_replay_as_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = fixture(tmp_path, monkeypatch)

    def failed() -> Any:
        raise RuntimeError("injected after math, before trajectory completion")

    monkeypatch.setattr(checks, "parity", failed)
    with pytest.raises(RuntimeError, match="injected"):
        checks.run(tmp_path, path)
    saved = json.loads(path.read_text())
    assert len(saved["math"]) == 12 and saved["trajectories"] == []
    assert saved["status"] == "failed_kernel_correctness_not_admitted"
    assert saved["failure"]["type"] == "RuntimeError"
    assert saved["long_run_admitted"] is False
    with pytest.raises(ArithmeticError, match="partial"):
        checks.replay(tmp_path, path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("long_run_admitted", True),
        ("full_shape_proof_complete", True),
        ("forecast_complete", True),
        ("reference_constructed", True),
        ("real_poker_training_performed", 0),
        ("seconds", True),
        ("source_sha256", "0" * 64),
        ("math", []),
        ("trajectories", []),
    ],
)
def test_reject_changed_counts_source_flags_and_nonfinite_clock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    path = fixture(tmp_path, monkeypatch)
    saved = checks.run(tmp_path, path)
    saved[field] = value
    path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        checks.replay(tmp_path, path)


def test_stale_source_rejected_without_weakening_old_source_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = fixture(tmp_path, monkeypatch)
    checks.run(tmp_path, path)
    (tmp_path / "test-source.py").write_text("# changed\n")
    with pytest.raises(ArithmeticError, match="source changed"):
        checks.replay(tmp_path, path)
