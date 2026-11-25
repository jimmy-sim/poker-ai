"""Exact-source publication and frozen-cohort guards for one transfer study."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive as require_archive

from known_turn_collision_medium_transfer.plan import (
    CONFIG,
    GAMES,
    PARENT,
    PROTOCOL,
    PROTOCOL_COMMIT,
    SPOTS,
    contract,
    digest,
)

OUTPUT = Path("results/known-turn-collision-medium-transfer")
SOURCE = OUTPUT / "source-checks"
SCREEN = OUTPUT / "screen"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
REPORT = OUTPUT / "report"
FINAL = OUTPUT / "final-checks"
FREEZE = Path("configs/known-turn-collision-medium-transfer-freeze.json")
ENTRYPOINTS = (
    "scripts/prepare_known_turn_collision_medium_transfer.py",
    "scripts/study_known_turn_collision_medium_transfer.py",
    "scripts/audit_known_turn_collision_medium_transfer.py",
    "scripts/report_known_turn_collision_medium_transfer.py",
)
REUSED_SOURCES = (
    "scripts/known_turn_work_budget/gate.py",
    "scripts/turn_collision_transfer_selection.py",
    "scripts/river_generalization/selection.py",
    "scripts/turn_exact_transfer/capture.py",
    "scripts/turn_exact_transfer/representation.py",
    "scripts/turn_exact_transfer/report.py",
    "scripts/river_strength/representation.py",
    "scripts/medium_dry_b8/report.py",
)


def clean_revision(root: Path) -> str:
    """Require a clean descendant of the exact published protocol."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("conditional transfer stage requires clean checkout")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    for ancestor in (PARENT, PROTOCOL_COMMIT):
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, head],
            cwd=root,
            check=False,
        ).returncode:
            raise ArithmeticError("required conditional transfer ancestor absent")
    contract(root)
    return head


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint isolated implementation/tests and published prerequisites."""
    data = contract(root)
    package = sorted(
        (root / "scripts/known_turn_collision_medium_transfer").glob("*.py")
    )
    tests = sorted(
        (root / "tests").glob("test_known_turn_collision_medium_transfer_*.py")
    )
    files = package + tests + [root / name for name in ENTRYPOINTS]
    files += [root / CONFIG, root / PROTOCOL, root / "uv.lock"]
    files += [root / name for name in REUSED_SOURCES]
    if (
        len(package) < 6
        or len(tests) < 2
        or len(files) != len(set(files))
        or any(not path.is_file() or path.is_symlink() for path in files)
    ):
        raise ArithmeticError("isolated conditional transfer source incomplete")
    hashes = {path.relative_to(root).as_posix(): digest(path) for path in files}
    hashes["historical_pr114"] = data["historical_source_fingerprints"][
        "pr114_work_budget"
    ]
    for name, value in data["prerequisite_sha256"].items():
        hashes["prerequisite_" + name] = value
    return hashes


def source_fingerprint(root: Path) -> str:
    """Stay stable across screen/freeze/evidence-only commits on tested source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require_frozen(root: Path, fingerprint: str) -> dict[str, Any]:
    """Bind selected inputs to the complete first-eligible published screen."""
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / SCREEN, "screen_selected", fingerprint)
    data: dict[str, Any] = json.loads((root / FREEZE).read_bytes())
    screen: dict[str, Any] = json.loads((root / SCREEN / "result.json").read_bytes())
    if (
        data["status"] != "frozen"
        or data["source_fingerprint"] != fingerprint
        or data["screen_result_sha256"] != digest(root / SCREEN / "result.json")
        or data["selected"] != screen["selected"]
        or len(data["spot_sha256"]) != len(GAMES)
        or set(data["spot_sha256"])
        != {(SPOTS / f"{game}.json").as_posix() for game in GAMES}
    ):
        raise ArithmeticError("published conditional cohort changed")
    for name, expected in data["spot_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError("frozen conditional input changed: " + name)
    return data


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute strict bound from separately published complete profile."""
    from known_turn_collision_medium_transfer.forecast import forecast

    require_frozen(root, fingerprint)
    for folder, status in (
        (PROOF, "proof_passed"),
        (PROFILE, "profile_published"),
        (ADMISSION, "admitted"),
    ):
        require_archive(root, root / folder, status, fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    decision: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    if forecast(profile) != decision or decision["status"] != "admitted":
        raise ArithmeticError("published conditional transfer admission changed")
    return decision
