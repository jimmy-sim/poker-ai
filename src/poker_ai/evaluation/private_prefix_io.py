"""Retain every own event and fresh archive destination, including failures."""

from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_artifacts import write_archive

PHASES = dict(capture="captures", mass="masses", profile="rows", fixed="fixed_matches")


def destinations(path: Path) -> list[Path]:
    candidates = [
        path,
        path.with_suffix(".tmp"),
        path.parent / "report",
        path.with_name(path.stem + "-child.json"),
    ]
    for name in ("captures", "masses", "profiles", "baseline", "baseline_extra"):
        archive = path.with_name(path.stem + "-" + name + ".jsonl.gz")
        candidates.extend((archive, archive.with_suffix(".tmp")))
    return candidates


def fresh(path: Path) -> None:
    if any(p.exists() or p.is_symlink() for p in destinations(path)):
        raise FileExistsError("retain existing complete/partial private-prefix attempt")


def gather(saved: dict[str, Any]) -> None:
    """Raw events are retained even if a later event fails validation."""
    for name in PHASES.values():
        saved[name] = []
    started, initialized = set(), set()
    for event in saved["events"]:
        if event["kind"] != "cell":
            raise ArithmeticError("unknown own private-prefix event kind")
        index, phase = event["index"], event["phase"]
        if type(index) is not int or not 0 <= index < 48:
            raise ArithmeticError("private-prefix event outside fixed path inventory")
        if phase in PHASES:
            saved[PHASES[phase]].append(event["row"])
        elif phase == "training_started":
            if index in started:
                raise ArithmeticError("duplicate private-prefix training start")
            started.add(index)
        elif phase == "training_initialized":
            if index not in started or index in initialized:
                raise ArithmeticError(
                    "private-prefix initialization without unique start"
                )
            initialized.add(index)
        elif phase != "trained":
            raise ArithmeticError("unknown own private-prefix event phase")
    saved["training_attempted_paths"] = len(started)
    saved["initialized_training_paths"] = len(initialized)
    saved["training_performed"] = bool(initialized)
    for name in PHASES.values():
        saved[name].sort(
            key=lambda r: (
                (r["own_snapshot_id"], r["opponent_profile_id"], r["target"])
                if name == "fixed_matches"
                else (r["path_index"], r["work_label"], r["readout"])
            )
        )


def archive(
    path: Path, saved: dict[str, Any], scratch: Path, key: str, stem: str
) -> None:
    target = path.with_name(path.stem + "-" + stem + ".jsonl.gz")
    if any(p.exists() or p.is_symlink() for p in (target, target.with_suffix(".tmp"))):
        raise FileExistsError("retain private-prefix complete/partial archive")
    prefix = {
        "rows": "details",
        "baseline_rows": "baseline",
        "baseline_extra_rows": "baseline_extra",
    }.get(key, key)
    fingerprint = write_archive(target, scratch, saved[key])
    saved[prefix + "_file"] = target.name
    saved[prefix + "_sha256"] = fingerprint


def retain_partial(path: Path, saved: dict[str, Any], scratch: Path) -> None:
    """Preserve completed rows in archives; never replace a preexisting archive.

    Each destination gets its own error record. A failed archive is not labeled
    complete, and later archive retention is still attempted independently.
    """
    saved.setdefault("retention_errors", [])
    for key, stem in (
        ("captures", "captures"),
        ("masses", "masses"),
        ("rows", "profiles"),
    ):
        prefix = "details" if key == "rows" else key
        if prefix + "_file" in saved or not saved.get(key):
            continue
        try:
            archive(path, saved, scratch, key, stem)
        except BaseException as error:
            saved["retention_errors"].append(
                dict(archive=stem, type=type(error).__name__, reason=str(error))
            )
