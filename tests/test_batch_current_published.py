"""Published scalar/archive/report proofs; full mathematical replay has a CLI."""

import json
from pathlib import Path
from typing import cast
from unittest.mock import patch

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.batch_current_protocol import require_checks
from poker_ai.evaluation.batch_current_report import write_report
from poker_ai.evaluation.batch_current_run import validate_replay
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.batch_currents import read
from poker_ai.solver_validation.reference import Reference

ROOT = Path(__file__).resolve().parents[1]
OWN = ROOT / "results/batch-current-diagnosis/own.json"


def test_published_current_receipts_archive_and_all_native_targets() -> None:
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("no native construction")
        ),
    ):
        checks = require_checks(ROOT, clean=False)
        own = json.loads(OWN.read_text())
        admission = json.loads((ROOT / inputs.ADMITTED).read_text())
        assert own["source_sha256"] == checks["source_sha256"]
        assert admission["source_sha256"] == checks["source_sha256"]
        assert len(admission["input_sha256"]) == 7
        for name, expected in admission["input_sha256"].items():
            assert digest(ROOT / name) == expected
        assert own["completed_current_profiles"] == 216
        assert own["completed_fixed_targets"] == 1728
        assert digest(OWN.with_name(own["details_file"])) == own["details_sha256"]
        validate_replay(own["own_replay"])
        native = read(
            ROOT, ROOT / "results/batch-current-diagnosis/native.json", own, OWN
        )
        assert native["maximum_error_chips"] <= 1e-9
        assert native["current_profiles"] == 216
        assert native["fixed_targets"] == 1728


def test_six_published_numeric_files_reproduce_from_metadata(tmp_path: Path) -> None:
    own = json.loads(OWN.read_text())
    source_path = ROOT / own["config"]["source_own"]
    source = json.loads(source_path.read_text())
    # Reports consume scalar metadata only. This deliberately avoids loading or
    # replaying game trees; the separate full reader verified all216+1728 values.
    metadata = inputs.Sources(source_path, source, cast(HistoryInputs, None), {})
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("no native construction")
        ),
    ):
        result = write_report(ROOT, own, metadata, tmp_path, plots=False)
    assert result["numerical_sha256"] == own["report"]["numerical_sha256"]
    assert len(result["numerical_sha256"]) == 6
    assert result["current_profiles"] == 216
    assert result["reused_average_profiles"] == 432
    assert result["self_pairs"] == 432
    assert result["fixed_targets"] == 1728
    assert result["paired_fixed_targets"] == 1152
