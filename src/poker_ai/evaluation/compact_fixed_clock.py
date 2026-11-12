"""Stdlib diagnostic clocks; fixed caps, cutoff reserve and partial retention."""

import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CAPS = {
    "software-own": 180,
    "software-native": 180,
    "own": 900,
    "native": 900,
    "replay": 900,
    "report": 900,
}


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Frozen-policy fixed-opponent diagnosis, no training."
    )
    parser.add_argument("operation", choices=CAPS)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--own", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--checks", type=Path)
    parser.add_argument("--repetition", type=int, choices=(0, 1, 2))
    parser.add_argument("--stop-at")
    parser.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def atomic(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def measurement(path: Path, operation: str) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    m: dict[str, Any] = saved["complete_command"]
    child = path.with_name(path.stem + "-child.json")
    if (
        m["operation"] != operation
        or m["returncode"] != 0
        or type(m["returncode"]) is not int
        or m["interrupted"] is not None
        or m["retained_temporary"] is not None
        or type(m["seconds"]) not in (int, float)
        or not math.isfinite(m["seconds"])
        or not 0 <= m["seconds"] < CAPS[operation]
        or m["child_file"] != child.name
        or child.is_symlink()
        or hashlib.sha256(child.read_bytes()).hexdigest() != m["child_sha256"]
        or json.loads(child.read_text())
        != {k: v for k, v in saved.items() if k != "complete_command"}
    ):
        raise ArithmeticError("incomplete/changed complete-command clock")
    return m


def schedule(operation: str, cutoff: str | None, now: datetime | None = None) -> None:
    if cutoff is None:
        return
    end = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    if end.tzinfo is None:
        raise ValueError("cutoff needs an explicit timezone")
    reserve = 4800 if operation == "own" else CAPS[operation] + 30
    if (end - (now or datetime.now(UTC))).total_seconds() < reserve:
        raise TimeoutError("full diagnostic/downstream caps do not fit user cutoff")


def execute(root: Path, argv: list[str], started: float) -> int:
    args = arguments(argv)
    path = (root / args.output).resolve()
    child_path = path.with_name(path.stem + "-child.json")
    for destination in (path, child_path, path.with_suffix(path.suffix + ".tmp")):
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("retain previous complete/partial command evidence")
    schedule(args.operation, args.stop_at)
    path.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, POKER_FIXED_STARTED=repr(started))
    command = [
        sys.executable,
        str(root / "scripts/diagnose_compact_fixed.py"),
        *argv,
        "--_child",
    ]
    process = subprocess.Popen(
        command, cwd=root, env=environment, start_new_session=True
    )
    interrupted = None
    try:
        returncode = process.wait(
            timeout=max(0.001, CAPS[args.operation] - (time.perf_counter() - started))
        )
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        interrupted = type(error).__name__
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        returncode = 124 if isinstance(error, subprocess.TimeoutExpired) else 130
    elapsed = time.perf_counter() - started
    temporary = path.with_suffix(path.suffix + ".tmp")
    retained = None
    if temporary.exists():
        raw = temporary.read_bytes()
        fingerprint = hashlib.sha256(raw).hexdigest()
        retained_path = path.with_name(
            path.stem + "-partial-" + fingerprint[:12] + ".tmp"
        )
        with retained_path.open("xb") as stream:
            stream.write(raw)
        retained = dict(file=retained_path.name, sha256=fingerprint)
        temporary.unlink()
        if returncode == 0:
            returncode = 1
    if path.exists():
        raw = path.read_bytes()
        saved = json.loads(raw)
    else:
        saved = dict(
            status="failed_before_child_receipt",
            failure=interrupted or "child exited",
            actual_admission=False,
            fresh_global_admission=False,
        )
        raw = json.dumps(saved, sort_keys=True).encode()
    with child_path.open("xb") as stream:
        stream.write(raw)
    saved["complete_command"] = dict(
        operation=args.operation,
        command=command,
        returncode=returncode,
        seconds=elapsed,
        interrupted=interrupted,
        retained_temporary=retained,
        child_file=child_path.name,
        child_sha256=hashlib.sha256(raw).hexdigest(),
        scope=(
            "startup/imports/prerequisites/work/replay/writes; "
            "excludes subsequent administrative clock copy"
        ),
    )
    atomic(path, saved)
    return returncode
