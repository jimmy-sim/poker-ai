"""Own card artifact round trips and retention of past abstract observations."""

import json
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction, Kind, fit_quantizer
from poker_ai.abstraction.potential import FeatureConfig, Potential
from poker_ai.cards import Deck, parse_card
from poker_ai.engine import Action, ActionKind, new_hand


def tiny_model(kind: Kind) -> CardAbstraction:
    models = {}
    for length in (0, 3, 4, 5):
        lengths = (length,) + tuple(t for t in (3, 4, 5) if t > length)
        features = [
            Potential(equity, lengths, np.tile(row, (len(lengths), 1)))
            for equity, row in ((0.0, [1.0, 0, 0]), (1.0, [0.0, 0, 1]))
        ]
        models[length] = fit_quantizer(
            features, kind=kind, buckets=2, rng=Generator(PCG64(31))
        )
    return CardAbstraction(
        models, FeatureConfig(bins=3, current_samples=4, runouts=1, opponent_samples=2)
    )


@pytest.mark.parametrize("kind", ["strength", "distribution", "potential"])
def test_own_model_roundtrip_preserves_bucket_and_cache(
    tmp_path: Path, kind: Kind
) -> None:
    model = tiny_model(kind)
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
) -> None:
    model = tiny_model("strength")
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
