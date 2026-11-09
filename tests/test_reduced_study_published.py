"""Published own/native evidence replays data-only; no new learning or solver."""

import json
from pathlib import Path
from unittest.mock import patch

from poker_ai.evaluation.frozen_batch_report import write_report
from poker_ai.evaluation.reduced_study_protocol import require_code_checks
from poker_ai.evaluation.reduced_study_run import read_saved
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.reduced_batches import read
from poker_ai.solver_validation.reference import Reference

ROOT = Path(__file__).resolve().parents[1]


def test_published_complete_evidence_and_archive_bytes_without_constructors() -> None:
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no new learning")
        ),
        patch.object(
            Reference,
            "__init__",
            side_effect=AssertionError("no reference construction"),
        ),
    ):
        checks = require_code_checks(ROOT, clean=False)
        path = ROOT / "results/reduced-batch-study/own.json"
        saved, _ = read_saved(ROOT, path)
        audit = read(
            ROOT, ROOT / "results/reduced-batch-study/native.json", saved, path
        )
    assert saved["source_sha256"] == checks["source_sha256"]
    assert audit["profiles"] == 480 and audit["maximum_error_chips"] <= 1e-9
    assert saved["own_replay"]["maximum_error_chips"] == 0
    for key in ("details", "mass_details", "current_details"):
        assert digest(path.with_name(saved[key + "_file"])) == saved[key + "_sha256"]


def test_published_four_numeric_reports_reproduce_from_receipt(tmp_path: Path) -> None:
    saved = json.loads((ROOT / "results/reduced-batch-study/own.json").read_text())
    report = write_report(ROOT, saved, tmp_path, plots=False)
    assert report["numerical_sha256"] == saved["report"]["numerical_sha256"]
    assert report["mean_rows"] == 192 and report["paired_seed_rows"] == 288
