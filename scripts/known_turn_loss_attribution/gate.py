"""Exact-source and ordered-publication guards for saved-policy attribution."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_turn_regret_recency.gate import source_fingerprint as parent_fingerprint
from river_generalization.gate import require_archive as require_archive

from known_turn_loss_attribution.forecast import forecast
from known_turn_loss_attribution.plan import CONFIG, PARENT, PROTOCOL, contract, digest

PROTOCOL_COMMIT = "1ce9300e143546d9c85879ac5515f577bcc8fa0d"
PARENT_FINGERPRINT = "133a5a77c19431bf1c220bc89d000c6a146cf53161532bcf26eab0499aa2cf10"
OUTPUT = Path("results/known-turn-loss-attribution")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "proof"
ADMISSION = OUTPUT / "admission"
DIAGNOSIS = OUTPUT / "diagnosis"
FINAL = OUTPUT / "final-checks"
ENTRYPOINTS = (
    "scripts/prove_known_turn_loss_attribution.py",
    "scripts/admit_known_turn_loss_attribution.py",
    "scripts/diagnose_known_turn_loss_attribution.py",
)


def clean_head(root: Path) -> str:
    """Require clean descendant of the exact published prospective bytes."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("loss-attribution stages require clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    for parent in (PARENT, PROTOCOL_COMMIT):
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", parent, head], cwd=root, check=False
        ).returncode:
            raise ArithmeticError("required publication ancestor absent")
    for path in (CONFIG, PROTOCOL):
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{PROTOCOL_COMMIT}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("published prospective bytes changed")
    contract(root)
    if parent_fingerprint(root) != PARENT_FINGERPRINT:
        raise ArithmeticError("historical regret-recency source changed")
    for name, status in (
        ("own", "own_published"),
        ("native", "native_audited"),
        ("report", "report_negative"),
        ("final-checks", "final_qualified"),
    ):
        require_archive(
            root,
            root / "results/known-turn-regret-recency" / name,
            status,
            PARENT_FINGERPRINT,
        )
    return head


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint only isolated new source, tests and frozen inputs."""
    contract(root)
    package = sorted((root / "scripts/known_turn_loss_attribution").glob("*.py"))
    tests = sorted((root / "tests").glob("test_known_turn_loss_attribution_*.py"))
    files = package + tests + [root / p for p in ENTRYPOINTS]
    files += [root / CONFIG, root / PROTOCOL, root / "uv.lock"]
    if (
        len(package) < 5
        or len(tests) < 2
        or len(files) != len(set(files))
        or any(not p.is_file() or p.is_symlink() for p in files)
    ):
        raise ArithmeticError("isolated attribution source missing or symlinked")
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in files}
    hashes["historical_recency_fingerprint"] = PARENT_FINGERPRINT
    return hashes


def source_fingerprint(root: Path) -> str:
    """Remain stable across evidence-only commits on the tested source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute a separately published conservative data-only gate."""
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / PROOF, "proof_passed", fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    decision: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    if decision != forecast(root) or decision["status"] != "admitted":
        raise ArithmeticError("published attribution admission changed")
    return decision
