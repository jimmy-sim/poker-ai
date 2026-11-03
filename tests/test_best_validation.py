"""Calibration coverage and failure detection; synthetic oracles test the harness.

Published validation reports use real Treys, not the synthetic oracle below.
"""

import json
from pathlib import Path

import pytest

from poker_ai.cards import cards_to_mask
from poker_ai.evaluator import HandRank, evaluate_best, evaluate_five
from poker_ai.validation.best_of_five import (
    SampleConfig,
    calibrate_reference,
    compare_samples,
    iter_samples,
    load_configs,
    representative_hands,
    run_validation,
)


@pytest.fixture(scope="module")
def synthetic_scores() -> dict[HandRank, int]:
    ranks = sorted({evaluate_five(cards) for cards in representative_hands()})
    return {rank: len(ranks) - index for index, rank in enumerate(ranks)}


def test_calibration_representatives_are_valid_and_cover_every_rank() -> None:
    cards = tuple(representative_hands())
    assert len(cards) == len(set(cards)) == 7462
    assert all(len(hand) == cards_to_mask(hand).bit_count() == 5 for hand in cards)
    assert len({evaluate_five(hand) for hand in cards}) == 7462


def test_calibration_checks_all_score_classes(
    synthetic_scores: dict[HandRank, int],
) -> None:
    mapping = calibrate_reference(lambda cards: synthetic_scores[evaluate_five(cards)])
    assert mapping == {score: rank for rank, score in synthetic_scores.items()}


def test_calibration_rejects_false_reference_ties() -> None:
    with pytest.raises(ValueError, match="distinguishes hands"):
        calibrate_reference(lambda cards: 1)


def test_calibration_rejects_inverted_reference_order(
    synthetic_scores: dict[HandRank, int],
) -> None:
    with pytest.raises(ValueError, match="ordering"):
        calibrate_reference(lambda cards: 7463 - synthetic_scores[evaluate_five(cards)])


@pytest.mark.parametrize("size", [6, 7])
def test_exact_comparison_accepts_consistent_reference(
    size: int, synthetic_scores: dict[HandRank, int]
) -> None:
    mapping = {score: rank for rank, score in synthetic_scores.items()}
    result = compare_samples(
        SampleConfig(size, 25, 20261103),
        lambda cards: synthetic_scores[evaluate_best(cards)],
        mapping,
    )
    assert result.status == "passed"
    assert result.hands_checked == 25
    assert result.failures == []
    assert sum(result.category_counts.values()) == 25


def test_exact_comparison_records_first_failure(
    synthetic_scores: dict[HandRank, int],
) -> None:
    def deliberately_wrong_score(cards: tuple[int, ...]) -> int:
        return 2 if synthetic_scores[evaluate_best(cards)] == 1 else 1

    result = compare_samples(
        SampleConfig(7, 25, 20261104),
        deliberately_wrong_score,
        {score: rank for rank, score in synthetic_scores.items()},
    )
    assert result.status == "failed"
    assert result.hands_checked == 1
    assert len(result.failures) == 1
    assert result.failures[0]["actual"] != result.failures[0]["expected"]


@pytest.mark.parametrize("size", [6, 7])
def test_sampling_replays_and_has_no_duplicate_cards(size: int) -> None:
    config = SampleConfig(size, 25, 20261103)
    first = tuple(iter_samples(config))
    assert first == tuple(iter_samples(config))
    assert len(first) == 25
    assert all(len(hand) == cards_to_mask(hand).bit_count() == size for hand in first)


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"runs": []},
        {"runs": None},
        {"runs": [{"hand_size": 6, "hands": 10, "seed": 1, "typo": 1}]},
        {"runs": [{"hand_size": 5, "hands": 10, "seed": 1}]},
        {"runs": [{"hand_size": True, "hands": 10, "seed": 1}]},
        {"runs": [{"hand_size": 6, "hands": True, "seed": 1}]},
        {"runs": [{"hand_size": 6, "hands": 0, "seed": 1}]},
        {"runs": [{"hand_size": 6, "hands": 10, "seed": None}]},
        {"runs": [{"hand_size": 6, "hands": 10, "seed": True}]},
        {"runs": [{"hand_size": 6, "hands": 10, "seed": -1}]},
        {"runs": [{"hand_size": 6, "hands": 10, "seed": 1}] * 2},
    ],
)
def test_invalid_configs_fail(tmp_path: Path, data: dict[str, object]) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_configs(path)


def test_load_valid_configs(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {"hand_size": 6, "hands": 10, "seed": 3},
                    {"hand_size": 7, "hands": 10, "seed": 4},
                ]
            }
        )
    )
    assert load_configs(path) == (SampleConfig(6, 10, 3), SampleConfig(7, 10, 4))


def test_empty_validation_plan_cannot_silently_pass() -> None:
    with pytest.raises(ValueError, match="at least one"):
        run_validation((), {})
