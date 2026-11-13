"""Complete child-command clocks and retained failures, using only the stdlib.

The clock starts before importing the numerical runner. Child startup,
preflight, prerequisites and final writes count. Administrative measurement
copying happens afterward and is explicitly identified in the receipt.
"""

import argparse
import hashlib
import json
import math
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CAPS = {
    "software-own": 180,
    "software-audit": 180,
    "cost-own": 900,
    "cost-audit": 900,
    "study": 7200,
    "audit": 900,
    "checks": 900,
    "forecast": 900,
    "admit": 900,
    "replay": 900,
    "report": 900,
}


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Own-opponent software, cost and gated known-game research."
    )
    parser.add_argument("operation", choices=CAPS)
    parser.add_argument("--own", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ci", type=Path)
    parser.add_argument("--local", type=Path)
    parser.add_argument("--repetition", type=int, choices=(0, 1, 2))
    parser.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--stop-at")
    args = parser.parse_args(argv)
    if args.operation.startswith("cost-") and args.repetition is None:
        parser.error("cost commands require --repetition 0, 1 or 2")
    return args


def output_path(root: Path, args: argparse.Namespace) -> Path:
    if args.output is not None:
        return root / Path(args.output)
    if args.operation == "software-own":
        return root / "results/compact-cached-learning/software/own.json"
    if args.operation == "software-audit":
        return root / "results/compact-cached-learning/software/native.json"
    if args.operation in ("cost-own", "cost-audit"):
        if args.repetition is None:
            raise ValueError("cost commands require the fixed repetition coordinate")
        name = "own" if args.operation == "cost-own" else "native"
        return (
            root
            / "results/compact-cached-learning/cost"
            / str(args.repetition)
            / f"{name}.json"
        )
    if args.operation in ("checks", "forecast", "admit", "study", "audit"):
        name = {
            "checks": "code-checks",
            "admit": "admission",
            "study": "own",
            "audit": "native",
            "forecast": "forecast",
        }[args.operation]
        return root / f"results/compact-cached-learning/{name}.json"
    raise ValueError("read-only commands require an explicit fresh --output")


def atomic(path: Path, saved: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(saved, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def child_path(path: Path) -> Path:
    return path.with_name(path.stem + "-child.json")


def preserve_temporary(path: Path) -> dict[str, Any] | None:
    """Keep exact interrupted-write bytes before recording a failure receipt."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    if not temporary.exists() and not temporary.is_symlink():
        return None
    if temporary.is_symlink():
        raise FileExistsError("retain unexpected temporary symlink")
    raw = temporary.read_bytes()
    fingerprint = hashlib.sha256(raw).hexdigest()
    retained = path.with_name(path.stem + "-partial-" + fingerprint[:12] + ".tmp")
    if retained.exists():
        if retained.read_bytes() != raw:
            raise FileExistsError("retain conflicting interrupted-write evidence")
    else:
        with retained.open("xb") as out:
            out.write(raw)
    temporary.unlink()
    return dict(file=retained.name, sha256=fingerprint, bytes=len(raw))


def measurement(path: Path, kind: str) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    m: dict[str, Any] = saved["complete_command"]
    child = child_path(path)
    if (
        m["operation"] != kind
        or m.get("interrupted") is not None
        or m.get("retained_temporary") is not None
        or type(m["returncode"]) is not int
        or m["returncode"] != 0
        or type(m["seconds"]) not in (int, float)
        or not 0 <= m["seconds"] < CAPS[kind]
        or type(m["started_perf_counter"]) not in (int, float)
        or not math.isfinite(m["started_perf_counter"])
        or m["started_perf_counter"] <= 0
        or m["source_sha256"] != saved["source_sha256"]
        or m["child_file"] != child.name
        or hashlib.sha256(child.read_bytes()).hexdigest() != m["child_sha256"]
        or json.dumps(json.loads(child.read_text()), sort_keys=True, allow_nan=False)
        != json.dumps(
            {k: v for k, v in saved.items() if k != "complete_command"},
            sort_keys=True,
            allow_nan=False,
        )
    ):
        raise ArithmeticError("incomplete or changed complete-command measurement")
    if kind == "software-audit" and (
        type(m["shared_seconds"]) not in (int, float)
        or not 0 <= m["shared_seconds"] < 180
    ):
        raise ArithmeticError("full software proof exceeded its shared180-second clock")
    return m


def schedule(operation: str, cutoff: str | None, now: datetime | None = None) -> None:
    if cutoff is None:
        return
    end = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    if end.tzinfo is None:
        raise ValueError("cutoff needs an explicit timezone")
    reserve = 11100 if operation == "study" else CAPS[operation] + 30
    if (end - (now or datetime.now(UTC))).total_seconds() < reserve:
        raise TimeoutError("full prescribed compact stage caps do not fit cutoff")


def execute(root: Path, argv: list[str], started: float) -> int:
    args = arguments(argv)
    schedule(args.operation, args.stop_at)
    path = output_path(root, args)
    if args.operation == "report":
        if path.exists() or path.is_symlink():
            raise FileExistsError("retain existing report destination")
        receipt = path.with_name(path.name + "-receipt.json")
    else:
        receipt = path
    destinations = [
        receipt,
        receipt.with_suffix(receipt.suffix + ".tmp"),
        child_path(receipt),
        receipt.with_name(receipt.stem + "-events.jsonl"),
    ]
    if args.operation in ("software-own", "cost-own", "study"):
        destinations.append(path.parent / "report")
        for name in ("captures", "masses", "warms", "composed", "details"):
            archive = path.parent / f"own-{name}.jsonl.gz"
            destinations.extend((archive, archive.with_suffix(".tmp")))
    for candidate in destinations:
        if candidate.exists() or candidate.is_symlink():
            raise FileExistsError("retain complete/partial own-opponent output")
    own_path = root / (args.own or "results/compact-cached-learning/software/own.json")
    hard_end = started + CAPS[args.operation]
    if args.operation == "software-audit":
        origin = measurement(own_path, "software-own")
        if origin["hostname"] != socket.gethostname():
            raise ArithmeticError("software publication clock changed host")
        age = time.perf_counter() - origin["started_perf_counter"]
        if not origin["seconds"] <= age < 180:
            raise TimeoutError(
                "software own publication clock expired; retain prior proof"
            )
        hard_end = origin["started_perf_counter"] + 180
    environment = dict(os.environ)
    environment["POKER_COMPACT_OPPONENT_STARTED"] = repr(started)
    command = [
        sys.executable,
        str(root / "scripts/validate_cached_compact.py"),
        *argv,
        "--_child",
    ]
    receipt.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        command, cwd=root, env=environment, start_new_session=True
    )
    interrupted: str | None = None
    try:
        returncode = process.wait(timeout=max(0.001, hard_end - time.perf_counter()))
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        interrupted = type(exc).__name__
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        returncode = 124 if isinstance(exc, subprocess.TimeoutExpired) else 130
    now = time.perf_counter()
    retained_temporary = preserve_temporary(receipt)
    if retained_temporary is not None and returncode == 0:
        returncode = 1
    if receipt.exists():
        raw = receipt.read_bytes()
        with child_path(receipt).open("xb") as out:
            out.write(raw)
        saved: dict[str, Any] = json.loads(raw)
    else:
        saved = dict(
            status="failed_before_child_receipt",
            failure=interrupted or "child exited before receipt",
            source_sha256=None,
            long_run_admitted=False,
            new_agent_default=False,
            fresh_global_admission=False,
        )
        raw = json.dumps(saved, sort_keys=True, allow_nan=False).encode()
        with child_path(receipt).open("xb") as out:
            out.write(raw)
    m = dict(
        operation=args.operation,
        command=command,
        returncode=returncode,
        seconds=now - started,
        started_perf_counter=started,
        hostname=socket.gethostname(),
        child_file=child_path(receipt).name,
        child_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256=saved["source_sha256"],
        interrupted=interrupted,
        child_exitcode=getattr(process, "returncode", None),
        retained_temporary=retained_temporary,
        scope=(
            "Complete child startup/preflight/prerequisites/work/writes; "
            "excludes this subsequent administrative copy/measurement receipt."
        ),
    )
    if args.operation == "software-audit":
        origin = measurement(own_path, "software-own")
        m["shared_seconds"] = now - origin["started_perf_counter"]
    saved["complete_command"] = m
    atomic(receipt, saved)
    return returncode
