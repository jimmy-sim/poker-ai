"""Lifecycle and clock fixtures, with no learner/reference or actual archive."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
import suit_candidates_support as kernel
from compact_suit import admission as gates
from compact_suit import cli, clock
from compact_suit.clock import atomic

from poker_ai.abstraction import potential

ROOT = Path(__file__).resolve().parents[1]


def test_missing_checks_block_even_card_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_suit import card_contract

    def fail(*args: Any, **kwargs: Any) -> None:
        raise LookupError("missing qualification")

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unqualified card contract")

    monkeypatch.setattr(gates, "require_checks", fail)
    monkeypatch.setattr(card_contract, "collect", forbidden)
    with pytest.raises(LookupError, match="missing qualification"):
        cli.child_main(ROOT, ["software-own", "--output", str(tmp_path / "own.json")])
    assert not (tmp_path / "own.json").exists()
    assert potential.canonical_cards is kernel.BASE


@pytest.mark.parametrize("kind", ["training", "native"])
def test_worker_wrapper_keeps_original_card_code_in_fresh_process(kind: str) -> None:
    code = """import json,sys
from pathlib import Path
from poker_ai.abstraction import potential
from compact_suit.normalization import kernel
from compact_suit import workers,native
def body(*args,**kwargs):
    assert potential.canonical_cards is kernel.BASE
    potential.canonical_cards((0,4),(11,15,19))
    return {"scope":"UNIT_WRAPPER_ONLY_NO_TRAINING_OR_REFERENCE"}
workers._training=body
native._independent=body
payload={"root":str(Path.cwd()),"source_sha256":None,"scope":None,"admission_sha256":None,
         "scratch":None,"deadline_started":None,"context_sha256":None}
job=workers.training if sys.argv[1]=="training" else native.independent
result=job(0,[],payload,lambda x:None)
assert potential.canonical_cards is kernel.BASE
assert result["normalization"]["enabled"] is False
assert result["normalization"]["requests"]==0
assert result["normalization"]["restored"] is True
assert not any(n=="pyspiel" or n.startswith("open_spiel") for n in sys.modules)
print(json.dumps(result["normalization"]))
"""
    env = dict(
        os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts")
    )
    subprocess.run(
        [sys.executable, "-c", code, kind],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=True,
    )


@pytest.mark.parametrize("failure", [False, True])
def test_final_record_follows_scope_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    path = tmp_path / "fixture.json"

    def body(root: Path, argv: list[str], execution: Any) -> int:
        cli.record(path, dict(status="fixture_only_not_a_run"), execution)
        assert json.loads(path.read_text())["normalization"]["active"] is True
        if failure:
            raise LookupError("primary fixture")
        return 0

    monkeypatch.setattr(cli, "_child_main", body)
    if failure:
        with pytest.raises(LookupError, match="primary fixture"):
            cli.child_main(ROOT, ["replay", "--output", str(path)])
    else:
        assert cli.child_main(ROOT, ["replay", "--output", str(path)]) == 0
    row = json.loads(path.read_text())["normalization"]
    assert row["restored"] is True and row["active"] is False
    assert row["status"] == ("failed_retained" if failure else "complete")
    assert potential.canonical_cards is kernel.BASE


def test_existing_receipt_is_never_rewritten(tmp_path: Path) -> None:
    path = tmp_path / "existing.json"
    path.write_bytes(b"EXACT ORIGINAL PARTIAL BYTES")
    with pytest.raises(FileExistsError):
        cli.child_main(ROOT, ["replay", "--output", str(path)])
    assert path.read_bytes() == b"EXACT ORIGINAL PARTIAL BYTES"


def test_replaced_receipt_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "fixture.json"

    def body(root: Path, argv: list[str], execution: Any) -> int:
        cli.record(path, dict(status="fixture_only"), execution)
        path.write_bytes(b"OTHER WRITER BYTES")
        return 0

    monkeypatch.setattr(cli, "_child_main", body)
    with pytest.raises(ArithmeticError, match="changed before final"):
        cli.child_main(ROOT, ["replay", "--output", str(path)])
    assert path.read_bytes() == b"OTHER WRITER BYTES"
    assert potential.canonical_cards is kernel.BASE


@pytest.mark.parametrize("primary", [False, True])
def test_final_save_error_preserves_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, primary: bool
) -> None:
    path = tmp_path / "fixture.json"
    original = atomic
    calls = 0

    def save(p: Path, data: Any) -> None:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise OSError("secondary final save")
        original(p, data)

    def body(root: Path, argv: list[str], execution: Any) -> int:
        cli.record(path, dict(status="fixture_only"), execution)
        if primary:
            raise LookupError("primary fixture")
        return 0

    monkeypatch.setattr(cli, "atomic", save)
    monkeypatch.setattr(cli, "_child_main", body)
    with pytest.raises(LookupError if primary else OSError):
        cli.child_main(ROOT, ["replay", "--output", str(path)])
    assert json.loads(path.read_text())["normalization"]["active"] is True
    assert potential.canonical_cards is kernel.BASE


@pytest.mark.parametrize("damage", [None, "bool_pid", "wrong_pid", "missing_pid"])
def test_complete_clock_binds_observed_child_pid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str | None
) -> None:
    path = tmp_path / "fixture.json"

    class Child:
        pid = 99001
        returncode = 0

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            path.write_text(
                json.dumps(
                    dict(
                        status="fictional_clock_only",
                        source_sha256="UNIT",
                        normalization=dict(pid=self.pid),
                    )
                )
            )

        def wait(self, timeout: float) -> int:
            assert 0 < timeout <= 900
            return 0

    monkeypatch.setattr(subprocess, "Popen", Child)
    assert (
        clock.execute(tmp_path, ["replay", "--output", str(path)], time.perf_counter())
        == 0
    )
    saved = json.loads(path.read_text())
    if damage == "bool_pid":
        saved["complete_command"]["child_pid"] = True
    elif damage == "wrong_pid":
        saved["complete_command"]["child_pid"] += 1
    elif damage == "missing_pid":
        saved["complete_command"].pop("child_pid")
    path.write_text(json.dumps(saved))
    if damage is None:
        assert clock.measurement(path, "replay")["child_pid"] == 99001
    else:
        with pytest.raises((ArithmeticError, KeyError)):
            clock.measurement(path, "replay")


@pytest.mark.parametrize("origin", [None, "nan", "inf", "-1", "0", "1e100"])
def test_formal_entry_rejects_missing_or_invalid_pre_python_origin(
    origin: str | None,
) -> None:
    env = dict(
        os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts")
    )
    env.pop("POKER_COMPACT_SUIT_COMMAND_STARTED", None)
    if origin is not None:
        env["POKER_COMPACT_SUIT_COMMAND_STARTED"] = origin
    run = subprocess.run(
        [
            sys.executable,
            "scripts/validate_suit_compact.py",
            "cost-own",
            "--repetition",
            "0",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert run.returncode != 0 and (
        "origin" in run.stderr or "launch operator" in run.stderr
    )
