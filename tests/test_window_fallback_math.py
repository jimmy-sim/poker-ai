"""Hand-computed toy policies, not measured Hold'em fallback outcomes."""

import copy
from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.window_fallback_math import (
    LABELS,
    MASKS,
    fill_rows,
    full_equivalence,
    panel_identity,
)
from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_training import score_data


def hidden_game() -> ArrayTree:
    """Player one cannot see player zero's action; asymmetric terminal chips."""
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, 1, -2, -2, 1, -2, -2]),
        np.array([0, 1, -1, -1, 1, -1, -1]),
        ("first", "hidden-first-action"),
        ((0, 1),) * 2,
        np.array([0, 1]),
        np.ones((2, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        np.array([0, 0, 3, -1, 0, -2, 2], dtype=np.float64),
        (np.array([0]), np.array([1, 4])),
    )


def unreachable_game() -> ArrayTree:
    children = np.zeros((5, 2), dtype=np.int64)
    children[0], children[2] = (1, 2), (3, 4)
    valid = np.zeros((5, 2), dtype=np.bool_)
    valid[[0, 2]] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, -2, 0, -2, -2]),
        np.array([0, -1, 1, -1, -1]),
        ("root", "after_own_zero_action"),
        ((0, 1),) * 2,
        np.array([0, 0]),
        np.ones((2, 2)),
        np.zeros((5, 2)),
        np.ones(5),
        np.array([0, 1, 0, 3, -2], dtype=np.float64),
        (np.array([0]), np.array([2])),
    )


def score(tree: ArrayTree, policy: Any) -> dict[str, Any]:
    zero = np.zeros(len(tree.keys), dtype=np.bool_)
    context = ScoringContext(tree, tree, np.arange(len(tree.keys)), (zero, zero))
    return score_data(context, context.score(policy))


def test_reachable_missing_mass_can_change_value_without_changing_a_learned_row() -> (
    None
):
    tree = hidden_game()
    mass = np.array([[8.0, 2.0], [0.0, 0.0]])
    window = tree.normalize(mass)
    whole = np.array([[0.25, 0.75], [0.3, 0.7]])
    originals = [a.tobytes() for a in (mass, window, whole)]
    filled = fill_rows(tree, window, mass, whole, (1,), np.array([False, True]))
    assert filled.policy[0].tobytes() == window[0].tobytes()
    np.testing.assert_array_equal(filled.policy[1], [0.3, 0.7])
    assert filled.support[1]["maximum_own_reach_at_eligible_histories"] == 1
    assert filled.support[1]["changed_river_rows"] == 1
    assert filled.support[0]["eligible_rows"] == 0
    raw_score, new_score = score(tree, window), score(tree, filled.policy)
    # Manual expectations: .8*.5*3-.8*.5-.2*.5*2+.2*.5*2 = .8.
    # Changing only seat one's probabilities to (.3,.7) yields .32 for seat zero.
    assert raw_score["metrics"]["value_player_zero_chips"] == pytest.approx(0.8)
    assert new_score["metrics"]["value_player_zero_chips"] == pytest.approx(0.32)
    assert raw_score["metrics"]["exact_exploitability_chips"] == pytest.approx(0.7)
    assert new_score["metrics"]["exact_exploitability_chips"] == pytest.approx(0.6)
    with pytest.raises(ArithmeticError, match="full zero-mass"):
        full_equivalence(filled, raw_score, new_score)
    assert originals == [a.tobytes() for a in (mass, window, whole)]
    assert not any(
        a.flags.writeable for a in (filled.policy, filled.eligible, filled.changed)
    )


@pytest.mark.parametrize("targets", MASKS)
def test_structurally_unreachable_missing_mass_has_no_realization_or_value_effect(
    targets: tuple[int, ...],
) -> None:
    tree = unreachable_game()
    mass = np.array([[1.0, 0.0], [0.0, 0.0]])
    window = tree.normalize(mass)
    whole = np.array([[0.3, 0.7], [0.0, 1.0]])
    filled = fill_rows(tree, window, mass, whole, targets, np.array([False, True]))
    assert filled.support[0]["eligible_uniform_reach_fraction"] > 0
    assert filled.support[0]["maximum_own_reach_at_eligible_histories"] == 0
    assert filled.maximum_realization_change == 0
    before, after = score(tree, window), score(tree, filled.policy)
    assert full_equivalence(filled, before, after) == 0
    assert before["metrics"]["value_player_zero_chips"] == 1
    assert after["metrics"]["value_player_zero_chips"] == 1


def test_complete_panel_has_additive_br_metrics_but_nonzero_ev_interaction() -> None:
    tree = hidden_game()
    mass = np.zeros_like(tree.legal)
    window = tree.normalize(mass)
    whole = np.array([[0.8, 0.2], [0.3, 0.7]])
    scores = {
        label: score(
            tree,
            fill_rows(
                tree, window, mass, whole, targets, np.zeros(2, dtype=np.bool_)
            ).policy,
        )
        for label, targets in zip(LABELS, MASKS, strict=True)
    }
    assert [
        scores[k]["metrics"]["exact_exploitability_chips"] for k in LABELS
    ] == pytest.approx([0.25, 0.7, 0.15, 0.6])
    result = panel_identity(scores)
    assert result["maximum_error_chips"] < 1e-14
    assert result["baseline_ev_interaction_chips"] == pytest.approx(-0.48)
    for changed in ("missing", "root", "metric", "nan"):
        bad = copy.deepcopy(scores)
        if changed == "missing":
            bad.pop("fill_1")
        elif changed == "root":
            bad["fill_0"]["responses"][0]["restricted_reply_value_chips"] += 1
        else:
            bad["fill_both"]["metrics"]["within_partition_gain_chips"] += (
                float("nan") if changed == "nan" else 1
            )
        with pytest.raises(ArithmeticError):
            panel_identity(bad)


@pytest.mark.parametrize("targets", [(-1,), (2,), (False,), (0.0,), (1, 0), (0, 0)])
def test_invalid_target_masks_are_not_silently_coerced(targets: Any) -> None:
    tree = hidden_game()
    with pytest.raises(ValueError):
        fill_rows(
            tree,
            tree.normalize(tree.legal),
            tree.legal,
            tree.normalize(tree.legal),
            targets,
            np.zeros(2, dtype=np.bool_),
        )


def test_no_rows_missing_is_identity_and_tiny_positive_rows_are_not_filled() -> None:
    tree = hidden_game()
    mass = np.array([[1.0, 2.0], [1e-300, 1e-300]])
    window = tree.normalize(mass)
    whole = np.array([[0.9, 0.1], [0.0, 1.0]])
    for targets in MASKS:
        filled = fill_rows(
            tree, window, mass, whole, targets, np.zeros(2, dtype=np.bool_)
        )
        assert filled.policy.tobytes() == window.tobytes()
        assert not filled.eligible.any()
        assert not filled.changed.any()


def test_wrong_window_and_river_mask_are_rejected() -> None:
    tree = hidden_game()
    mass = np.zeros_like(tree.legal)
    uniform = tree.normalize(mass)
    with pytest.raises(ArithmeticError, match="reconstruct"):
        fill_rows(
            tree,
            np.array([[1.0, 0.0], [0.5, 0.5]]),
            mass,
            uniform,
            (0,),
            np.zeros(2, dtype=np.bool_),
        )
    with pytest.raises(ValueError):
        fill_rows(tree, uniform, mass, uniform, (), np.zeros(1, dtype=np.bool_))


def test_full_control_gate_checks_separate_unitless_tolerance() -> None:
    tree = unreachable_game()
    mass = np.array([[1.0, 0.0], [0.0, 0.0]])
    window = tree.normalize(mass)
    filled = fill_rows(tree, window, mass, window, (0,), np.zeros(2, dtype=np.bool_))
    raw_score = score(tree, window)
    with pytest.raises(ArithmeticError):
        full_equivalence(
            replace(filled, maximum_realization_change=2e-11), raw_score, raw_score
        )
    with pytest.raises(ValueError):
        full_equivalence(filled, raw_score, raw_score, tolerance_unitless=1e-9)
