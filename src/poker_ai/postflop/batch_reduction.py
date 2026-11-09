"""Optional ndarray reduction dispatch; all original checks/arithmetic retained.

The original implementation remains frozen. Only the batch mean's all/any
wrappers become array-method reductions. No finite/negative/overflow check is
removed. B1 calls the original step, including its counters, exactly once.
"""

from collections.abc import Iterable

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.frozen_batches import FrozenBatchTrainer
from poker_ai.training.mccfr import Updates, external_updates


def array_mean_updates(samples: Iterable[Updates], count: int) -> Updates:
    """Fresh sparse sums, traversal/key encounter order, divide once at the end.

    Missing rows contribute zero; averaging only the appearances would bias the
    estimator. Visits are SUMMED rather than averaged. Inputs are never mutated.
    Target ownership/menu validation remains the original updater's obligation.
    """
    if type(count) is not int or count <= 0:
        raise ValueError("batch count must be a positive integer")
    result = Updates({}, {})
    observed = 0
    for sample in samples:
        if type(sample.visited) is not int or sample.visited <= 0:
            raise ValueError("batch traversal must charge positive integer visits")
        observed += 1
        if observed > count:
            raise ValueError("too many batch traversals")
        for incoming, outgoing, average in (
            (sample.regrets, result.regrets, False),
            (sample.averages, result.averages, True),
        ):
            for key, values in incoming.items():
                if (
                    not isinstance(key, str)
                    or not key
                    or values.ndim != 1
                    or not values.size
                    or not np.isfinite(values).all()
                    or (average and (values < 0).any())
                ):
                    raise ValueError("invalid raw batch increment")
                if key not in outgoing:
                    outgoing[key] = values.copy()
                elif outgoing[key].shape != values.shape:
                    raise ValueError("batch menu width changed")
                else:
                    outgoing[key] += values
                if not np.isfinite(outgoing[key]).all():
                    raise ArithmeticError("nonfinite batch sum")
        result.visited += sample.visited
    if observed != count:
        raise ValueError("incomplete batch traversals")
    for table in (result.regrets, result.averages):
        for values in table.values():
            values /= count
    return result


class ReducedDispatchBatchTrainer(FrozenBatchTrainer):
    """Opt-in batch execution; policies, estimators and updater stay original."""

    def step(self) -> None:
        if self.batch_size == 1:
            super().step()
            return
        t = self.iteration + 1
        sizes = []
        for target in (0, 1):
            cache: dict[int, FloatArray] = {}

            def frozen(
                key: str, actions: tuple[int, ...], cache: dict[int, FloatArray] = cache
            ) -> FloatArray:
                info = self.lookup[key]
                if actions != self.tree.actions[info]:
                    raise ValueError("controlled action menu mismatch")
                self.sampled_keys.add(key)
                if info not in cache:
                    cache[info] = self._policy_row(info)
                    self.row_evaluations += 1
                return cache[info][: len(actions)].copy()

            def select(probabilities: FloatArray) -> int:
                return int(self.rng.choice(len(probabilities), p=probabilities))

            update = array_mean_updates(
                (
                    external_updates(self.cached_nodes[0], target, frozen, select)
                    for _ in range(self.batch_size)
                ),
                self.batch_size,
            )
            self._apply(update, target, t)
            self.nodes_visited += update.visited
            self.sampled_traversals += self.batch_size
            sizes.append(len(cache))
        self.last_pass_rows = sizes[0], sizes[1]
        self.iteration = t
