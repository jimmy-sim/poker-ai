"""Seven fresh archived prerequisite loads; no cache or native construction."""

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
from prerequisite_identity_support import (
    PrerequisiteGraph,
    disjoint,
    observe,
    pinned_bytes,
)

from poker_ai.evaluation.frozen_batch_inputs import prerequisites

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 180
CALLS = 7
VERSIONS = {"3.11.17": "2.4.6", "3.12.15": "2.5.4"}


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
        raise ArithmeticError("actual locked runtime differs from prospective protocol")
    head, dirty = revision()
    if dirty or "pyspiel" in sys.modules:
        raise ArithmeticError("clean source and reference-free process required")
    before = pinned_bytes(ROOT)
    state: dict[str, Any] = {
        "status": "running",
        "head": head,
        "dirty": dirty,
        "python": version,
        "numpy": np.__version__,
        "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "hardware": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpus": os.cpu_count(),
        },
        "seed": None,
        "limit_seconds": LIMIT,
        "expected_calls": CALLS,
        "input_sha256": before,
        "observations": [],
    }
    receipt = folder / "child.json"
    write(receipt, state)
    graphs: list[PrerequisiteGraph] = []
    started = time.perf_counter()
    cpu = time.process_time()
    for index in range(CALLS):
        loaded = prerequisites(ROOT)
        graph, found = observe(loaded)
        for earlier in graphs:
            disjoint(earlier, graph)
        graphs.append(graph)
        state["observations"].append(
            {
                "index": index,
                "witness": found.witness,
                "semantic_sha256": found.semantic_sha256,
                "mutable_count": found.mutable_count,
                "array_count": found.array_count,
                "elapsed_seconds": time.perf_counter() - started,
                "parent_cpu_seconds": time.process_time() - cpu,
            }
        )
        write(receipt, state)
        print("completed prerequisite load", index + 1, flush=True)
    observations = state["observations"]
    if (
        len({row["witness"] for row in observations}) != 1
        or len({row["semantic_sha256"] for row in observations}) != 1
        or pinned_bytes(ROOT) != before
        or revision() != (head, False)
        or "pyspiel" in sys.modules
    ):
        raise ArithmeticError("prerequisite identity, inputs or source changed")
    state.update(
        status="seven_identical_fresh_disjoint_prerequisites",
        elapsed_seconds=time.perf_counter() - started,
        parent_cpu_seconds=time.process_time() - cpu,
    )
    write(receipt, state)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: audit_receipt_prerequisites.py OUTPUT [--child]")
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
        {
            "status": status,
            "returncode": code,
            "outer_elapsed_seconds": elapsed,
            "outer_cap_seconds": LIMIT,
            "child_receipt_present": (folder / "child.json").is_file(),
        },
    )
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
