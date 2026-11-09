"""Actual published archives, own/public observation and constructor-free browsing."""

import hashlib
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation import batch_strategy_viewer as viewer
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.solver_validation.reference import Reference

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def comparison() -> viewer.Comparison:
    choice = viewer.Selection(
        "dev_medium_oop",
        "texture_range_q8_b8",
        "signed",
        20261301,
        10_000_000,
        4,
        "current",
    )
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("cannot train")
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("cannot construct solver")
        ),
    ):
        return viewer.load(ROOT, choice, replace(choice, readout="linear_average"))


def test_actual_selected_bytes_match_both_immutable_source_hashes(
    comparison: viewer.Comparison,
) -> None:
    for policy, row in (
        (comparison.left_policy, comparison.left),
        (comparison.right_policy, comparison.right),
    ):
        assert (
            hashlib.sha256(np.asarray(policy, dtype="<f8").tobytes()).hexdigest()
            == row["receipt"]["policy_sha256"]
        )
        comparison.context.partition.validate_policy(policy)
    assert comparison.left["work_label"] == comparison.right["work_label"]
    assert comparison.left["path_index"] == comparison.right["path_index"]
    assert comparison.left["iteration"] == comparison.right["iteration"]


def test_actual_representative_is_own_and_public_only(
    comparison: viewer.Comparison,
) -> None:
    for seat in (0, 1):
        info, difference = comparison.rows(seat)[0]
        view = viewer.example(comparison.context, info, seat)
        assert set(view) == {
            "hole",
            "board",
            "street",
            "pot",
            "actions",
            "exact_members",
        }
        assert len(view["hole"]) == 2 and len(view["board"]) in (4, 5)
        assert view["exact_members"] >= 1
        assert 0 <= difference <= 2 + 1e-12
        assert len(view["actions"]) == len(comparison.context.partition.actions[info])
        with pytest.raises(ValueError, match="other seat"):
            viewer.example(comparison.context, info, 1 - seat)
        with pytest.raises(ValueError):
            viewer.example(comparison.context, True, seat)
        text = viewer.display(comparison, seat, 1)
        assert "not EV loss" in text and "one example" in text
        assert "current" in text and "linear_average" in text


def test_actual_self_comparison_and_scripted_navigation(
    comparison: viewer.Comparison,
) -> None:
    same = replace(
        comparison,
        right=comparison.left,
        right_policy=comparison.left_policy,
        right_request=comparison.left_request,
    )
    assert all(value == 0 for _, value in same.rows(0))
    commands = iter(["n", "p", "q"])
    output: list[str] = []
    viewer.browse(comparison, 0, 1, read=lambda _: next(commands), write=output.append)
    assert len(output) == 3
    assert "rank 1/" in output[0] and "rank 2/" in output[1]
    assert output[0] == output[2]
