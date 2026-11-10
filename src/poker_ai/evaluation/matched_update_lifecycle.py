"""Retain early destination failures and time complete frozen child commands.

This additive CLI does not change any numerical worker or scientific cap. It
checks all output destinations before launch, never deletes them, and retains
both the exact child receipt and the measured receipt. Publication and final
replay share the original 180-second tiny-proof clock, measured from this parent.
The small administrative measurement receipt is written after the child clock.
"""

import argparse
import hashlib
import json
import math
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import digest

CONFIG = "configs/matched-update-lifecycle.json"
CONFIG_SHA = "bcd09b1e7cdee209920a05c431dd78f1af65f2977a658e8d0e27817a76fddee6"
FOLDER = "results/matched-update-pipeline/"
CAPS = dict(
    tiny_own=180,
    tiny_native=180,
    profile=900,
    timing_native=900,
    study=7200,
    real_native=900,
)


def contract(root: Path) -> None:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("lifecycle IO contract changed")
    saved = json.loads((root / CONFIG).read_text())
    if digest(root / saved["parent_config"]) != saved["parent_sha256"]:
        raise ArithmeticError("parent IO contract changed")


def child_path(path: Path) -> Path:
    return path.with_name(path.stem + "-child.json")


def destinations(path: Path, *, archives: bool, report: bool) -> list[Path]:
    candidates = [
        path,
        path.with_suffix(".tmp"),
        child_path(path),
        child_path(path).with_suffix(".tmp"),
    ]
    if archives:
        for name in ("captures", "masses", "profiles"):
            archive = path.with_name(path.stem + "-" + name + ".jsonl.gz")
            candidates.extend((archive, archive.with_suffix(".tmp")))
    if report:
        candidates.append(path.parent / "report")
    return candidates


def fresh(paths: list[Path]) -> None:
    existing = [str(p) for p in paths if p.exists() or p.is_symlink()]
    if existing:
        raise FileExistsError(
            "retain existing matched-update destinations: " + ", ".join(existing)
        )


def measured(root: Path, path: Path, kind: str) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    m: dict[str, Any] = saved["complete_command"]
    child = child_path(path)
    if (
        m["kind"] != kind
        or type(m["returncode"]) is not int
        or m["returncode"] != 0
        or m["source_sha256"] != saved["source_sha256"]
        or m["child_file"] != child.name
        or digest(child) != m["child_sha256"]
        or json.loads(child.read_text())
        != {k: v for k, v in saved.items() if k != "complete_command"}
        or type(m["seconds"]) not in (int, float)
        or not math.isfinite(m["seconds"])
        or not 0 <= m["seconds"] < CAPS[kind]
    ):
        raise ArithmeticError("incomplete/changed complete-command receipt")
    if kind == "timing_native" and not 2 * m["seconds"] < 900:
        raise ArithmeticError("complete native overhead fails twice-elapsed gate")
    if kind == "tiny_native" and (
        type(m["shared_seconds"]) not in (int, float)
        or not math.isfinite(m["shared_seconds"])
        or not 0 <= m["shared_seconds"] < 180
    ):
        raise ArithmeticError("complete tiny proof exceeded shared clock")
    return m


def prerequisites(root: Path, kind: str, own: Path | None) -> None:
    if kind == "tiny_own":
        return
    if kind == "tiny_native":
        assert own is not None
        m = measured(root, own, "tiny_own")
        if (
            m["hostname"] != socket.gethostname()
            or not 0 <= time.perf_counter() - m["started_perf_counter"] < 180
        ):
            raise ArithmeticError("tiny proof clock expired or changed host")
        return
    measured(root, root / FOLDER / "software-own.json", "tiny_own")
    measured(root, root / FOLDER / "software-native.json", "tiny_native")
    if kind == "profile":
        return
    measured(root, root / FOLDER / "profile.json", "profile")
    if kind == "timing_native":
        return
    measured(root, root / FOLDER / "overhead/native.json", "timing_native")
    if kind == "real_native":
        assert own is not None
        measured(root, own, "study")


def finish(
    path: Path,
    kind: str,
    command: list[str],
    started: float,
    returncode: int,
    own: Path | None,
) -> None:
    """Preserve exact child bytes; append measurements without changing its values."""
    raw = path.read_bytes()
    saved: dict[str, Any] = json.loads(raw)
    target = child_path(path)
    with target.open("xb") as stream:
        stream.write(raw)
    now = time.perf_counter()
    m: dict[str, Any] = dict(
        kind=kind,
        command=command,
        returncode=returncode,
        seconds=now - started,
        started_perf_counter=started,
        hostname=socket.gethostname(),
        child_file=target.name,
        child_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256=saved["source_sha256"],
        measurement_scope=(
            "complete child with preflight, prerequisites, startup and final writes; "
            "excludes subsequent administrative measurement receipt"
        ),
    )
    if kind == "tiny_native":
        assert own is not None
        origin = json.loads(own.read_text())["complete_command"]
        m["shared_seconds"] = now - origin["started_perf_counter"]
    saved["complete_command"] = m
    persist(path, saved)


def execute(root: Path, arguments: list[str]) -> int:
    started = time.perf_counter()
    contract(root)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "operation", choices=("check", "profile", "study", "audit", "report")
    )
    for key in ("output", "overhead", "own", "replay"):
        parser.add_argument("--" + key, type=Path)
    parser.add_argument("--record-checks", nargs=2)
    for key in ("admit", "tiny", "timing"):
        parser.add_argument("--" + key, action="store_true")
    args, _ = parser.parse_known_args(arguments)
    command = [
        sys.executable,
        "-m",
        "poker_ai.evaluation.matched_update_parent_io",
        *arguments,
    ]
    if "--help" in arguments:
        return subprocess.run(command, cwd=root, check=False).returncode
    kind: str | None = None
    if args.operation == "check" and not (
        args.replay or args.record_checks or args.admit
    ):
        kind = "tiny_own"
    elif args.operation == "profile":
        kind = "profile"
    elif args.operation == "study":
        kind = "study"
    elif args.operation == "audit":
        kind = (
            "tiny_native"
            if args.tiny
            else "timing_native"
            if args.timing
            else "real_native"
        )
    if kind is None:
        if args.admit:
            prerequisites(root, "study", None)
        return subprocess.run(command, cwd=root, check=False).returncode
    if args.output is None:
        raise ValueError("lifecycle compute commands require explicit --output")
    output = root / args.output
    own = root / args.own if args.own else None
    try:
        paths = destinations(
            output, archives=kind in ("tiny_own", "study"), report=kind == "study"
        )
        if kind == "profile":
            if args.overhead is None:
                raise ValueError("profile requires explicit --overhead")
            paths.extend(destinations(root / args.overhead, archives=True, report=True))
        fresh(paths)
        prerequisites(root, kind, own)
    except BaseException as error:
        rejection = (
            output.parent
            / "rejections"
            / (output.stem + "-" + str(time.time_ns()) + ".json")
        )
        persist(
            rejection,
            dict(
                status="rejected_before_child",
                kind=kind,
                failure=dict(type=type(error).__name__, reason=str(error)),
                command=command,
                child_launched=False,
                training_performed=False,
                reference_constructed=False,
                seconds=time.perf_counter() - started,
            ),
        )
        raise
    result = subprocess.run(
        command, cwd=root, env={**os.environ, "PYTHONPATH": "src"}, check=False
    )
    if output.exists():
        finish(output, kind, command, started, result.returncode, own)
    if result.returncode:
        return result.returncode
    measured(root, output, kind)
    return 0


def main() -> int:
    return execute(Path(__file__).resolve().parents[3], sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
