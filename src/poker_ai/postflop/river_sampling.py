"""Own external updates with selected chance edges integrated exactly.

Prefix weight m is the product of ENUMERATED chance probabilities only. Returns
are local conditional utility; m scales regret/averaging increments, not returns.
Sampled chance/opponent probabilities enter through their selection frequencies.
Policies must remain frozen throughout a target pass; callers apply updates later.
"""

from collections.abc import Callable
from typing import ClassVar

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.matrix import IndexedState
from poker_ai.postflop.sampling import PostflopMCCFR, SamplerKind
from poker_ai.training.mccfr import Policy, SampleState, Selector, Updates

ChancePredicate = Callable[[SampleState], bool]


def integrated_external_updates(
    root: SampleState,
    target: int,
    policy: Policy,
    select: Selector,
    integrate_chance: ChancePredicate,
) -> Updates:
    """Unbiased frozen-policy external updates; count every recursive visit.

    Enumerated chance children return sum p*conditional_value. Each descendant
    update receives its prefix product m; applying m to returned values as well
    would double-weight chance. The opponent's simple averaging is weighted by
    the same m. Own actions enumerate, opponent actions sample as usual. Multiple
    histories sharing an information set accumulate before the caller updates it.
    """
    if target not in (0, 1):
        raise ValueError("target must be player zero or one")
    updates = Updates({}, {})

    def add(table: dict[str, FloatArray], key: str, value: FloatArray) -> None:
        if key in table:
            table[key] += value
        else:
            table[key] = value.copy()

    def visit(state: SampleState, mass: float) -> float:
        updates.visited += 1
        if state.terminal:
            return state.payoff * (1 if target == 0 else -1)
        actions = state.actions
        if state.chance:
            probabilities = np.asarray(state.chance_probabilities, dtype=np.float64)
            if (
                probabilities.shape != (len(actions),)
                or not np.all(np.isfinite(probabilities))
                or np.any(probabilities < 0)
                or not np.isclose(probabilities.sum(), 1, rtol=0, atol=1e-12)
            ):
                raise ValueError("invalid chance distribution")
            if integrate_chance(state):
                return sum(
                    float(p) * visit(state.child(action), mass * float(p))
                    for action, p in zip(actions, probabilities, strict=True)
                    if p > 0
                )
            return visit(state.child(actions[select(probabilities)]), mass)
        key = state.information
        sigma = policy(key, actions)
        if state.actor != target:
            add(updates.averages, key, mass * sigma)
            return visit(state.child(actions[select(sigma)]), mass)
        values = np.array([visit(state.child(action), mass) for action in actions])
        value = float(sigma @ values)
        add(updates.regrets, key, mass * (values - value))
        return value

    visit(root, 1.0)
    return updates


def is_hidden_river(state: SampleState) -> bool:
    """Chance classifier only; never constructs or changes a player's policy key."""
    if not isinstance(state, IndexedState) or len(state.tree.source.spot.board) != 4:
        raise ValueError("river integration requires an indexed turn-only game")
    source = state.tree.source.states[state.node]
    return bool(
        state.chance
        and source.first is not None
        and source.second is not None
        and source.dealer is None
    )


class RiverIntegratedMCCFR(PostflopMCCFR):
    """Own turn-game sampler; private worlds sampled, all legal rivers integrated.

    Inherits alternating frozen passes, weighting, deferred updates and visit
    accounting. Restore via load_learning_checkpoint(...,
    solver_class=RiverIntegratedMCCFR); the default loader rejects this sampler.
    """

    sampler: ClassVar[SamplerKind] = "river_integrated"

    def _updates(self, root: SampleState, target: int, select: Selector) -> Updates:
        # Reject an unsupported root before a target pass creates any rows.
        is_hidden_river(root)
        return integrated_external_updates(
            root, target, self.policy, select, is_hidden_river
        )
