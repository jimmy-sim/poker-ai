"""Prerequisite failures persist and minimal/fake admission cannot enable training."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_admission as admission
from poker_ai.evaluation import matched_update_code_gate as code_gate
from poker_ai.evaluation import matched_update_overhead as overhead
from poker_ai.evaluation import matched_update_profile as profile
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline


def test_profile_pre_input_failure_retained_without_prefix_training(
    tmp_path: Path,
) -> None:
    output = tmp_path / "profile.json"
    with patch.object(
        profile, "source", side_effect=OSError("injected source failure")
    ):
        with pytest.raises(OSError):
            profile.run(tmp_path, output, tmp_path / "overhead/own.json")
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["prefix_training_requested"] is False
    assert saved["completed_prefix_timings"] == 0
    assert saved["reference_constructed"] is False
    assert saved["failure"]["type"] == "OSError"


def test_dirty_shared_parent_cannot_be_relabelled_clean_for_overhead(
    tmp_path: Path,
) -> None:
    output = tmp_path / "own.json"
    with patch.object(overhead, "source", return_value=dict(dirty=True, sha256={})):
        with pytest.raises(ArithmeticError, match="originally-clean"):
            overhead.run(tmp_path, output, Deadline(900), dict(dirty=True, sha256={}))
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["completed_captures"] == 0
    assert saved["new_prefix_training"] is False


def test_minimal_fake_admission_still_requires_pushed_exact_bytes(
    tmp_path: Path,
) -> None:
    path = tmp_path / admission.PATH
    path.parent.mkdir(parents=True)
    binding = sha({})
    path.write_text(json.dumps(dict(source_sha256=binding)))
    with (
        patch.object(code_gate, "require", return_value=dict(source=dict(sha256={}))),
        patch.object(
            admission, "published", side_effect=ArithmeticError("unpublished admission")
        ),
    ):
        with pytest.raises(ArithmeticError, match="unpublished"):
            admission.require_admission(tmp_path, binding)


def test_admission_with_different_source_rejected_before_publication(
    tmp_path: Path,
) -> None:
    path = tmp_path / admission.PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(source_sha256="a" * 64)))
    with patch.object(
        admission, "published", side_effect=AssertionError("different source")
    ):
        with pytest.raises(ArithmeticError, match="differs"):
            admission.require_admission(tmp_path, "b" * 64)
