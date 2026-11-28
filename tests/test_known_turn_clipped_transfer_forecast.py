"""Synthetic complete-grid and rejection checks for conservative admission."""

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_clipped_transfer.forecast import forecast  # noqa: E402
from known_turn_clipped_transfer.plan import PROFILE_WORK, paths  # noqa: E402


def profile() -> dict[str, Any]:
    """Make twelve fictional timing rows in the fixed two-worker order."""
    specs = paths()
    rows = [
        dict(
            index=index,
            repeat=index // 4,
            path=dict(
                index=specs[index % 4].index,
                game=specs[index % 4].game,
                arm=specs[index % 4].arm,
                seed=0,
            ),
            captures=2,
            final_work=PROFILE_WORK,
            whole_path_seconds=2.0,
            worker_peak_rss_bytes=100_000_000,
        )
        for index in range(12)
    ]
    assignments = [list(range(0, 12, 2)), list(range(1, 12, 2))]
    return dict(
        status="completed",
        worker_count=2,
        assignments=assignments,
        seconds=30.0,
        workers=[
            dict(
                exitcode=0,
                messages=[
                    dict(kind="done", summary=dict(summaries=[rows[i] for i in group]))
                ],
            )
            for group in assignments
        ],
    )


def test_forecast_uses_slowest_repeat_per_game_and_strict_bound() -> None:
    record = profile()
    record["workers"][1]["messages"][0]["summary"]["summaries"][2][
        "whole_path_seconds"
    ] = 4.0
    decision = forecast(record)
    assert decision["per_path_maxima"][1]["maximum_seconds"] == 32.0
    assert decision["fixed_worker_sums_seconds"] == [32.0, 48.0]
    assert decision["strict_bound_seconds"] == 1392.0
    assert decision["status"] == "admitted"


@pytest.mark.parametrize("change", ["missing", "duplicate", "memory", "cap", "binding"])
def test_forecast_rejects_bad_profile(change: str) -> None:
    record = deepcopy(profile())
    rows = record["workers"][0]["messages"][0]["summary"]["summaries"]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[0]["index"] = rows[1]["index"]
    elif change == "memory":
        rows[0]["worker_peak_rss_bytes"] = 1_500_000_000
    elif change == "cap":
        record["seconds"] = 900
    else:
        rows[0]["path"]["seed"] = 1
    with pytest.raises(ArithmeticError):
        forecast(record)


def test_forecast_can_reject_unfavorable_conservative_bound() -> None:
    record = profile()
    for worker in record["workers"]:
        for row in worker["messages"][0]["summary"]["summaries"]:
            row["whole_path_seconds"] = 100.0
    assert forecast(record)["status"] == "rejected"
