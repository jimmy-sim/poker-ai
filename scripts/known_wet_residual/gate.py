"""Bind the prospective saved-policy diagnostic to published parent bytes."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from known_wet_turn_mechanism.gate import source_fingerprint as parent_source
from river_generalization.gate import require_archive as require_archive

CONFIG = Path("configs/known-wet-residual-diagnosis.json")
PROTOCOL = Path("docs/known-wet-residual-diagnosis.md")
CONFIG_SHA256 = "0b858e35435ed961e667077f4a4533571374ec79b3660259a36a04f3c4d33c31"
PROTOCOL_SHA256 = "34180f016bf48e63732094cce475f51dbf63940a78199a3b6e8164ef368ec324"
PROTOCOL_COMMIT = "23d3cf5de7dd14ebcb27a83febdbba9f3e321d1d"
PARENT_MERGE = "8b43f94ded36e09538a4d62d227cb560b8c184e6"
PARENT_SOURCE = "5e29c490f3b05cf7b98dc016628a9765ab76b7a920965590e0d086abcda16b12"
OUTPUT = Path("results/known-wet-residual-diagnosis")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "proof"
ADMISSION = OUTPUT / "admission"
DIAGNOSIS = OUTPUT / "diagnosis"
ENTRYPOINTS = (
    Path("scripts/diagnose_known_wet_residual.py"),
    Path("scripts/prove_known_wet_residual.py"),
    Path("scripts/admit_known_wet_residual.py"),
)
SPOT = Path(
    "results/turn-collision-transfer/screen/attempts/collision_medium_wet_oop-02.json"
)


def sha(path: Path) -> str:
    """Hash one exact repository file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract(root: Path) -> dict[str, Any]:
    """Reject changed scope, source, published policies or reference audit."""
    if sha(root / CONFIG) != CONFIG_SHA256 or sha(root / PROTOCOL) != PROTOCOL_SHA256:
        raise ArithmeticError("published residual-diagnosis protocol changed")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["issue"] != 4
        or data["parent_merge"] != PARENT_MERGE
        or data["historical_source_fingerprint"] != PARENT_SOURCE
        or data["input"]["file"] != SPOT.as_posix()
        or data["seed_per_arm"] != [0]
        or data["work_labels"] != [100000, 1000000, 10000000]
        or data["readouts"] != ["current", "linear_average"]
        or data["saved_policy_cases"] != 12
        or data["responding_seat_traces"] != 24
        or data["concentrated_street_share"] != 0.5
        or data["hard_cap_seconds"] != 900
    ):
        raise ArithmeticError("residual-diagnosis grid changed")
    if (
        sha(root / SPOT) != data["input"]["sha256"]
        or parent_source(root) != PARENT_SOURCE
    ):
        raise ArithmeticError("known wet input or parent source changed")
    for name, expected in data["prerequisite_sha256"].items():
        if sha(root / name) != expected:
            raise ArithmeticError(f"residual-diagnosis prerequisite changed: {name}")
    bound = 2 * data["parent_report_wall_seconds"] + 120
    if bound != data["forecast_bound_seconds"] or bound >= data["hard_cap_seconds"]:
        raise ArithmeticError("published conservative forecast changed")
    for stage, status in (
        ("own", "own_published"),
        ("native", "native_audited"),
        ("report", "report_negative"),
        ("final-checks", "final_qualified"),
    ):
        require_archive(
            root,
            root / "results/known-wet-turn-mechanism" / stage,
            status,
            PARENT_SOURCE,
        )
    return data


def clean_head(root: Path) -> str:
    """Require a clean clone descended from the published prospective plan."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("residual diagnosis requires a clean checkout")
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
            raise ArithmeticError("published protocol bytes changed")
    contract(root)
    return head


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint only new isolated code, tests and immutable prerequisites."""
    contract(root)
    files = sorted((root / "scripts/known_wet_residual").glob("*.py"))
    files += [root / path for path in ENTRYPOINTS]
    files += sorted((root / "tests").glob("test_known_wet_residual*.py"))
    files += [root / CONFIG, root / PROTOCOL, root / SPOT, root / "uv.lock"]
    if any(not path.is_file() or path.is_symlink() for path in files) or len(
        files
    ) != len(set(files)):
        raise ArithmeticError("closed residual-diagnosis source missing or repeated")
    hashes = {path.relative_to(root).as_posix(): sha(path) for path in files}
    hashes["qualified_parent_source_fingerprint"] = PARENT_SOURCE
    return hashes


def source_fingerprint(root: Path) -> str:
    """Remain stable across evidence-only commits on qualified source."""
    return hashlib.sha256(
        json.dumps(source_files(root), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
