"""Publication provenance may drift; original bytes and corpus identities may not."""

import copy
import hashlib
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_overhead as legacy
from poker_ai.evaluation import matched_update_parent_io as adapter
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import ScalarReference

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = tmp_path / "EXPLICIT-original.py"
    path.write_text("EXPLICIT=1\n")
    original: dict[str, Any] = dict(
        targets=[dict(id="EXPLICIT-target", iteration=8)],
        input_sha256={"EXPLICIT-data": "a" * 64},
        source=dict(
            git_commit="OWN_BEFORE_PUBLICATION",
            git_status=["new own data"],
            dirty=True,
            sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()},
        ),
    )
    current = copy.deepcopy(original)
    current["source"].update(
        git_commit="NATIVE_AFTER_PUBLICATION", git_status=["new native data"]
    )
    current["source"]["sha256"]["EXPLICIT-added.py"] = "b" * 64
    return original, current


def test_publication_provenance_drift_allowed_without_modifying_saved_view(
    tmp_path: Path,
) -> None:
    old, current = fixture(tmp_path)
    before = copy.deepcopy(old)
    assert adapter.manifest_view(tmp_path, old, current) is old
    assert old == before


@pytest.mark.parametrize(
    "kind", ["target", "input", "extra_field", "original_bytes", "original_hash"]
)
def test_stable_identity_or_original_code_change_is_still_rejected(
    tmp_path: Path, kind: str
) -> None:
    old, current = fixture(tmp_path)
    if kind == "target":
        current["targets"][0]["iteration"] += 1
    elif kind == "input":
        current["input_sha256"]["EXPLICIT-data"] = "f" * 64
    elif kind == "extra_field":
        current["extra"] = True
    elif kind == "original_bytes":
        (tmp_path / "EXPLICIT-original.py").write_text("EXPLICIT=2\n")
    else:
        old["source"]["sha256"]["EXPLICIT-original.py"] = "f" * 64
    with pytest.raises(ArithmeticError):
        adapter.manifest_view(tmp_path, old, current)


def test_parent_service_is_explicit_reentrant_and_restored_after_failure() -> None:
    original = legacy.read
    with pytest.raises(RuntimeError, match="injected"):
        with adapter.activate(ROOT):
            assert legacy.read is adapter.read
            with adapter.activate(ROOT):
                assert legacy.read is adapter.read
            raise RuntimeError("injected")
    assert legacy.read is original


def test_invalid_adapter_contract_rejected_before_binding(tmp_path: Path) -> None:
    path = tmp_path / adapter.CONFIG
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    original = legacy.read
    with pytest.raises(ArithmeticError, match="contract"):
        with adapter.activate(tmp_path):
            raise AssertionError("invalid contract cannot activate")
    assert legacy.read is original


@pytest.mark.slow
def test_published_corpus_replay_blocks_learner_and_reference() -> None:
    path = (
        ROOT / "results/matched-update-pipeline/source-cohort-06a3402/overhead/own.json"
    )
    before = path.read_bytes()
    original_read, original_corpus = legacy.read, vars(legacy)["corpus"]
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(
            ScalarReference, "__init__", side_effect=AssertionError("no reference")
        ),
    ):
        with adapter.activate(ROOT):
            saved, _ = legacy.read(ROOT, path, Deadline(900))
    assert len(saved["captures"]) == len(saved["rows"]) == 144
    assert len(saved["masses"]) == 96
    assert len(saved["fixed_matches"]) == 1152
    assert path.read_bytes() == before
    assert legacy.read is original_read
    assert vars(legacy)["corpus"] is original_corpus


def test_corpus_service_restored_after_pre_input_failure(tmp_path: Path) -> None:
    path = tmp_path / "own.json"
    path.write_text('{"manifest": {}}')
    original = vars(legacy)["corpus"]
    with patch.object(
        adapter, "_BASE_READ", side_effect=OSError("injected read failure")
    ):
        with pytest.raises(OSError, match="read failure"):
            adapter.read(ROOT, path, Deadline(30))
    assert vars(legacy)["corpus"] is original


def test_parent_service_restored_after_cli_exit() -> None:
    original = legacy.read
    with pytest.raises(SystemExit):
        with adapter.activate(ROOT):
            raise SystemExit(2)
    assert legacy.read is original
