"""Exact isolated-source and publication guards for the residual map."""

import hashlib
import json
import subprocess
from pathlib import Path

from known_turn_half_policy_mixture.gate import source_fingerprint as prior_fingerprint
from river_generalization.gate import require_archive

from known_mixture_residual_map.plan import PROTOCOL_COMMIT, contract, digest

OUTPUT = Path("results/known-mixture-residual-map")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "proof"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
REPORT = OUTPUT / "report"
FINAL = OUTPUT / "final-checks"


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint only this isolated implementation and immutable inputs."""
    contract(root)
    files = sorted((root / "scripts/known_mixture_residual_map").glob("*.py"))
    tests = sorted((root / "tests").glob("test_known_mixture_residual_map_*.py"))
    entrypoints = sorted((root / "scripts").glob("*known_mixture_residual_map.py"))
    paths = files + tests + entrypoints
    if len(files) < 4 or len(tests) < 2 or len(entrypoints) < 1:
        raise ArithmeticError("isolated residual-map source incomplete")
    if len(paths) != len(set(paths)) or any(
        not p.is_file() or p.is_symlink() for p in paths
    ):
        raise ArithmeticError("residual-map source inventory changed")
    result = {path.relative_to(root).as_posix(): digest(path) for path in paths}
    result["prior_pr118_source_fingerprint"] = prior_fingerprint(root)
    result["contract_sha256"] = digest(root / "configs/known-mixture-residual-map.json")
    result["protocol_sha256"] = digest(root / "docs/known-mixture-residual-map.md")
    result["lock_sha256"] = digest(root / "uv.lock")
    return result


def source_fingerprint(root: Path) -> str:
    """Remain constant across evidence-only commits."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def clean_head(root: Path) -> str:
    """Require clean descendant of the verified protocol before measurements."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("residual-map measurement requires clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("published protocol is not an ancestor")
    source_fingerprint(root)
    return head


def require_source(root: Path, fingerprint: str) -> None:
    """Require exact-source local, optional and hosted qualification."""
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)


def require_proof(root: Path, fingerprint: str) -> None:
    """Require the separate published fictional proof."""
    require_source(root, fingerprint)
    require_archive(root, root / PROOF, "proof_passed", fingerprint)


def require_admission(root: Path, fingerprint: str) -> None:
    """Require a published strict data-only compute decision."""
    require_proof(root, fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    from known_mixture_residual_map.admission import forecast

    saved = json.loads((root / ADMISSION / "decision.json").read_bytes())
    if saved != forecast(root) or saved["status"] != "admitted":
        raise ArithmeticError("residual-map admission changed")


def require_own(root: Path, fingerprint: str) -> None:
    """Require all four own row traces published before interpretation."""
    require_admission(root, fingerprint)
    require_archive(root, root / OWN, "own_published", fingerprint)
