"""Exact-source and ordered publication guards for PR #118."""

import hashlib
import json
import subprocess
from pathlib import Path

from known_turn_collision_medium_transfer.gate import (
    source_fingerprint as prior_fingerprint,
)
from river_generalization.gate import require_archive

from known_turn_half_policy_mixture.plan import (
    PROTOCOL_COMMIT,
    contract,
    digest,
)

OUTPUT = Path("results/known-turn-half-policy-mixture")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
REPORT = OUTPUT / "report"
FINAL = OUTPUT / "final-checks"


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint only isolated new source, tests and immutable dependencies."""
    data = contract(root)
    if prior_fingerprint(root) != data["source_fingerprint"]:
        raise ArithmeticError("historical PR #116 source pin changed")
    files = sorted((root / "scripts/known_turn_half_policy_mixture").glob("*.py"))
    tests = sorted((root / "tests").glob("test_known_turn_half_policy_mixture_*.py"))
    entrypoints = sorted((root / "scripts").glob("*known_turn_half_policy_mixture.py"))
    paths = files + tests + entrypoints
    if (
        len(files) < 5
        or len(tests) < 2
        or len(entrypoints) < 4
        or len(paths) != len(set(paths))
        or any(not path.is_file() or path.is_symlink() for path in paths)
    ):
        raise ArithmeticError("isolated half-mixture source incomplete")
    result = {path.relative_to(root).as_posix(): digest(path) for path in paths}
    result["prior_pr116_source_fingerprint"] = data["source_fingerprint"]
    result["contract_sha256"] = digest(
        root / "configs/known-turn-half-policy-mixture.json"
    )
    result["protocol_sha256"] = digest(root / data["protocol_path"])
    result["uv_lock_sha256"] = digest(root / "uv.lock")
    return result


def source_fingerprint(root: Path) -> str:
    """Stay stable across evidence-only commits after exact source qualification."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def clean_head(root: Path) -> str:
    """Require a clean published-protocol descendant before every measured stage."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("half-mixture stage requires clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("published half-mixture protocol is not an ancestor")
    contract(root)
    source_fingerprint(root)
    return head


def require_source(root: Path, fingerprint: str) -> None:
    """Require exact-source local, optional and hosted qualification receipt."""
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)


def require_proof(root: Path, fingerprint: str) -> None:
    """Require separately published synthetic proof before any input replay."""
    require_source(root, fingerprint)
    require_archive(root, root / PROOF, "proof_passed", fingerprint)


def require_admission(root: Path, fingerprint: str) -> None:
    """Require the data-only strict compute decision before own scoring."""
    require_proof(root, fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    from known_turn_half_policy_mixture.admission import forecast

    saved = json.loads((root / ADMISSION / "decision.json").read_bytes())
    if saved != forecast(root) or saved["status"] != "admitted":
        raise ArithmeticError("half-mixture compute admission changed")


def require_own(root: Path, fingerprint: str) -> None:
    """Keep every own mixed policy public before a reference audit."""
    require_admission(root, fingerprint)
    require_archive(root, root / OWN, "own_published", fingerprint)
