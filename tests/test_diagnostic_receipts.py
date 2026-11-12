"""Strict six-role receipt/guard tests, with explicitly mocked source blobs."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import diagnostic_receipts as receipts
from poker_ai.postflop import compact_full_artifacts as files


def fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    current = dict(fingerprint="mocked-source", sha256={"fixture.py": "a" * 64})
    monkeypatch.setattr(files, "commit_sources", lambda *a, **k: None)
    rows = []
    for role in ("base", "optional", "hosted"):
        for minor in ("311", "312"):
            p = tmp_path / (role + minor + ".log")
            p.write_text("mocked-check-commit: fixture passed\n")
            rows.append(
                dict(
                    role=role,
                    minor=minor,
                    status="passed",
                    source_fingerprint="mocked-source",
                    checked_commit="mocked-check-commit",
                    python="3.11.17" if minor == "311" else "3.12.15",
                    head_sha="mocked-check-commit",
                    job_id=1,
                    run_id=2,
                    conclusion="success",
                    log=receipts.bound(tmp_path, p),
                )
            )
    p = tmp_path / "checks.json"
    p.write_text(json.dumps(dict(source_fingerprint="mocked-source", checks=rows)))
    return p, current


def test_six_mocked_source_roles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p, c = fixture(tmp_path, monkeypatch)
    assert receipts.checks(tmp_path, p, c)["file"] == "checks.json"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "fp",
        "commit",
        "failed",
        "version",
        "hash",
        "head",
        "ci_failed",
        "bool_job",
        "bool_run",
    ],
)
def test_bad_source_roles_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    p, c = fixture(tmp_path, monkeypatch)
    x = json.loads(p.read_text())
    if mutation == "missing":
        x["checks"].pop()
    elif mutation == "duplicate":
        x["checks"][-1] = x["checks"][0]
    elif mutation == "fp":
        x["source_fingerprint"] = "different"
    elif mutation == "commit":
        x["checks"][0]["checked_commit"] = "different"
    elif mutation == "failed":
        x["checks"][0]["status"] = "failed"
    elif mutation == "version":
        x["checks"][0]["python"] = "3.10"
    elif mutation == "hash":
        x["checks"][0]["log"]["sha256"] = "b" * 64
    elif mutation == "head":
        x["checks"][-1]["head_sha"] = "different"
    elif mutation == "ci_failed":
        x["checks"][-1]["conclusion"] = "failure"
    elif mutation == "bool_job":
        x["checks"][-1]["job_id"] = True
    else:
        x["checks"][-1]["run_id"] = True
    p.write_text(json.dumps(x))
    with pytest.raises(ArithmeticError):
        receipts.checks(tmp_path, p, c)


def test_prospective_pin_and_local_path_are_required(tmp_path: Path) -> None:
    p = tmp_path / "config.json"
    p.write_text(json.dumps(dict(input_sha256={})))
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    assert receipts.config(tmp_path, "config.json", sha)["input_sha256"] == {}
    with pytest.raises(ArithmeticError):
        receipts.config(tmp_path, "config.json", "a" * 64)
    p.write_text(json.dumps(dict(input_sha256={"../outside": "a" * 64})))
    with pytest.raises((ArithmeticError, FileNotFoundError)):
        receipts.config(
            tmp_path, "config.json", hashlib.sha256(p.read_bytes()).hexdigest()
        )


def test_fresh_process_blocks_learner_and_reference_imports() -> None:
    code = """
import importlib
from poker_ai.evaluation.compact_information_run import run
from poker_ai.evaluation.diagnostic_guard import own_only
assert callable(run)
with own_only():
    from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
    try:
        ReducedDispatchBatchTrainer()
    except AssertionError:
        pass
    else:
        raise AssertionError("learner not blocked")
    for name in (
        "pyspiel", "open_spiel",
        "poker_ai.solver_validation.matched_array_reference",
    ):
        try:
            importlib.import_module(name)
        except AssertionError:
            pass
        else:
            raise AssertionError("reference not blocked")
print("learners and every reference import blocked")
"""
    result = subprocess.run(
        [sys.executable, "-c", code], text=True, capture_output=True, check=True
    )
    assert "learners and every reference import blocked" in result.stdout
