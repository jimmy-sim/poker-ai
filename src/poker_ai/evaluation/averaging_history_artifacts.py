"""Compact immutable OWN cumulative masses, distinct from normalized policies."""

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_math import validate_mass
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.parallel_profile import same

MASS_FORMAT = "poker-ai-own-cumulative-strategy-mass-v1"
OUTER_FIELDS = {"receipt", "metadata_sha256", "file", "seconds", "cpu_seconds"}


def array_sha(weights: FloatArray) -> str:
    return hashlib.sha256(np.asarray(weights, dtype="<f8").tobytes()).hexdigest()


def pack_mass(tree: ArrayTree, weights: FloatArray) -> list[list[float]]:
    validate_mass(tree, weights)
    if np.any(np.signbit(weights) & (tree.legal == 0)):
        raise ValueError("cumulative mass requires canonical positive-zero padding")
    return [weights[i, : len(menu)].tolist() for i, menu in enumerate(tree.actions)]


def unpack_mass(tree: ArrayTree, rows: Any) -> FloatArray:
    if (
        not isinstance(rows, list)
        or len(rows) != len(tree.keys)
        or any(
            not isinstance(row, list)
            or len(row) != len(menu)
            or any(type(v) not in (int, float) for v in row)
            for row, menu in zip(rows, tree.actions, strict=True)
        )
    ):
        raise ArithmeticError("cumulative mass requires all legal numeric rows")
    mass = np.zeros_like(tree.legal)
    for i, row in enumerate(rows):
        mass[i, : len(row)] = row
    validate_mass(tree, mass)
    return mass


def write_mass(
    path: Path, tree: ArrayTree, mass: FloatArray, metadata: dict[str, Any]
) -> dict[str, Any]:
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain complete/partial own cumulative mass")
    payload = dict(
        format=MASS_FORMAT,
        dtype="<f8",
        shape=list(tree.legal.shape),
        actions=[list(menu) for menu in tree.actions],
        metadata=metadata,
        mass=pack_mass(tree, mass),
    )
    blob = gzip.compress(canonical(payload), mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(blob)
    temporary.replace(path)
    return dict(
        bytes=len(blob),
        sha256=hashlib.sha256(blob).hexdigest(),
        mass_sha256=array_sha(mass),
    )


def decode_mass(blob: bytes, tree: ArrayTree, row: dict[str, Any]) -> FloatArray:
    receipt = row["receipt"]
    if (
        type(receipt["bytes"]) is not int
        or len(blob) != receipt["bytes"]
        or hashlib.sha256(blob).hexdigest() != receipt["sha256"]
    ):
        raise ArithmeticError("cumulative mass bytes changed")
    saved = json.loads(gzip.decompress(blob))
    if (
        set(saved) != {"format", "dtype", "shape", "actions", "metadata", "mass"}
        or saved["format"] != MASS_FORMAT
        or saved["dtype"] != "<f8"
        or not same(saved["shape"], list(tree.legal.shape))
        or not same(saved["actions"], [list(menu) for menu in tree.actions])
        or sha(saved["metadata"]) != row["metadata_sha256"]
        or any(
            not same(saved["metadata"][k], v)
            for k, v in row.items()
            if k not in OUTER_FIELDS
        )
    ):
        raise ArithmeticError("cumulative mass schema/menu/source binding changed")
    mass = unpack_mass(tree, saved["mass"])
    if array_sha(mass) != receipt["mass_sha256"]:
        raise ArithmeticError("cumulative mass fingerprint changed")
    mass.flags.writeable = False
    return mass
