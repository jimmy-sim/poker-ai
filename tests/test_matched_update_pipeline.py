"""Full logical tiny shape through production capture/scoring/archive/replay."""

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_run as run
from poker_ai.evaluation import matched_update_software as software
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.matched_update_admission import require_admission
from poker_ai.evaluation.matched_update_replay import replay_archives
from poker_ai.evaluation.matched_update_software_inputs import SCOPE, build
from poker_ai.postflop.river_study import Deadline


def exercise(tmp_path: Path) -> tuple[dict[str, Any], Any, Path]:
    fixture = build("a" * 64, Deadline(30))
    saved = dict(
        scope=SCOPE,
        source_sha256="a" * 64,
        scratch=str(tmp_path / "scratch"),
        captures=[],
        masses=[],
        checkpoints=[],
        rows=[],
        fixed_matches=[],
        self_pairs=[],
        fixed_pairs=[],
    )
    path = tmp_path / "own.json"
    software.exercise(path, saved, fixture, Deadline(30))
    return saved, fixture, path


def test_complete_shape_and_identical_policy_zero_gaps(tmp_path: Path) -> None:
    saved, fixture, path = exercise(tmp_path)
    assert len(saved["captures"]) == len(saved["rows"]) == 144
    assert len(saved["masses"]) == 96
    assert len(saved["checkpoints"]) == 72
    assert len(saved["fixed_matches"]) == len(saved["fixed_pairs"]) == 1152
    assert all(
        v == 0
        for p in saved["self_pairs"]
        for v in p["difference_prefix_minus_batched_chips"].values()
    )
    assert saved["replay"]["training_performed"] is False
    assert saved["replay"]["reference_constructed"] is False
    assert saved["replay"]["maximum_error_chips"] == 0
    with patch.object(
        software, "collect", side_effect=AssertionError("replay must not train")
    ):
        proof = replay_archives(
            path,
            saved,
            fixture.manifest,
            fixture.expected,
            lambda _: toy_context(),
            fixture.fixed,
            fixture.right,
            fixture.right_fixed,
            Deadline(30),
        )
    assert proof == saved["replay"]


def test_late_case_failure_prevents_any_new_captured_profile_scoring(
    tmp_path: Path,
) -> None:
    fixture = build("a" * 64, Deadline(30))
    fixture.expected[-1]["guard_sha256"] = "f" * 64
    saved = dict(
        scope=SCOPE,
        source_sha256="a" * 64,
        scratch=str(tmp_path / "scratch"),
        captures=[],
        masses=[],
        checkpoints=[],
        rows=[],
        fixed_matches=[],
        self_pairs=[],
        fixed_pairs=[],
    )
    with patch.object(
        software, "score_capture", side_effect=AssertionError("barrier not passed")
    ):
        with pytest.raises(ArithmeticError, match="mismatch"):
            software.exercise(tmp_path / "own.json", saved, fixture, Deadline(30))
    assert len(saved["captures"]) == 144
    assert saved["rows"] == []
    assert saved["fixed_matches"] == []
    assert len(list((tmp_path / "scratch/captures").glob("*.gz"))) == 144


@pytest.mark.parametrize(
    "kind",
    [
        "profile_hash",
        "capture_hash",
        "source",
        "missing_mass",
        "duplicate_capture",
        "missing_fixed",
        "fixed_value",
        "pair_gap",
    ],
)
def test_archive_lineage_and_metric_corruption_rejected(
    tmp_path: Path, kind: str
) -> None:
    saved, fixture, path = exercise(tmp_path)
    bad = copy.deepcopy(saved)
    if kind == "profile_hash":
        bad["rows"][0]["receipt"]["policy_sha256"] = "f" * 64
    elif kind == "capture_hash":
        bad["rows"][0]["capture_sha256"] = "f" * 64
    elif kind == "source":
        bad["captures"][0]["source_sha256"] = "f" * 64
    elif kind == "missing_mass":
        bad["masses"].pop()
    elif kind == "duplicate_capture":
        bad["captures"][-1] = copy.deepcopy(bad["captures"][0])
    elif kind == "missing_fixed":
        bad["fixed_matches"].pop()
    elif kind == "fixed_value":
        bad["fixed_matches"][0]["baseline_value_chips"] += 1
    else:
        bad["self_pairs"][0]["difference_prefix_minus_batched_chips"][
            "exact_exploitability_chips"
        ] += 1
    with pytest.raises(ArithmeticError):
        replay_archives(
            path,
            bad,
            fixture.manifest,
            fixture.expected,
            lambda _: toy_context(),
            fixture.fixed,
            fixture.right,
            fixture.right_fixed,
            Deadline(30),
        )


def test_pre_input_failure_persists_without_training(tmp_path: Path) -> None:
    path = tmp_path / "own.json"
    with patch.object(run, "source", side_effect=OSError("missing source")):
        with pytest.raises(OSError):
            run.run(tmp_path, path)
    saved = json.loads(path.read_text())
    assert saved["status"] == "incomplete"
    assert saved["training_performed"] is False
    assert saved["completed_captures"] == 0
    assert saved["failure"]["type"] == "OSError"


def test_real_admission_stays_closed_even_if_a_file_is_named_admission(
    tmp_path: Path,
) -> None:
    (tmp_path / "admission.json").write_text('{"admitted": true}')
    with pytest.raises(ArithmeticError, match="blocked"):
        require_admission(tmp_path, "a" * 64)
