"""Exact prospective protocol, cohort, source and ordered archive gates."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from medium_dry_full.gate import fingerprint as historical_fingerprint
from medium_dry_full.gate import fixed_contract as historical_contract
from river_generalization.gate import require_archive as require_archive
from river_generalization.selection import tracked_known_spots

from river_full_broader.learning import CONFIG, CONFIG_SHA256, FREEZE, GAMES, contract

PROTOCOL_COMMIT = "ee822909e2836c5cd037a69ebc2c381dfc97c8cf"
COHORT_COMMIT = ""  # Set to the one published freeze commit before qualification.
HISTORICAL_FINGERPRINT = (
    "a549976f0811872dcc9057e112f40def8af5d2f3e16b81d1a678fdcf8bc62aab"
)
OUTPUT = Path("results/river-full-broader")
SOURCE = OUTPUT / "source-checks"
PROOF = OUTPUT / "own-proof"
PROFILE = OUTPUT / "profile"
ADMISSION = OUTPUT / "admission"
OWN = OUTPUT / "own"
NATIVE = OUTPUT / "native"
ENTRYPOINTS = (
    "scripts/river_full_broader_selection.py",
    "scripts/prepare_river_full_broader.py",
    "scripts/study_river_full_broader.py",
    "scripts/audit_river_full_broader.py",
    "scripts/report_river_full_broader.py",
)


def frozen_cohort(root: Path) -> dict[str, Any]:
    """Reject substituted selected spots or a changed known-spot inventory."""
    config = contract(root)
    frozen: dict[str, Any] = json.loads((root / FREEZE).read_bytes())
    if (
        frozen.get("format") != "river-full-broader-cohort-v1"
        or frozen.get("config_sha256") != CONFIG_SHA256
        or sorted(frozen.get("spot_sha256", {}))
        != sorted(f"configs/river-full-broader-spots/{game}.json" for game in GAMES)
        or len(frozen.get("selection", [])) != len(GAMES)
        or len(frozen.get("known_spot_sha256", {})) != config["known_spot_count"]
    ):
        raise ArithmeticError("fixed broader-full cohort changed")
    for group in ("selection_source_sha256", "known_spot_sha256", "spot_sha256"):
        for name, expected in frozen[group].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                raise ArithmeticError(f"frozen broader-full member changed: {name}")
    if sorted(config["known_spot_directories"]) != sorted(
        {str(Path(name).parent) for name in frozen["known_spot_sha256"]}
    ):
        raise ArithmeticError("known spot inventory changed")
    tracked = {
        path.relative_to(root).as_posix()
        for path in tracked_known_spots(root, config["known_spot_directories"])
    }
    if tracked != set(frozen["known_spot_sha256"]):
        raise ArithmeticError("tracked known-spot inventory changed")
    return frozen


def source_files(root: Path) -> dict[str, str]:
    """Close the new source, selected inputs and unchanged historical source."""
    frozen_cohort(root)
    historical_contract(root)
    if historical_fingerprint(root) != HISTORICAL_FINGERPRINT:
        raise ArithmeticError("historical full-pass source changed")
    paths = sorted((root / "scripts/river_full_broader").glob("*.py"))
    paths += [root / name for name in ENTRYPOINTS]
    paths += [
        root / CONFIG,
        root / FREEZE,
        *(root / f"configs/river-full-broader-spots/{game}.json" for game in GAMES),
        root / "uv.lock",
    ]
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise ArithmeticError("broader-full source missing or symlinked")
    hashes = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    hashes["historical_full_source_fingerprint"] = HISTORICAL_FINGERPRINT
    return hashes


def source_fingerprint(root: Path) -> str:
    """Stable across evidence-only commits on the same qualified source."""
    encoded = json.dumps(source_files(root), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def clean_revision(root: Path) -> str:
    """Require clean published protocol and one immutable selected cohort."""
    if subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    ):
        raise RuntimeError("broader-full work requires a clean checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if len(COHORT_COMMIT) != 40:
        raise RuntimeError("fixed cohort has not been published")
    for commit, path in ((PROTOCOL_COMMIT, CONFIG), (COHORT_COMMIT, FREEZE)):
        if subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", commit, head],
            check=False,
        ).returncode:
            raise RuntimeError("prospective protocol/cohort absent from history")
        if (
            subprocess.check_output(
                ["git", "-C", str(root), "show", f"{commit}:{path.as_posix()}"]
            )
            != (root / path).read_bytes()
        ):
            raise RuntimeError("prospective protocol/cohort bytes changed")
    frozen = frozen_cohort(root)
    selection_commit = frozen["selection_source_commit"]
    if subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            selection_commit,
            COHORT_COMMIT,
        ],
        check=False,
    ).returncode:
        raise RuntimeError("selection source not published before cohort")
    for name, expected in frozen["selection_source_sha256"].items():
        published = subprocess.check_output(
            ["git", "-C", str(root), "show", f"{selection_commit}:{name}"]
        )
        if hashlib.sha256(published).hexdigest() != expected:
            raise RuntimeError("selection source bytes absent at published commit")
    return head


def require_admission(root: Path, fingerprint: str) -> dict[str, Any]:
    """Recompute the published strict forecast before permitting own training."""
    from river_full_broader.forecast import forecast

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
        raise ArithmeticError("broader-full forecast/admission changed")
    return decision
