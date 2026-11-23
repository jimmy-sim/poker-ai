"""Bind prospective contract, frozen cohort and ordered evidence archives."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive as require_archive

from turn_exact_transfer.learning import (
    CONFIG,
    FREEZE,
    GAMES,
    contract,
)

PROTOCOL_COMMIT = "b7fb1442a7fddb66ff0bcaf881a3aedff1c7ba73"
SELECTION_COMMIT = "c036dd920dacd82a80e87d8886586e5f9d807d63"
COHORT_COMMIT = "a779abf5c169471b050554dd7c802befa19279a2"
OUTPUT = Path("results/turn-exact-transfer")
SOURCE = OUTPUT / "source-checks"
INVENTORY = OUTPUT / "inventory"
PROOF = OUTPUT / "proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
ENTRYPOINTS = (
    "scripts/turn_exact_transfer_selection.py",
    "scripts/prepare_turn_exact_transfer.py",
    "scripts/study_turn_exact_transfer.py",
    "scripts/audit_turn_exact_transfer.py",
    "scripts/report_turn_exact_transfer.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_revision(root: Path) -> str:
    """Require clean published prospective/selection/freeze order and bytes."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("exact-turn work requires clean published source")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    for commit, path in ((PROTOCOL_COMMIT, CONFIG), (COHORT_COMMIT, FREEZE)):
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, head],
            cwd=root,
            check=False,
        ).returncode:
            raise ArithmeticError("prospective protocol/cohort absent from history")
        if (root / path).read_bytes() != subprocess.check_output(
            ["git", "show", f"{commit}:{path.as_posix()}"], cwd=root
        ):
            raise ArithmeticError("published prospective bytes changed")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", SELECTION_COMMIT, COHORT_COMMIT],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("selection source did not precede frozen cohort")
    _, frozen = contract(root)
    if frozen["selection_source_commit"] != SELECTION_COMMIT:
        raise ArithmeticError("selected source commit changed")
    for name, expected in frozen["selection_source_sha256"].items():
        published = subprocess.check_output(
            ["git", "show", f"{SELECTION_COMMIT}:{name}"], cwd=root
        )
        if hashlib.sha256(published).hexdigest() != expected:
            raise ArithmeticError("published selection source bytes changed")
    return head


def source_files(root: Path) -> dict[str, str]:
    """Close new isolated source, tests and all frozen scientific inputs."""
    plan, frozen = contract(root)
    if (
        plan["control_representation"] != "q8_turn_exact_river"
        or plan["candidate_representation"] != "exact_turn_exact_river"
    ):
        raise ArithmeticError("fixed representation pair changed")
    paths = sorted((root / "scripts/turn_exact_transfer").glob("*.py"))
    paths += [root / name for name in ENTRYPOINTS]
    paths += sorted((root / "tests").glob("test_turn_exact_transfer_*.py"))
    paths += [root / CONFIG, root / FREEZE, root / "uv.lock"]
    paths += [root / name for name in frozen["spot_sha256"]]
    paths += [root / plan["known_mechanistic_spot"]]
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise ArithmeticError("closed exact-turn source missing or symlinked")
    if len(paths) != len(set(paths)):
        raise ArithmeticError("duplicate source file")
    hashes = {path.relative_to(root).as_posix(): digest(path) for path in paths}
    hashes["historical_full_source_fingerprint"] = (
        "5aafb939fdc4ac75b06480dbd8203efddbd0e1f1b02170ab086ff8bf61668ac6"
    )
    hashes["diagnostic_source_fingerprint"] = (
        "5c33aa0cdfddefe33a69be2c93526223bde1df49eda2957f1f5de4d82901957f"
    )
    return hashes


def source_fingerprint(root: Path) -> str:
    """Stable across evidence-only commits on the same qualified source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_inventory(root: Path, fingerprint: str) -> dict[str, Any]:
    """Reject unmeasured or zero-opportunity selected cohorts."""
    require_archive(root, root / INVENTORY, "inventory_complete", fingerprint)
    result: dict[str, Any] = json.loads((root / INVENTORY / "result.json").read_bytes())
    if (
        result["status"] != "inventory_complete"
        or result["source_fingerprint"] != fingerprint
        or len(result["spots"]) != 4
        or [row["game"] for row in result["spots"]] != list(GAMES)
        or sum(row["turn_collided_exact_rows"] for row in result["spots"][1:]) <= 0
    ):
        raise ArithmeticError("frozen selected inputs have no admitted turn collision")
    return result


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute fixed published profile forecast before longer work."""
    from turn_exact_transfer.forecast import forecast

    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    require_archive(root, root / ADMISSION, "admitted", fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    decision: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    calculated = forecast(profile)
    if (
        profile["stage"] != "profile"
        or profile["source_fingerprint"] != fingerprint
        or calculated != decision
        or decision["status"] != "admitted"
    ):
        raise ArithmeticError("published exact-turn admission changed")
    return decision
