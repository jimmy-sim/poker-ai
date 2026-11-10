"""Lifecycle failures must precede any child, without changing caps or old bytes."""

import json
import socket
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_lifecycle as io
from poker_ai.postflop.learning_run import persist

ROOT = Path(__file__).resolve().parents[1]


def test_pinned_contract_and_unchanged_scientific_caps() -> None:
    io.contract(ROOT)
    assert io.CAPS == dict(
        tiny_own=180,
        tiny_native=180,
        profile=900,
        timing_native=900,
        study=7200,
        real_native=900,
    )


@pytest.mark.parametrize(
    "name",
    [
        "own.json",
        "own.tmp",
        "own-child.json",
        "own-captures.jsonl.gz",
        "own-masses.jsonl.tmp",
        "own-profiles.jsonl.gz",
        "report",
    ],
)
def test_existing_destination_rejected_even_when_empty(
    tmp_path: Path, name: str
) -> None:
    p = tmp_path / name
    if name == "report":
        p.mkdir()
    else:
        p.write_text("retain me")
    with pytest.raises(FileExistsError, match="retain existing"):
        io.fresh(io.destinations(tmp_path / "own.json", archives=True, report=True))
    assert p.exists()


def test_dangling_symlink_is_retained(tmp_path: Path) -> None:
    path = tmp_path / "own.json"
    path.symlink_to(tmp_path / "absent")
    with pytest.raises(FileExistsError):
        io.fresh(io.destinations(path, archives=False, report=False))
    assert path.is_symlink()


def test_empty_report_rejected_before_child_and_receipt_retained(
    tmp_path: Path,
) -> None:
    report = tmp_path / "overhead/report"
    report.mkdir(parents=True)
    with patch.object(io, "contract"), patch.object(subprocess, "run") as child:
        with pytest.raises(FileExistsError, match="report"):
            io.execute(
                tmp_path,
                [
                    "profile",
                    "--output",
                    "profile.json",
                    "--overhead",
                    "overhead/own.json",
                ],
            )
    child.assert_not_called()
    assert not (tmp_path / "profile.json").exists()
    saved = json.loads(next((tmp_path / "rejections").glob("*.json")).read_text())
    assert saved["status"] == "rejected_before_child"
    assert (
        saved["child_launched"]
        is saved["training_performed"]
        is saved["reference_constructed"]
        is False
    )
    assert list(report.iterdir()) == []


def receipt(tmp_path: Path, kind: str = "profile", returncode: int = 0) -> Path:
    p = tmp_path / "own.json"
    persist(p, dict(source_sha256="a" * 64, value=[1, 2], status="fixture"))
    io.finish(
        p, kind, ["EXPLICIT-test-child"], time.perf_counter() - 0.01, returncode, None
    )
    return p


def test_complete_child_bytes_and_values_preserved(tmp_path: Path) -> None:
    p = receipt(tmp_path)
    m = io.measured(tmp_path, p, "profile")
    assert m["seconds"] >= 0.01
    assert json.loads(io.child_path(p).read_text()) == dict(
        source_sha256="a" * 64, value=[1, 2], status="fixture"
    )
    assert m["returncode"] == 0


@pytest.mark.parametrize(
    "change",
    [
        "child_bytes",
        "value",
        "source",
        "path",
        "kind",
        "bool",
        "nan",
        "cap",
        "nonzero",
        "bool_returncode",
    ],
)
def test_invalid_complete_receipt_rejected(tmp_path: Path, change: str) -> None:
    p = receipt(tmp_path)
    s = json.loads(p.read_text())
    m = s["complete_command"]
    if change == "child_bytes":
        io.child_path(p).write_text("{}")
    elif change == "value":
        s["value"][0] = 9
    elif change == "source":
        m["source_sha256"] = "b" * 64
    elif change == "path":
        m["child_file"] = "../other.json"
    elif change == "kind":
        m["kind"] = "study"
    elif change == "bool":
        m["seconds"] = True
    elif change == "nan":
        m["seconds"] = float("nan")
    elif change == "cap":
        m["seconds"] = 900
    elif change == "bool_returncode":
        m["returncode"] = False
    else:
        m["returncode"] = 1
    p.write_text(json.dumps(s))
    with pytest.raises(ArithmeticError):
        io.measured(tmp_path, p, "profile")


def test_partial_child_retained_but_not_accepted(tmp_path: Path) -> None:
    p = receipt(tmp_path, returncode=1)
    assert io.child_path(p).exists()
    with pytest.raises(ArithmeticError):
        io.measured(tmp_path, p, "profile")


def test_strict_twice_complete_native_guard(tmp_path: Path) -> None:
    p = receipt(tmp_path, kind="timing_native")
    s = json.loads(p.read_text())
    s["complete_command"]["seconds"] = 450
    persist(p, s)
    with pytest.raises(ArithmeticError, match="twice-elapsed"):
        io.measured(tmp_path, p, "timing_native")


@pytest.mark.parametrize("fault", ["expired", "host"])
def test_tiny_shared_clock_checks_publication_interval(
    tmp_path: Path, fault: str
) -> None:
    p = receipt(tmp_path, kind="tiny_own")
    s = json.loads(p.read_text())
    m = s["complete_command"]
    if fault == "expired":
        m["started_perf_counter"] = time.perf_counter() - 180
    else:
        m["hostname"] = socket.gethostname() + "-different"
    persist(p, s)
    with pytest.raises(ArithmeticError, match="clock expired or changed host"):
        io.prerequisites(tmp_path, "tiny_native", p)


def test_child_failure_is_not_silently_retried(tmp_path: Path) -> None:
    def fail(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        persist(
            tmp_path / "own.json", dict(source_sha256="a" * 64, status="incomplete")
        )
        return subprocess.CompletedProcess(command, 1)

    with (
        patch.object(io, "contract"),
        patch.object(subprocess, "run", side_effect=fail) as child,
    ):
        assert io.execute(tmp_path, ["check", "--output", "own.json"]) == 1
    assert child.call_count == 1
    assert json.loads((tmp_path / "own.json").read_text())["status"] == "incomplete"
    assert (
        json.loads(io.child_path(tmp_path / "own.json").read_text())["status"]
        == "incomplete"
    )


@pytest.mark.parametrize("elapsed", [180.0, float("nan"), True])
def test_tiny_final_shared_boundary_is_strict(tmp_path: Path, elapsed: float) -> None:
    own = receipt(tmp_path, kind="tiny_own")
    native = tmp_path / "native.json"
    persist(native, dict(source_sha256="a" * 64, status="EXPLICIT-fixture"))
    io.finish(native, "tiny_native", ["EXPLICIT-native"], time.perf_counter(), 0, own)
    saved = json.loads(native.read_text())
    saved["complete_command"]["shared_seconds"] = elapsed
    native.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError, match="shared clock"):
        io.measured(tmp_path, native, "tiny_native")
