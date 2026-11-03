"""Spot config/card-removal contracts and hidden continuation information."""

import json
from pathlib import Path

import pytest

from poker_ai.solver_validation.spots import SpotState, load_spot

ROOT = Path(__file__).resolve().parents[1]


def test_five_spots_have_declared_variety_and_exact_public_roots() -> None:
    spots = [
        load_spot(path) for path in sorted((ROOT / "configs/spots").glob("*.json"))
    ]
    assert len(spots) == 5
    assert {s.texture for s in spots} == {"dry", "wet"}
    assert {s.actor for s in spots} == {0, 1}
    assert min(s.stacks[s.hero] / s.pot for s in spots) < 0.2
    assert max(s.stacks[s.hero] / s.pot for s in spots) > 40
    assert all(s.worlds == 176 for s in spots)
    for spot in spots:
        assert sum(p for _, _, p in spot.joint) == pytest.approx(1)


def test_future_river_and_opponent_hand_are_hidden_at_root() -> None:
    spot = load_spot(ROOT / "configs/spots/dry_high_oop.json")
    dealt = SpotState(spot).child(0).child(0)
    a, b = dealt.child(dealt.actions[0]), dealt.child(dealt.actions[1])
    assert not a.chance and not b.chance
    assert a.information == b.information
    other = SpotState(spot).child(0).child(1)
    c = other.child(other.actions[0])
    assert a.information == c.information
    assert a.dealer is not None and b.dealer is not None
    assert a.dealer.board == b.dealer.board == spot.board


def test_range_overlap_is_conditioned_and_renormalized(tmp_path: Path) -> None:
    raw = json.loads((ROOT / "configs/spots/dry_high_oop.json").read_text())
    raw["ranges"][1][0] = {"cards": ["Ah", "Kh"], "weight": 3.0}
    path = tmp_path / "spot.json"
    path.write_text(json.dumps(raw))
    spot = load_spot(path)
    assert len(spot.joint) == 3
    assert sum(p for _, _, p in spot.joint) == pytest.approx(1)
    assert not any(i == 0 and j == 0 for i, j, _ in spot.joint)
    root = SpotState(spot)
    assert sum(root.chance_probabilities) == pytest.approx(1)
    for action in root.actions:
        child = root.child(action)
        assert sum(child.chance_probabilities) == pytest.approx(1)


@pytest.mark.parametrize(
    "mutation",
    [
        "bad_board",
        "bad_pot",
        "duplicate_combo",
        "no_joint",
        "negative_weight",
        "unknown_field",
    ],
)
def test_invalid_spots_are_rejected(tmp_path: Path, mutation: str) -> None:
    raw = json.loads((ROOT / "configs/spots/dry_high_oop.json").read_text())
    if mutation == "bad_board":
        raw["board"] = ["As", "As", "2c", "9h"]
    elif mutation == "bad_pot":
        raw["pot"] = 5
    elif mutation == "duplicate_combo":
        raw["ranges"][0].append(raw["ranges"][0][0])
    elif mutation == "no_joint":
        raw["ranges"][0] = [{"cards": ["As", "Ah"], "weight": 1}]
    elif mutation == "negative_weight":
        raw["ranges"][0][0]["weight"] = -1
    else:
        raw["extra"] = "ignored values must fail"
    path = tmp_path / "spot.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        load_spot(path)
