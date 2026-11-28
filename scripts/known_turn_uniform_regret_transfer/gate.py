"""Exact-source and ordered publication guards for the uniform-regret study."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_collision_medium_transfer.gate import (
    source_fingerprint as prior_fingerprint,
)
from river_generalization.gate import require_archive

from known_turn_uniform_regret_transfer.plan import (
    CONFIG,
    PROTOCOL,
    PROTOCOL_COMMIT,
    contract,
    digest,
)

OUTPUT = Path("results/known-turn-uniform-regret-transfer")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
AUDIT_ADMISSION = OUTPUT / "audit-admission"
REPORT = OUTPUT / "report"
FINAL = OUTPUT / "final-checks"
PRIOR_FINGERPRINT = "4ab36412d18231aada57b9cc4a4e96c9491f3e37418f8794e7768d3d19073eb0"


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint isolated code, tests, entrypoints and old source pins."""
    contract(root)
    package = sorted((root / "scripts/known_turn_uniform_regret_transfer").glob("*.py"))
    tests = sorted(
        (root / "tests").glob("test_known_turn_uniform_regret_transfer_*.py")
    )
    entrypoints = sorted(
        (root / "scripts").glob("*known_turn_uniform_regret_transfer.py")
    )
    paths = package + tests + entrypoints
    if (
        len(package) < 6
        or len(tests) < 2
        or len(entrypoints) < 3
        or len(paths) != len(set(paths))
        or any(not path.is_file() or path.is_symlink() for path in paths)
    ):
        raise ArithmeticError("closed uniform-regret source incomplete")
    result = {path.relative_to(root).as_posix(): digest(path) for path in paths}
    old = prior_fingerprint(root)
    result["prior_pr116_fingerprint"] = old
    result["contract_sha256"] = digest(root / CONFIG)
    result["protocol_sha256"] = digest(root / PROTOCOL)
    result["uv_lock_sha256"] = digest(root / "uv.lock")
    if old != PRIOR_FINGERPRINT:
        raise ArithmeticError("historical source changed")
    return result


def source_fingerprint(root: Path) -> str:
    """Remain stable over evidence-only commits on identical tested source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def clean_head(root: Path) -> str:
    """Require clean descendant of the exact prospective publication."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("uniform-regret stage requires clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("uniform-regret protocol not in ancestry")
    contract(root)
    source_fingerprint(root)
    return head


def require_source(root: Path, fingerprint: str) -> None:
    """Require exact-source local, optional and hosted receipt."""
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)


def require_proof(root: Path, fingerprint: str) -> None:
    """Require published fictional proof before real input profiling."""
    require_source(root, fingerprint)
    require_archive(root, root / PROOF, "proof_passed", fingerprint)


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute strict forecast from published complete profile."""
    from known_turn_uniform_regret_transfer.forecast import forecast

    require_proof(root, fingerprint)
    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    profile = json.loads((root / PROFILE / "result.json").read_bytes())
    decision: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    if decision != forecast(profile) or decision["status"] != "admitted":
        raise ArithmeticError("uniform-regret admission changed")
    return decision


def require_own(root: Path, fingerprint: str) -> None:
    """Require the complete candidate own evidence before reference use."""
    require_admission(root, fingerprint)
    require_archive(root, root / OWN, "own_published", fingerprint)
