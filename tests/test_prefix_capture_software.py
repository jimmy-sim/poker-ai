"""Software-only independent utility/sign checks and invalid numeric guard."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation import prefix_capture_software as software
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.prefix_capture_software import metric_error
from poker_ai.evaluation.tiny_policy_math import metrics, terminal_sum


def test_constant_terminal_utility_has_known_value_and_zero_exploitability() -> None:
    original = toy_context().partition
    tree = replace(
        original, terminal_values=np.full_like(original.terminal_values, 2.5)
    )
    policy = tree.legal / tree.legal.sum(axis=1, keepdims=True)
    actual = metrics(tree, policy)
    assert actual["value_player_zero_chips"] == pytest.approx(2.5, abs=1e-14)
    assert actual["exact_exploitability_chips"] == pytest.approx(0.0, abs=1e-14)
    assert terminal_sum(tree, policy, policy, 1) == pytest.approx(-2.5, abs=1e-14)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, None, "0"])
def test_nonfinite_or_non_numeric_metric_cannot_disappear_in_max(bad: Any) -> None:
    with pytest.raises(ArithmeticError, match="invalid tiny score"):
        metric_error(dict(value=bad), dict(value=0.0))


def test_metric_error_keeps_sign_errors_and_exact_self_zero() -> None:
    assert metric_error(dict(value=-2.0), dict(value=2.0)) == 4.0
    assert metric_error(dict(value=2.0), dict(value=2.0)) == 0.0


def test_dirty_source_rejection_is_retained_before_toy_training(tmp_path: Path) -> None:
    output = tmp_path / "own.json"
    with (
        patch.object(
            software,
            "source_provenance",
            return_value=dict(
                dirty=True, sha256={}, git_commit="EXPLICIT_DIRTY_SOURCE_FIXTURE"
            ),
        ),
        patch.object(software, "learner", side_effect=AssertionError("must not train")),
    ):
        with pytest.raises(ArithmeticError, match="clean committed"):
            software.run(tmp_path, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["software_training_attempted"] is False
    assert saved["completed_profiles"] == 0
