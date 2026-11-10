"""Historical archive readers and fresh-source admission have different boundaries."""

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_code_gate as gate
from poker_ai.postflop.learning_artifacts import sha


def fixture(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    old = root / "src/old.py"
    old.parent.mkdir()
    old.write_text("EXPLICIT_OLD=1\n")
    hashes = {"src/old.py": hashlib.sha256(old.read_bytes()).hexdigest()}
    source = dict(dirty=False, git_commit="a" * 40, sha256=hashes)
    h = sha(hashes)
    saved = dict(
        status="tested_software_not_real_study_admission",
        source=source,
        source_sha256=h,
        ci=dict(source_sha256=h, checked_commit="a" * 40, jobs=gate.JOBS, run_id=1),
        local=dict(
            source_sha256=h,
            results={
                k: dict(status="passed", tests_passed=1) for k in gate.REQUIRED_LOCAL
            },
        ),
    )
    path = root / gate.CHECKS
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(saved))
    current = dict(source, sha256=dict(hashes, **{"src/new.py": "b" * 64}))
    return saved, current


def test_historical_reader_allows_added_source_files(tmp_path: Path) -> None:
    saved, current = fixture(tmp_path)
    with (
        patch.object(gate, "source", return_value=current),
        patch.object(gate, "checked_tree", return_value=saved["source"]),
    ):
        assert gate.require(tmp_path, clean=False) == saved


def test_fresh_source_gate_rejects_added_source_files(tmp_path: Path) -> None:
    saved, current = fixture(tmp_path)
    with (
        patch.object(gate, "source", return_value=current),
        patch.object(gate, "checked_tree", return_value=saved["source"]),
    ):
        with pytest.raises(ArithmeticError, match="differs"):
            gate.require(tmp_path, clean=True)


def test_historical_reader_still_rejects_changed_original_bytes(tmp_path: Path) -> None:
    saved, current = fixture(tmp_path)
    (tmp_path / "src/old.py").write_text("EXPLICIT_OLD=2\n")
    with (
        patch.object(gate, "source", return_value=current),
        patch.object(gate, "checked_tree", return_value=saved["source"]),
    ):
        with pytest.raises(ArithmeticError, match="originally-clean"):
            gate.require(tmp_path, clean=False)


@pytest.mark.parametrize(
    "kind", ["ci_failed", "local_missing", "local_bool_count", "ci_bool_run"]
)
def test_incomplete_observed_checks_rejected_even_for_old_reader(
    tmp_path: Path, kind: str
) -> None:
    saved, current = fixture(tmp_path)
    if kind == "ci_failed":
        saved["ci"]["jobs"] = dict(gate.JOBS, **{"Python 3.11": "failure"})
    elif kind == "local_missing":
        saved["local"]["results"].pop("optional312")
    elif kind == "local_bool_count":
        saved["local"]["results"]["base311"]["tests_passed"] = True
    else:
        saved["ci"]["run_id"] = True
    (tmp_path / gate.CHECKS).write_text(json.dumps(saved))
    with (
        patch.object(gate, "source", return_value=current),
        patch.object(gate, "checked_tree", return_value=saved["source"]),
    ):
        with pytest.raises(ArithmeticError, match="gate changed"):
            gate.require(tmp_path, clean=False)
