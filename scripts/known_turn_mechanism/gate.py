"""Bind published known-case protocol, isolated source and stage archives."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive as require_archive
from turn_exact_transfer.gate import SOURCE as PARENT_SOURCE

from known_turn_mechanism.plan import (
    CONFIG,
    PROTOCOL,
    SPOT,
    contract,
    digest,
)

PROTOCOL_COMMIT = "0dca303167799ab43266359884191eb6b7448546"
OUTPUT = Path("results/known-turn-exact-mechanism")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
ENTRYPOINTS = (
    "scripts/study_known_turn_mechanism.py",
    "scripts/audit_known_turn_mechanism.py",
    "scripts/report_known_turn_mechanism.py",
)


def clean_revision(root: Path) -> str:
    """Require a clean descendant of the exact published protocol commit."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("known-turn work requires a clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("prospective protocol absent from history")
    for path in (CONFIG, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("published known-turn bytes changed")
    contract(root)
    require_archive(
        root,
        root / PARENT_SOURCE,
        "source_qualified",
        "fb9006517142ee23076f2c0b6d581475dfdaed8127cb2c146a60731af901b09c",
    )
    return head


def source_files(root: Path) -> dict[str, str]:
    """Close all new code/tests and frozen prerequisites without rewriting old pins."""
    contract(root)
    files = sorted((root / "scripts/known_turn_mechanism").glob("*.py"))
    files += [root / path for path in ENTRYPOINTS]
    files += sorted((root / "tests").glob("test_known_turn_mechanism_*.py"))
    files += [root / CONFIG, root / PROTOCOL, root / SPOT, root / "uv.lock"]
    if any(not path.is_file() or path.is_symlink() for path in files) or len(
        files
    ) != len(set(files)):
        raise ArithmeticError("closed known-turn source missing, repeated or symlinked")
    hashes = {path.relative_to(root).as_posix(): digest(path) for path in files}
    hashes["qualified_parent_source_fingerprint"] = (
        "fb9006517142ee23076f2c0b6d581475dfdaed8127cb2c146a60731af901b09c"
    )
    return hashes


def source_fingerprint(root: Path) -> str:
    """Stay stable across evidence-only commits on unchanged tested source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute the published strict conservative forecast before own work."""
    from known_turn_mechanism.forecast import forecast

    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    saved: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    current = forecast(profile)
    if (
        profile["source_fingerprint"] != fingerprint
        or current != saved
        or saved["status"] != "admitted"
    ):
        raise ArithmeticError("published known-turn admission changed")
    return saved
