"""Selection prerequisites and structural invariants use no new draw stream."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_collision_medium_transfer.plan import contract, forbidden_signatures  # noqa: E402
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
