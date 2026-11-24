"""Fictional paired cases exercise the prospectively frozen decision rule."""

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_work_budget.plan import CANDIDATE, CONTROL, GAMES, LABELS, READOUTS  # noqa: E402
from known_turn_work_budget.report import decision, paired  # noqa: E402


def cases() -> list[dict[str, Any]]:
    """Use arbitrary fake scores, not poker observations."""
    result = []
    for game in GAMES:
        for work in LABELS:
            for readout in READOUTS:
                for arm in (CONTROL, CANDIDATE):
                    value = (
                        0.02
                        if arm == CONTROL
                        else {LABELS[0]: 0.014, LABELS[1]: 0.009, LABELS[2]: 0.007}[
                            work
                        ]
                    )
                    result.append(
                        dict(
                            game=game,
                            work_label=work,
                            readout=readout,
                            arm=arm,
                            seed=0,
                            actual_node_work=work + 10,
                            exploitability_fraction_initial_pot=value,
                            whole_coverage=0.97,
                            recall_violations=0,
                        )
                    )
    return result


def test_fixed_positive_and_wet_budget_readout() -> None:
    rows = cases()
    assert len(paired(rows)) == 12
    result = decision(rows)
    assert result["classification"] == "positive"
    assert result["wet_trend"] == "continuing decline"


def test_failure_is_negative_and_matched_work_mismatch_rejected() -> None:
    rows = cases()
    row = next(
        item
        for item in rows
        if item["game"] == GAMES[0]
        and item["work_label"] == LABELS[-1]
        and item["readout"] == "linear_average"
        and item["arm"] == CANDIDATE
    )
    row["whole_coverage"] = 0.94
    assert decision(rows)["classification"] == "negative"
    row["actual_node_work"] += 1
    with pytest.raises(ArithmeticError):
        paired(rows)
