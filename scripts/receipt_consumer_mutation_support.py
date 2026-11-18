"""Read-only witnesses around the original archive receipt consumers."""

import functools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

from prerequisite_identity_support import Observation, observe
from receipt_cpu_support import ModuleAlias

from poker_ai.evaluation import batch_cost_inputs as cost
from poker_ai.evaluation import batch_reduction_inputs as reduction
from poker_ai.evaluation import frozen_batch_protocol as frozen
from poker_ai.evaluation import reduced_study_run as study
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs


class Capture:
    """Keep each loaded object alive and compare it after its consumer returns."""

    def __init__(self, publish: Callable[[list[dict[str, Any]]], None]) -> None:
        self.publish = publish
        self.rows: list[dict[str, Any]] = []
        self.objects: list[HistoryInputs] = []
        self.active_profile: int | None = None

    def load(
        self, original: Callable[..., HistoryInputs], kind: str
    ) -> Callable[..., HistoryInputs]:
        @functools.wraps(original)
        def wrapped(*args: Any, **kwargs: Any) -> HistoryInputs:
            if kind == "nested" and self.active_profile is None:
                raise ArithmeticError("nested prerequisite outside receipt")
            if kind == "direct" and self.active_profile is not None:
                raise ArithmeticError("direct prerequisite inside receipt")
            data = original(*args, **kwargs)
            _, found = observe(data)
            self.objects.append(data)
            self.rows.append(
                dict(
                    index=len(self.rows),
                    kind=kind,
                    load=self.record(found),
                    after_caller=None,
                    after_archive=None,
                )
            )
            self.publish(self.rows)
            return data

        return wrapped

    @staticmethod
    def record(found: Observation) -> dict[str, Any]:
        return dict(
            witness=found.witness,
            semantic_sha256=found.semantic_sha256,
            mutable_count=found.mutable_count,
            array_count=found.array_count,
        )

    def check(self, index: int, field: str) -> None:
        _, found = observe(self.objects[index])
        current = self.record(found)
        if current != self.rows[index]["load"]:
            raise ArithmeticError("prerequisite graph changed during " + field)
        self.rows[index][field] = current
        self.publish(self.rows)

    def profile(
        self, original: Callable[..., dict[str, Any]]
    ) -> Callable[..., dict[str, Any]]:
        @functools.wraps(original)
        def wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
            if self.active_profile is not None:
                raise ArithmeticError("nested receipt profile unsupported")
            index = len(self.rows)
            self.active_profile = index
            try:
                result = original(*args, **kwargs)
                if len(self.rows) != index + 1 or self.rows[index]["kind"] != "nested":
                    raise ArithmeticError("receipt prerequisite count changed")
                self.check(index, "after_caller")
                return result
            finally:
                self.active_profile = None

        return wrapped

    def finish(self) -> None:
        if len(self.rows) != 7 or [r["kind"] for r in self.rows] != ["nested"] * 6 + [
            "direct"
        ]:
            raise ArithmeticError("complete archive prerequisite order changed")
        for index in range(7):
            self.check(index, "after_archive")
        if len({r["load"]["witness"] for r in self.rows}) != 1:
            raise ArithmeticError("fresh prerequisite contents changed")
        if len({r["load"]["semantic_sha256"] for r in self.rows}) != 1:
            raise ArithmeticError("fresh prerequisite semantic inventory changed")


@contextmanager
def instrument(capture: Capture) -> Iterator[None]:
    """Replace only importing aliases; restore all four bindings on every exit."""
    original_frozen: ModuleType = vars(frozen)["inputs"]
    original_study: ModuleType = vars(study)["inputs"]
    original_reduction: Callable[..., dict[str, Any]] = vars(reduction)["read_profile"]
    original_cost: Callable[..., dict[str, Any]] = vars(cost)["read_profile"]
    if (
        original_reduction is not original_cost
        or original_frozen.prerequisites is not original_study.prerequisites
    ):
        raise ArithmeticError("original prerequisite/receipt aliases changed")
    nested_alias = ModuleAlias(
        original_frozen,
        "prerequisites",
        capture.load(original_frozen.prerequisites, "nested"),
    )
    direct_alias = ModuleAlias(
        original_study,
        "prerequisites",
        capture.load(original_study.prerequisites, "direct"),
    )
    wrapped_profile = capture.profile(original_reduction)
    try:
        vars(frozen)["inputs"] = nested_alias
        vars(study)["inputs"] = direct_alias
        vars(reduction)["read_profile"] = wrapped_profile
        vars(cost)["read_profile"] = wrapped_profile
        yield
    finally:
        vars(cost)["read_profile"] = original_cost
        vars(reduction)["read_profile"] = original_reduction
        vars(study)["inputs"] = original_study
        vars(frozen)["inputs"] = original_frozen


def read(root: Path, capture: Capture) -> dict[str, Any]:
    """Run the unchanged saved-archive reader and retain its original output."""
    with instrument(capture):
        saved, returned = study.read_saved(
            root, root / "results/reduced-batch-study/own.json"
        )
    if not capture.objects or returned is not capture.objects[-1]:
        raise ArithmeticError("archive returned a different prerequisite object")
    capture.finish()
    return saved
