"""Prospective input, exact source and ordered publication gates for own learning."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from poker_ai.evaluation.river_strength_forecast import forecast
from poker_ai.evaluation.river_strength_learning import CONFIG, contract

ORIGINAL_PROTOCOL_COMMIT = "492e419"
PROTOCOL_COMMIT = "e1571df"
ENTRYPOINT = "scripts/study_river_strength.py"
NATIVE_ENTRYPOINT = "scripts/audit_river_strength.py"
REPORT_ENTRYPOINT = "scripts/report_river_strength.py"
PROFILE = Path("results/river-strength/profile")
ADMISSION = Path("results/river-strength/admission")


def source_files(root: Path) -> dict[str, str]:
    """Hash all own source, lock, protocol and thin entrypoint bytes."""
    paths = sorted((root / "src").rglob("*.py"))
    paths += [
        root / ENTRYPOINT,
        root / NATIVE_ENTRYPOINT,
        root / REPORT_ENTRYPOINT,
        root / CONFIG,
        root / "pyproject.toml",
        root / "uv.lock",
    ]
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def source_fingerprint(root: Path) -> str:
    """Stable across later evidence-only commits while source bytes stay fixed."""
    contract(root)
    encoded = json.dumps(source_files(root), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def clean_revision(root: Path) -> str:
    """Require a normal clone containing the published prospective commit."""
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    )
    if status:
        raise RuntimeError("own river-strength work requires a clean checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    for protocol in (ORIGINAL_PROTOCOL_COMMIT, PROTOCOL_COMMIT):
        if subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", protocol, head],
            check=False,
        ).returncode:
            raise RuntimeError("prospective river protocol missing from history")
    saved = subprocess.check_output(
        ["git", "-C", str(root), "show", f"{PROTOCOL_COMMIT}:{CONFIG}"]
    )
    if saved != (root / CONFIG).read_bytes():
        raise RuntimeError("prospective river protocol changed after publication")
    return head


def require_archive(
    root: Path,
    folder: Path,
    status: str,
    fingerprint: str,
) -> dict[str, Any]:
    """Verify every member and publication ancestor before the next stage.

    GitHub byte availability is checked separately at each publication gate;
    this offline reader proves the normal clone has that committed ancestry.
    """
    manifest: dict[str, Any] = json.loads((folder / "manifest.json").read_bytes())
    relative = (folder / "manifest.json").relative_to(root).as_posix()
    introducing = subprocess.check_output(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", relative],
        text=True,
    ).strip()
    if (
        manifest["status"] != status
        or manifest["source_fingerprint"] != fingerprint
        or len(introducing) != 40
        or subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                introducing,
                "HEAD",
            ],
            check=False,
        ).returncode
        or subprocess.check_output(
            ["git", "-C", str(root), "show", f"{introducing}:{relative}"]
        )
        != (folder / "manifest.json").read_bytes()
    ):
        raise ArithmeticError("river-strength stage publication gate changed")
    listed = manifest["files"]
    if len(listed) != len({row["file"] for row in listed}) or sorted(
        row["file"] for row in listed
    ) != sorted(
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    ):
        raise ArithmeticError("river-strength archive inventory changed")
    for row in listed:
        raw = (folder / row["file"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ArithmeticError("river-strength archive member changed")
    return manifest


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute the public profile forecast before permitting long learning."""
    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    decision: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    calculated = forecast(profile)
    if (
        profile["stage"] != "profile"
        or profile["source_fingerprint"] != fingerprint
        or calculated != decision
        or decision["status"] != "admitted"
    ):
        raise ArithmeticError("river-strength forecast/admission changed")
    return decision
