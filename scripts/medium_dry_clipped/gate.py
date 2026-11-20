"""Frozen input, source and stage gates for the clipped-regret comparison."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from medium_dry_budget.gate import fingerprint as parent_fingerprint
from medium_dry_budget.gate import fixed_contract as parent_contract
from river_generalization.gate import require_archive, source_fingerprint
from river_generalization.learning import ARMS as HISTORICAL_ARMS
from river_generalization.learning import GAMES as HISTORICAL_GAMES
from river_generalization.learning import SEEDS as HISTORICAL_SEEDS

PROTOCOL = Path("configs/medium-dry-clipped-regret.json")
PROTOCOL_COMMIT = "3ad6004782d1d7f412168d908027b257fef2f1ad"
PROTOCOL_SHA256 = "007536fd4a6f8b19c1a28568f44452a3f63511e25f7aaa6286d573482fe46dca"
PARENT_FINGERPRINT = "60ee266a4d644e748008ab77812a413380a9bd1b3d67238b6bb69da46e029217"
HISTORICAL_FINGERPRINT = (
    "152b357b6942d065e402c84abc14ca3631b29d54551ead71bb668729ccbc81d3"
)
GAMES = ("new_low_wet_ip", "new_medium_dry_oop")
ARMS = ("signed_linear", "clipped_linear")
SEEDS = (20261371, 20261372, 20261373)
WORK = (100_000, 1_000_000, 10_000_000)
PROFILE_WORK = 100_000
OUTPUT = Path("results/medium-dry-clipped-regret")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"


def paths() -> tuple[tuple[int, str, int, str], ...]:
    """Return fixed path index, known game, seed and training arm."""
    return tuple(
        (index, game, seed, arm)
        for index, (game, seed, arm) in enumerate(
            (g, s, a) for g in GAMES for s in SEEDS for a in ARMS
        )
    )


def fixed_contract(root: Path) -> dict[str, Any]:
    """Bind the published protocol and all inherited source dependencies."""
    parent_contract(root)
    if (
        parent_fingerprint(root) != PARENT_FINGERPRINT
        or source_fingerprint(root) != HISTORICAL_FINGERPRINT
    ):
        raise ArithmeticError("published parent experiment source changed")
    raw = (root / PROTOCOL).read_bytes()
    published = subprocess.check_output(
        ["git", "-C", str(root), "show", f"{PROTOCOL_COMMIT}:{PROTOCOL}"]
    )
    if hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256 or raw != published:
        raise ArithmeticError("prospective clipped-regret protocol changed")
    plan: dict[str, Any] = json.loads(raw)
    if (
        tuple(plan["known_spots"]) != GAMES
        or tuple(plan["arms"]) != ARMS
        or tuple(plan["seeds"]) != SEEDS
        or tuple(plan["node_work_labels"]) != WORK
        or plan["profile"]["path_work_label"] != PROFILE_WORK
        or plan["profile"]["paths"] != 36
        or tuple(HISTORICAL_GAMES[-2:]) != GAMES
        or tuple(HISTORICAL_SEEDS) != SEEDS
        or plan["representation"] != HISTORICAL_ARMS[-1]
        or plan["arm_rules"]
        != {
            "signed_linear": ["signed", "linear", "linear"],
            "clipped_linear": ["clipped", "linear", "linear"],
        }
    ):
        raise ArithmeticError("fixed clipped-regret grid changed")
    return plan


def clean_head(root: Path) -> str:
    """Require a clean normal clone containing the prospective checkpoint."""
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    )
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    ancestor = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        check=False,
    ).returncode
    if status or ancestor:
        raise RuntimeError("clean published clipped-regret source required")
    return head


def fingerprint(root: Path) -> str:
    """Close the new source set while binding its unchanged parent source."""
    new = sorted((root / "scripts/medium_dry_clipped").glob("*.py"))
    new.append(root / "scripts/study_medium_dry_clipped.py")
    new.append(root / PROTOCOL)
    if len(new) != 10 or any(path.is_symlink() for path in new):
        raise ArithmeticError("closed clipped-regret source set changed")
    hashes = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in new
    }
    hashes["parent_source_fingerprint"] = PARENT_FINGERPRINT
    return hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_stage(root: Path, folder: Path, status: str) -> dict[str, Any]:
    return require_archive(root, root / folder, status, fingerprint(root))
