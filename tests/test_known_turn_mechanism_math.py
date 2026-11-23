"""Fictional fixed-grid forecast and classification regressions."""

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_mechanism.forecast import forecast  # noqa: E402
from known_turn_mechanism.plan import (  # noqa: E402
    CANDIDATE,
    CONTROL,
    GAME,
    LABELS,
    contract,
    paths,
)
from known_turn_mechanism.report import decision  # noqa: E402


def profile_record(
    seconds_per_path: tuple[float, float] = (10.0, 12.0),
) -> dict[str, Any]:
    """Two fictional paths, three complete repeats each, no poker outcome."""
    workers = []
    for slot, spec in enumerate(paths()):
        rows = [
            dict(
                index=2 * repeat + slot,
                repeat=repeat,
                path=dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0),
                captures=2,
                final_work=1_000_000,
                whole_path_seconds=seconds_per_path[slot] + repeat,
                worker_peak_rss_bytes=100_000_000,
            )
            for repeat in range(3)
        ]
        workers.append(
            dict(exitcode=0, messages=[dict(kind="done", summary=dict(summaries=rows))])
        )
    return dict(
        status="completed",
        worker_count=2,
        assignments=[[0, 2, 4], [1, 3, 5]],
        seconds=40.0,
        workers=workers,
    )


def case(arm: str, score: float, *, coverage: float = 1.0) -> dict[str, Any]:
    return dict(
        game=GAME,
        seed=0,
        arm=arm,
        work_label=LABELS[-1],
        readout="linear_average",
        exploitability_fraction_initial_pot=score,
        whole_coverage=coverage,
        recall_violations=0,
    )


def test_published_contract_and_two_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    plan = contract(root)
    assert (
        plan["spot_sha256"]
        == "b7c74e0de96e9949f8eb0e359d085b4e3281ea3172b9979f8a23f394bb642dea"
    )
    assert [spec.arm for spec in paths()] == [CONTROL, CANDIDATE]
    assert all(spec.seed == 0 for spec in paths())


def test_strict_forecast_keeps_worst_repeat_and_rejects_equality() -> None:
    accepted = forecast(profile_record())
    assert accepted["fixed_worker_sums_seconds"] == [120.0, 140.0]
    assert accepted["strict_bound_seconds"] == 1760.0
    assert accepted["status"] == "admitted"
    equal = forecast(profile_record((148.0, 148.0)))
    assert equal["strict_bound_seconds"] == 7200.0
    assert equal["status"] == "rejected"
    bad = profile_record()
    bad["assignments"] = [[0, 1, 2], [3, 4, 5]]
    with pytest.raises(ArithmeticError, match="profile"):
        forecast(bad)


def test_fixed_strength_gates_do_not_relabel_partial_improvement() -> None:
    assert (
        decision([case(CONTROL, 0.03), case(CANDIDATE, 0.009)])["classification"]
        == "positive"
    )
    partial = decision([case(CONTROL, 0.03), case(CANDIDATE, 0.02)])
    assert partial["candidate_minus_control"] < 0
    assert partial["classification"] == "negative"
    assert (
        decision([case(CONTROL, 0.009), case(CANDIDATE, 0.011)])["classification"]
        == "negative"
    )
    assert (
        decision([case(CONTROL, 0.009), case(CANDIDATE, 0.0085)])["classification"]
        == "inconclusive"
    )
    assert (
        decision([case(CONTROL, 0.03), case(CANDIDATE, 0.009, coverage=0.94)])[
            "classification"
        ]
        == "negative"
    )


def test_fictional_no_collision_representation_is_bijective(tmp_path: Path) -> None:
    """A one-hand-per-seat toy split cannot invent an information collision."""
    import json

    import numpy as np
    from river_strength.representation import build_river_candidate
    from turn_exact_transfer.representation import exact_turn_candidate

    from poker_ai.abstraction.model import CardAbstraction
    from poker_ai.postflop.game import load_spot
    from poker_ai.postflop.tree import SpotTree

    raw = json.loads(
        (
            ROOT / "configs/river-full-broader-spots/full_new_medium_dry_oop.json"
        ).read_bytes()
    )
    raw["name"] = "fictional_no_collision"
    raw["ranges"] = [[seat[0]] for seat in raw["ranges"]]
    fixture = tmp_path / "fictional.json"
    fixture.write_text(json.dumps(raw))
    source = SpotTree.build(load_spot(fixture))
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    control = build_river_candidate(source, model)
    candidate = exact_turn_candidate(source, control)
    assert len(control.keys) == len(candidate.keys)
    assert len(set(int(i) for i in control.exact_to_abstract)) == len(candidate.keys)
    assert control.node_actions == candidate.node_actions
    np.testing.assert_array_equal(control.player, candidate.player)
    np.testing.assert_array_equal(control.terminal_values, candidate.terminal_values)
