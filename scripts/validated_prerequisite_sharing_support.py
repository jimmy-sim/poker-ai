"""Test sharing one graph only after each original loader has fully validated."""

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Any

from prerequisite_identity_support import PrerequisiteGraph, disjoint, observe
from receipt_consumer_mutation_support import Capture, instrument

from poker_ai.evaluation import reduced_study_run as study
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs


class ValidatedShare(Capture):
    """Use the first returned graph inside one original saved-archive read.

    Every call invokes its unmodified loader first. The retained first graph
    is passed to later original consumers only after exact and independent
    equality checks. The inherited caller/root checks detect subsequent edits.
    """

    def __init__(self, publish: Callable[[list[dict[str, Any]]], None]) -> None:
        super().__init__(publish)
        self.donor: HistoryInputs | None = None
        self.donor_graph: PrerequisiteGraph | None = None

    def load(
        self, original: Callable[..., HistoryInputs], kind: str
    ) -> Callable[..., HistoryInputs]:
        @functools.wraps(original)
        def wrapped(*args: Any, **kwargs: Any) -> HistoryInputs:
            if kind == "nested" and self.active_profile is None:
                raise ArithmeticError("nested prerequisite outside receipt")
            if kind == "direct" and self.active_profile is not None:
                raise ArithmeticError("direct prerequisite inside receipt")
            fresh = original(*args, **kwargs)
            graph, found = observe(fresh)
            witness = self.record(found)
            index = len(self.rows)
            if index == 0:
                if kind != "nested" or self.donor is not None:
                    raise ArithmeticError("first validated donor must be nested")
                self.donor, self.donor_graph = fresh, graph
            else:
                if self.donor is None or self.donor_graph is None:
                    raise ArithmeticError("validated donor missing")
                if witness != self.rows[0]["load"]:
                    raise ArithmeticError("fresh prerequisite differs from donor")
                disjoint(self.donor_graph, graph)
                if self.record(observe(self.donor)[1]) != self.rows[0]["load"]:
                    raise ArithmeticError("shared donor changed before later call")
            if self.donor is None:
                raise ArithmeticError("validated donor missing")
            self.objects.append(self.donor)
            self.rows.append(
                dict(
                    index=index,
                    kind=kind,
                    load=witness,
                    fresh=witness,
                    substituted=index > 0,
                    after_caller=None,
                    after_archive=None,
                )
            )
            self.publish(self.rows)
            return self.donor

        return wrapped

    def finish(self) -> None:
        super().finish()
        if [row["substituted"] for row in self.rows] != [False] + [True] * 6:
            raise ArithmeticError("validated sharing substitution count changed")
        if any(row["fresh"] != row["load"] for row in self.rows):
            raise ArithmeticError("original fresh output differs from donor")


def read_saved(
    root: Path, path: Path, capture: ValidatedShare
) -> tuple[dict[str, Any], HistoryInputs]:
    """Run one unchanged original archive reader with root-local sharing."""
    with instrument(capture):
        saved, returned = study.read_saved(root, path)
    if returned is not capture.donor or returned is not capture.objects[-1]:
        raise ArithmeticError("archive returned a different prerequisite graph")
    capture.finish()
    return saved, returned


def read(root: Path, path: Path, capture: ValidatedShare) -> dict[str, Any]:
    """Return the saved receipt for the reference-free own proof."""
    saved, _ = read_saved(root, path, capture)
    return saved
