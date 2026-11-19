"""Bound one reference-free original archive read with guarded skipping."""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from audit_receipt_consumer_mutation import revision, write
from guarded_prerequisite_skip_support import GuardedSkip, complete_snapshot, read

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 180
OWN = "results/reduced-batch-study/own.json"
CHECKS = "results/guarded-prerequisite-skip/source-checks/manifest.json"
VERSIONS = {"3.11.17": "2.4.6", "3.12.15": "2.5.4"}
SOURCE_FILES = (
    "scripts/guarded_prerequisite_skip_support.py",
    "scripts/prove_guarded_prerequisite_skip.py",
    "scripts/compare_guarded_prerequisite_skip.py",
    "scripts/launch_guarded_skip_optional.py",
)


def source_checks() -> dict[str, Any]:
    from compact_suit.admission import published

    checks = ROOT / CHECKS
    published(ROOT, checks)
    saved: dict[str, Any] = json.loads(checks.read_bytes())
    if saved["status"] != "six_roles_qualified_before_guarded_skip_proof" or set(
        saved["source_files"]
    ) != set(SOURCE_FILES):
        raise ArithmeticError("published guarded-skip source qualification required")
    source_members(checks.parent, saved, published)
    checked = saved["checked_commit"]
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", checked, "HEAD"],
        cwd=ROOT,
        check=True,
    )
    for name in SOURCE_FILES:
        current = (ROOT / name).read_bytes()
        original = subprocess.check_output(
            ["git", "show", f"{checked}:{name}"], cwd=ROOT
        )
        if (
            current != original
            or hashlib.sha256(current).hexdigest() != saved["source_files"][name]
        ):
            raise ArithmeticError("qualified guarded-skip source changed")
    return saved


def source_members(
    folder: Path,
    saved: dict[str, Any],
    published: Callable[[Path, Path], None],
) -> None:
    """Require every archived qualification byte in the pushed Git tree.

    The manifest itself is checked separately. A listed ignored file cannot
    satisfy `published`, even if it exists in the collecting checkout.
    """
    files = saved["files"]
    if not isinstance(files, list) or len(files) < 30:
        raise ArithmeticError("complete source-check member list required")
    names: set[str] = set()
    for member in files:
        name = member["file"]
        if (
            not isinstance(name, str)
            or not name
            or name in names
            or Path(name).is_absolute()
            or ".." in Path(name).parts
        ):
            raise ArithmeticError("source-check member changed or escaped")
        path = folder / name
        raw = path.read_bytes()
        if (
            len(raw) != member["bytes"]
            or hashlib.sha256(raw).hexdigest() != member["sha256"]
        ):
            raise ArithmeticError("source-check member changed or escaped")
        published(ROOT, path)
        names.add(name)
    required = {
        "hosted/python311.log",
        "hosted/python312.log",
        "local/base311.log",
        "local/base312.log",
        "local/optional311.log",
        "local/optional312.log",
        "local/hooks.log",
        "verify-all.py.txt",
    }
    if not required <= names:
        raise ArithmeticError("source-check role evidence missing")


def child(folder: Path) -> None:
    version = sys.version.split()[0]
    if version not in VERSIONS or np.__version__ != VERSIONS[version]:
        raise ArithmeticError("actual locked runtime differs from protocol")
    head, dirty = revision()
    if dirty or "pyspiel" in sys.modules:
        raise ArithmeticError("clean reference-free source required")
    checked = source_checks()
    before = complete_snapshot(ROOT)
    own_hash = hashlib.sha256((ROOT / OWN).read_bytes()).hexdigest()
    state: dict[str, Any] = dict(
        status="running",
        head=head,
        checked_source_commit=checked["checked_commit"],
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
        reference_constructed=False,
        new_postflop_training_performed=False,
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
    capture = GuardedSkip(ROOT, publish)
    try:
        saved = read(ROOT, ROOT / OWN, capture)
        if (
            complete_snapshot(ROOT) != before
            or hashlib.sha256((ROOT / OWN).read_bytes()).hexdigest() != own_hash
            or revision() != (head, False)
            or "pyspiel" in sys.modules
        ):
            raise ArithmeticError("source, input or reference-free guard changed")
        state.update(
            status="one_original_loader_six_guarded_returns_complete",
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
        raise SystemExit("usage: prove_guarded_prerequisite_skip.py OUTPUT [--child]")
    folder = Path(sys.argv[1]).resolve()
    if len(sys.argv) == 3:
        if sys.argv[2] != "--child" or not folder.is_dir():
            raise SystemExit("invalid child invocation")
        child(folder)
        return
    if not folder.is_relative_to(ROOT / "results/runs"):
        raise ValueError("fresh ignored own-proof output required")
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
