"""Prospective source, input and publication gates for the fixed budget study."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive, source_fingerprint
from river_generalization.learning import ARMS, GAMES, LABELS, SEEDS, contract

PROTOCOL = Path("configs/medium-dry-training-budget.json")
PROTOCOL_COMMIT = "41473857bbd944527c0b95f63aa368d18dab5682"
PROTOCOL_SHA256 = "192ceb8036b2f59e5c836e1108e89235538bc7314a20805dd3ebd10ff94a0a51"
PARENT_FINGERPRINT = "152b357b6942d065e402c84abc14ca3631b29d54551ead71bb668729ccbc81d3"
GAME = "new_medium_dry_oop"
WORK = (10_000_000, 30_000_000, 100_000_000)
PROFILE_WORK = 1_000_000
OUTPUT = Path("results/medium-dry-training-budget")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[tuple[int, int, str], ...]:
    """Return fixed index, seed and arm order for matched-work partitions."""
    return tuple(
        (index, seed, arm)
        for index, (seed, arm) in enumerate((s, a) for s in SEEDS for a in ARMS)
    )


def fixed_contract(root: Path) -> dict[str, Any]:
    """Check original source/cohort and byte-identical published new plan."""
    contract(root)
    if source_fingerprint(root) != PARENT_FINGERPRINT:
        raise ArithmeticError("historical river source changed")
    raw = (root / PROTOCOL).read_bytes()
    if (
        hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256
        or subprocess.check_output(
            ["git", "-C", str(root), "show", f"{PROTOCOL_COMMIT}:{PROTOCOL}"]
        )
        != raw
    ):
        raise ArithmeticError("published training-budget protocol changed")
    plan: dict[str, Any] = json.loads(raw)
    if (
        GAMES[-1] != GAME
        or plan["known_spot"] != f"configs/river-generalization-spots/{GAME}.json"
        or plan["arms"] != list(ARMS)
        or plan["seeds"] != list(SEEDS)
        or plan["node_work_labels"] != list(WORK)
        or plan["diagnostic_rows"] != [2443, 1596, 14]
        or plan["profile"]["path_work_label"] != PROFILE_WORK
        or plan["profile"]["paths"] != 18
        or LABELS[-1] != WORK[0]
        or digest(root / plan["known_spot"])
        != "395727a4fa22d0d4aa6bd182740a5463ef97f7b90e37d6b42ac8a81916d4b51d"
    ):
        raise ArithmeticError("fixed budget grid or known input changed")
    return plan


def clean_head(root: Path) -> str:
    """Require published plan and a clean normal clone before each own stage."""
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    )
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if (
        status
        or subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                PROTOCOL_COMMIT,
                head,
            ],
            check=False,
        ).returncode
    ):
        raise RuntimeError("clean published budget source required")
    return head


def fingerprint(root: Path) -> str:
    """Bind only this isolated adapter and the fixed historical source ID."""
    new = sorted((root / "scripts/medium_dry_budget").glob("*.py"))
    new += [root / "scripts/study_medium_dry_budget.py", root / PROTOCOL]
    if len(new) != 8 or any(path.is_symlink() for path in new):
        raise ArithmeticError("closed budget source set changed")
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in new}
    hashes["historical_source_fingerprint"] = PARENT_FINGERPRINT
    return hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_stage(root: Path, folder: Path, status: str) -> dict[str, Any]:
    return require_archive(root, root / folder, status, fingerprint(root))
