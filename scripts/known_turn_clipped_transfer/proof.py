"""Independent fictional check of clipped accumulated regrets."""

from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from known_turn_clipped_transfer.learning import RULES
from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.controlled_training import (
    ControlledTrainer,
    Rules,
    expected_pass,
)
from poker_ai.training.mccfr import Updates


def fictional_math() -> dict[str, Any]:
    """Force one negative legal advantage at t=2 on a non-poker toy tree."""
    tree = software_context(0).scoring["coarse"].partition
    old, candidate = [
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
    old.initialize_exact()
    candidate.initialize_exact()
    if (
        old.iteration != 1
        or candidate.iteration != 1
        or old.nodes_visited != candidate.nodes_visited
        or not np.array_equal(old.strategy_sum, candidate.strategy_sum)
        or not np.array_equal(old.current_policy, candidate.current_policy)
    ):
        raise ArithmeticError("fictional initialization differs beyond clipping")

    updates = expected_pass(tree, old.current_policy, 0)
    key = next(iter(updates.regrets))
    forced = {name: value.copy() for name, value in updates.regrets.items()}
    forced[key][:] = -1.0
    forced_updates = Updates(forced, updates.averages, updates.visited)
    old_before, candidate_before = old.regrets.copy(), candidate.regrets.copy()
    old._apply(forced_updates, 0, 2)
    candidate._apply(forced_updates, 0, 2)
    expected_old, expected_candidate = old_before.copy(), candidate_before.copy()
    for name, value in forced.items():
        index = old.lookup[name]
        n = len(value)
        expected_old[index, :n] += 2 * value
        expected_candidate[index, :n] = np.maximum(
            0, expected_candidate[index, :n] + 2 * value
        )
    signed_error = float(np.max(np.abs(old.regrets - expected_old)))
    clipped_error = float(np.max(np.abs(candidate.regrets - expected_candidate)))
    average_error = float(np.max(np.abs(old.strategy_sum - candidate.strategy_sum)))
    negative_signed = int(np.count_nonzero(old.regrets < 0))
    negative_clipped = int(np.count_nonzero(candidate.regrets < 0))
    if (
        max(signed_error, clipped_error, average_error) > 1e-12
        or negative_signed == 0
        or negative_clipped != 0
    ):
        raise ArithmeticError("fictional clipped-regret update differs")

    old.step()
    candidate.step()
    for solver in (old, candidate):
        tree.validate_policy(solver.current_policy)
        tree.validate_policy(solver.average_policy)
    if (
        old.nodes_visited != candidate.nodes_visited
        or old.rng.bit_generator.state != candidate.rng.bit_generator.state
    ):
        raise ArithmeticError("fictional charge or RNG differs")
    return dict(
        status="proof_passed",
        fixture="fictional signal game with forced negative legal advantage",
        signed_error=signed_error,
        clipped_error=clipped_error,
        average_error=average_error,
        negative_signed_entries=negative_signed,
        negative_clipped_entries=negative_clipped,
        charged_nodes_each=old.nodes_visited,
        rng_equal=True,
        real_policy_opened=False,
    )
