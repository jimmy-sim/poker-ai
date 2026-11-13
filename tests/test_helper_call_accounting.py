"""Transparent software fixtures; no real source-path or poker measurement."""

import copy
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
tool = importlib.import_module("helper_call_accounting")
COMMANDS = ("status", "show", "rev-parse")


def command(root: Path) -> list[str]:
    return ["git", "-C", str(root), "status", "--porcelain"]


def test_original_object_bytes_and_kwargs_preserved(tmp_path: Path) -> None:
    stdout = b"raw\x00\xffSECRET"
    result = subprocess.CompletedProcess(command(tmp_path), 0, stdout, b"err SECRET")
    calls = []
    events: list[dict[str, Any]] = []

    def run(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        return result

    recorder = tool.Recorder(tmp_path, COMMANDS, original=run, emit=events.append)
    argv = command(tmp_path)
    env = {"TOKEN": "SECRET"}
    actual = recorder(argv, capture_output=True, env=env, input=b"SECRET")
    assert actual is result and actual.stdout is stdout
    assert calls[0][0][0] is argv and calls[0][1]["env"] is env
    assert events[0]["status"] == "running" and events[1]["status"] == "complete"
    assert "SECRET" not in json.dumps(recorder.rows) and str(
        tmp_path
    ) not in json.dumps(recorder.rows)
    recorder.require_complete_coverage()
    assert recorder.summary()["exclusive_pid_attribution"] is False


def test_keyword_argv_and_text_fingerprint(tmp_path: Path) -> None:
    result = subprocess.CompletedProcess([], 0, "text\udcff", None)
    recorder = tool.Recorder(tmp_path, COMMANDS, original=lambda **k: result)
    assert recorder(args=command(tmp_path), text=True) is result
    assert recorder.rows[0]["stdout"]["kind"] == "text_utf8_surrogatepass"
    assert recorder.rows[0]["stderr"]["kind"] == "none"
    recorder.require_complete_coverage()


@pytest.mark.parametrize(
    "argv,kwargs",
    [
        ("SECRET", {}),
        (["other", "SECRET"], {}),
        (["git", "-C", "/outside", "status"], {}),
        (["git", "-C", "\0", "status"], {}),
        (["git", "-C", "ROOT", "config", "SECRET"], {}),
        (["git", "-C", "ROOT", "status"], {"shell": True}),
    ],
)
def test_unsupported_calls_execute_without_contents(
    argv: Any, kwargs: dict[str, Any], tmp_path: Path
) -> None:
    if isinstance(argv, list):
        argv = [str(tmp_path) if a == "ROOT" else a for a in argv]
    result = subprocess.CompletedProcess([], 0, "SECRET", "SECRET")
    calls = []

    def run(*args: Any, **kw: Any) -> Any:
        calls.append((args, kw))
        return result

    recorder = tool.Recorder(tmp_path, COMMANDS, original=run)
    assert recorder(argv, **kwargs) is result and len(calls) == 1
    assert recorder.summary()["unsupported"] == 1 and "SECRET" not in json.dumps(
        recorder.rows
    )
    with pytest.raises(ArithmeticError, match="coverage"):
        recorder.require_complete_coverage()


def test_original_exception_identity_and_no_error_contents(tmp_path: Path) -> None:
    error = subprocess.CalledProcessError(17, ["SECRET"], output=b"SECRET")
    events: list[dict[str, Any]] = []

    def run(*args: Any, **kwargs: Any) -> Any:
        raise error

    recorder = tool.Recorder(tmp_path, COMMANDS, original=run, emit=events.append)
    with pytest.raises(subprocess.CalledProcessError) as actual:
        recorder(command(tmp_path))
    assert actual.value is error and recorder.rows[0]["returncode"] == 17
    assert "SECRET" not in json.dumps(recorder.rows)
    with pytest.raises(ArithmeticError):
        recorder.require_complete_coverage()


def test_start_retention_failure_blocks_execution(tmp_path: Path) -> None:
    calls = []

    def run(*a: Any, **k: Any) -> Any:
        calls.append(True)

    def emit(row: dict[str, Any]) -> None:
        raise OSError("fixture")

    recorder = tool.Recorder(tmp_path, COMMANDS, original=run, emit=emit)
    with pytest.raises(OSError):
        recorder(command(tmp_path))
    assert not calls and recorder.summary()["retention_errors"] == 1
    with pytest.raises(ArithmeticError):
        recorder.require_complete_coverage()


def test_secondary_observer_failure_preserves_primary_exception(tmp_path: Path) -> None:
    error = ValueError("SECRET")

    def run(*a: Any, **k: Any) -> Any:
        raise error

    def emit(row: dict[str, Any]) -> None:
        if row["status"] != "running":
            raise OSError("sink")

    recorder = tool.Recorder(tmp_path, COMMANDS, original=run, emit=emit)
    with pytest.raises(ValueError) as actual:
        recorder(command(tmp_path))
    assert actual.value is error and recorder.summary()["observer_errors"] == 1
    assert "SECRET" not in json.dumps(recorder.rows)


def test_successful_command_with_failed_final_retention_is_not_complete(
    tmp_path: Path,
) -> None:
    def emit(row: dict[str, Any]) -> None:
        if row["status"] == "complete":
            raise OSError("sink")

    result = subprocess.CompletedProcess([], 0, b"ok", b"")
    recorder = tool.Recorder(
        tmp_path, COMMANDS, original=lambda *a, **k: result, emit=emit
    )
    with pytest.raises(OSError):
        recorder(command(tmp_path))
    with pytest.raises(ArithmeticError):
        recorder.require_complete_coverage()


def test_hooks_check_output_and_restore_on_failure(tmp_path: Path) -> None:
    original = subprocess.run
    result = subprocess.CompletedProcess([], 0, b"unchanged", b"")
    recorder = tool.Recorder(tmp_path, COMMANDS, original=lambda *a, **k: result)
    with pytest.raises(ValueError, match="fixture"):
        with tool.hooks(recorder):
            assert subprocess.check_output(command(tmp_path)) is result.stdout
            with pytest.raises(RuntimeError, match="nested"):
                with tool.hooks(recorder):
                    pass
            raise ValueError("fixture")
    assert subprocess.run is original
    recorder.require_complete_coverage()


def test_tiny_real_git_fixture_and_raw_accounting(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    recorder = tool.Recorder(tmp_path, COMMANDS)
    with tool.hooks(recorder):
        output = subprocess.check_output(command(tmp_path))
    assert output == b""
    recorder.require_complete_coverage()
    damaged = copy.deepcopy(recorder.rows[0])
    damaged["observation"]["interval"]["clocks"]["perf_seconds"] += 1
    recorder.rows[0] = damaged
    with pytest.raises(ArithmeticError):
        recorder.require_complete_coverage()


@pytest.mark.parametrize("commands", [(), ("push",), ("status", "status")])
def test_unsafe_or_duplicate_categories_rejected(
    commands: tuple[str, ...], tmp_path: Path
) -> None:
    with pytest.raises(ValueError):
        tool.Recorder(tmp_path, commands)


def test_empty_coverage_and_config_does_not_authorize_collection(
    tmp_path: Path,
) -> None:
    recorder = tool.Recorder(tmp_path, COMMANDS)
    with pytest.raises(ArithmeticError):
        recorder.require_complete_coverage()
    c = json.loads((ROOT / "configs/helper-call-accounting.json").read_text())
    assert c["stage"] == "SOFTWARE_COMPONENT_ONLY_NO_FORMAL_COLLECTION"
    assert (
        c["real_source_collector_implemented"]
        is c["formal_collection_this_window"]
        is c["admission_evidence"]
        is False
    )


def test_complete_coverage_is_not_command_success(tmp_path: Path) -> None:
    result = subprocess.CompletedProcess([], 5, b"unchanged", b"")
    recorder = tool.Recorder(tmp_path, COMMANDS, original=lambda *a, **k: result)
    assert recorder(command(tmp_path), check=False) is result
    assert recorder.rows[0]["returncode"] == 5
    recorder.require_complete_coverage()


def test_relative_root_with_child_cwd_is_unsupported(tmp_path: Path) -> None:
    result = subprocess.CompletedProcess([], 0, b"unchanged", b"")
    calls = []

    def run(*a: Any, **k: Any) -> Any:
        calls.append((a, k))
        return result

    recorder = tool.Recorder(Path.cwd(), COMMANDS, original=run)
    argv = ["git", "-C", ".", "status"]
    assert recorder(argv, cwd=tmp_path) is result
    assert calls == [((argv,), {"cwd": tmp_path})]
    assert recorder.summary()["unsupported"] == 1
    with pytest.raises(ArithmeticError, match="coverage"):
        recorder.require_complete_coverage()
