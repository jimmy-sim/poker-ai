"""Publication gates and durable one-shot execution for row-vector analysis."""

import hashlib
import json
import math
import os
import platform
import resource
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import Any

from known_turn_residual_distribution.analysis import analyze_report, summarize_street

PROTOCOL_COMMIT = "05fe22324a36739ddfb0bd609983a7c91d940707"
PROTOCOL = Path("docs/known-turn-residual-distribution.md")
CONFIG = Path("configs/known-turn-residual-distribution.json")
PRIOR_JOB = Path("results/known-turn-collision-medium-transfer/report/job-state.json")
PRIOR_JOB_SHA256 = "6f7cf51e810a00a14dfd040b19c86e22fc3c779d35d0afde291dd1935dd51414"
ARCHIVE = Path("results/known-turn-residual-distribution")
SOURCE_FILES = (
    "scripts/known_turn_residual_distribution/__init__.py",
    "scripts/known_turn_residual_distribution/analysis.py",
    "scripts/known_turn_residual_distribution/workflow.py",
    "scripts/diagnose_known_turn_residual_distribution.py",
    "tests/test_residual_distribution.py",
    "tests/test_residual_distribution_workflow.py",
    CONFIG.as_posix(),
    PROTOCOL.as_posix(),
    "uv.lock",
)


def digest(path: Path) -> str:
    """Return the SHA-256 of one immutable file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fingerprint(root: Path) -> str:
    """Pin isolated implementation and tests without later evidence commits."""
    hashes = {name: digest(root / name) for name in SOURCE_FILES}
    return hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def clean_head(root: Path) -> str:
    """Require the published prospective commit, exact bytes and clean source."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("residual diagnosis requires clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("published prospective ancestor absent")
    for path in (PROTOCOL, CONFIG):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("published prospective bytes changed")
    return head


def contract(root: Path) -> dict[str, Any]:
    """Check every already published scientific input before any readout."""
    plan: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    for path_key, sha_key in (
        ("report_path", "report_sha256"),
        ("report_manifest_path", "report_manifest_sha256"),
        ("freeze_path", "freeze_sha256"),
    ):
        if digest(root / plan[path_key]) != plan[sha_key]:
            raise ArithmeticError("pinned published input changed")
    if digest(root / "uv.lock") != plan["lock_sha256"]:
        raise ArithmeticError("locked dependency bytes changed")
    return plan


def require_archive(
    root: Path, folder: Path, expected_status: str, fingerprint: str
) -> dict[str, Any]:
    """Check committed archive ancestry and every listed member's bytes."""
    manifest_path = folder / "manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_bytes())
    relative = manifest_path.relative_to(root).as_posix()
    introducing = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", relative],
        cwd=root,
        text=True,
    ).strip()
    if (
        manifest["status"] != expected_status
        or manifest["source_fingerprint"] != fingerprint
        or len(introducing) != 40
        or subprocess.run(
            ["git", "merge-base", "--is-ancestor", introducing, "HEAD"],
            cwd=root,
            check=False,
        ).returncode
        or subprocess.check_output(
            ["git", "show", f"{introducing}:{relative}"], cwd=root
        )
        != manifest_path.read_bytes()
    ):
        raise ArithmeticError("stage publication gate changed")
    listed = manifest["files"]
    if len(listed) != len({row["file"] for row in listed}) or sorted(
        row["file"] for row in listed
    ) != sorted(
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    ):
        raise ArithmeticError("stage file inventory changed")
    for row in listed:
        path = folder / row["file"]
        if (
            path.is_symlink()
            or path.stat().st_size != row["bytes"]
            or digest(path) != row["sha256"]
        ):
            raise ArithmeticError("stage member bytes changed")
    return manifest


def _save(path: Path, value: dict[str, Any]) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _event(path: Path, value: dict[str, Any]) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _start(
    root: Path, output: Path, stage: str
) -> tuple[dict[str, Any], str, str, float]:
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    try:
        head = clean_head(root)
        plan = contract(root)
        fingerprint = source_fingerprint(root)
        _save(
            output / "started.json",
            {
                "status": "started",
                "stage": stage,
                "head": head,
                "source_fingerprint": fingerprint,
                "report_sha256": plan["report_sha256"],
                "lock_sha256": plan["lock_sha256"],
                "python": sys.version.split()[0],
                "hardware": platform.platform(),
                "started_utc": datetime.now(UTC).isoformat(),
            },
        )
        _event(output / "events.jsonl", {"stage": stage, "status": "started"})
        return plan, head, fingerprint, started
    except BaseException as exc:
        _save(
            output / "failed.json",
            {"stage": stage, "status": "failed_preflight", "error": repr(exc)},
        )
        raise


def _finish(output: Path, stage: str, started: float, value: dict[str, Any]) -> None:
    elapsed = time.monotonic() - started
    result = {
        **value,
        "stage": stage,
        "wall_seconds": elapsed,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "finished_utc": datetime.now(UTC).isoformat(),
    }
    _event(output / "events.jsonl", {"stage": stage, "status": result["status"]})
    _save(output / "result.json", result)


def _failure(output: Path, stage: str, started: float, exc: BaseException) -> None:
    _save(
        output / "failed.json",
        {
            "stage": stage,
            "status": "failed",
            "error": repr(exc),
            "wall_seconds": time.monotonic() - started,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "finished_utc": datetime.now(UTC).isoformat(),
        },
    )
    _event(output / "events.jsonl", {"stage": stage, "status": "failed"})


def _forecast(root: Path, plan: dict[str, Any]) -> float:
    if digest(root / PRIOR_JOB) != PRIOR_JOB_SHA256:
        raise ArithmeticError("prior complete report clock changed")
    job = json.loads((root / PRIOR_JOB).read_bytes())
    if (
        job["status"] != "passed"
        or job["source_head"] != plan["report_head"]
        or math.ceil(job["observed_wall_seconds"] * 1000) / 1000
        != plan["prior_report_seconds"]
    ):
        raise ArithmeticError("prior complete report runtime changed")
    bound = (
        plan["forecast_multiplier"] * plan["prior_report_seconds"]
        + plan["failure_save_reserve_seconds"]
    )
    if bound != plan["forecast_seconds"]:
        raise ArithmeticError("prospective forecast arithmetic changed")
    return float(bound)


def _raise_timeout(_signal_number: int, _frame: FrameType | None) -> None:
    raise TimeoutError("reserved computation time exhausted")


def execute(root: Path, output: Path, stage: str) -> None:
    """Run one fictional proof, data-only admission, or admitted diagnosis."""
    if stage not in {"proof", "admission", "analysis"}:
        raise ValueError("unknown residual-distribution stage")
    plan, head, fingerprint, started = _start(root, output, stage)
    try:
        require_archive(
            root, root / ARCHIVE / "source-checks", "source_qualified", fingerprint
        )
        if stage in {"admission", "analysis"}:
            require_archive(root, root / ARCHIVE / "proof", "proof_passed", fingerprint)
        if stage == "proof":
            prior_handler = signal.signal(signal.SIGALRM, _raise_timeout)
            signal.setitimer(signal.ITIMER_REAL, plan["proof_cap_seconds"] - 30)
            try:
                fictional = summarize_street(
                    [0.2, 0.1, 0.0, 0.3],
                    [0.4, 0.0, 0.1, 0.1],
                    [0, 1],
                    top_k=2,
                    concentration_share=0.5,
                    nonnegative_slack=1e-12,
                )
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, prior_handler)
            if (
                abs(fictional["net_change_chips"]) > 1e-12
                or abs(fictional["positive_worsening_chips"] - 0.3) > 1e-12
                or abs(fictional["negative_offset_chips"] - 0.3) > 1e-12
                or time.monotonic() - started >= plan["proof_cap_seconds"]
            ):
                raise ArithmeticError("fictional vector proof failed")
            _finish(
                output,
                stage,
                started,
                {"status": "proof_passed", "head": head, "fictional": fictional},
            )
        elif stage == "admission":
            bound = _forecast(root, plan)
            admitted = bound < plan["analysis_cap_seconds"]
            _finish(
                output,
                stage,
                started,
                {
                    "status": "admitted" if admitted else "rejected",
                    "head": head,
                    "forecast_seconds": bound,
                    "cap_seconds": plan["analysis_cap_seconds"],
                    "prior_job_sha256": PRIOR_JOB_SHA256,
                },
            )
            if not admitted:
                raise ArithmeticError("strict compute admission failed")
        else:
            require_archive(root, root / ARCHIVE / "admission", "admitted", fingerprint)
            decision = json.loads(
                (root / ARCHIVE / "admission" / "result.json").read_bytes()
            )
            if decision["forecast_seconds"] != _forecast(root, plan):
                raise ArithmeticError("published admission changed")
            prior_handler = signal.signal(signal.SIGALRM, _raise_timeout)
            signal.setitimer(
                signal.ITIMER_REAL,
                plan["analysis_cap_seconds"] - plan["failure_save_reserve_seconds"],
            )
            try:
                report = json.loads((root / plan["report_path"]).read_bytes())
                analyzed = analyze_report(report, plan)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, prior_handler)
            if (
                time.monotonic() - started >= plan["analysis_cap_seconds"]
                or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                >= plan["peak_rss_bytes_exclusive"]
            ):
                raise ArithmeticError("analysis resource cap failed")
            _finish(
                output,
                stage,
                started,
                {"status": "analyzed_known_rows", "head": head, "analysis": analyzed},
            )
    except BaseException as exc:
        if (
            not (output / "failed.json").exists()
            and not (output / "result.json").exists()
        ):
            _failure(output, stage, started, exc)
        raise
