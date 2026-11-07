"""Public feature boundaries, symmetry, history and small-game key correctness."""

import itertools
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.public_board import (
    BoardTexture,
    board_texture,
    board_texture_history,
    canonical_public_board,
)
from poker_ai.cards import parse_card
from poker_ai.postflop.game import SpotState, load_spot
from poker_ai.postflop.matrix import (
    Encoding,
    MatrixTree,
    observation_key,
    recall_violations,
)
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]
NEW_ENCODINGS: tuple[Encoding, ...] = ("canonical_b8", "texture_b8")


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(c) for c in text.split())


@pytest.fixture(scope="module")
def model() -> CardAbstraction:
    return CardAbstraction.load(ROOT / "results/card-models/potential-8.json")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", BoardTexture((0, 0, 0, 0, 0), (0, 0, 0, 0), 0, 0, 0)),
        ("As 2s 3s", BoardTexture((1, 1, 1, 0, 0), (3, 0, 0, 0), 1, 1, 3)),
        ("Ac Ad 7h", BoardTexture((2, 1, 0, 0, 0), (1, 1, 1, 0), 2, 2, 1)),
        ("Tc Jd Qh Ks Ac", BoardTexture((1, 1, 1, 1, 1), (2, 1, 1, 1), 5, 1, 5)),
        ("Ac 2d 3h 4s 5c", BoardTexture((1, 1, 1, 1, 1), (2, 1, 1, 1), 1, 1, 5)),
        ("2c 2d 2h 2s 9c", BoardTexture((4, 1, 0, 0, 0), (2, 1, 1, 1), 0, 0, 1)),
    ],
)
def test_texture_has_documented_meaning(text: str, expected: BoardTexture) -> None:
    assert board_texture(cards(text)) == expected


@pytest.mark.parametrize(
    "board", [(0,), (0, 1), tuple(range(6)), (0, 0, 1), (-1, 1, 2), (0, 1, 52)]
)
def test_public_features_reject_invalid_boards(board: tuple[int, ...]) -> None:
    for function in (canonical_public_board, board_texture, board_texture_history):
        with pytest.raises(ValueError):
            function(board)


@pytest.mark.parametrize("bad", [True, 1.5, np.int64(3)])
def test_public_features_reject_non_builtin_card_ids(bad: object) -> None:
    for function in (canonical_public_board, board_texture, board_texture_history):
        with pytest.raises(TypeError):
            function((0, 1, bad))  # type: ignore[arg-type]


@settings(max_examples=40)
@given(st.lists(st.integers(0, 51), min_size=5, max_size=5, unique=True))
def test_global_suit_renaming_and_unordered_flop(board_list: list[int]) -> None:
    board = tuple(board_list)
    canonical = canonical_public_board(board)
    texture = board_texture_history(board)
    for suits in itertools.permutations(range(4)):
        renamed = tuple(4 * (c // 4) + suits[c % 4] for c in board)
        assert canonical_public_board(renamed) == canonical
        assert board_texture_history(renamed) == texture
    for flop in itertools.permutations(board[:3]):
        permuted = flop + board[3:]
        assert canonical_public_board(permuted) == canonical
        assert board_texture_history(permuted) == texture
    assert canonical_public_board(canonical) == canonical
    for length in (3, 4, 5):
        # Future reveals cannot change the canonical view of an earlier street.
        assert canonical_public_board(canonical[:length]) == canonical_public_board(
            board[:length]
        )
        assert board_texture_history(board[:length]) == texture[: length - 2]


def test_same_texture_can_merge_different_exact_ranks() -> None:
    first, second = cards("2c 3d 7h"), cards("3c 4d 8h")
    assert board_texture(first) == board_texture(second)
    assert canonical_public_board(first) != canonical_public_board(second)


def test_global_suit_links_survive_canonicalization() -> None:
    matching, different = cards("Ac Kc 2d 7c"), cards("Ac Kc 2d 7d")
    assert canonical_public_board(matching) != canonical_public_board(different)


def test_later_key_remembers_earlier_texture_and_reveal_order() -> None:
    first = cards("Ac Kc 2d 7c 7d")
    second = cards("Ac Kc 2d 7d 7c")
    # Same final card set and texture; the turn's flush texture differs.
    assert board_texture(first) == board_texture(second)
    assert board_texture_history(first) != board_texture_history(second)
    assert canonical_public_board(first) != canonical_public_board(second)


def test_hidden_opponent_and_actual_future_do_not_enter_keys(
    model: CardAbstraction,
) -> None:
    spot = load_spot(ROOT / "configs/learning-spots/dev_low_oop.json")
    base = SpotState(spot).child(0).child(0)
    other_opponent = SpotState(spot).child(0).child(1)
    worlds = (
        base.child(base.actions[0]),
        base.child(base.actions[1]),
        other_opponent.child(other_opponent.actions[0]),
    )
    observations = []
    for world in worlds:
        assert world.dealer is not None
        observations.append(world.dealer.observe(world.actor))
    for encoding in NEW_ENCODINGS:
        assert len({observation_key(o, encoding, model) for o in observations}) == 1


def test_only_acting_player_observations_and_a_model_are_accepted(
    model: CardAbstraction,
) -> None:
    state = SpotState(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    state = state.child(0).child(0)
    state = state.child(state.actions[0])
    assert state.dealer is not None
    observation = state.dealer.observe(state.actor)
    for encoding in NEW_ENCODINGS:
        with pytest.raises(ValueError, match="model"):
            observation_key(observation, encoding, None)
        for invalid in (
            state.dealer.observe(1 - state.actor),
            replace(observation, terminal=True),
        ):
            with pytest.raises(ValueError, match="acting player"):
                observation_key(invalid, encoding, model)
        payload = json.loads(observation_key(observation, encoding, model))
        assert payload[:2] == ["public-board-v1", encoding]
        assert payload[2] == model.information(observation)


def test_existing_public_and_legacy_keys_are_byte_compatible(
    model: CardAbstraction,
) -> None:
    state = SpotState(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    state = state.child(0).child(0)
    state = state.child(state.actions[0])
    assert state.dealer is not None
    observation = state.dealer.observe(state.actor)
    legacy = model.information(observation)
    assert observation_key(observation, "legacy_b8", model) == legacy
    assert observation_key(observation, "public_b8", model) == json.dumps(
        [legacy, observation.board], separators=(",", ":")
    )


def test_complete_keys_are_invariant_to_suit_names_and_flop_order(
    model: CardAbstraction,
) -> None:
    state = SpotState(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    state = state.child(0).child(0)
    state = state.child(state.actions[0])
    assert state.dealer is not None
    observation = state.dealer.observe(state.actor)
    for suits in itertools.permutations(range(4)):
        renamed = replace(
            observation,
            hole_cards=tuple(
                4 * (c // 4) + suits[c % 4] for c in observation.hole_cards
            ),
            board=tuple(4 * (c // 4) + suits[c % 4] for c in observation.board),
        )
        permuted = replace(renamed, board=renamed.board[:3][::-1] + renamed.board[3:])
        for encoding in NEW_ENCODINGS:
            expected = observation_key(observation, encoding, model)
            assert observation_key(renamed, encoding, model) == expected
            assert observation_key(permuted, encoding, model) == expected


@pytest.mark.parametrize("encoding", NEW_ENCODINGS)
@pytest.mark.parametrize("game", ["dev_low_oop", "dev_medium_oop"])
def test_new_keys_preserve_game_menus_recall_and_uniform_value(
    encoding: Encoding, game: str, model: CardAbstraction
) -> None:
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{game}.json"))
    exact = MatrixTree.build(source)
    abstract = MatrixTree.build(source, encoding, model)
    assert recall_violations(abstract) == 0
    uniform = abstract.normalize(abstract.legal)
    lifted = exact.dense_exact(abstract.exact_policy(uniform))
    np.testing.assert_array_equal(lifted, exact.normalize(exact.legal))
    assert float(exact.values(exact.edges(lifted))[0]) == pytest.approx(
        float(abstract.values(abstract.edges(uniform))[0]), abs=1e-12
    )


def test_prospective_config_keeps_all_controls_and_fixed_budgets() -> None:
    raw = json.loads((ROOT / "configs/public-board-study.json").read_text())
    assert raw["status"] == "preregistered_not_run"
    assert raw["encodings"] == [
        "exact",
        "legacy_b8",
        "public_b8",
        "canonical_b8",
        "texture_b8",
    ]
    assert raw["candidate"] == "texture_b8"
    assert len(set(raw["seeds"])) == 3
    assert raw["sampled_node_checkpoints"] == [100000, 1000000, 10000000]
    assert raw["limits"]["maximum_recall_violations"] == 0
    assert all((ROOT / path).is_file() for path in raw["development_spots"])


def test_inspector_shows_observed_cards_and_prefixes_and_rejects_duplicates() -> None:
    command = [sys.executable, str(ROOT / "scripts/inspect_public_board.py")]
    result = subprocess.run(command + ["Ac", "Kc", "2d", "7c"], capture_output=True)
    assert result.returncode == 0, result.stderr
    raw = json.loads(result.stdout)
    assert raw["observed_board"] == ["Ac", "Kc", "2d", "7c"]
    assert [row["board_length"] for row in raw["lossy_texture_history"]] == [3, 4]
    invalid = subprocess.run(command + ["Ac", "Ac", "2d"], capture_output=True)
    assert invalid.returncode == 2 and b"duplicate" in invalid.stderr
