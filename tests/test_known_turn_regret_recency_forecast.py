"""Synthetic strict admission and immutable known-input guard checks."""

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_regret_recency.forecast import forecast  # noqa: E402
from known_turn_regret_recency.plan import contract, paths  # noqa: E402
from study_known_turn_regret_recency import verify_work  # noqa: E402


def synthetic_profile(wet_seconds: float, dry_seconds: float) -> dict[str, Any]:
    """Six fixed fictional timing cells with exactly the planned assignment."""
    specs = paths()
    workers = []
    for slot in (0, 1):
        summaries = []
        for repeat in (0, 1, 2):
            index = 2 * repeat + slot
            spec = specs[slot]
            summaries.append(
                dict(
                    index=index,
                    repeat=repeat,
                    path=dict(
                        index=spec.index,
                        game=spec.game,
                        arm=spec.arm,
                        seed=spec.seed,
                    ),
                    captures=2,
                    final_work=1_000_000,
                    whole_path_seconds=(wet_seconds if slot == 0 else dry_seconds),
                    worker_peak_rss_bytes=1000,
                )
            )
        done = dict(kind="done", summary=dict(summaries=summaries))
        workers.append(dict(exitcode=0, messages=[done]))
    return dict(
        status="completed",
        worker_count=2,
        assignments=[[0, 2, 4], [1, 3, 5]],
        seconds=800.0,
        workers=workers,
    )


def test_published_known_controls_and_grid_are_pinned() -> None:
    plan = contract(ROOT)
    assert [row["game"] for row in plan["inputs"]] == [spec.game for spec in paths()]
    assert plan["work_labels"] == [100000, 1000000, 10000000]
    assert plan["budgets_seconds"]["whole_own"] == 7200


def test_strict_forecast_uses_slowest_fixed_repeat_and_rejects_equality() -> None:
    admitted = forecast(synthetic_profile(3.0, 2.0))
    assert admitted["status"] == "admitted"
    assert admitted["T_seconds"] == 30.0
    assert admitted["strict_bound_seconds"] == 1320.0
    equality = forecast(synthetic_profile(150.0, 2.0))
    assert equality["strict_bound_seconds"] == 7200.0
    assert equality["status"] == "rejected"


def test_forecast_rejects_missing_fixed_cell() -> None:
    record = synthetic_profile(3.0, 2.0)
    record["workers"][0]["messages"][0]["summary"]["summaries"].pop()
    with pytest.raises(ArithmeticError, match="grid incomplete"):
        forecast(record)


def test_candidate_work_must_match_immutable_control() -> None:
    plan = contract(ROOT)
    spec = paths()[0]
    labels = (100000, 1000000, 10000000)
    work = plan["inputs"][0]["control_actual_node_work"]
    saved = dict(
        path=dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0),
        labels=list(labels),
        final_work=work[-1],
        captures=[
            dict(metadata=dict(work_label=label, total_work=actual))
            for label, actual in zip(labels, work, strict=True)
            for _ in range(2)
        ],
    )
    verify_work(saved, spec, labels, plan)
    saved["captures"][0]["metadata"]["total_work"] += 1
    with pytest.raises(ArithmeticError, match="charged-work identity"):
        verify_work(saved, spec, labels, plan)
