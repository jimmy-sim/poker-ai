"""Ensure the independent-check harness detects ties and ordering errors."""

import json
from math import comb
from pathlib import Path

import pytest

from poker_ai.cards import cards_to_mask
from poker_ai.evaluator import HandCategory, HandRank
from poker_ai.validation.five_card import (
    RankAgreement,
    ValidationConfig,
    expected_category_counts,
    expected_distinct_ranks,
    iter_hands,
    load_config,
)

WEAKER = HandRank(HandCategory.HIGH_CARD, (7, 5, 4, 3, 2))
STRONGER = HandRank(HandCategory.ONE_PAIR, (2, 5, 4, 3))


def test_reference_agreement_accepts_same_classes_and_opposite_score_direction() -> (
    None
):
    agreement = RankAgreement()
    agreement.observe(WEAKER, 200)
    agreement.observe(WEAKER, 200)
    agreement.observe(STRONGER, 100)
    agreement.check_order()
    assert len(agreement.own_to_reference) == 2


def test_reference_agreement_detects_false_ties() -> None:
    agreement = RankAgreement()
    agreement.observe(WEAKER, 200)
    with pytest.raises(ValueError, match="ties hands"):
        agreement.observe(WEAKER, 100)


def test_reference_agreement_detects_false_distinctions() -> None:
    agreement = RankAgreement()
    agreement.observe(WEAKER, 200)
    with pytest.raises(ValueError, match="distinguishes hands"):
        agreement.observe(STRONGER, 200)


def test_reference_agreement_detects_inverted_ordering() -> None:
    agreement = RankAgreement()
    agreement.observe(WEAKER, 100)
    agreement.observe(STRONGER, 200)
    with pytest.raises(ValueError, match="ordering"):
        agreement.check_order()


@pytest.mark.parametrize("score", [0, -1, 7463, True])
def test_reference_agreement_rejects_invalid_scores(score: int) -> None:
    with pytest.raises(ValueError, match="invalid Treys"):
        RankAgreement().observe(WEAKER, score)


def test_combinatorial_counts_cover_all_physical_hands_and_distinct_ranks() -> None:
    assert sum(expected_category_counts().values()) == comb(52, 5)
    assert expected_category_counts()[HandCategory.STRAIGHT_FLUSH] == 40
    assert expected_distinct_ranks() == 7462


def test_seeded_sampling_replays_and_produces_valid_hands() -> None:
    config = ValidationConfig("random", hands=25, seed=20261102)
    first, replay = tuple(iter_hands(config)), tuple(iter_hands(config))
    assert first == replay
    assert len(first) == 25
    assert all(len(cards) == cards_to_mask(cards).bit_count() == 5 for cards in first)


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"mode": "random", "hands": 10, "seed": 1, "typo": 1},
        {"mode": "random", "hands": 0, "seed": 1},
        {"mode": "random", "hands": True, "seed": 1},
        {"mode": "random", "hands": 10, "seed": None},
        {"mode": "random", "hands": 10, "seed": True},
        {"mode": "random", "hands": 10, "seed": -1},
        {"mode": "exhaustive", "hands": 10, "seed": None},
        {"mode": "exhaustive", "hands": comb(52, 5), "seed": 1},
        {"mode": "other", "hands": 10, "seed": 1},
    ],
)
def test_loader_rejects_ambiguous_or_invalid_configs(
    tmp_path: Path, data: dict[str, object]
) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_config(path)


def test_loader_accepts_full_enumeration_with_no_rng(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"mode": "exhaustive", "hands": comb(52, 5), "seed": None})
    )
    assert load_config(path) == ValidationConfig("exhaustive", comb(52, 5), None)
