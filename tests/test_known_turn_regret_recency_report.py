"""Frozen two-game acceptance gates and complete matched-work grid."""

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_regret_recency.plan import ARM, GAMES, LABELS, READOUTS  # noqa: E402
from known_turn_regret_recency.report import (  # noqa: E402
    CONTROL,
    contrasts,
    decision,
)


def cases(wet: float, dry: float) -> list[dict[str, Any]]:
    """Synthetic 24-policy grid without scoring either known game."""
    result = []
    for game, candidate in zip(GAMES, (wet, dry), strict=True):
        for arm in (CONTROL, ARM):
            for work in LABELS:
                for readout in READOUTS:
                    result.append(
                        dict(
                            game=game,
                            arm=arm,
                            seed=0,
                            work_label=work,
                            actual_node_work=work,
                            readout=readout,
                            exploitability_fraction_initial_pot=(
                                candidate if arm == ARM else 0.008
                            ),
                            whole_coverage=1.0,
                            recall_violations=0,
                        )
                    )
    return result


def test_frozen_positive_negative_and_inconclusive() -> None:
    assert decision(cases(0.006, 0.008))["classification"] == "positive"
    assert decision(cases(0.02, 0.008))["classification"] == "negative"
    assert decision(cases(0.009, 0.008))["classification"] == "inconclusive"
    assert decision(cases(0.006, 0.0091))["classification"] == "negative"
    assert decision(cases(0.006, 0.009))["classification"] == "positive"
    failed_coverage = cases(0.006, 0.008)
    failed_coverage[-1]["whole_coverage"] = 0.94
    assert decision(failed_coverage)["classification"] == "negative"


def test_grid_rejects_unmatched_work_and_missing_cases() -> None:
    grid = cases(0.006, 0.008)
    assert len(contrasts(grid)) == 12
    grid[-1]["actual_node_work"] += 1
    with pytest.raises(ArithmeticError, match="matched work"):
        contrasts(grid)
    with pytest.raises(ArithmeticError, match="24 fixed"):
        decision(grid[:-1])
