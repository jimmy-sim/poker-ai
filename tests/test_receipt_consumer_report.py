"""Check that the data-only renderer rejects changed archived evidence."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/receipt-consumer-mutation/raw"
REPORT = ROOT / "scripts/report_receipt_consumer_mutation.py"


def run_report(raw: Path) -> subprocess.CompletedProcess[str]:
    code = (
        "import importlib.util,sys; "
        "s=importlib.util.spec_from_file_location('report',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "m.RAW=__import__('pathlib').Path(sys.argv[2]); m.verify()"
    )
    return subprocess.run(
        [sys.executable, "-c", code, str(REPORT), str(raw)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def raw_copy(tmp_path: Path) -> Path:
    destination = tmp_path / "raw"
    shutil.copytree(RAW, destination)
    return destination


def test_published_raw_passes_without_poker_import(raw_copy: Path) -> None:
    assert run_report(raw_copy).returncode == 0


def test_original_reader_import_is_blocked() -> None:
    code = (
        "import importlib.util,sys; "
        "s=importlib.util.spec_from_file_location('report',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "c=m.block_poker_readers(); c.__enter__(); "
        "__import__('poker_ai')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(REPORT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "poker readers blocked" in result.stderr


def test_tampered_raw_hash_rejected(raw_copy: Path) -> None:
    child = raw_copy / "311/child.json"
    child.write_bytes(child.read_bytes() + b" ")
    result = run_report(raw_copy)
    assert result.returncode != 0
    assert "raw member changed" in result.stderr


def test_mutated_receipt_rejected_even_with_matching_hash(raw_copy: Path) -> None:
    child_path = raw_copy / "311/child.json"
    child: dict[str, Any] = json.loads(child_path.read_bytes())
    child["observations"][0]["after_caller"]["witness"] = "changed"
    changed = (json.dumps(child, indent=2) + "\n").encode()
    child_path.write_bytes(changed)
    manifest_path = raw_copy / "manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_bytes())
    manifest["files"]["311/child.json"]["bytes"] = len(changed)
    manifest["files"]["311/child.json"]["sha256"] = hashlib.sha256(changed).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    result = run_report(raw_copy)
    assert result.returncode != 0
    assert "receipt changed prerequisite" in result.stderr
