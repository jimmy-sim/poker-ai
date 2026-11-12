"""Fresh training workers are reference-free; read-only parents cannot learn."""

import importlib.abc
import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from typing import Any
from unittest.mock import patch


class NativeBlocker(importlib.abc.MetaPathFinder):
    def __init__(self, *, worker: bool) -> None:
        self.worker = worker

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
        if (
            fullname == "pyspiel"
            or fullname.startswith("open_spiel")
            or self.worker
            and fullname.startswith("poker_ai.solver_validation")
        ):
            raise AssertionError("own compact pipeline attempted a reference import")
        return None


def runtime(*, worker: bool) -> None:
    if any(
        n == "pyspiel"
        or n.startswith("open_spiel")
        or worker
        and n.startswith("poker_ai.solver_validation")
        for n in sys.modules
    ):
        raise ArithmeticError("own compact runtime already imported a reference")


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("read-only compact parent constructed a learner/reference")


@contextmanager
def isolated(*, worker: bool) -> Iterator[None]:
    runtime(worker=worker)
    finder = NativeBlocker(worker=worker)
    sys.meta_path.insert(0, finder)
    try:
        with ExitStack() as stack:
            if not worker:
                # Historical loaders import pure reference receipt validators;
                # permit their metadata, forbid native construction/imports and
                # every own learner constructor. No parent is a training worker.
                for name in (
                    "poker_ai.solver_validation.reference.Reference.__init__",
                    "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
                    "poker_ai.postflop.batch_reduction.ReducedDispatchBatchTrainer.__init__",
                    "poker_ai.postflop.frozen_batches.FrozenBatchTrainer.__init__",
                    "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
                    "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
                    "poker_ai.postflop.compact_full_run.solver",
                ):
                    stack.enter_context(patch(name, forbidden))
            yield
            runtime(worker=worker)
    finally:
        sys.meta_path.remove(finder)
