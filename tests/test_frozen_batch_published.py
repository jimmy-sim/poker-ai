"""Audit the committed software proof and complete failed timing gate offline."""

import json
from pathlib import Path
from unittest.mock import patch

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation import frozen_batch_protocol as protocol
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.solver_validation.reference import Reference

ROOT = Path(__file__).resolve().parents[1]


def test_published_software_and_observed_code_receipts_replay() -> None:
    config = inputs.config_inputs(ROOT)
    saved = json.loads((ROOT / protocol.SOFTWARE).read_text())
    protocol.validate_correctness(ROOT, saved, config)
    checked = protocol.require_code_checks(ROOT, config, clean=False)
    assert checked["checked_commit"] == "48c0960579db72a419835c1087a0e06440f7b897"
    assert checked["ci_run"] == 42606554182
    assert saved["software"]["replay"]["maximum_error_chips"] == 0


def test_published_all216_prefix_timings_replay_failure_without_training() -> None:
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("no replay training"),
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("no native construction")
        ),
    ):
        saved = protocol.read_profile(ROOT, ROOT / protocol.TIMING)
    forecast = saved["forecast"]
    assert len(saved["rows"]) == 216 and forecast["paths"] == 72
    assert forecast["repeated_B1_readout_prefix_checks"] == 144
    assert forecast["guarded_own_seconds"] == 7201.492438541833
    assert forecast["decision"] == "exceeds_cap_stop_before_long_learning"
    assert forecast["strength_scores_measured"] is False
    assert not (ROOT / protocol.ADMITTED).exists()
