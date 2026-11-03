"""Explicit traversal limits; abort rather than introduce biased truncation."""

from dataclasses import dataclass

from numpy.random import Generator

from poker_ai.training.mccfr import RootFactory, SampleState


class NodeBudgetExceeded(RuntimeError):
    """A pass exceeded its declared cost; discard the solver and resume a checkpoint."""


@dataclass
class NodeBudget:
    limit: int
    used: int = 1  # Root counts as one visit.

    def __post_init__(self) -> None:
        if type(self.limit) is not int or self.limit < 1:
            raise ValueError("node budget must be a positive built-in int")

    def consume(self) -> None:
        if self.used >= self.limit:
            raise NodeBudgetExceeded(f"target traversal exceeded {self.limit} nodes")
        self.used += 1


@dataclass(frozen=True)
class BudgetedState:
    inner: SampleState
    budget: NodeBudget

    @property
    def terminal(self) -> bool:
        return self.inner.terminal

    @property
    def chance(self) -> bool:
        return self.inner.chance

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        return self.inner.chance_probabilities

    @property
    def actor(self) -> int:
        return self.inner.actor

    @property
    def actions(self) -> tuple[int, ...]:
        return self.inner.actions

    @property
    def information(self) -> str:
        return self.inner.information

    @property
    def payoff(self) -> float:
        return self.inner.payoff

    def child(self, action: int) -> "BudgetedState":
        self.budget.consume()
        return BudgetedState(self.inner.child(action), self.budget)


def bounded_sample(factory: RootFactory, limit: int, rng: Generator) -> BudgetedState:
    """A fresh counter per target pass, shared across all its own-action branches.

    If exceeded, no truncated value is returned. Do not catch and continue the
    partially completed alternating iteration: abort and resume the last completed
    checkpoint. This wrapper limits computation and never changes policy inputs.
    """
    return BudgetedState(factory(rng), NodeBudget(limit))
