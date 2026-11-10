"""Append/fsync raw events as they arrive, preserving progress before final JSON.

This adapts only the parent record container used by the unchanged spawn helper.
Every child's message remains identical; no RNG or numerical operation changes.
"""

import json
import os
from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest


class Journal:
    def __init__(self, path: Path, binding: str, stage: str) -> None:
        if path.exists() or path.is_symlink():
            raise FileExistsError("retain existing raw event journal")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.stream = path.open("xb")
        self.count = 0
        self.stage = stage
        self.stream.write(
            canonical(
                dict(
                    format="poker-ai-private-prefix-events-v1",
                    source_sha256=binding,
                    stage=stage,
                )
            )
            + b"\n"
        )
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def append(self, slot: int, event: dict[str, Any]) -> None:
        self.stream.write(
            canonical(dict(sequence=self.count, slot=slot, event=event)) + b"\n"
        )
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.count += 1

    def close(self) -> dict[str, Any]:
        if not self.stream.closed:
            self.stream.flush()
            os.fsync(self.stream.fileno())
            self.stream.close()
        return dict(
            file=self.path.name,
            sha256=digest(self.path),
            events=self.count,
            stage=self.stage,
        )


class Events(list[dict[str, Any]]):
    def __init__(
        self, journal: Journal, slot: int, initial: list[dict[str, Any]] | None = None
    ) -> None:
        # Worker cells already occur in the raw worker journal. Keep them in
        # the combined own list without logging them twice; later parent
        # scoring messages use a separate journal slot.
        super().__init__(initial or [])
        self.journal, self.slot = journal, slot

    def append(self, value: dict[str, Any]) -> None:
        super().append(value)
        self.journal.append(self.slot, value)


class Batch(dict[str, Any]):
    def __init__(self, journal: Journal) -> None:
        super().__init__()
        self.journal = journal

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(*args, **kwargs)
        for worker in self.get("workers", []):
            if not isinstance(worker["messages"], Events):
                if worker["messages"]:
                    raise ArithmeticError(
                        "journal adapter requires fresh worker messages"
                    )
                worker["messages"] = Events(self.journal, worker["slot"])


def validate(
    path: Path,
    receipt: dict[str, Any],
    binding: str,
    expected: dict[int, list[dict[str, Any]]],
) -> None:
    if digest(path) != receipt["sha256"]:
        raise ArithmeticError("raw worker journal hash changed")
    groups: dict[int, list[dict[str, Any]]] = {slot: [] for slot in expected}
    with path.open() as stream:
        header = json.loads(next(stream))
        if (
            header["format"] != "poker-ai-private-prefix-events-v1"
            or header["source_sha256"] != binding
            or header["stage"] != receipt["stage"]
        ):
            raise ArithmeticError("raw worker journal header/source changed")
        count = 0
        for line in stream:
            row = json.loads(line)
            if (
                not same(row["sequence"], count)
                or type(row["slot"]) is not int
                or row["slot"] not in groups
            ):
                raise ArithmeticError("raw worker journal sequence/slot changed")
            groups[row["slot"]].append(row["event"])
            count += 1
    if not same(count, receipt["events"]) or not same(
        groups, {slot: list(events) for slot, events in expected.items()}
    ):
        raise ArithmeticError("raw worker journal differs from retained messages")
