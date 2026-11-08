"""The frozen-row display does not mistake examples for per-hand action advice."""

from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.controlled_reply_inspect import display, inspect


@pytest.mark.parametrize("target,rank", [(0, 0), (0, -1), (0, True), (True, 1), (2, 1)])
def test_invalid_rank_or_target_fails_before_loading_files(
    target: Any, rank: Any
) -> None:
    with pytest.raises(ValueError):
        inspect(
            Path("/missing"),
            Path("/missing/own.json"),
            game="fixture",
            representation="exact",
            traversal="full",
            seed=None,
            clip="signed",
            average="uniform",
            target=target,
            rank=rank,
        )


def test_display_labels_merged_values_and_only_own_example_cards() -> None:
    row = dict(
        case=dict(
            spot_file="EXPLICIT_SOFTWARE_FIXTURE.json",
            representation="fixture",
            traversal="full",
            regret_rule="signed",
            average_weight="linear",
            seed=None,
        ),
        target=0,
        info=3,
        rank=1,
        total_owned_rows=10,
        audit_status="native audit absent; own-trace view only",
        source_iteration=128,
        source_work=10000001,
        gain_chips=1.5,
        loss_chips=0.1,
        street_losses_chips=dict(TURN=0.2, RIVER=1.3),
        hole=["Ac", "Kd"],
        board=["2s", "3c", "4d", "5h"],
        hand_category="STRAIGHT",
        street="TURN",
        exact_members=3,
        reply_action="call",
        saved_reach_mass=0.5,
        actions=["fold", "call"],
        saved_probabilities=[0.3, 0.7],
        conditional_values_chips=[-18.0, 200.0],
        private_opponent_cards=["Jh", "Jd"],
    )
    text = display(row)
    assert "all compatible histories" in text
    assert "not universal poker advice" in text
    assert "native audit absent" in text
    assert "Ac Kd" in text
    assert "Jh" not in text and "Jd" not in text
    assert "0.300000" in text and "-18.000000" in text
