"""Independent fictional check that only regret time weight changes."""

from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from known_turn_uniform_regret_transfer.learning import RULES
from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.controlled_training import (
    ControlledTrainer,
    Rules,
    expected_pass,
)


def fictional_math() -> dict[str, Any]:
    """Compare t=2 signed updates on a synthetic two-seat tree, no poker input."""
    tree = software_context(0).scoring["coarse"].partition
    trainers = [
        ControlledTrainer(
            tree,
            Generator(PCG64(0)),
            traversal="full",
            rules=rules,
            average_phase="opponent_pass",
            average_mass="chance_own_reach",
        )
        for rules in (Rules("signed", "linear", "linear"), RULES)
    ]
    old, candidate = trainers
    old.initialize_exact()
    candidate.initialize_exact()
    if (
        old.iteration != 1
        or candidate.iteration != 1
        or old.nodes_visited != candidate.nodes_visited
        or not np.array_equal(old.regrets, candidate.regrets)
        or not np.array_equal(old.strategy_sum, candidate.strategy_sum)
        or not np.array_equal(old.current_policy, candidate.current_policy)
    ):
        raise ArithmeticError("fictional initialization differs")
    initial = old.regrets.copy()
    updates = expected_pass(tree, old.current_policy, 0)
    old._apply(updates, 0, 2)
    candidate._apply(updates, 0, 2)
    expected = initial.copy()
    for key, value in updates.regrets.items():
        index = old.lookup[key]
        expected[index, : len(value)] += value
    regret_error = float(np.max(np.abs(candidate.regrets - expected)))
    linear_error = float(
        np.max(np.abs(old.regrets - (initial + 2 * (expected - initial))))
    )
    average_error = float(np.max(np.abs(old.strategy_sum - candidate.strategy_sum)))
    if max(regret_error, linear_error, average_error) > 1e-12:
        raise ArithmeticError("fictional 1-versus-t regret update differs")
    old.step()
    candidate.step()
    tree.validate_policy(old.current_policy)
    tree.validate_policy(candidate.current_policy)
    tree.validate_policy(old.average_policy)
    tree.validate_policy(candidate.average_policy)
    if (
        old.nodes_visited != candidate.nodes_visited
        or old.rng.bit_generator.state != candidate.rng.bit_generator.state
    ):
        raise ArithmeticError("fictional charge or RNG differs")
    return dict(
        status="proof_passed",
        fixture="fictional signal game",
        control_regret_multiplier_at_iteration_2=2,
        candidate_regret_multiplier_at_iteration_2=1,
        regret_error=regret_error,
        linear_error=linear_error,
        average_error=average_error,
        charged_nodes_each=old.nodes_visited,
        rng_equal=True,
        real_policy_opened=False,
    )
