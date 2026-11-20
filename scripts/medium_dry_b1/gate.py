"""Frozen input, source and stage gates for the B1 update comparison."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from medium_dry_clipped.gate import fingerprint as parent_fingerprint
from medium_dry_clipped.gate import fixed_contract as parent_contract
from river_generalization.gate import require_archive, source_fingerprint

PROTOCOL = Path("configs/medium-dry-b1-updates.json")
PROTOCOL_COMMIT = "9c8f613dbece72afa8f6f9776f88321d92a7777f"
PROTOCOL_SHA256 = "35427c63709778a90743c440df85e9c7991b393549fb88070d4b99c4cb4bdb8f"
PARENT_FINGERPRINT = "7c2312727903a44a347be5ea1bf5c6d1d2c1ed17c447bac7e3605fa8773320ab"
HISTORICAL_FINGERPRINT = (
    "152b357b6942d065e402c84abc14ca3631b29d54551ead71bb668729ccbc81d3"
)
CONTROL_OWN_COMMIT = "ef3ac5d03b87659fefc84206521412a289821786"
CONTROL_OWN_SHA256 = "82ec824335129f41316d88103c8d07ce5bf8d496ad42e2b98e44daf84fe9333d"
CONTROL_NATIVE_COMMIT = "804f35dd57c7b01f9d517ef2cf2ee90c957e4b81"
CONTROL_NATIVE_SHA256 = (
    "4a2d2e5b143872e2c168a7dd8f5c327227faab7b5f1ca175327417fedf375f0a"
)
CONTROL_OWN = Path("results/medium-dry-clipped-regret/own")
CONTROL_NATIVE = Path("results/medium-dry-clipped-regret/native")
GAMES = ("new_low_wet_ip", "new_medium_dry_oop")
SEEDS = (20261371, 20261372, 20261373)
ARM = "signed_b1"
CONTROL_ARM = "signed_linear"
WORK = (100_000, 1_000_000, 10_000_000)
PROFILE_WORK = 100_000
OUTPUT = Path("results/medium-dry-b1-updates")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"


def paths() -> tuple[tuple[int, str, int, str], ...]:
    """Return the six fixed candidate paths in game/seed order."""
    return tuple(
        (i, game, seed, ARM)
        for i, (game, seed) in enumerate((g, s) for g in GAMES for s in SEEDS)
    )


def _published_bytes(root: Path, commit: str, path: Path) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{path}"])


def fixed_contract(root: Path) -> dict[str, Any]:
    """Bind prospective bytes and both immutable published control archives."""
    parent_contract(root)
    if (
        parent_fingerprint(root) != PARENT_FINGERPRINT
        or source_fingerprint(root) != HISTORICAL_FINGERPRINT
    ):
        raise ArithmeticError("historical river source changed")
    raw = (root / PROTOCOL).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256 or raw != _published_bytes(
        root, PROTOCOL_COMMIT, PROTOCOL
    ):
        raise ArithmeticError("prospective B1 protocol changed")
    plan: dict[str, Any] = json.loads(raw)
    if (
        tuple(plan["known_spots"]) != GAMES
        or tuple(plan["seeds"]) != SEEDS
        or tuple(plan["node_work_labels"]) != WORK
        or plan["representation"] != "q8_turn_exact_river"
        or plan["candidate"]
        != dict(
            batch_size=1,
            regret_rule="signed",
            regret_weight="linear",
            average_weight="linear",
            traversal="IID external sampling",
            warm_start="exact uniform initialization",
        )
        or plan["control"]["batch_size"] != 4
        or plan["control"]["own_commit"] != CONTROL_OWN_COMMIT
        or plan["control"]["own_manifest_sha256"] != CONTROL_OWN_SHA256
        or plan["control"]["native_commit"] != CONTROL_NATIVE_COMMIT
        or plan["control"]["native_manifest_sha256"] != CONTROL_NATIVE_SHA256
        or plan["profile"]["paths"] != 18
        or plan["profile"]["candidate_paths"] != 6
        or plan["profile"]["path_work_label"] != PROFILE_WORK
        or plan["workers"]["count"] != 3
    ):
        raise ArithmeticError("fixed B1 grid changed")
    for folder, commit, expected in (
        (CONTROL_OWN, CONTROL_OWN_COMMIT, CONTROL_OWN_SHA256),
        (CONTROL_NATIVE, CONTROL_NATIVE_COMMIT, CONTROL_NATIVE_SHA256),
    ):
        manifest = folder / "manifest.json"
        data = (root / manifest).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected or data != _published_bytes(
            root, commit, manifest
        ):
            raise ArithmeticError("published B4 control archive changed")
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
        raise RuntimeError("clean published B1 source required")
    return head


def fingerprint(root: Path) -> str:
    """Close the new source set while binding its unchanged parent source."""
    new = sorted((root / "scripts/medium_dry_b1").glob("*.py"))
    new.extend((root / "scripts/study_medium_dry_b1.py", root / PROTOCOL))
    if len(new) != 10 or any(path.is_symlink() for path in new):
        raise ArithmeticError("closed B1 source set changed")
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
