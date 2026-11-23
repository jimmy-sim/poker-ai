"""Frozen two-path known-case comparison and source prerequisites."""

import hashlib
import json
from pathlib import Path
from typing import Any

from turn_exact_transfer.gate import SOURCE as PARENT_SOURCE
from turn_exact_transfer.gate import source_fingerprint as parent_fingerprint
from turn_exact_transfer.learning import (
    CANDIDATE as CANDIDATE,
)
from turn_exact_transfer.learning import (
    CONTROL as CONTROL,
)
from turn_exact_transfer.learning import (
    GAMES,
    PathSpec,
    context,
)

CONFIG = Path("configs/known-turn-exact-mechanism.json")
PROTOCOL = Path("docs/known-turn-exact-mechanism.md")
CONFIG_SHA256 = "00d714f87a2b990c3b2dccf5421f5926d9e3a1b34b0721781ae9b49900f88cd5"
PROTOCOL_SHA256 = "f38ee26d4dc7764ea3cfea7935e30d9cc7ec282763fedd65d655eba2d7f169cf"
PARENT_FINGERPRINT = "fb9006517142ee23076f2c0b6d581475dfdaed8127cb2c146a60731af901b09c"
PARENT_SOURCE_SHA256 = (
    "af541362cdea019e33bca2385b83b79ebbed40b52fc926ba287243ccf2dc4071"
)
GAME = GAMES[0]
SPOT = Path("configs/river-full-broader-spots/full_new_medium_dry_oop.json")
SPOT_SHA256 = "b7c74e0de96e9949f8eb0e359d085b4e3281ea3172b9979f8a23f394bb642dea"
ARMS = (CONTROL, CANDIDATE)
LABELS = (100_000, 1_000_000, 10_000_000)
READOUTS = ("current", "linear_average")


def digest(path: Path) -> str:
    """Return a file's SHA-256 without following protocol alterations."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths() -> tuple[PathSpec, PathSpec]:
    """A single known input, control first, then candidate, seed zero."""
    return PathSpec(0, GAME, CONTROL), PathSpec(1, GAME, CANDIDATE)


def contract(root: Path) -> dict[str, Any]:
    """Guard published plan, known input and unchanged PR #107 source."""
    if (
        digest(root / CONFIG) != CONFIG_SHA256
        or digest(root / PROTOCOL) != PROTOCOL_SHA256
    ):
        raise ArithmeticError("published known-turn protocol changed")
    data: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        data["issue"] != 4
        or data["spot"] != SPOT.as_posix()
        or data["spot_sha256"] != SPOT_SHA256
        or data["control"] != CONTROL
        or data["candidate"] != CANDIDATE
        or data["seed_per_path"] != 0
        or tuple(data["work_labels"]) != LABELS
        or tuple(data["readouts"]) != READOUTS
        or data["path_order"] != ["control", "candidate"]
        or data["profile"]["worker_count"] != 2
        or data["profile"]["repeats_per_path"] != 3
        or data["caps_seconds"]["whole_own"] != 7200
        or data["caps_seconds"]["native_audit"] != 900
    ):
        raise ArithmeticError("known-turn contract grid changed")
    if digest(root / SPOT) != SPOT_SHA256:
        raise ArithmeticError("known turn input changed")
    if (
        parent_fingerprint(root) != PARENT_FINGERPRINT
        or digest(root / PARENT_SOURCE / "manifest.json") != PARENT_SOURCE_SHA256
    ):
        raise ArithmeticError("qualified PR #107 source changed")
    return data


__all__ = [
    "ARMS",
    "CONFIG",
    "CONFIG_SHA256",
    "GAME",
    "LABELS",
    "PROTOCOL",
    "READOUTS",
    "SPOT",
    "contract",
    "context",
    "paths",
]
