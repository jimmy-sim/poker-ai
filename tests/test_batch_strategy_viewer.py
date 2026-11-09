"""Distribution math, retained selection and bounded offline navigation."""

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation import batch_strategy_viewer as viewer
from poker_ai.evaluation.averaging_history_software import toy_context


def request() -> viewer.Selection:
    return viewer.Selection(
        "dev_medium_oop",
        "texture_range_q8_b8",
        "signed",
        20261301,
        10_000_000,
        4,
        "current",
    )


def row() -> dict[str, Any]:
    return dict(
        id="EXPLICIT_SELECTION_ONLY",
        variant="current",
        batch_size=4,
        work_label=10_000_000,
        case=dict(
            spot_file="configs/learning-spots/dev_medium_oop.json",
            representation="texture_range_q8_b8",
            regret_rule="signed",
            seed=20261301,
            average_weight="linear",
        ),
    )


def test_l1_independent_definition_self_zero_symmetry_and_owner_ties() -> None:
    tree = toy_context().partition
    left = tree.legal / tree.legal.sum(axis=1, keepdims=True)
    right = left.copy()
    owned = [i for i, owner in enumerate(tree.owners) if owner == 0]
    right[owned[:2]] = 0
    right[owned[:2], 0] = 1
    expected = [
        (
            i,
            sum(
                abs(float(a) - float(b)) for a, b in zip(left[i], right[i], strict=True)
            ),
        )
        for i in owned
    ]
    expected.sort(key=lambda x: (-x[1], x[0]))
    assert viewer.rank_rows(tree, left, right, 0) == expected
    assert viewer.rank_rows(tree, right, left, 0) == expected
    assert viewer.rank_rows(tree, left, left, 0) == [(i, 0.0) for i in owned]
    assert all(0 <= x <= 2 for _, x in expected)
    # Deterministic opposite actions attain the full L1 bound, not one.
    left[owned] = 0
    left[owned, 0] = 1
    right[owned] = 0
    for i in owned:
        right[i, len(tree.actions[i]) - 1] = 1
    assert viewer.rank_rows(tree, left, right, 0) == [(i, 2.0) for i in owned]
    assert viewer.rank_rows(tree, left, right, 1) == [
        (i, 0.0) for i, owner in enumerate(tree.owners) if owner == 1
    ]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 2.0])
def test_invalid_policy_mass_is_rejected(value: float) -> None:
    tree = toy_context().partition
    policy = tree.legal / tree.legal.sum(axis=1, keepdims=True)
    bad = policy.copy()
    bad[0, 0] = value
    with pytest.raises(ValueError):
        viewer.rank_rows(tree, policy, bad, 0)
    with pytest.raises(ValueError):
        viewer.rank_rows(tree, policy, policy[:-1], 0)


def test_padded_illegal_action_mass_rejected() -> None:
    original = toy_context().partition
    tree = copy.copy(original)
    # Explicit third padded column; no need to build a new poker game.
    object.__setattr__(tree, "legal", np.pad(original.legal, ((0, 0), (0, 1))))
    left = tree.legal / tree.legal.sum(axis=1, keepdims=True)
    right = left.copy()
    right[0, 0] -= 0.1
    right[0, -1] = 0.1
    with pytest.raises(ValueError):
        viewer.rank_rows(tree, left, right, 0)


@pytest.mark.parametrize("seat", [True, -1, 2])
def test_invalid_seat_rejected(seat: int) -> None:
    tree = toy_context().partition
    policy = tree.legal / tree.legal.sum(axis=1, keepdims=True)
    with pytest.raises(ValueError):
        viewer.rank_rows(tree, policy, policy, seat)


def test_unique_selection_and_average_readouts_are_distinct() -> None:
    a = row()
    b = copy.deepcopy(a)
    b.pop("variant")
    b["id"] = "AVG"
    assert viewer.select([a, b], request()) == a
    assert viewer.select([a, b], replace(request(), readout="linear_average")) == b
    with pytest.raises(ValueError, match="exactly one"):
        viewer.select([a, a], request())
    with pytest.raises(ValueError, match="exactly one"):
        viewer.select([a], replace(request(), batch=16))


@pytest.mark.parametrize(
    "field,value",
    [
        ("game", "live"),
        ("representation", "unknown"),
        ("rule", "unknown"),
        ("seed", True),
        ("seed", 7),
        ("work", 0),
        ("work", True),
        ("batch", True),
        ("batch", 2),
        ("readout", "reference"),
    ],
)
def test_unretained_selection_rejected(field: str, value: Any) -> None:
    with pytest.raises(ValueError):
        replace(request(), **{field: value})


def test_mismatched_context_cannot_load_or_compare(tmp_path: Path) -> None:
    with patch.object(viewer, "read_saved", side_effect=AssertionError("no read")):
        with pytest.raises(ValueError, match="same game"):
            viewer.load(tmp_path, request(), replace(request(), seed=20261302))


def test_nonpoker_examples_rejected() -> None:
    with pytest.raises(ValueError, match="saved poker"):
        viewer.example(toy_context(), 0, 0)


def test_navigation_clamps_handles_invalid_keys_and_eof() -> None:
    # Navigation alone gets an explicit stand-in; actual IO is separately slow-tested.
    comparison = cast(viewer.Comparison, None)
    commands = iter(["p", "bad", "n", "n", "q"])
    output: list[str] = []
    with (
        patch.object(viewer.Comparison, "rows", return_value=[(0, 0.0), (1, 0.0)]),
        patch.object(viewer, "display", side_effect=lambda c, s, r: f"rank={r}"),
    ):
        # Use a real object with a stubbed rows method, not None dispatch.
        comparison = object.__new__(viewer.Comparison)
        viewer.browse(
            comparison, 0, 1, read=lambda _: next(commands), write=output.append
        )
        assert output == ["rank=1", "rank=1", "Use n, p or q.", "rank=2", "rank=2"]

        def eof(_: str) -> str:
            raise EOFError

        viewer.browse(comparison, 0, 1, read=eof, write=output.append)


def test_bad_rank_rejected_before_observation() -> None:
    comparison = object.__new__(viewer.Comparison)
    with patch.object(viewer.Comparison, "rows", return_value=[(0, 0.0)]):
        for rank in (0, 2, True):
            with pytest.raises(ValueError, match="rank"):
                viewer.display(comparison, 0, rank)
