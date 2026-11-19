"""Predeclared whole-path forecast arithmetic and complete-grid rejection."""

from copy import deepcopy
from typing import Any

import pytest

from poker_ai.evaluation.river_strength_forecast import forecast
from poker_ai.evaluation.river_strength_learning import paths


def record(seconds: float) -> dict[str, Any]:
    workers = []
    for slot in range(3):
        rows = []
        for index in range(slot, 36, 3):
            spec = paths()[index % 12]
            rows.append(
                dict(
                    index=index,
                    repeat=index // 12,
                    path=dict(
                        index=spec.index,
                        game=spec.game,
                        seed=spec.seed,
                        arm=spec.arm,
                    ),
                    captures=3,
                    final_work=100_000,
                    whole_path_seconds=seconds,
                )
            )
        workers.append(
            dict(exitcode=0, messages=[dict(kind="done", summary=dict(summaries=rows))])
        )
    return dict(
        status="completed",
        worker_count=3,
        assignments=[list(range(slot, 36, 3)) for slot in range(3)],
        seconds=100.0,
        workers=workers,
    )


def test_conservative_forecast_uses_all_three_repeats_and_worker_sums() -> None:
    saved = record(1.0)
    result = forecast(saved)
    assert result["fixed_worker_sums_seconds"] == [400.0] * 3
    assert result["strict_bound_seconds"] == 2800.0
    assert result["status"] == "admitted"
    changed = deepcopy(saved)
    changed["workers"][0]["messages"][0]["summary"]["summaries"][0][
        "whole_path_seconds"
    ] = 2.0
    result = forecast(changed)
    assert result["fixed_worker_sums_seconds"] == [500.0, 400.0, 400.0]
    assert result["strict_bound_seconds"] == 3200.0
    assert forecast(record(10.0))["status"] == "rejected"


def test_forecast_rejects_missing_path_duplicate_and_budget_drift() -> None:
    saved = record(1.0)
    saved["workers"][0]["messages"][0]["summary"]["summaries"].pop()
    with pytest.raises(ArithmeticError, match="grid incomplete"):
        forecast(saved)
    saved = record(1.0)
    saved["workers"][0]["messages"][0]["summary"]["summaries"][0]["final_work"] = 99_999
    with pytest.raises(ArithmeticError, match="source/work/timing"):
        forecast(saved)
    saved = record(1.0)
    saved["seconds"] = 900.0
    with pytest.raises(ArithmeticError, match="capped"):
        forecast(saved)
