"""Fictional full-work proof for both isolated representation labels."""

import sys
from pathlib import Path

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from turn_exact_transfer.capture import capture_path, replay_path  # noqa: E402
from turn_exact_transfer.learning import (  # noqa: E402
    CANDIDATE,
    CONTROL,
    PathSpec,
)


@pytest.mark.parametrize("arm", (CONTROL, CANDIDATE))
def test_fictional_capture_preserves_paired_arm_and_seed(
    tmp_path: Path, arm: str
) -> None:
    scoring = software_context(0).scoring["coarse"]
    path = PathSpec(0 if arm == CONTROL else 1, "FICTIONAL_SIGNAL_GAME", arm)
    folder = tmp_path / arm
    saved = capture_path(scoring, path, folder, "1" * 64, (80, 240, 720), Deadline(180))
    replayed = replay_path(scoring, folder)
    assert replayed == saved
    assert saved["path"] == dict(index=path.index, game=path.game, arm=arm, seed=0)
    assert len(saved["captures"]) == 6
    assert saved["final_work"] >= 720
    assert all(row["metadata"]["arm"] == arm for row in saved["captures"])
    assert all(row["metadata"]["seed"] == 0 for row in saved["captures"])
