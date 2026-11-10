"""Nonuniform chance, native scalar roots and OWN reply values only."""

import importlib
from dataclasses import replace
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.tiny_policy_math import metrics
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.training_isolation import sentinel_policy, sentinel_tree
from poker_ai.solver_validation.matched_array_reference import (
    ScalarReference,
    compare,
    efg,
)


def test_export_contains_actual_nonuniform_chance_and_shared_groups() -> None:
    text = efg(sentinel_tree())
    assert '"a0" 0.10000000000000001' in text
    assert '"a2" 0.59999999999999998' in text
    assert text.count('p ""') > len(sentinel_tree().keys)


def test_export_rejects_nonfinite_chance_before_reference_construction() -> None:
    tree = sentinel_tree()
    chance = tree.chance_edges.copy()
    chance[0, 0] = np.nan
    with pytest.raises(ArithmeticError, match="chance probabilities"):
        efg(replace(tree, chance_edges=chance))


@pytest.mark.parametrize("name", ["uniform", "positive", "zero_support"])
def test_independent_native_roots_and_achieved_own_replies(name: str) -> None:
    pytest.importorskip("pyspiel")
    context = toy_context()
    tree = context.partition
    policy = (
        tree.normalize(tree.legal) if name == "uniform" else sentinel_policy(tree, name)
    )
    own = context.score(policy)
    detail = dict(
        policy=pack_policy(tree, policy),
        **score_data(context, own),
        replies=[{k: pack_policy(tree, v) for k, v in r.items()} for r in own.replies],
    )
    # These APIs would extract/train a native strategy. The adapter must not use them.
    pyspiel = importlib.import_module("pyspiel")

    with patch.object(
        pyspiel, "CFRPlusSolver", side_effect=AssertionError("no native training")
    ):
        reference = ScalarReference(tree)
        result = compare(context, (reference, reference), detail)
    expected = metrics(tree, policy)
    assert result["maximum_error_chips"] < 1e-12
    for k, value in expected.items():
        assert abs(value - result["native_metrics"][k]) < 1e-12
    assert not hasattr(reference, "policy")
    assert not hasattr(reference, "train_to")
    assert set(result) == {"native_metrics", "responses", "maximum_error_chips"}


def test_invalid_response_seat_does_not_call_native() -> None:
    reference = object.__new__(ScalarReference)
    for value in (True, -1, 2):
        with pytest.raises(ValueError, match="target"):
            reference.response_value(np.empty((0, 0)), value)
