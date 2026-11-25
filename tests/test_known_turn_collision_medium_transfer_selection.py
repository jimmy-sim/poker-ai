"""Selection prerequisites and structural invariants use no new draw stream."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from poker_ai.cards import parse_card

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import known_turn_collision_medium_transfer.selection as selector  # noqa: E402
from known_turn_collision_medium_transfer.gate import SCREEN  # noqa: E402
from known_turn_collision_medium_transfer.plan import (  # noqa: E402
    contract,
    digest,
    forbidden_signatures,
)
from river_generalization.selection import rank_signature  # noqa: E402
from turn_collision_transfer_selection import collision_summary  # noqa: E402


def test_published_contract_excludes_all_inspected_inputs() -> None:
    data = contract(ROOT)
    assert len(data["prior_inspected_input_sha256"]) == 49
    forbidden = forbidden_signatures(ROOT, data)
    assert forbidden
    assert len(forbidden) <= 49
    assert all(len(signature[0]) == 3 for signature in forbidden)
    for name in data["prior_inspected_input_sha256"]:
        assert len(json.loads((ROOT / name).read_bytes())["board"]) == 4


def test_turn_collision_is_exact_row_grouping_only() -> None:
    mapping = np.array([0, 1, 0, 2, 3, 4], dtype=np.int64)
    turn = np.array([True, True, True, True, False, False])
    river = np.logical_not(turn)
    result = collision_summary(mapping, turn, river, 5)
    assert result["turn_collided_exact_rows"] == 2
    assert result["turn_collided_abstract_groups"] == 1
    assert result["river_collided_exact_rows"] == 0


def test_screen_rejects_skipping_first_eligible_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A synthetic published screen cannot choose a later favorable case."""
    plan = {
        "selection": {
            "strata": [{"name": "synthetic", "texture": "wet"}],
            "max_candidates_per_stratum": 20,
            "minimum_collided_exact_turn_rows": 4,
            "whole_cap_seconds": 900,
            "max_tree_nodes": 200_000,
        }
    }
    monkeypatch.setattr(selector, "contract", lambda root: plan)
    monkeypatch.setattr(selector, "forbidden_signatures", lambda root, data: set())
    monkeypatch.setattr(selector, "GAMES", ("synthetic",))
    board = ["2s", "3s", "4d", "9h"]
    signature = rank_signature([parse_card(card) for card in board])
    path = tmp_path / SCREEN / "attempts" / "synthetic-01.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"name": "synthetic", "board": board}))
    row = {
        "stratum": "synthetic",
        "attempt": 1,
        "outcome": "selected",
        "turn_collided_exact_rows": 4,
        "river_collided_exact_rows": 0,
        "tree_nodes": 100,
        "file": "attempts/synthetic-01.json",
        "sha256": digest(path),
        "board_signature": signature,
    }
    result = {
        "status": "selected",
        "no_policy_or_score_read": True,
        "seconds": 2.0,
        "peak_rss_bytes": 100_000_000,
        "attempts": [row],
        "selected": [row],
    }
    selector.validate_screen(tmp_path, result)
    later = dict(row, attempt=2, file="attempts/synthetic-02.json")
    later_path = path.with_name("synthetic-02.json")
    later_path.write_bytes(path.read_bytes())
    result["attempts"] = [row, later]
    result["selected"] = [later]
    with pytest.raises(ArithmeticError, match="first-eligible"):
        selector.validate_screen(tmp_path, result)
