"""Independent small checks for the one-time collision-only selector."""

import json
import sys
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
from numpy.random import Generator

from poker_ai.cards import parse_card
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from turn_collision_transfer_selection import (  # noqa: E402
    CONFIG_SHA256,
    candidate,
    collision_summary,
    contract,
    digest,
    draw_board,
    save,
    validate_complete_screen,
)


class FixedDraws:
    """Synthetic draw stream; never uses the registered selection seed."""

    def __init__(self, boards: list[list[int]]) -> None:
        self.boards = boards
        self.index = 0

    def choice(
        self, values: Any, size: int, replace: bool = False
    ) -> np.ndarray[Any, Any]:
        assert not replace
        if size == 4:
            board = self.boards[self.index]
            self.index += 1
            return np.asarray(board)
        assert size == 20
        return np.asarray(values[:20])

    def integers(self, low: int, high: int, size: int) -> np.ndarray[Any, Any]:
        assert (low, high, size) == (1, 4, 10)
        return np.asarray([1, 2, 3, 1, 2, 3, 1, 2, 3, 1])


def test_published_contract_pins_all_prior_spots() -> None:
    plan, known = contract(Path(__file__).resolve().parents[1])
    assert len(known) == 24
    assert len(plan["known_spot_sha256"]) == 24
    assert plan["selection"]["minimum_collided_turn_exact_rows"] == 4
    assert plan["source_parent_fingerprint"] == (
        "6e09c02673ca596e6082ea8d0a57ba12cd2533acfaf2c777991c4d29f395e0f4"
    )


def test_first_novel_dry_board_skips_forbidden_signature() -> None:
    first = [0, 13, 26, 39]  # dry, distinct ranks 2/5/8/11
    second = [4, 17, 30, 43]  # dry, distinct ranks 3/6/9/12
    forbidden: set[tuple[tuple[int, ...], int]] = {((2, 5, 8), 11)}
    rng = cast(Generator, FixedDraws([first, second]))
    board, signature, draws = draw_board(rng, "dry", forbidden, 2, Deadline(10))
    assert board == second and signature == ((3, 6, 9), 12)
    assert draws == 2 and signature in forbidden


def test_candidate_has_disjoint_five_combo_ranges_and_declared_actor(
    tmp_path: Path,
) -> None:
    template = tmp_path / "template.json"
    template.write_text(
        json.dumps(
            {
                "button": 0,
                "actor": 0,
                "hero": 0,
                "prefix_actions": [],
                "ranges": [],
            }
        )
    )
    row = dict(
        name="synthetic", texture="dry", position="oop", template="template.json"
    )
    board = [0, 13, 26, 39]
    raw = candidate(tmp_path, row, board, cast(Generator, FixedDraws([])), 200000)
    assert raw["actor"] == raw["hero"] == 1
    assert raw["prefix_actions"] == [{"kind": "check"}]
    assert raw["max_tree_nodes"] == 200000
    assert [len(seat) for seat in raw["ranges"]] == [5, 5]
    cards = [
        parse_card(card)
        for seat in raw["ranges"]
        for pair in seat
        for card in pair["cards"]
    ]
    assert len(cards) == len(set(cards)) == 20
    assert not set(cards) & set(board)
    assert [pair["weight"] for seat in raw["ranges"] for pair in seat] == [
        1,
        2,
        3,
        1,
        2,
        3,
        1,
        2,
        3,
        1,
    ]


def test_collision_summary_matches_independent_group_reference() -> None:
    mapping = np.asarray([0, 1, 0, 2, 1, 3, 4])
    turn = np.asarray([True, True, True, True, True, False, False])
    river = ~turn
    result = collision_summary(mapping, turn, river, 5)
    groups: dict[int, list[int]] = {}
    for index, abstract in enumerate(mapping):
        groups.setdefault(int(abstract), []).append(index)
    expected_rows = sum(len(group) for group in groups.values() if len(group) > 1)
    expected_groups = sum(1 for group in groups.values() if len(group) > 1)
    assert result == dict(
        turn_collided_exact_rows=expected_rows,
        turn_collided_abstract_groups=expected_groups,
        river_collided_exact_rows=0,
    )
    assert expected_rows == 4 and expected_groups == 2


def test_collision_summary_rejects_river_grouping_and_invalid_streets() -> None:
    mapping = np.asarray([0, 0, 1])
    with pytest.raises(ArithmeticError, match="river"):
        collision_summary(
            mapping,
            np.asarray([True, False, True]),
            np.asarray([False, True, False]),
            2,
        )
    with pytest.raises(ValueError, match="street"):
        collision_summary(
            mapping,
            np.asarray([True, False, False]),
            np.asarray([False, False, False]),
            2,
        )


def test_one_time_record_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    save(path, {"status": "first"})
    with pytest.raises(FileExistsError):
        save(path, {"status": "replacement"})
    assert json.loads(path.read_text()) == {"status": "first"}


def test_freeze_reader_checks_all_attempts_and_first_eligible(tmp_path: Path) -> None:
    strata = [dict(name=name) for name in ("dry", "wet", "low")]
    attempts = []
    selected = []
    for name in ("dry", "wet", "low"):
        for index, collided in ((1, 2), (2, 4)):
            path = tmp_path / "attempts" / f"{name}-{index}.json"
            save(path, dict(board=[name, index]))
            row = dict(
                stratum=name,
                attempt=index,
                file=path.relative_to(tmp_path).as_posix(),
                sha256=digest(path),
                turn_collided_exact_rows=collided,
                river_collided_exact_rows=0,
                tree_nodes=100,
            )
            attempts.append(row)
            if index == 2:
                selected.append(row)
    result = dict(
        status="selected",
        config_sha256=CONFIG_SHA256,
        no_policy_or_score_read=True,
        seconds=1.0,
        attempts=attempts,
        selected=selected,
    )
    validate_complete_screen(result, strata, tmp_path)
    attempts[0]["turn_collided_exact_rows"] = 4
    with pytest.raises(ArithmeticError, match="first eligible"):
        validate_complete_screen(result, strata, tmp_path)
    attempts[0]["turn_collided_exact_rows"] = 2
    (tmp_path / str(attempts[0]["file"])).write_text("changed\n")
    with pytest.raises(ArithmeticError, match="retained structural"):
        validate_complete_screen(result, strata, tmp_path)
