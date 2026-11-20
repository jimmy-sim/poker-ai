"""Exact-source and ordered publication gates for the fixed readout panel."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive as require_archive

from river_uniform_readout.learning import CONFIG, GAMES, contract

PROTOCOL_COMMIT = "af73bd8e841b20c09504903905665f1169c54caf"
# Set only after the one selected cohort is published. No own run is permitted
# while this value is absent; the selector itself is source-pinned in its freeze.
COHORT_COMMIT = ""
FREEZE = Path("configs/river-uniform-readout-freeze.json")
PROFILE = Path("results/river-uniform-readout/profile")
ADMISSION = Path("results/river-uniform-readout/admission")
ENTRYPOINTS = (
    "scripts/prepare_river_uniform_readout.py",
    "scripts/study_river_uniform_readout.py",
    "scripts/audit_river_uniform_readout.py",
    "scripts/report_river_uniform_readout.py",
)


def frozen_cohort(root: Path) -> dict[str, Any]:
    """Read exact frozen inputs and reject substituted or missing spots."""
    config = contract(root)
    raw = (root / FREEZE).read_bytes()
    frozen: dict[str, Any] = json.loads(raw)
    if (
        frozen.get("config_sha256")
        != hashlib.sha256((root / CONFIG).read_bytes()).hexdigest()
        or sorted(frozen.get("spot_sha256", {}))
        != [f"configs/river-uniform-readout-spots/{game}.json" for game in GAMES]
        or len(frozen.get("selection", [])) != len(GAMES)
    ):
        raise ArithmeticError("fixed uniform-readout cohort changed")
    for group in ("selection_source_sha256", "known_spot_sha256", "spot_sha256"):
        for name, expected in frozen[group].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                raise ArithmeticError(f"frozen uniform-readout member changed: {name}")
    if sorted(config["known_spot_directories"]) != sorted(
        {str(Path(name).parent) for name in frozen["known_spot_sha256"]}
    ):
        raise ArithmeticError("known spot inventory changed")
    return frozen


def source_files(root: Path) -> dict[str, str]:
    """Fingerprint all own, pinned parent, input and entrypoint source bytes."""
    frozen_cohort(root)
    paths = sorted((root / "src").rglob("*.py"))
    for package in ("river_strength", "river_generalization", "river_uniform_readout"):
        paths += sorted((root / "scripts" / package).rglob("*.py"))
    paths += [root / name for name in ENTRYPOINTS]
    paths += [
        root / "scripts/study_river_strength.py",
        root / "scripts/audit_river_strength.py",
        root / "scripts/report_river_strength.py",
        root / "scripts/study_river_generalization.py",
        root / "scripts/audit_river_generalization.py",
        root / "scripts/report_river_generalization.py",
        root / CONFIG,
        root / FREEZE,
        *(root / f"configs/river-uniform-readout-spots/{game}.json" for game in GAMES),
        root / "pyproject.toml",
        root / "uv.lock",
    ]
    if any(path.is_symlink() for path in paths):
        raise ArithmeticError("river source may not be symlinked")
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def source_fingerprint(root: Path) -> str:
    """Stable across evidence-only commits while exact source is unchanged."""
    encoded = json.dumps(source_files(root), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def clean_revision(root: Path) -> str:
    """Require a clean normal clone with published protocol and cohort commits."""
    if subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    ):
        raise RuntimeError("uniform-readout work requires a clean checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if len(COHORT_COMMIT) != 40:
        raise RuntimeError("fixed cohort has not been published")
    for commit in (PROTOCOL_COMMIT, COHORT_COMMIT):
        if subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", commit, head],
            check=False,
        ).returncode:
            raise RuntimeError("prospective river protocol/cohort absent from history")
    for commit, path in ((PROTOCOL_COMMIT, CONFIG), (COHORT_COMMIT, FREEZE)):
        if (
            subprocess.check_output(
                ["git", "-C", str(root), "show", f"{commit}:{path.as_posix()}"]
            )
            != (root / path).read_bytes()
        ):
            raise RuntimeError("prospective river protocol/cohort changed")
    frozen_cohort(root)
    return head


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute the published profile before permitting 10m own learning."""
    from river_uniform_readout.forecast import forecast

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
        raise ArithmeticError("uniform-readout forecast/admission changed")
    return decision
