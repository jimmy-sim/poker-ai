"""One original saved-archive read with seven read-only prerequisite witnesses."""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from prerequisite_identity_support import pinned_bytes
from receipt_consumer_mutation_support import Capture, read

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 180
VERSIONS = {"3.11.17": "2.4.6", "3.12.15": "2.5.4"}
OWN = "results/reduced-batch-study/own.json"


def revision() -> tuple[str, bool]:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    return head, dirty


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def child(folder: Path) -> None:
    version = sys.version.split()[0]
    if version not in VERSIONS or np.__version__ != VERSIONS[version]:
        raise ArithmeticError("actual locked runtime differs from protocol")
    head, dirty = revision()
    if dirty or "pyspiel" in sys.modules:
        raise ArithmeticError("clean source and reference-free process required")
    before = pinned_bytes(ROOT)
    own_hash = hashlib.sha256((ROOT / OWN).read_bytes()).hexdigest()
    state: dict[str, Any] = dict(
        status="running",
        head=head,
        dirty=dirty,
        python=version,
        numpy=np.__version__,
        lock_sha256=hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        hardware=dict(
            platform=platform.platform(),
            machine=platform.machine(),
            cpus=os.cpu_count(),
        ),
        seed=None,
        limit_seconds=LIMIT,
        own_sha256=own_hash,
        input_sha256=before,
        observations=[],
    )
    receipt = folder / "child.json"
    write(receipt, state)

    def publish(rows: list[dict[str, Any]]) -> None:
        state["observations"] = rows
        write(receipt, state)

    started, cpu = time.perf_counter(), time.process_time()
    capture = Capture(publish)
    try:
        saved = read(ROOT, capture)
        if (
            pinned_bytes(ROOT) != before
            or hashlib.sha256((ROOT / OWN).read_bytes()).hexdigest() != own_hash
            or revision() != (head, False)
            or "pyspiel" in sys.modules
        ):
            raise ArithmeticError("source, input or reference-free guard changed")
        state.update(
            status="seven_prerequisites_unchanged_through_complete_read",
            saved_status=saved["status"],
            saved_source_sha256=saved["source_sha256"],
            saved_own_replay=saved["own_replay"],
            saved_batch_count=len(saved["batches"]),
            saved_row_count=len(saved["rows"]),
            saved_mass_count=len(saved["masses"]),
            saved_current_count=len(saved["currents"]),
            elapsed_seconds=time.perf_counter() - started,
            parent_cpu_seconds=time.process_time() - cpu,
        )
    except BaseException as error:
        state.update(
            status="failed", failure=dict(type=type(error).__name__, reason=str(error))
        )
        raise
    finally:
        write(receipt, state)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: audit_receipt_consumer_mutation.py OUTPUT [--child]")
    folder = Path(sys.argv[1]).resolve()
    if len(sys.argv) == 3:
        if sys.argv[2] != "--child" or not folder.is_dir():
            raise SystemExit("invalid child invocation")
        child(folder)
        return
    folder.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    with (folder / "child.log").open("x") as stream:
        try:
            result = subprocess.run(
                [sys.executable, __file__, str(folder), "--child"],
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=LIMIT,
                check=False,
            )
            status = "passed" if result.returncode == 0 else "failed"
            code = result.returncode
        except subprocess.TimeoutExpired:
            status, code = "timed_out", None
    elapsed = time.perf_counter() - started
    if status == "passed" and elapsed >= LIMIT:
        status = "timed_out"
    write(
        folder / "outer.json",
        dict(
            status=status,
            returncode=code,
            outer_elapsed_seconds=elapsed,
            outer_cap_seconds=LIMIT,
            child_receipt_present=(folder / "child.json").is_file(),
        ),
    )
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
