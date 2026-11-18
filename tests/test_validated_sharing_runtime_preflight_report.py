"""Reject changed published failure bytes in the data-only report."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/validated-sharing-runtime-preflight"
REPORT = ROOT / "scripts/report_validated_sharing_runtime_preflight.py"


def run_report(evidence: Path) -> subprocess.CompletedProcess[str]:
    code = (
        "import importlib.util,sys; "
        "s=importlib.util.spec_from_file_location('report',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "m.EVIDENCE=__import__('pathlib').Path(sys.argv[2]); "
        "m.REPAIR=m.EVIDENCE/'source-check-repair.json'; "
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


def replace_member(evidence: Path, name: str, value: dict[str, Any]) -> None:
    member = evidence / "failed-pair" / name
    raw = (json.dumps(value, indent=2) + "\n").encode()
    member.write_bytes(raw)
    manifest_path = evidence / "failed-pair/manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_bytes())
    manifest["files"][name] = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def test_published_failure_renders_without_reader_imports(evidence_copy: Path) -> None:
    result = run_report(evidence_copy)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["status"] == "failed_pair_with_incomplete_publication_gate"
    assert report["publication"]["source_archive_complete_at_pair_time"] is False
    assert report["publication"]["pair_admissible"] is False
    assert report["complete_pair"]["original_loader_calls"] == 14
    assert report["complete_pair"]["validated_share_child_started"] is False


@pytest.mark.parametrize("module", ["poker_ai", "numpy", "numba", "pyspiel", "treys"])
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
    replace_member(evidence_copy, "raw/ordinary/child.json", child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published failed pair changed" in result.stderr


def test_changed_profile_shape_rejected_even_with_matching_hash(
    evidence_copy: Path,
) -> None:
    native_path = evidence_copy / "failed-pair/raw/ordinary/native.json"
    native: dict[str, Any] = json.loads(native_path.read_bytes())
    native["profiles"] = {str(i): value for i, value in enumerate(native["profiles"])}
    replace_member(evidence_copy, "raw/ordinary/native.json", native)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published failed pair changed" in result.stderr


def test_changed_late_repair_receipt_rejected(evidence_copy: Path) -> None:
    path = evidence_copy / "source-check-repair.json"
    repair: dict[str, Any] = json.loads(path.read_bytes())
    repair["pair_admissible"] = True
    path.write_text(json.dumps(repair, indent=2) + "\n")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published gate sequence or outcome changed" in result.stderr
