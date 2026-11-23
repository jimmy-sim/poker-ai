"""Fictional fixed-grid admission and classification boundary checks."""

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from turn_exact_transfer.forecast import forecast  # noqa: E402
from turn_exact_transfer.learning import (  # noqa: E402
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    paths,
)
from turn_exact_transfer.report import decision  # noqa: E402


def profile(seconds_per_path: float) -> dict[str, Any]:
    """Build all 24 complete fictional rows with fixed worker assignment."""
    workers = []
    for slot in range(3):
        summaries = []
        for index in range(slot, 24, 3):
            spec = paths()[index % 8]
            summaries.append(
                dict(
                    index=index,
                    repeat=index // 8,
                    path=dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0),
                    captures=2,
                    final_work=1_000_000,
                    whole_path_seconds=seconds_per_path,
                )
            )
        workers.append(
            dict(
                exitcode=0,
                messages=[dict(kind="done", summary=dict(summaries=summaries))],
            )
        )
    return dict(
        status="completed",
        worker_count=3,
        assignments=[list(range(slot, 24, 3)) for slot in range(3)],
        seconds=100.0,
        workers=workers,
    )


def test_strict_conservative_admission_and_grid() -> None:
    admitted = forecast(profile(10.0))
    assert admitted["status"] == "admitted"
    assert admitted["T_seconds"] == 300.0
    assert admitted["strict_bound_seconds"] == 2400.0
    equality = forecast(profile(50.0))
    assert equality["strict_bound_seconds"] == 7200.0
    assert equality["status"] == "rejected"
    broken = profile(10.0)
    broken["workers"][0]["messages"][0]["summary"]["summaries"].pop()
    with pytest.raises(ArithmeticError, match="grid incomplete"):
        forecast(broken)


def cases(
    control: tuple[float, ...], candidate: tuple[float, ...]
) -> list[dict[str, Any]]:
    rows = []
    for game, old, new in zip(GAMES, control, candidate, strict=True):
        for arm, value in ((CONTROL, old), (CANDIDATE, new)):
            rows.append(
                dict(
                    game=game,
                    arm=arm,
                    seed=0,
                    work_label=LABELS[-1],
                    readout="linear_average",
                    exploitability_fraction_initial_pot=value,
                    whole_coverage=1.0,
                    recall_violations=0,
                )
            )
    return rows


def test_fixed_strength_decision_boundaries() -> None:
    control = (0.008, 0.007, 0.007, 0.007)
    assert (
        decision(cases(control, (0.006, 0.005, 0.007, 0.007)))["classification"]
        == "positive"
    )
    assert (
        decision(cases(control, (0.008, 0.007, 0.007, 0.007)))["classification"]
        == "inconclusive"
    )
    assert (
        decision(cases(control, (0.006, 0.011, 0.007, 0.007)))["classification"]
        == "negative"
    )
    assert (
        decision(cases(control, (0.006, 0.005, 0.007, 0.0081)))["classification"]
        == "negative"
    )
