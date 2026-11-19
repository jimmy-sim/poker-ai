"""Prospective root-local prerequisite skip with explicit byte and graph guards."""

import functools
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import profile_receipt_cpu as scientific
from prerequisite_identity_support import observe, pinned_bytes
from receipt_consumer_mutation_support import Capture, instrument

from poker_ai.evaluation import batch_cost_inputs as cost
from poker_ai.evaluation import batch_reduction_inputs as reduction
from poker_ai.evaluation import frozen_batch_protocol as frozen
from poker_ai.evaluation import reduced_study_run as study
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.postflop.river_study import digest

SOURCE_FINGERPRINT = "b475bfefb92963f25458d97260264743ff4d751b4513c307529742eaf10fc97d"
LOCK_SHA256 = "db5529861ae56225daaf8a18513013e52bee88ef667227855b719a7e1364250c"
OPERATOR_FILES = (
    "scripts/guarded_prerequisite_skip_support.py",
    "scripts/prove_guarded_prerequisite_skip.py",
    "scripts/compare_guarded_prerequisite_skip.py",
    "scripts/launch_guarded_skip_optional.py",
)


def complete_snapshot(root: Path) -> dict[str, str]:
    """Hash all declared input and current/historical source bytes.

    The original first load validates the content. Later calls require this
    same complete byte inventory, including historical source files absent
    from the present scientific-source fingerprint.
    """
    pins = pinned_bytes(root)
    _, source = scientific.binding(root, clean=True)
    if (
        len(source["sha256"]) != 458
        or source["fingerprint"] != SOURCE_FINGERPRINT
        or pins["uv.lock"] != LOCK_SHA256
    ):
        raise ArithmeticError("guard source or lock changed")
    snapshot: dict[str, str] = dict(pins)
    for name, expected in source["sha256"].items():
        if name in snapshot and snapshot[name] != expected:
            raise ArithmeticError("guard current source overlaps changed pin")
        snapshot[name] = expected
    for pinned_name in pins:
        if not pinned_name.endswith(".json"):
            continue
        saved: dict[str, Any] = json.loads((root / pinned_name).read_bytes())
        archived = saved.get("source")
        if not isinstance(archived, dict) or "sha256" not in archived:
            continue
        files = archived["sha256"]
        if not isinstance(files, dict):
            raise ArithmeticError("historical source inventory changed")
        for name, expected in files.items():
            if (
                not isinstance(name, str)
                or not isinstance(expected, str)
                or Path(name).is_absolute()
                or ".." in Path(name).parts
                or not (root / name).resolve().is_relative_to(root.resolve())
                or len(expected) != 64
            ):
                raise ArithmeticError("historical source path or digest changed")
            if digest(root / name) != expected:
                raise ArithmeticError("historical source bytes changed: " + name)
            if name in snapshot and snapshot[name] != expected:
                raise ArithmeticError("historical source conflicts with current pin")
            snapshot[name] = expected
    for name in OPERATOR_FILES:
        if name in snapshot:
            raise ArithmeticError("guard operator overlaps historical source")
        snapshot[name] = digest(root / name)
    if len(snapshot) != 486:
        raise ArithmeticError("incomplete closed prerequisite byte inventory")
    return snapshot


class GuardedSkip(Capture):
    """Call the original loader once per root, then guard six donor returns."""

    def __init__(
        self,
        root: Path,
        publish: Callable[[list[dict[str, Any]]], None],
        snapshot: Callable[[Path], dict[str, str]] = complete_snapshot,
    ) -> None:
        super().__init__(publish)
        self.root = root
        self.snapshot = snapshot
        self.baseline: dict[str, str] | None = None
        self.donor: HistoryInputs | None = None
        self.witness: dict[str, Any] | None = None
        self.original_loader: Callable[..., HistoryInputs] | None = None
        self.aliases: tuple[object, ...] | None = None

    @staticmethod
    def current_aliases() -> tuple[object, ...]:
        return (
            vars(frozen)["inputs"],
            vars(study)["inputs"],
            vars(reduction)["read_profile"],
            vars(cost)["read_profile"],
        )

    def guard(self) -> None:
        if self.aliases is None:
            self.aliases = self.current_aliases()
        elif self.current_aliases() != self.aliases:
            raise ArithmeticError("guarded prerequisite alias changed")
        actual = self.snapshot(self.root)
        if self.baseline is None:
            self.baseline = actual
        elif actual != self.baseline:
            raise ArithmeticError("guarded prerequisite pinned bytes changed")

    def load(
        self, original: Callable[..., HistoryInputs], kind: str
    ) -> Callable[..., HistoryInputs]:
        if self.original_loader is None:
            self.original_loader = original
        elif original is not self.original_loader:
            raise ArithmeticError("original prerequisite loader alias changed")

        @functools.wraps(original)
        def wrapped(*args: Any, **kwargs: Any) -> HistoryInputs:
            if len(args) != 1 or kwargs or args[0] != self.root:
                raise ArithmeticError("guarded prerequisite root or arguments changed")
            if kind == "nested" and self.active_profile is None:
                raise ArithmeticError("nested prerequisite outside receipt")
            if kind == "direct" and self.active_profile is not None:
                raise ArithmeticError("direct prerequisite inside receipt")
            index = len(self.rows)
            if (index < 6 and kind != "nested") or (index == 6 and kind != "direct"):
                raise ArithmeticError("guarded prerequisite call order changed")
            if index >= 7:
                raise ArithmeticError("extra prerequisite call")
            self.guard()
            if index == 0:
                data = original(*args, **kwargs)
                self.guard()
                _, found = observe(data)
                self.donor = data
                self.witness = self.record(found)
            else:
                if self.donor is None or self.witness is None:
                    raise ArithmeticError("guarded prerequisite donor missing")
                data = self.donor
                _, found = observe(data)
                if self.record(found) != self.witness:
                    raise ArithmeticError("guarded prerequisite donor changed")
            if self.witness is None:
                raise ArithmeticError("guarded prerequisite witness missing")
            self.objects.append(data)
            self.rows.append(
                dict(
                    index=index,
                    kind=kind,
                    load=self.witness,
                    original_called=index == 0,
                    guarded_return=index > 0,
                    after_caller=None,
                    after_archive=None,
                )
            )
            self.publish(self.rows)
            return data

        return wrapped

    def check(self, index: int, field: str) -> None:
        self.guard()
        super().check(index, field)

    def finish(self) -> None:
        super().finish()
        if (
            [row["original_called"] for row in self.rows] != [True] + [False] * 6
            or [row["guarded_return"] for row in self.rows] != [False] + [True] * 6
            or any(data is not self.donor for data in self.objects)
        ):
            raise ArithmeticError("guarded prerequisite skip inventory changed")


def read_saved(
    root: Path, path: Path, capture: GuardedSkip
) -> tuple[dict[str, Any], HistoryInputs]:
    """Run the original saved reader with one guarded donor per root."""
    with instrument(capture):
        saved, returned = study.read_saved(root, path)
        if returned is not capture.donor or returned is not capture.objects[-1]:
            raise ArithmeticError("archive returned a different prerequisite graph")
        capture.finish()
    return saved, returned


def read(root: Path, path: Path, capture: GuardedSkip) -> dict[str, Any]:
    saved, _ = read_saved(root, path, capture)
    return saved
