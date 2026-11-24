"""Admission rejects missing, duplicate and over-cap fixed profiles."""

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_work_budget.forecast import forecast  # noqa: E402
from known_turn_work_budget.plan import PROFILE_WORK, paths  # noqa: E402


def complete_profile() -> dict[str, Any]:
    """Construct fictional timing records for the exact registered grid."""
    rows = [
        dict(
            index=index,
            repeat=index // 4,
            path=dict(
                index=paths()[index % 4].index,
                game=paths()[index % 4].game,
                arm=paths()[index % 4].arm,
                seed=0,
            ),
            captures=2,
            final_work=PROFILE_WORK,
            whole_path_seconds=2.0,
            worker_peak_rss_bytes=100_000_000,
        )
        for index in range(12)
    ]
    return dict(
        status="completed",
        worker_count=2,
        assignments=[[0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11]],
        seconds=30.0,
        workers=[
            dict(
                exitcode=0,
                messages=[
                    dict(
                        kind="done",
                        summary=dict(summaries=[rows[index] for index in group]),
                    )
                ],
            )
            for group in ([0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11])
        ],
    )


def test_forecast_uses_slowest_repeat_per_path() -> None:
    record = complete_profile()
    target = record["workers"][1]["messages"][0]["summary"]["summaries"][2]
    target["whole_path_seconds"] = 4.0
    decision = forecast(record)
    assert decision["per_path_maxima"][1]["maximum_seconds"] == 160.0
    assert decision["fixed_worker_sums_seconds"] == [160.0, 240.0]
    assert decision["strict_bound_seconds"] == 2160.0
    assert decision["status"] == "admitted"


@pytest.mark.parametrize("change", ["missing", "duplicate", "memory", "cap", "binding"])
def test_forecast_rejects_incomplete_or_changed_profile(change: str) -> None:
    record = deepcopy(complete_profile())
    rows = record["workers"][0]["messages"][0]["summary"]["summaries"]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[0]["index"] = rows[1]["index"]
    elif change == "memory":
        rows[0]["worker_peak_rss_bytes"] = 1_500_000_001
    elif change == "cap":
        record["seconds"] = 900
    else:
        rows[0]["path"]["seed"] = 1
    with pytest.raises(ArithmeticError):
        forecast(record)


def test_forecast_can_reject_conservative_bound() -> None:
    record = complete_profile()
    for worker in record["workers"]:
        for row in worker["messages"][0]["summary"]["summaries"]:
            row["whole_path_seconds"] = 30.0
    assert forecast(record)["status"] == "rejected"
