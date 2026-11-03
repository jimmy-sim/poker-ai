"""Own card artifact round trips and retention of past abstract observations."""

import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction, Kind
from poker_ai.cards import Deck, parse_card
from poker_ai.engine import Action, ActionKind, new_hand


@pytest.mark.parametrize("kind", ["strength", "distribution", "potential"])
def test_own_model_roundtrip_preserves_bucket_and_cache(
    tmp_path: Path, kind: Kind, card_model_factory: Callable[[Kind], CardAbstraction]
) -> None:
    model = card_model_factory(kind)
    path = tmp_path / "own-card-model.json"
    model.save(path, provenance={"test": True})
    loaded = CardAbstraction.load(path)
    hole = tuple(map(parse_card, "As Kh".split()))
    board = tuple(map(parse_card, "Qs Jh Td".split()))
    assert model.bucket(hole, board) == loaded.bucket(hole, board)
    model.bucket(hole, board)
    assert model.cached_bucket.cache_info().hits >= 1


def test_key_retains_every_past_bucket_and_public_history(
    monkeypatch: pytest.MonkeyPatch,
    card_model_factory: Callable[[Kind], CardAbstraction],
) -> None:
    model = card_model_factory("strength")
    state = new_hand((200, 200), Deck(), button=1)
    while not state.terminal and len(state.board) < 5:
        state = state.apply(
            Action(
                ActionKind.CHECK if state.legal_actions.can_check else ActionKind.CALL
            )
        )
    observed = []

    def bucket(hole: tuple[int, ...], board: tuple[int, ...]) -> int:
        observed.append(board)
        return len(board)

    monkeypatch.setattr(model, "bucket", bucket)
    assert state.actor is not None
    key = json.loads(model.information(state.observe(state.actor)))
    assert key["buckets"] == [0, 3, 4, 5]
    assert observed == [state.board[:n] for n in (0, 3, 4, 5)]
    assert len(key["history"]) == len(state.history)
    assert "hole" not in key and "board" not in key


def test_reference_artifact_is_not_a_card_model(tmp_path: Path) -> None:
    path = tmp_path / "reference.json"
    path.write_text('{"reference_strategy": [0.5,0.5]}')
    with pytest.raises(ValueError, match="own card"):
        CardAbstraction.load(path)


def test_abstract_limit_resume_recomputes_feature_cache_identically(
    tmp_path: Path, card_model_factory: Callable[[Kind], CardAbstraction]
) -> None:
    from functools import partial

    from poker_ai.training.checkpoint import load_checkpoint, save_checkpoint
    from poker_ai.training.holdem import LimitRules, sample_limit
    from poker_ai.training.mccfr import MCCFR

    model = card_model_factory("potential")
    artifact = tmp_path / "card-model.json"
    model.save(artifact, provenance={})
    fresh_model = CardAbstraction.load(artifact)
    rules = LimitRules(bet_cap=2)
    factory = partial(sample_limit, rules, information_builder=model.information)
    fresh_factory = partial(
        sample_limit, rules, information_builder=fresh_model.information
    )
    whole = MCCFR(factory, Generator(PCG64(33)))
    split = MCCFR(factory, Generator(PCG64(33)))
    whole.train(4)
    split.train(2)
    checkpoint = tmp_path / "own-training.json"
    config = {"model": "test-potential", "cap": 2}
    save_checkpoint(split, checkpoint, config=config, provenance={})
    resumed = load_checkpoint(checkpoint, fresh_factory, expected_config=config)
    resumed.train(2)
    assert whole.rng.bit_generator.state == resumed.rng.bit_generator.state
    assert whole.rows.keys() == resumed.rows.keys()
    for key in whole.rows:
        np.testing.assert_array_equal(
            whole.rows[key].regrets, resumed.rows[key].regrets
        )
        np.testing.assert_array_equal(
            whole.rows[key].strategy_sum, resumed.rows[key].strategy_sum
        )
