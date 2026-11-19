"""Comparison-only wrapper retains all tiny own scalars without solver targets."""

from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.evaluation.river_strength_capture import capture_path
from poker_ai.evaluation.river_strength_learning import PathSpec
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation import river_strength_native as native


def test_native_wrapper_uses_published_own_rows_and_retains_each(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scoring = software_context(0).scoring["coarse"]
    spec = PathSpec(0, "FICTIONAL_SIGNAL_GAME", 20261301, "coarse")
    folder = tmp_path / "toy"
    capture_path(scoring, spec, folder, "a" * 64, (80,), Deadline(10))
    inspected: list[dict[str, Any]] = []

    def scalar_check(
        context: object, refs: object, detail: dict[str, Any]
    ) -> dict[str, float]:
        assert context is scoring
        assert len(detail["replies"]) == 2
        assert all(len(group) == 3 for group in detail["replies"])
        return {"maximum_error_chips": 0.0}

    monkeypatch.setattr(native, "compare", scalar_check)
    rows = native.audit_path(
        scoring, folder, spec, (None, None), Deadline(10), inspected.append
    )  # type: ignore[arg-type]
    assert len(rows) == 3 and inspected == rows
    assert {row["readout"] for row in rows} == {
        "current",
        "uniform_average",
        "linear_average",
    }
    with pytest.raises(ArithmeticError, match="identity"):
        native.audit_path(
            scoring,
            folder,
            PathSpec(1, spec.game, spec.seed, spec.arm),
            (None, None),
            Deadline(10),
            inspected.append,  # type: ignore[arg-type]
        )
