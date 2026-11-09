"""Published tiny archive replays independently without training or native setup."""

import json
from pathlib import Path
from unittest.mock import patch

from poker_ai.evaluation import prefix_capture_software as software
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.reference import Reference

ROOT = Path(__file__).resolve().parents[1]


def test_published_tiny_source_archives_and_independent_replay() -> None:
    path = ROOT / "results/matched-prefix-capture/own.json"
    saved = json.loads(path.read_text())
    checks = json.loads(path.with_name("code-checks.json").read_text())
    reproduced = json.loads(path.with_name("replay-312.json").read_text())
    check_source(ROOT, checks["source"])
    assert saved["source_sha256"] == checks["source_sha256"]
    assert saved["source"]["dirty"] is False
    assert checks["holdem_run_admitted"] is False
    assert reproduced["own_sha256"] == digest(path)
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("no native construction")
        ),
    ):
        proof = software.read(ROOT, path)
    software.compare_proofs(proof, reproduced["proof"])
    assert proof["profiles"] == 144 and proof["raw_ledgers"] == 96
    assert proof["full_step_checks"] == 384 and proof["source_work_checks"] == 72
    assert proof["maximum_error_fixture_chips"] <= 1e-12
    assert proof["poker_training_performed"] is False
    assert proof["long_run_admitted"] is False
