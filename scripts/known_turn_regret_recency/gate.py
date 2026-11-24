"""Bind the prospective regret update, historical controls and stage order."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_mechanism.gate import source_fingerprint as dry_fingerprint
from known_wet_turn_mechanism.gate import source_fingerprint as wet_fingerprint
from river_generalization.gate import require_archive as require_archive

from known_turn_regret_recency.plan import CONFIG, PROTOCOL, contract, digest

PROTOCOL_COMMIT = "17165d2b21423a3889bff7b714875fd89153f508"
WET_FINGERPRINT = "5e29c490f3b05cf7b98dc016628a9765ab76b7a920965590e0d086abcda16b12"
DRY_FINGERPRINT = "6e09c02673ca596e6082ea8d0a57ba12cd2533acfaf2c777991c4d29f395e0f4"
OUTPUT = Path("results/known-turn-regret-recency")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
REPORT = OUTPUT / "report"
FINAL = OUTPUT / "final-checks"
ENTRYPOINTS = (
    "scripts/study_known_turn_regret_recency.py",
    "scripts/audit_known_turn_regret_recency.py",
    "scripts/report_known_turn_regret_recency.py",
)


def historical_controls(root: Path) -> None:
    """Require unchanged old source and complete audited control archives."""
    if (
        wet_fingerprint(root) != WET_FINGERPRINT
        or dry_fingerprint(root) != DRY_FINGERPRINT
    ):
        raise ArithmeticError("historical exact-turn source changed")
    for name, fingerprint, report_status in (
        ("known-wet-turn-mechanism", WET_FINGERPRINT, "report_negative"),
        ("known-turn-exact-mechanism", DRY_FINGERPRINT, "reported"),
    ):
        for stage, status in (
            ("own", "own_published"),
            ("native", "native_audited"),
            ("report", report_status),
            ("final-checks", "final_qualified"),
        ):
            require_archive(root, root / "results" / name / stage, status, fingerprint)


def clean_head(root: Path) -> str:
    """Require a clean descendant of the exact published protocol bytes."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("regret-recency stages require a clean checkout")
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
            raise ArithmeticError("published regret-recency protocol bytes changed")
    contract(root)
    historical_controls(root)
    return head


def source_files(root: Path) -> dict[str, str]:
    """Close all new code and tests without repinning historical source."""
    contract(root)
    package = sorted((root / "scripts/known_turn_regret_recency").glob("*.py"))
    tests = sorted((root / "tests").glob("test_known_turn_regret_recency_*.py"))
    files = package + tests + [root / name for name in ENTRYPOINTS]
    files += [root / CONFIG, root / PROTOCOL, root / "uv.lock"]
    if (
        len(package) < 5
        or len(tests) < 2
        or len(files) != len(set(files))
        or any(not path.is_file() or path.is_symlink() for path in files)
    ):
        raise ArithmeticError("closed regret-recency source missing or symlinked")
    hashes = {path.relative_to(root).as_posix(): digest(path) for path in files}
    hashes["wet_historical_fingerprint"] = WET_FINGERPRINT
    hashes["dry_historical_fingerprint"] = DRY_FINGERPRINT
    return hashes


def source_fingerprint(root: Path) -> str:
    """Remain stable across evidence commits on identical tested source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute the strict forecast from the published complete profile."""
    from known_turn_regret_recency.forecast import forecast

    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    saved: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    if (
        profile["source_fingerprint"] != fingerprint
        or forecast(profile) != saved
        or saved["status"] != "admitted"
    ):
        raise ArithmeticError("published regret-recency admission changed")
    return saved
