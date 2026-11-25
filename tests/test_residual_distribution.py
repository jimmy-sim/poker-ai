"""Fictional arithmetic and fixed-grid guards for read-only row diagnosis."""

from copy import deepcopy
from typing import Any

import pytest

from poker_ai.evaluation.residual_distribution import analyze_report, summarize_street


def test_signed_masses_ties_and_zero_denominators() -> None:
    control = [0.0] * 24
    candidate = [1.0] * 24
    observed = summarize_street(
        control,
        candidate,
        [0, 2],
        top_k=10,
        concentration_share=0.5,
        nonnegative_slack=1e-12,
    )
    assert observed["candidate_top_indices"] == list(range(10))
    assert observed["worsening_top_indices"] == list(range(10))
    assert observed["improvement_top_indices"] == list(range(10))
    assert observed["candidate_top_one_share"] == pytest.approx(1 / 24)
    assert observed["candidate_top_ten_share"] == pytest.approx(10 / 24)
    assert observed["known_candidate_share"] == pytest.approx(2 / 24)
    assert observed["candidate_location"] == "distributed"
    assert observed["worsening_location"] == "distributed"
    assert observed["improvement_location"] == "none"
    assert observed["improvement_top_ten_share"] is None
    reversed_result = summarize_street(
        candidate,
        control,
        [],
        top_k=10,
        concentration_share=0.5,
        nonnegative_slack=1e-12,
    )
    assert reversed_result["candidate_location"] == "none"
    assert reversed_result["worsening_location"] == "none"
    assert reversed_result["improvement_location"] == "distributed"
    assert reversed_result["net_change_chips"] == -24


def test_positive_worsening_and_negative_offset_reconcile() -> None:
    observed = summarize_street(
        [0.2, 0.1, 0.0, 0.3],
        [0.4, 0.0, 0.1, 0.1],
        [0, 1],
        top_k=2,
        concentration_share=0.5,
        nonnegative_slack=1e-12,
    )
    assert observed["positive_worsening_chips"] == pytest.approx(0.3)
    assert observed["negative_offset_chips"] == pytest.approx(0.3)
    assert observed["net_change_chips"] == pytest.approx(0.0)
    assert observed["worsening_top_indices"] == [0, 2]
    assert observed["improvement_top_indices"] == [3, 1]
    assert observed["worsening_location"] == "concentrated"
    assert observed["improvement_location"] == "concentrated"


@pytest.mark.parametrize(
    ("control", "candidate", "known"),
    [
        ([0.0], [0.0, 0.0], []),
        ([0.0], [float("nan")], []),
        ([0.0], [-0.1], []),
        ([0.0], [0.0], [0, 0]),
        ([0.0], [0.0], [1]),
    ],
)
def test_reject_invalid_alignment(
    control: list[float], candidate: list[float], known: list[int]
) -> None:
    with pytest.raises(ArithmeticError, match="invalid aligned"):
        summarize_street(
            control,
            candidate,
            known,
            top_k=1,
            concentration_share=0.5,
            nonnegative_slack=1e-12,
        )


def fictional_grid() -> tuple[dict[str, Any], dict[str, Any]]:
    """Make four tiny fictional games with eight fixed final policies."""
    games = ["dry_a", "wet_a", "dry_b", "wet_b"]
    contract: dict[str, Any] = {
        "games": games,
        "control": "q8",
        "candidate": "exact",
        "work_label": 40_000_000,
        "readout": "linear_average",
        "actual_work": 40_205_562,
        "seed_metadata": 0,
        "initial_pot_chips": 36,
        "cases": 8,
        "exact_rows_per_street_vector": 12,
        "top_k": 10,
        "concentration_share": 0.5,
        "arithmetic_tolerance_chips": 1e-9,
        "nonnegative_slack_chips": 1e-12,
        "whole_coverage_min": 0.95,
        "absolute_fraction_max": 0.01,
        "worst_fraction_max": 0.025,
        "recall_violations_max": 0,
        "paired_improvement_fraction_max": -0.001,
        "paired_remaining_fraction_max": 0.001,
        "report_head": "fictional-head",
        "source_fingerprint": "fictional-source",
        "prior_result": "negative",
    }
    cases: list[dict[str, Any]] = [
        {"work_label": 10_000_000, "readout": "current"} for _ in range(40)
    ]
    primary: dict[str, Any] = {}
    diagnostics: list[dict[str, Any]] = []
    for game in games:
        for arm in ("q8", "exact"):
            turn = [0.0] * 12
            river = [0.0] * 12
            turn[0] = 0.2 if arm == "q8" else 0.3
            river[6] = 0.5 if arm == "q8" else 0.1
            chips = sum(turn) + sum(river)
            cases.append(
                {
                    "game": game,
                    "arm": arm,
                    "work_label": 40_000_000,
                    "readout": "linear_average",
                    "seed": 0,
                    "actual_node_work": 40_205_562,
                    "recall_violations": 0,
                    "whole_coverage": 1.0,
                    "policy_sha256": "a" * 64,
                    "native_maximum_error_chips": 0.0,
                    "exploitability_chips": chips,
                    "exploitability_fraction_initial_pot": chips / 36,
                    "turn_contribution_chips": sum(turn),
                    "river_contribution_chips": sum(river),
                    "turn_row_contributions_chips": turn,
                    "river_row_contributions_chips": river,
                }
            )
        primary[game] = {
            "control": 0.7 / 36,
            "candidate": 0.4 / 36,
            "candidate_minus_control": -0.3 / 36,
            "candidate_absolute_pass": False,
            "candidate_worst_fraction_initial_pot": 0.4 / 36,
        }
        for street in ("TURN", "RIVER"):
            diagnostics.extend(
                {"game": game, "street": street, "exact_info": i} for i in range(4)
            )
    report = {
        "head": "fictional-head",
        "source_fingerprint": "fictional-source",
        "primary": {"classification": "negative", "by_game": primary},
        "cases": cases,
        "diagnostics": diagnostics,
    }
    return report, contract


def test_fixed_grid_and_all_row_accounting() -> None:
    report, contract = fictional_grid()
    result = analyze_report(report, contract)
    assert result["prior_strength_classification"] == "negative"
    assert len(result["cases"]) == 8
    assert result["cases"][0]["game"] == "dry_a"
    assert result["cases"][0]["street"] == "TURN"
    assert result["cases"][0]["net_change_chips"] == pytest.approx(0.1)
    assert result["cases"][1]["net_change_chips"] == pytest.approx(-0.4)


def test_reject_changed_work_or_street_sum() -> None:
    report, contract = fictional_grid()
    wrong_work = deepcopy(report)
    wrong_work["cases"][-1]["actual_node_work"] += 1
    with pytest.raises(ArithmeticError, match="metadata"):
        analyze_report(wrong_work, contract)
    wrong_sum = deepcopy(report)
    wrong_sum["cases"][-1]["river_row_contributions_chips"][6] += 0.1
    with pytest.raises(ArithmeticError, match="street vector"):
        analyze_report(wrong_sum, contract)
