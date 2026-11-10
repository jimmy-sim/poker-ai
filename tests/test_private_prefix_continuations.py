"""Independent tiny continuation arithmetic, not a poker-strength study."""

import importlib.util
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.finite import ArrayTree

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "continuation_cli", ROOT / "scripts/contrast_private_prefix_continuations.py"
)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def fixture(target: int = 0) -> tuple[ArrayTree, Any, Any, Any, Any]:
    # Stop earns1. Continue then choose bad(0) or good(4).
    # Fictional river label: second own decision, not a poker board.
    children = np.zeros((5, 2), dtype=np.int64)
    children[0], children[2] = (1, 2), (3, 4)
    valid = np.zeros((5, 2), dtype=np.bool_)
    valid[[0, 2]] = True
    sign = 1 if target == 0 else -1
    tree = ArrayTree(
        children,
        valid,
        np.array([target, -2, target, -2, -2]),
        np.array([0, -1, 1, -1, -1]),
        ("first", "later"),
        ((0, 1), (0, 1)),
        np.array([target, target]),
        np.ones((2, 2)),
        np.zeros((5, 2)),
        np.ones(5),
        sign * np.array([0, 1, 0, 0, 4], dtype=np.float64),
        (np.array([0]), np.array([2])),
    )
    saved = np.array([[1.0, 0.0], [1.0, 0.0]])
    profiles = dict(
        exact=np.array([[0.0, 1.0], [0.0, 1.0]]),
        restricted=saved.copy(),
        river_before=np.array([[0.0, 1.0], [1.0, 0.0]]),
    )
    return (
        tree,
        saved,
        profiles,
        np.array([False, True]),
        dict(exact=4.0, restricted=1.0, river_before=0.0),
    )


@pytest.mark.parametrize("target", [0, 1])
def test_future_choice_changes_earlier_value_with_correct_target_sign(
    target: int,
) -> None:
    tree, saved, profiles, river, roots = fixture(target)
    q, support, error, mass_error = CLI.values(
        tree, saved, profiles, river, target, roots, 1e-9, 1e-12
    )
    assert error == mass_error == 0
    np.testing.assert_array_equal(q["exact"], [[1, 4], [0, 4]])
    np.testing.assert_array_equal(q["river_before"], [[1, 0], [0, 4]])
    # Own past reach is excluded: second info still has cf mass1 when saved stops.
    np.testing.assert_array_equal(support, [1, 1])
    assert CLI.choice(q["exact"][0].tolist(), 1) == 1
    assert CLI.choice(q["river_before"][0].tolist(), 1) == 0


@pytest.mark.parametrize("bad", ["root", "nan", "prefix", "river", "mask", "trio"])
def test_reject_changed_control_or_bound_roots(bad: str) -> None:
    tree, saved, profiles, river, roots = fixture()
    if bad == "root":
        roots["exact"] = 3.5
    elif bad == "nan":
        roots["exact"] = float("nan")
    elif bad == "prefix":
        profiles["river_before"][0] = [1, 0]
    elif bad == "river":
        profiles["river_before"][1] = [0, 1]
    elif bad == "mask":
        river = np.array([0, 1])
    else:
        profiles.pop("restricted")
    with pytest.raises(ArithmeticError):
        CLI.values(tree, saved, profiles, river, 0, roots, 1e-9, 1e-12)


def test_opponent_rows_are_never_changed() -> None:
    tree, saved, profiles, river, roots = fixture()
    tree = replace(tree, owners=np.array([1, 0]), player=np.array([1, -2, 0, -2, -2]))
    with pytest.raises(ArithmeticError, match="fixed opponent"):
        CLI.values(tree, saved, profiles, river, 0, roots, 1e-9, 1e-12)


def test_first_legal_tie_and_unsupported_choices() -> None:
    assert CLI.choice([2.0, 2.0], 1.0) == 0
    assert CLI.choice([2.0, 3.0], 0.0) is None
    with pytest.raises(ArithmeticError):
        CLI.choice([float("nan")], 0.0)
    with pytest.raises(ArithmeticError):
        CLI.choice([1.0], -1.0)


def test_existing_output_preserved_before_inputs(tmp_path: Path) -> None:
    output = tmp_path / "partial"
    output.mkdir()
    marker = output / "keep"
    marker.write_text("earlier work")
    with pytest.raises(FileExistsError):
        CLI.run(tmp_path, output)
    assert marker.read_text() == "earlier work"


def test_support_disagreement_rejected_in_unitless_units(monkeypatch: Any) -> None:
    tree, saved, profiles, river, roots = fixture()
    original = CLI.conditional_actions
    calls = 0

    def changed(t: Any, p: Any) -> Any:
        nonlocal calls
        q, mass = original(t, p)
        calls += 1
        if calls == 2:
            mass = mass.copy()
            mass[0] += 1e-10  # Below chip tolerance, above unitless tolerance.
        return q, mass

    monkeypatch.setattr(CLI, "conditional_actions", changed)
    with pytest.raises(ArithmeticError, match="roots/support"):
        CLI.values(tree, saved, profiles, river, 0, roots, 1e-9, 1e-12)


def test_nonfinite_action_values_rejected(monkeypatch: Any) -> None:
    tree, saved, profiles, river, roots = fixture()
    original = CLI.conditional_actions

    def changed(t: Any, p: Any) -> Any:
        q, mass = original(t, p)
        q[0, 0] = float("nan")
        return q, mass

    monkeypatch.setattr(CLI, "conditional_actions", changed)
    with pytest.raises(ArithmeticError, match="nonfinite"):
        CLI.values(tree, saved, profiles, river, 0, roots, 1e-9, 1e-12)
