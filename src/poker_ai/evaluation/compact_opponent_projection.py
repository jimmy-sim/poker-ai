"""Declared OLD-OWN cost shapes, never learned compact books or training input."""

from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import validate_mass
from poker_ai.evaluation.compact_opponent_contexts import refinement
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.finite import FloatArray, IntArray
from poker_ai.postflop.learning_artifacts import sha


def lift_policy(
    old: Contexts, new: Contexts, mapping: IntArray, policy: FloatArray
) -> FloatArray:
    check_mapping(old, new, mapping)
    old.coarse.validate_policy(policy)
    result = policy[mapping].copy()
    new.coarse.validate_policy(result)
    if not np.array_equal(policy[old.mapping], result[new.mapping]):
        raise ArithmeticError("cost probability lift changes fine-game actions")
    result.flags.writeable = False
    return result


def lift_mass(
    old: Contexts, new: Contexts, mapping: IntArray, mass: FloatArray
) -> tuple[FloatArray, dict[str, Any]]:
    """New warm + new/old warm ratio times OLD positive post-warm density.

    Only a cost stand-in. Both origins are exact simultaneous uniform own
    expectations. Scaling raw totals would manufacture a different warm origin.
    Reject missing warm support rather than inventing mass at unseen rows.
    """
    check_mapping(old, new, mapping)
    validate_mass(old.coarse, mass)
    before, after = warm_mass(old.coarse), warm_mass(new.coarse)
    delta = mass - before
    if np.any(delta < 0):
        raise ArithmeticError("old cost book predates its exact warm origin")
    denominator = before[mapping]
    supported = denominator > 0
    if np.any((~supported) & ((after != 0) | (delta[mapping] != 0))):
        raise ArithmeticError("cost density has no original warm support")
    ratio = np.divide(after, denominator, out=np.zeros_like(after), where=supported)
    for i, menu in enumerate(new.coarse.actions):
        if not np.all(ratio[i, : len(menu)] == ratio[i, 0]):
            raise ArithmeticError("warm ratio changes action probabilities")
    result = after + ratio * delta[mapping]
    validate_mass(new.coarse, result)
    expected = old.coarse.normalize(mass)[mapping]
    if not np.allclose(new.coarse.normalize(result), expected, atol=1e-12, rtol=0):
        raise ArithmeticError("cost density lift changes old policy probabilities")
    result.flags.writeable = False
    return result, dict(
        projection="new_exact_warm_plus_warm_ratio_times_old_post_warm_density",
        old_book_sha256=array_sha(mass),
        new_cost_book_sha256=array_sha(result),
        old_warm_sha256=array_sha(before),
        new_warm_sha256=array_sha(after),
        refinement_sha256=sha(mapping.tolist()),
        learned_compact_book=False,
        new_training_nodes=0,
    )


def check_mapping(old: Contexts, new: Contexts, mapping: IntArray) -> None:
    if (
        mapping.dtype != np.int64
        or mapping.shape != (len(new.coarse.keys),)
        or not np.array_equal(mapping, refinement(old, new))
    ):
        raise ArithmeticError("cost lift needs the exact structural refinement")


def lift_book_and_average(
    old: Contexts,
    new: Contexts,
    mapping: IntArray,
    book: FloatArray,
    average: FloatArray,
) -> tuple[FloatArray, FloatArray, dict[str, Any]]:
    """Keep the frozen replay's EXACT book/average relationship after a lift.

    Density scaling can change normalized probabilities by a final floating bit.
    The cost-only contract allows 1e-12 proximity to the OLD policy; it does not
    permit disagreement between the NEW cost book and its own normalization.
    This operation never supplies training input or alters an original table.
    """
    old.coarse.validate_policy(average)
    if not np.array_equal(old.coarse.normalize(book), average):
        raise ArithmeticError("original cost average differs from its raw book")
    lifted, receipt = lift_mass(old, new, mapping, book)
    result = new.coarse.normalize(lifted)
    if not np.allclose(result, average[mapping], atol=1e-12, rtol=0):
        raise ArithmeticError("cost average lift changes old probabilities")
    result.flags.writeable = False
    return (
        lifted,
        result,
        dict(
            receipt,
            old_average_sha256=array_sha(average),
            new_cost_average_sha256=array_sha(result),
            average_origin="exact_normalization_of_lifted_cost_book",
            maximum_old_probability_difference=float(
                np.max(np.abs(result - average[mapping]))
            ),
        ),
    )
