"""Block learner factories and every reference import in fresh own diagnostics."""

import importlib.abc
import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from typing import Any
from unittest.mock import patch

from poker_ai.evaluation.compact_sampled_own import no_reference_runtime

BLOCKED = (
    "poker_ai.postflop.batch_reduction.ReducedDispatchBatchTrainer.__init__",
    "poker_ai.postflop.frozen_batches.FrozenBatchTrainer.__init__",
    "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
    "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
    "poker_ai.postflop.compact_full_run.solver",
)


class ReferenceBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
        if fullname == "pyspiel" or fullname.startswith(
            ("open_spiel", "poker_ai.solver_validation")
        ):
            raise AssertionError("read-only diagnostic attempted a reference import")
        return None


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("read-only diagnostic attempted a learner constructor")


@contextmanager
def own_only() -> Iterator[None]:
    no_reference_runtime()
    finder = ReferenceBlocker()
    sys.meta_path.insert(0, finder)
    try:
        with ExitStack() as stack:
            for name in BLOCKED:
                stack.enter_context(patch(name, forbidden))
            yield
            no_reference_runtime()
    finally:
        sys.meta_path.remove(finder)
