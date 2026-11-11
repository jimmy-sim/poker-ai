"""Clock/partial-command fixtures only; no learner, reference or real admission."""

import hashlib
import json
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import opponent_learning_clock as clock


def measured(
    path: Path, kind: str = "software-own", *, start: float = 100.0
) -> dict[str, Any]:
    body = dict(source_sha256="a" * 64, status="fixture_only", integer_counter=0)
    raw = json.dumps(body, sort_keys=True).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    clock.child_path(path).write_bytes(raw)
    receipt = dict(
        body,
        complete_command=dict(
            operation=kind,
            returncode=0,
            seconds=10.0,
            started_perf_counter=start,
            source_sha256=body["source_sha256"],
            child_file=clock.child_path(path).name,
            child_sha256=hashlib.sha256(raw).hexdigest(),
            hostname=socket.gethostname(),
            shared_seconds=30.0,
        ),
    )
    path.write_text(json.dumps(receipt))
    return receipt


def test_complete_measurement_binds_exact_typed_child_body(tmp_path: Path) -> None:
    path = tmp_path / "own.json"
    saved = measured(path)
    assert clock.measurement(path, "software-own")["seconds"] == 10
    saved["integer_counter"] = False
    path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        clock.measurement(path, "software-own")


@pytest.mark.parametrize(
    "field,value",
    [
        ("returncode", False),
        ("returncode", 1),
        ("seconds", float("nan")),
        ("seconds", 180.0),
        ("started_perf_counter", float("nan")),
        ("started_perf_counter", True),
        ("child_sha256", "b" * 64),
    ],
)
def test_invalid_complete_measurement_cannot_pass(
    tmp_path: Path, field: str, value: Any
) -> None:
    path = tmp_path / "own.json"
    saved = measured(path)
    saved["complete_command"][field] = value
    path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        clock.measurement(path, "software-own")


@pytest.mark.parametrize(
    "name", ["own-events.jsonl", "own-captures.jsonl.tmp", "report"]
)
def test_partial_destinations_block_before_child_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    folder = tmp_path / "results"
    folder.mkdir()
    old = folder / name
    old.write_text("retain partial")

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("partial output launched numerical child")

    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.subprocess.Popen", forbidden
    )
    with pytest.raises(FileExistsError):
        clock.execute(tmp_path, ["software-own", "--output", "results/own.json"], 100.0)
    assert old.read_text() == "retain partial"


def test_shared_clock_uses_absolute_end_without_double_charging_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own = tmp_path / "results/own.json"
    measured(own)
    ticks = iter([125.0, 130.0, 140.0])
    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.time.perf_counter",
        lambda: next(ticks),
    )
    timeouts = []

    class Process:
        def wait(self, timeout: float) -> int:
            timeouts.append(timeout)
            clock.atomic(
                tmp_path / "results/native.json",
                dict(source_sha256="a" * 64, status="fixture_only"),
            )
            return 0

    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.subprocess.Popen",
        lambda *a, **k: Process(),
    )
    assert (
        clock.execute(
            tmp_path,
            [
                "software-audit",
                "--own",
                "results/own.json",
                "--output",
                "results/native.json",
            ],
            120.0,
        )
        == 0
    )
    assert timeouts == [150.0]  # original own start100 +180 - current130.
    m = clock.measurement(tmp_path / "results/native.json", "software-audit")
    assert m["seconds"] == 20 and m["shared_seconds"] == 40


@pytest.mark.parametrize("start", [300.0, -100.0])
def test_future_or_expired_shared_clock_blocks_before_reference_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    start: float,
) -> None:
    measured(tmp_path / "results/own.json", start=start)
    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.time.perf_counter", lambda: 200.0
    )

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("bad shared clock launched child")

    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.subprocess.Popen", forbidden
    )
    with pytest.raises((TimeoutError, ArithmeticError)):
        clock.execute(
            tmp_path,
            [
                "software-audit",
                "--own",
                "results/own.json",
                "--output",
                "results/native.json",
            ],
            190.0,
        )


def test_early_child_failure_is_retained_without_a_child_created_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        def wait(self, timeout: float) -> int:
            return 7

    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.subprocess.Popen",
        lambda *a, **k: Process(),
    )
    assert (
        clock.execute(
            tmp_path,
            ["software-own", "--output", "new/own.json"],
            time.perf_counter(),
        )
        == 7
    )
    saved = json.loads((tmp_path / "new/own.json").read_text())
    assert saved["status"] == "failed_before_child_receipt"
    assert saved["complete_command"]["returncode"] == 7
    assert clock.child_path(tmp_path / "new/own.json").exists()


def test_timeout_terminates_group_and_keeps_partial_child_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    class Process:
        pid = 12345
        count = 0

        def wait(self, timeout: float) -> int:
            self.count += 1
            if self.count == 1:
                clock.atomic(
                    tmp_path / "results/own.json",
                    dict(source_sha256="a" * 64, status="running_fixture"),
                )
                raise subprocess.TimeoutExpired("fixture", timeout)
            return -15

    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.subprocess.Popen",
        lambda *a, **k: Process(),
    )
    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_clock.os.killpg",
        lambda pid, sig: calls.append((pid, sig)),
    )
    assert (
        clock.execute(
            tmp_path,
            ["software-own", "--output", "results/own.json"],
            time.perf_counter(),
        )
        == 124
    )
    saved = json.loads((tmp_path / "results/own.json").read_text())
    assert saved["status"] == "running_fixture"
    assert saved["complete_command"]["interrupted"] == "TimeoutExpired"
    assert calls == [(12345, signal.SIGTERM)]
    with pytest.raises(ArithmeticError):
        clock.measurement(tmp_path / "results/own.json", "software-own")


def test_interrupted_temporary_bytes_are_retained_exactly(tmp_path: Path) -> None:
    path = tmp_path / "own.json"
    temporary = path.with_suffix(".json.tmp")
    raw = b'{"interrupted":\n'
    temporary.write_bytes(raw)
    retained = clock.preserve_temporary(path)
    assert retained is not None
    assert (tmp_path / retained["file"]).read_bytes() == raw
    assert retained["sha256"] == hashlib.sha256(raw).hexdigest()
    assert retained["bytes"] == len(raw)
    assert not temporary.exists()
    assert clock.preserve_temporary(path) is None
    temporary.write_bytes(raw)
    assert clock.preserve_temporary(path) == retained


@pytest.mark.parametrize(
    "operation, cap",
    [("cost-own", 900), ("cost-audit", 900), ("study", 7200), ("audit", 900)],
)
def test_original_real_caps_and_fixed_cost_repetitions(
    operation: str, cap: int
) -> None:
    assert clock.CAPS[operation] == cap
    if operation.startswith("cost-"):
        with pytest.raises(SystemExit):
            clock.arguments([operation, "--output", "fresh.json"])
        args = clock.arguments([operation, "--repetition", "2"])
        assert args.repetition == 2
