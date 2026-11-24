"""One fixed signed-regret discount with the historical full-pass rules intact."""

from collections.abc import Callable, Sequence

import numpy as np
from medium_dry_full.learning import Capture, guard, observe
from numpy.random import PCG64, Generator

from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_training import ControlledTrainer, Rules
from poker_ai.postflop.river_study import Deadline
from poker_ai.training.mccfr import Updates


class RecencyTrainer(ControlledTrainer):
    """Discount stale owned regrets after each normal signed target update.

    For complete iteration t >= 2 and target i, first add t times the
    counterfactual advantage in acting-seat chips as the historical linear
    trainer does. Then multiply positive/zero owned regrets by
    t**1.5/(1+t**1.5) and negative owned regrets by 1/2. The chance and
    opponent reach weights, frozen target policies, average masses,
    t-weighted strategy sums, and two-pass uniform initialization are
    unchanged. This is not textbook DCFR, whose increment and average
    weights differ.
    """

    def __init__(self, tree: ArrayTree, rng: Generator) -> None:
        super().__init__(
            tree,
            rng,
            traversal="full",
            rules=Rules("signed", "linear", "linear"),
            average_phase="opponent_pass",
            average_mass="chance_own_reach",
        )

    def _apply(self, updates: Updates, target: int, iteration: int) -> None:
        """Keep the parent update, then discount only the target's regrets."""
        super()._apply(updates, target, iteration)
        if iteration < 2:
            return
        owned = self.tree.owners == target
        old = self.regrets[owned]
        t_alpha = float(iteration) ** 1.5
        positive_factor = t_alpha / (1.0 + t_alpha)
        self.regrets[owned] = old * np.where(old >= 0.0, positive_factor, 0.5)
        if not np.all(np.isfinite(self.regrets[owned])):
            raise ArithmeticError("nonfinite discounted signed regret")


def train(
    tree: ArrayTree,
    labels: Sequence[int],
    deadline: Deadline,
    capture: Capture,
    warm_capture: Callable[[ControlledTrainer], None] | None = None,
) -> RecencyTrainer:
    """Observe one deterministic path with the old full-work accounting."""
    solver = RecencyTrainer(tree, Generator(PCG64(0)))
    solver.initialize_exact()
    if warm_capture is not None:
        before = guard(solver)
        warm_capture(solver)
        if guard(solver) != before:
            raise ArithmeticError("warm observer mutated recency training state")
    observe(solver, labels, capture, deadline)
    return solver
