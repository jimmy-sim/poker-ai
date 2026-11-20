"""Prospective input, exact source and ordered publication gates for own learning."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

PROTOCOL_COMMIT = "4dafb82bba48689038ec27938c81388ee3dff76d"
COHORT_COMMIT = "5a96ab97c0618c7c7a31fc7899ead40ebe9cf2a6"
ARMS = ("texture_range_q8_b8", "q8_turn_exact_river")
GAMES = ("new_low_wet_ip", "new_medium_dry_oop")
SEEDS = (20261371, 20261372, 20261373)
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "uniform_average", "linear_average")
CONFIG = "configs/river-generalization-fixed-spots.json"
CONFIG_SHA256 = "1eed2b627071fcad27c88958cba6ceaa939b4437760f775e3c715a6c4954099b"
FREEZE = "configs/river-generalization-freeze.json"
ENTRYPOINT = "scripts/study_river_generalization.py"
NATIVE_ENTRYPOINT = "scripts/audit_river_generalization.py"
REPORT_ENTRYPOINT = "scripts/report_river_generalization.py"
PROFILE = Path("results/river-generalization/profile")
ADMISSION = Path("results/river-generalization/admission")


def config_grid(config: dict[str, Any]) -> None:
    """Reject any departure from the published game, seed or readout grid."""
    expected = [(g, s, a) for g in GAMES for s in SEEDS for a in ARMS]
    actual = [
        (game, seed, arm)
        for game in (row["name"] for row in config["strata"])
        for seed in config["seeds"]
        for arm in config["arms"]
    ]
    if (
        actual != expected
        or config["training"]["node_work_labels"] != list(LABELS)
        or config["training"]["readouts"] != list(READOUTS)
        or config["training"]["paths"] != len(expected)
        or config["training"]["logical_profiles"]
        != len(expected) * len(LABELS) * len(READOUTS)
    ):
        raise ValueError("prospective river-generalization grid changed")


def contract(root: Path) -> dict[str, Any]:
    """Check published protocol and all pinned inputs without poker imports."""
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ArithmeticError("prospective river-generalization contract changed")
    config: dict[str, Any] = json.loads(raw)
    config_grid(config)
    for name, expected in config["input_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ArithmeticError(f"pinned river-generalization input changed: {name}")
    frozen: dict[str, Any] = json.loads((root / FREEZE).read_bytes())
    if (
        frozen.get("config_sha256") != CONFIG_SHA256
        or frozen.get("selection_source_commit")
        != "3fc07f95954bdb7430edf8834f1447eb15b04a27"
        or sorted(frozen.get("spot_sha256", {}))
        != [f"configs/river-generalization-spots/{game}.json" for game in GAMES]
    ):
        raise ArithmeticError("fixed prospective cohort changed")
    for group in ("selection_source_sha256", "known_spot_sha256", "spot_sha256"):
        for name, expected in frozen[group].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                raise ArithmeticError(f"frozen cohort member changed: {name}")
    return config


def source_files(root: Path) -> dict[str, str]:
    """Hash all own source, lock, protocol and thin entrypoint bytes."""
    paths = sorted((root / "src").rglob("*.py"))
    historical = sorted((root / "scripts/river_strength").rglob("*.py"))
    adapters = sorted((root / "scripts/river_generalization").rglob("*.py"))
    if len(historical) != 7 or len(adapters) != 7:
        raise ArithmeticError("closed river adapter package changed")
    paths += historical + adapters
    paths += [
        root / ENTRYPOINT,
        root / NATIVE_ENTRYPOINT,
        root / REPORT_ENTRYPOINT,
        root / "scripts/prepare_river_generalization.py",
        root / CONFIG,
        root / FREEZE,
        *(root / f"configs/river-generalization-spots/{game}.json" for game in GAMES),
        root / "scripts/study_river_strength.py",
        root / "scripts/audit_river_strength.py",
        root / "scripts/report_river_strength.py",
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
    """Stable across later evidence-only commits while source bytes stay fixed."""
    contract(root)
    encoded = json.dumps(source_files(root), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def clean_revision(root: Path) -> str:
    """Require a normal clone containing the published prospective commit."""
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    )
    if status:
        raise RuntimeError("own river-generalization work requires a clean checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    for protocol in (PROTOCOL_COMMIT, COHORT_COMMIT):
        if subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", protocol, head],
            check=False,
        ).returncode:
            raise RuntimeError("prospective river protocol missing from history")
    saved = subprocess.check_output(
        ["git", "-C", str(root), "show", f"{PROTOCOL_COMMIT}:{CONFIG}"]
    )
    if saved != (root / CONFIG).read_bytes():
        raise RuntimeError("prospective river protocol changed after publication")
    frozen = subprocess.check_output(
        ["git", "-C", str(root), "show", f"{COHORT_COMMIT}:{FREEZE}"]
    )
    if frozen != (root / FREEZE).read_bytes():
        raise RuntimeError("fixed river cohort changed after publication")
    return head


def require_archive(
    root: Path,
    folder: Path,
    status: str,
    fingerprint: str,
) -> dict[str, Any]:
    """Verify every member and publication ancestor before the next stage.

    GitHub byte availability is checked separately at each publication gate;
    this offline reader proves the normal clone has that committed ancestry.
    """
    manifest: dict[str, Any] = json.loads((folder / "manifest.json").read_bytes())
    relative = (folder / "manifest.json").relative_to(root).as_posix()
    introducing = subprocess.check_output(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", relative],
        text=True,
    ).strip()
    if (
        manifest["status"] != status
        or manifest["source_fingerprint"] != fingerprint
        or len(introducing) != 40
        or subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                introducing,
                "HEAD",
            ],
            check=False,
        ).returncode
        or subprocess.check_output(
            ["git", "-C", str(root), "show", f"{introducing}:{relative}"]
        )
        != (folder / "manifest.json").read_bytes()
    ):
        raise ArithmeticError("river-generalization stage publication gate changed")
    listed = manifest["files"]
    if len(listed) != len({row["file"] for row in listed}) or sorted(
        row["file"] for row in listed
    ) != sorted(
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    ):
        raise ArithmeticError("river-generalization archive inventory changed")
    for row in listed:
        raw = (folder / row["file"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ArithmeticError("river-generalization archive member changed")
    return manifest


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute the public profile forecast before permitting long learning."""
    from river_generalization.forecast import forecast

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
        raise ArithmeticError("river-generalization forecast/admission changed")
    return decision
