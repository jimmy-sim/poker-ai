"""Check the data-only failed-pair renderer against changed public receipts."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/validated-prerequisite-sharing"
REPORT = ROOT / "scripts/report_validated_prerequisite_sharing.py"


def run_report(evidence: Path) -> subprocess.CompletedProcess[str]:
    code = (
        "import importlib.util,sys; "
        "s=importlib.util.spec_from_file_location('report',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "m.EVIDENCE=__import__('pathlib').Path(sys.argv[2]); "
        "print(__import__('json').dumps(m.verify()))"
    )
    return subprocess.run(
        [sys.executable, "-c", code, str(REPORT), str(evidence)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def evidence_copy(tmp_path: Path) -> Path:
    destination = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, destination)
    return destination


def replace_member(
    evidence: Path, folder: str, name: str, value: dict[str, Any]
) -> None:
    member = evidence / folder / name
    raw = (json.dumps(value, indent=2) + "\n").encode()
    member.write_bytes(raw)
    manifest_path = evidence / folder / "manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_bytes())
    manifest["files"][name] = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def test_published_failure_renders_without_reader_imports(evidence_copy: Path) -> None:
    result = run_report(evidence_copy)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "failed_before_validated_share_child"
    assert output["complete_pair"]["validated_share_child_started"] is False


@pytest.mark.parametrize("module", ["poker_ai", "numpy", "numba", "pyspiel"])
def test_reader_numerical_and_reference_imports_blocked(module: str) -> None:
    code = (
        "import importlib.util,sys; "
        "s=importlib.util.spec_from_file_location('report',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "c=m.block_readers(); c.__enter__(); __import__(sys.argv[2])"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(REPORT), module],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "reader, numerical and reference imports blocked" in result.stderr


def test_changed_raw_byte_rejected(evidence_copy: Path) -> None:
    child = evidence_copy / "failed-pair/raw/ordinary/child.json"
    child.write_bytes(child.read_bytes() + b" ")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published raw member changed" in result.stderr


def test_changed_failure_rejected_even_with_matching_hash(evidence_copy: Path) -> None:
    child_path = evidence_copy / "failed-pair/raw/ordinary/child.json"
    child: dict[str, Any] = json.loads(child_path.read_bytes())
    child["failure"]["type"] = "ChangedFailure"
    replace_member(evidence_copy, "failed-pair", "raw/ordinary/child.json", child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published failed pair changed" in result.stderr


def test_changed_own_witness_rejected_even_with_matching_hash(
    evidence_copy: Path,
) -> None:
    child_path = evidence_copy / "own/child.json"
    child: dict[str, Any] = json.loads(child_path.read_bytes())
    child["observations"][0]["after_caller"]["witness"] = "changed"
    replace_member(evidence_copy, "own", "child.json", child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published own proof changed" in result.stderr
