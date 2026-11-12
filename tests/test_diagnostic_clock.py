"""Reusable clock retains complete/failing/timeout software-only receipts."""

import hashlib
import json
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import diagnostic_clock as clock


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
        "poker_ai.evaluation.diagnostic_clock.subprocess.Popen", Process
    )
    signals: list[tuple[int, int]] = []
    monkeypatch.setattr(
        "poker_ai.evaluation.diagnostic_clock.os.killpg",
        lambda pid, sig: signals.append((pid, sig)),
    )
    rc = clock.execute(
        tmp_path,
        ["software-own", "--output", "own.json"],
        time.perf_counter(),
        "scripts/trace_compact_information.py",
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
            tmp_path,
            ["software-own", "--output", "own.json"],
            time.perf_counter(),
            "scripts/trace_compact_information.py",
        )


def test_trace_deadline_preserves_all_downstream_caps() -> None:
    now = datetime(2026, 11, 12, 16, 55, tzinfo=UTC)
    clock.schedule("own", "2026-11-12T18:00:00Z", now)
    with pytest.raises(TimeoutError):
        clock.schedule("own", "2026-11-12T18:00:00Z", now + timedelta(seconds=1))
    with pytest.raises(ValueError):
        clock.schedule("own", "2026-11-12T18:00:00", now)
    assert clock.CAPS == dict(own=900, report=900, replay=900, **{"software-own": 180})
