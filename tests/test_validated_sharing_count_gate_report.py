"""Check the published complete pair with only authenticated data."""

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
EVIDENCE = ROOT / "results/validated-sharing-count-gate"
REPORT = ROOT / "scripts/report_validated_sharing_count_gate.py"


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
    destination = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, destination)
    return destination


def replace_raw_member(evidence: Path, name: str, value: dict[str, Any]) -> None:
    folder = evidence / "pair-raw"
    manifest_path = folder / "manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_bytes())
    with tarfile.open(folder / "raw.tar.gz", "r:gz") as archive:
        rows = {
            member.name: archive.extractfile(member).read()  # type: ignore[union-attr]
            for member in archive.getmembers()
        }
    raw = (json.dumps(value, indent=2) + "\n").encode()
    rows[name] = raw
    manifest["files"][name] = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
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
    manifest["archive"] = {
        "bytes": len(compressed),
        "sha256": hashlib.sha256(compressed).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def raw_json(evidence: Path, name: str) -> dict[str, Any]:
    with tarfile.open(evidence / "pair-raw/raw.tar.gz", "r:gz") as archive:
        stream = archive.extractfile(name)
        assert stream is not None
        value: dict[str, Any] = json.loads(stream.read())
        return value


def test_published_pair_renders_without_reader_imports() -> None:
    result = run_report(EVIDENCE, publication=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "complete_validated_sharing_behavior_identity"
    assert report["publication"]["behavior_pair_admissible"] is True
    assert report["complete_pair"]["original_loader_calls_each"] == 14
    assert report["complete_pair"]["validated_substitutions"] == 12
    assert report["complete_pair"]["exact_result_and_work_identity"] is True
    assert report["limits"]["cpu_savings_established"] is False


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


def test_changed_compressed_byte_rejected(evidence_copy: Path) -> None:
    path = evidence_copy / "pair-raw/raw.tar.gz"
    path.write_bytes(path.read_bytes() + b" ")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published raw archive or verifier changed" in result.stderr


def test_changed_profile_shape_rejected_even_with_rehashed_archive(
    evidence_copy: Path,
) -> None:
    name = "raw/ordinary/child.json"
    child = raw_json(evidence_copy, name)
    child["result"]["identity"]["profiles"] = 432
    replace_raw_member(evidence_copy, name, child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published child result or work changed" in result.stderr


def test_changed_shared_work_rejected_even_with_rehashed_archive(
    evidence_copy: Path,
) -> None:
    name = "raw/validated_share/child.json"
    child = raw_json(evidence_copy, name)
    child["result"]["identity"]["validation_cache"]["hits"] += 1
    replace_raw_member(evidence_copy, name, child)
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "complete scientific or work identity changed" in result.stderr


def test_changed_source_publication_rejected(evidence_copy: Path) -> None:
    path = evidence_copy / "source-checks/manifest.json"
    source: dict[str, Any] = json.loads(path.read_bytes())
    source["checked_commit"] = "0" * 40
    path.write_text(json.dumps(source, indent=2) + "\n")
    result = run_report(evidence_copy)
    assert result.returncode != 0
    assert "published count-gate sequence changed" in result.stderr
