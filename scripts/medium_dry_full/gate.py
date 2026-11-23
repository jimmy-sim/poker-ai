"""Frozen protocol, historical source and archive gates for full passes."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from medium_dry_b8.gate import fingerprint as parent_fingerprint
from medium_dry_b8.gate import fixed_contract as parent_contract
from river_generalization.gate import require_archive

PROTOCOL = Path("configs/medium-dry-full-expectation.json")
PROTOCOL_COMMIT = "8770e3243356aad82d6cc07fac70320f04cdfc34"
PROTOCOL_SHA256 = "d339f16e5dfb69c2c65a0219588fdf811b1558be82f0d29f5610e7bdced4d046"
PARENT_FINGERPRINT = "666ac9e4322ca84f93ad43acf972e8a758125f1aa1276da2847a6025049b40ad"
CONTROL_OWN = Path("results/medium-dry-clipped-regret/own")
CONTROL_NATIVE = Path("results/medium-dry-clipped-regret/native")
GAMES = ("new_low_wet_ip", "new_medium_dry_oop")
ARM = "signed_full_expectation"
CONTROL_ARM = "signed_linear"
SEEDS = (20261371, 20261372, 20261373)
WORK = (100_000, 1_000_000, 10_000_000)
PROFILE_WORK = 1_000_000
OUTPUT = Path("results/medium-dry-full-expectation")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"


def paths() -> tuple[tuple[int, str, str], ...]:
    """Exactly one deterministic candidate path per known spot."""
    return tuple((i, game, ARM) for i, game in enumerate(GAMES))


def _published(root: Path, commit: str, path: Path) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{path}"])


def fixed_contract(root: Path) -> dict[str, Any]:
    """Require exact prospective bytes and unchanged historical control pins."""
    parent_contract(root)
    if parent_fingerprint(root) != PARENT_FINGERPRINT:
        raise ArithmeticError("historical B8 source changed")
    raw = (root / PROTOCOL).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256 or raw != _published(
        root, PROTOCOL_COMMIT, PROTOCOL
    ):
        raise ArithmeticError("prospective full-pass protocol changed")
    plan: dict[str, Any] = json.loads(raw)
    control = plan["control"]
    candidate = plan["candidate"]
    profile = plan["profile"]
    if (
        tuple(plan["known_spots"]) != GAMES
        or plan["representation"] != "q8_turn_exact_river"
        or tuple(control["seeds"]) != SEEDS
        or tuple(plan["node_work_labels"]) != WORK
        or control["arm"] != CONTROL_ARM
        or control["own_commit"] != "ef3ac5d03b87659fefc84206521412a289821786"
        or control["native_commit"] != "804f35dd57c7b01f9d517ef2cf2ee90c957e4b81"
        or candidate["arm"] != ARM
        or candidate["paths"] != 2
        or candidate["regret_rule"] != "signed"
        or candidate["regret_weight"] != "linear"
        or candidate["average_weight"] != "linear"
        or candidate["average_phase"] != "opponent_pass"
        or candidate["average_mass"] != "chance_own_reach"
        or candidate["stochastic_replicates"] != 0
        or profile["paths"] != 6
        or profile["candidate_paths"] != 2
        or profile["path_work_label"] != PROFILE_WORK
        or profile["repeats"] != 3
        or profile["workers"] != 1
        or plan["budgets_seconds"]["whole_own"] != 7200
        or plan["tolerance_chips"] != 1e-9
    ):
        raise ArithmeticError("full-pass fixed grid changed")
    for folder, commit, expected in (
        (CONTROL_OWN, control["own_commit"], control["own_manifest_sha256"]),
        (CONTROL_NATIVE, control["native_commit"], control["native_manifest_sha256"]),
    ):
        manifest = folder / "manifest.json"
        data = (root / manifest).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected or data != _published(
            root, commit, manifest
        ):
            raise ArithmeticError("published B4 control archive changed")
    return plan


def clean_head(root: Path) -> str:
    """Require clean normal-clone descendant of the prospective checkpoint."""
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
        raise RuntimeError("clean published full-pass source required")
    return head


def fingerprint(root: Path) -> str:
    """Close the isolated full-pass source and bind its unchanged parent."""
    new = sorted((root / "scripts/medium_dry_full").glob("*.py"))
    new.extend((root / "scripts/study_medium_dry_full.py", root / PROTOCOL))
    if len(new) != 10 or any(not path.is_file() or path.is_symlink() for path in new):
        raise ArithmeticError("closed full-pass source set changed")
    hashes = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in new
    }
    hashes["parent_source_fingerprint"] = PARENT_FINGERPRINT
    return hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_stage(root: Path, folder: Path, status: str) -> dict[str, Any]:
    return require_archive(root, root / folder, status, fingerprint(root))
