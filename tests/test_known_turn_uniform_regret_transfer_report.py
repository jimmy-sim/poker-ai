"""Fixed-grid strength classification without reading new policy outcomes."""

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_uniform_regret_transfer.plan import (  # noqa: E402
    ARM,
    GAMES,
    LABELS,
    READOUTS,
    contract,
)
from known_turn_uniform_regret_transfer.report import (  # noqa: E402
    PRIOR_ARM,
    decision,
    paired,
)


def grid(candidate: tuple[float, ...]) -> list[dict[str, Any]]:
    """Make fictional matched cases at the frozen work/readout crossings."""
    rows = []
    for index, game in enumerate(GAMES):
        for work in LABELS:
            for readout in READOUTS:
                for arm, value in ((PRIOR_ARM, 0.01), (ARM, candidate[index])):
                    rows.append(
                        dict(
                            game=game,
                            arm=arm,
                            work_label=work,
                            readout=readout,
                            actual_node_work={
                                LABELS[0]: 10_117_956,
                                LABELS[1]: 20_235_912,
                                LABELS[2]: 40_205_562,
                            }[work],
                            exploitability_fraction_initial_pot=value,
                            whole_coverage=1.0,
                            recall_violations=0,
                        )
                    )
    return rows


def test_fixed_protocol_and_positive_negative_inconclusive_boundaries() -> None:
    assert contract(ROOT)["issue"] == 4
    good = grid((0.008, 0.008, 0.008, 0.01))
    assert decision(good)["classification"] == "positive"
    assert len(paired(good)) == 24
    bad = grid((0.008, 0.008, 0.011, 0.008))
    assert decision(bad)["classification"] == "negative"
    borderline = grid((0.0095, 0.0095, 0.0095, 0.0095))
    assert decision(borderline)["classification"] == "inconclusive"


def test_final_absolute_and_coverage_gates_fail_closed() -> None:
    cases = grid((0.008, 0.008, 0.008, 0.008))
    case = next(
        row
        for row in cases
        if row["arm"] == ARM
        and row["game"] == GAMES[0]
        and row["work_label"] == LABELS[-1]
        and row["readout"] == "linear_average"
    )
    case["whole_coverage"] = 0.949
    assert decision(cases)["classification"] == "negative"
