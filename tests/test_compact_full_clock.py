"""Complete-command failure/timeout receipts; subprocess fixtures do no poker."""

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import compact_full_clock as clock
from poker_ai.postflop import compact_full_gate as gate
from poker_ai.postflop.learning_artifacts import canonical


@pytest.mark.parametrize(
    "kind", ["complete", "failed", "timeout", "interrupt", "temporary", "early"]
)
def test_complete_command_retains_every_exit_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    output = tmp_path / "own.json"

    class Process:
        pid = 123456789
        returncode = 0
        calls = 0

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            if kind != "early":
                clock.atomic(output, dict(status="completed", actual_admission=False))
            if kind == "temporary":
                output.with_suffix(".json.tmp").write_bytes(b"unfinished exact bytes")

        def wait(self, timeout: float) -> int:
            self.calls += 1
            if kind == "timeout" and self.calls == 1:
                raise subprocess.TimeoutExpired("fixture", timeout)
            if kind == "interrupt" and self.calls == 1:
                raise KeyboardInterrupt
            self.returncode = 1 if kind in ("failed", "early") else 0
            return self.returncode

    monkeypatch.setattr(
        "poker_ai.postflop.compact_full_clock.subprocess.Popen", Process
    )
    signals: list[tuple[int, int]] = []
    monkeypatch.setattr(
        "poker_ai.postflop.compact_full_clock.os.killpg",
        lambda pid, sig: signals.append((pid, sig)),
    )
    rc = clock.execute(
        tmp_path, ["software-own", "--output", "own.json"], time.perf_counter()
    )
    result = json.loads(output.read_text())
    child = output.with_name("own-child.json")
    assert child.exists()
    assert (
        result["complete_command"]["child_sha256"]
        == hashlib.sha256(child.read_bytes()).hexdigest()
    )
    if kind == "complete":
        assert rc == 0
        clock.measurement(output, "software-own")
    else:
        assert rc != 0
        with pytest.raises(ArithmeticError):
            clock.measurement(output, "software-own")
    if kind in ("timeout", "interrupt"):
        assert signals
    if kind == "temporary":
        retained = result["complete_command"]["retained_temporary"]
        assert (tmp_path / retained["file"]).read_bytes() == b"unfinished exact bytes"
    with pytest.raises(FileExistsError):
        clock.execute(
            tmp_path, ["software-own", "--output", "own.json"], time.perf_counter()
        )


def check_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    raw = b"fixture source"
    monkeypatch.setattr(
        "poker_ai.postflop.compact_full_gate.artifacts.source",
        lambda *a, **k: dict(
            fingerprint="fixture", sha256={"dummy.py": hashlib.sha256(raw).hexdigest()}
        ),
    )
    monkeypatch.setattr(
        "poker_ai.postflop.compact_full_gate.artifacts.commit_sources",
        lambda *a, **k: None,
    )
    rows = []
    for role in ("base", "optional", "hosted"):
        for minor in ("311", "312"):
            log = tmp_path / f"{role}-{minor}.log"
            log.write_text("commit fixture-commit; unit fixture passed\n")
            rows.append(
                dict(
                    role=role,
                    minor=minor,
                    source_fingerprint="fixture",
                    status="passed",
                    python="3.11.17" if minor == "311" else "3.12.15",
                    checked_commit="fixture-commit",
                    conclusion="success",
                    head_sha="fixture-commit",
                    job_id=1,
                    run_id=2,
                    log=gate.bound(tmp_path, log),
                )
            )
    path = tmp_path / "checks.json"
    path.write_bytes(canonical(dict(source_fingerprint="fixture", checks=rows)))
    return path


def test_complete_source_check_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = check_fixture(tmp_path, monkeypatch)
    assert len(gate.checks(tmp_path, path)["checks"]) == 6


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "fingerprint",
        "source_commit",
        "status",
        "runtime",
        "log",
        "ci_head",
        "ci_failed",
    ],
)
def test_source_check_receipts_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    path = check_fixture(tmp_path, monkeypatch)
    saved = json.loads(path.read_text())
    if mutation == "missing":
        saved["checks"].pop()
    elif mutation == "duplicate":
        saved["checks"][-1] = saved["checks"][0]
    elif mutation == "fingerprint":
        saved["source_fingerprint"] = "different"
    elif mutation == "source_commit":
        saved["checks"][0]["checked_commit"] = "different"
    elif mutation == "status":
        saved["checks"][0]["status"] = "failed"
    elif mutation == "runtime":
        saved["checks"][0]["python"] = "different"
    elif mutation == "log":
        saved["checks"][0]["log"]["sha256"] = "different"
    elif mutation == "ci_head":
        saved["checks"][-1]["head_sha"] = "different"
    else:
        saved["checks"][-1]["conclusion"] = "failure"
    path.write_bytes(canonical(saved))
    with pytest.raises(ArithmeticError):
        gate.checks(tmp_path, path)


def test_changed_tested_source_object_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = check_fixture(tmp_path, monkeypatch)

    def reject(*a: Any, **k: Any) -> None:
        raise ArithmeticError("tested commit source differs")

    monkeypatch.setattr(
        "poker_ai.postflop.compact_full_gate.artifacts.commit_sources", reject
    )
    with pytest.raises(ArithmeticError, match="tested commit"):
        gate.checks(tmp_path, path)


def test_prerequisite_paths_stay_in_repository(tmp_path: Path) -> None:
    with pytest.raises(ArithmeticError):
        gate.checked_path(tmp_path, dict(file="../elsewhere", sha256="wrong"))


def test_fixed_forecast_formula() -> None:
    assert gate.conservative_bounds(10, 5, 2, 3, 4) == (68, 48)
    assert gate.conservative_bounds(0, 0, 225, 0, 0) == (900, 900)


@pytest.mark.parametrize("value", [True, "1", -1, float("nan"), float("inf")])
def test_invalid_forecast_costs_rejected(value: Any) -> None:
    with pytest.raises(ValueError):
        gate.conservative_bounds(value, 0, 0, 0, 0)
