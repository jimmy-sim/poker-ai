"""Keep the one failed pair's data-only interpretation honest."""

import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/guarded-prerequisite-skip"
REPORT = ROOT / "scripts/report_guarded_skip_failure.py"


def run_report(
    evidence: Path, *, publication: bool = False
) -> subprocess.CompletedProcess[str]:
    code = (
        "import importlib.util,json,sys; "
        "s=importlib.util.spec_from_file_location('report',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "print(json.dumps(m.verify(__import__('pathlib').Path(sys.argv[2]), "
        "publication=sys.argv[3]=='1')))"
    )
    return subprocess.run(
        [sys.executable, "-c", code, str(REPORT), str(evidence), str(int(publication))],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def evidence_copy(tmp_path: Path) -> Path:
    target = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, target)
    return target


def raw_json(evidence: Path, name: str) -> dict[str, Any]:
    with tarfile.open(evidence / "pair-raw/raw.tar.gz", "r:gz") as archive:
        stream = archive.extractfile(name)
        assert stream is not None
        value: dict[str, Any] = json.loads(stream.read())
    return value


def replace_raw_member(evidence: Path, name: str, value: dict[str, Any]) -> None:
    folder = evidence / "pair-raw"
    manifest_path = folder / "manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_bytes())
    rows: dict[str, bytes] = {}
    with tarfile.open(folder / "raw.tar.gz", "r:gz") as archive:
        for member in archive.getmembers():
            stream = archive.extractfile(member)
            assert stream is not None
            rows[member.name] = stream.read()
    raw = (json.dumps(value, indent=2) + "\n").encode()
    rows[name] = raw
    manifest["files"][name] = dict(
        bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()
    )
    with (folder / "raw.tar.gz").open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as archive:
                for member_name in sorted(rows):
                    data = rows[member_name]
                    info = tarfile.TarInfo(member_name)
                    info.size = len(data)
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(data))
    compressed = (folder / "raw.tar.gz").read_bytes()
    manifest["archive"] = dict(
        bytes=len(compressed), sha256=hashlib.sha256(compressed).hexdigest()
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def test_published_failure_is_not_admitted() -> None:
    result = run_report(EVIDENCE, publication=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "failed_exact_work_identity"
    assert report["publication"]["pair_admissible"] is False
    assert report["complete_pair"]["scientific_fields_identical_except_work"] is True
    assert report["complete_pair"]["exact_result_and_work_identity"] is False
    assert report["complete_pair"]["ordinary_original_loads"] == 14
    assert report["complete_pair"]["guarded_original_loads"] == 2
    assert report["complete_pair"]["guarded_returns"] == 12
    assert report["limits"]["cpu_savings_established"] is False


@pytest.mark.parametrize("module", ["poker_ai", "numpy", "numba", "pyspiel", "treys"])
def test_poker_numerical_and_reference_imports_blocked(module: str) -> None:
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
    assert "poker, numerical and reference imports blocked" in result.stderr


def test_changed_compressed_byte_rejected(evidence_copy: Path) -> None:
    path = evidence_copy / "pair-raw/raw.tar.gz"
    path.write_bytes(path.read_bytes() + b" ")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "raw archive or verifier changed" in result.stderr


def test_rehashed_profile_shape_rejected(evidence_copy: Path) -> None:
    name = "raw/ordinary/child.json"
    child = raw_json(evidence_copy, name)
    child["result"]["identity"]["profiles"] = 432
    replace_raw_member(evidence_copy, name, child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "complete child scope changed" in result.stderr


def test_rehashed_guarded_work_change_rejected(evidence_copy: Path) -> None:
    name = "raw/guarded_skip/child.json"
    child = raw_json(evidence_copy, name)
    child["result"]["identity"]["validation_cache"]["hits"] += 1
    replace_raw_member(evidence_copy, name, child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "failed scientific/work identity record changed" in result.stderr


def test_source_publication_drift_rejected(evidence_copy: Path) -> None:
    path = evidence_copy / "source-checks/manifest.json"
    source: dict[str, Any] = json.loads(path.read_bytes())
    source["checked_commit"] = "0" * 40
    path.write_text(json.dumps(source, indent=2) + "\n")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published guarded-skip sequence changed" in result.stderr


def test_own_raw_member_change_rejected(evidence_copy: Path) -> None:
    path = evidence_copy / "own/child.json"
    path.write_bytes(path.read_bytes() + b" ")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "own member changed" in result.stderr
