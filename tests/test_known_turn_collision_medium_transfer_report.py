"""Fixed four-input decision arithmetic without training or selecting inputs."""

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_collision_medium_transfer.plan import (  # noqa: E402
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    READOUTS,
)
from known_turn_collision_medium_transfer.report import decision, paired  # noqa: E402


def cases() -> list[dict[str, Any]]:
    """Construct 48 independent fictional matched-work policy scores."""
    rows = []
    for game in GAMES:
        for arm in (CONTROL, CANDIDATE):
            for work in LABELS:
                for readout in READOUTS:
                    rows.append(
                        dict(
                            game=game,
                            arm=arm,
                            seed=0,
                            work_label=work,
                            readout=readout,
                            actual_node_work=work + 100,
                            exploitability_fraction_initial_pot=(
                                0.009 if arm == CONTROL else 0.007
                            ),
                            whole_coverage=0.97,
                            recall_violations=0,
                        )
                    )
    return rows


def test_positive_requires_absolute_and_both_textures() -> None:
    rows = cases()
    assert decision(rows)["classification"] == "positive"
    contrasts = paired(rows)
    assert len(contrasts) == 24
    assert all(
        row["candidate_minus_control"] == pytest.approx(-0.002) for row in contrasts
    )


def test_negative_gate_keeps_unfavorable_case() -> None:
    rows = cases()
    target = next(
        row
        for row in rows
        if row["game"] == GAMES[1]
        and row["arm"] == CANDIDATE
        and row["work_label"] == LABELS[-1]
        and row["readout"] == "linear_average"
    )
    target["exploitability_fraction_initial_pot"] = 0.01004401976136313
    result = decision(rows)
    assert result["classification"] == "negative"
    assert result["by_game"][GAMES[1]]["candidate_absolute_pass"] is False


def test_inconclusive_and_mismatched_work() -> None:
    rows = cases()
    for row in rows:
        if row["game"] in GAMES[:2] and row["arm"] == CANDIDATE:
            row["exploitability_fraction_initial_pot"] = 0.0085
    assert decision(rows)["classification"] == "inconclusive"
    changed = deepcopy(rows)
    changed[0]["actual_node_work"] += 1
    with pytest.raises(ArithmeticError, match="matched charged work"):
        paired(changed)
