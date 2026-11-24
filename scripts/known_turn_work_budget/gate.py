"""Exact prospective bytes, isolated source and ordered publication gates."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive as require_archive

from known_turn_work_budget.plan import CONFIG, PARENT, PROTOCOL, contract, digest

PROTOCOL_COMMIT = "01b50a3e590143a7653bcfbe1e724fc25868d26b"
OUTPUT = Path("results/known-turn-work-budget")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
REPORT = OUTPUT / "report"
FINAL = OUTPUT / "final-checks"
ENTRYPOINTS = (
    "scripts/study_known_turn_work_budget.py",
    "scripts/audit_known_turn_work_budget.py",
    "scripts/report_known_turn_work_budget.py",
)


def clean_revision(root: Path) -> str:
    """Require a clean descendant with byte-identical published protocol."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("known-turn budget stage requires clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    for ancestor in (PARENT, PROTOCOL_COMMIT):
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, head],
            cwd=root,
            check=False,
        ).returncode:
            raise ArithmeticError("required known-turn budget ancestor absent")
    for path in (CONFIG, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("published known-turn budget protocol changed")
    data = contract(root)
    historical = data["historical_source_fingerprints"]
    for folder, status, fingerprint in (
        (
            "results/known-wet-turn-mechanism/source-checks",
            "source_qualified",
            historical["wet_exact_turn_study"],
        ),
        (
            "results/known-turn-exact-mechanism/source-checks",
            "source_qualified",
            historical["dry_exact_turn_study"],
        ),
        (
            "results/known-turn-regret-recency/report",
            "report_negative",
            historical["recency_negative_report"],
        ),
        (
            "results/known-turn-loss-attribution/diagnosis",
            "failed_binding",
            "11125bcb2b866b409d9e3bfd4d7f51c3c6fde53c1fc80575c14d8f526516ed68",
        ),
    ):
        require_archive(root, root / folder, status, fingerprint)
    return head


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint isolated implementation, tests and frozen inputs only."""
    data = contract(root)
    package = sorted((root / "scripts/known_turn_work_budget").glob("*.py"))
    tests = sorted((root / "tests").glob("test_known_turn_work_budget_*.py"))
    files = package + tests + [root / path for path in ENTRYPOINTS]
    files += [root / CONFIG, root / PROTOCOL, root / "uv.lock"]
    files += [root / row["spot"] for row in data["games"]]
    if (
        len(package) < 4
        or len(tests) < 2
        or len(files) != len(set(files))
        or any(not path.is_file() or path.is_symlink() for path in files)
    ):
        raise ArithmeticError("isolated known-turn budget source incomplete")
    hashes = {path.relative_to(root).as_posix(): digest(path) for path in files}
    hashes.update(
        {
            "historical_" + key: value
            for key, value in data["historical_source_fingerprints"].items()
        }
    )
    return hashes


def source_fingerprint(root: Path) -> str:
    """Stay stable across evidence-only commits on unchanged tested source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute strict bound from the separately published profile."""
    from known_turn_work_budget.forecast import forecast

    for stage, status in (
        (SOURCE, "source_qualified"),
        (PROOF, "proof_passed"),
        (PROFILE, "profile_published"),
        (ADMISSION, "admitted"),
    ):
        require_archive(root, root / stage, status, fingerprint)
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
        raise ArithmeticError("published known-turn budget admission changed")
    return saved
