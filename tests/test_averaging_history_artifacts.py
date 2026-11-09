"""Own raw masses retain time weights; corrupted schema/menus/weights fail closed."""

import copy
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_artifacts import (
    decode_mass,
    pack_mass,
    unpack_mass,
    write_mass,
)
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.training_isolation import sentinel_tree


def fixture(path: Path) -> tuple[Any, ...]:
    tree = sentinel_tree()
    mass = tree.legal * 7.0
    # Legal signed zeros preserve their exact bits; illegal padding is positive 0.
    mass[0, 0] = -0.0
    metadata = dict(
        id="explicit-toy-mass", index=0, work_label=123, source_sha256="f" * 64
    )
    receipt = write_mass(path, tree, mass, metadata)
    row = dict(
        **metadata, receipt=receipt, metadata_sha256=sha(metadata), file=path.name
    )
    return tree, mass, row, path.read_bytes()


def test_raw_cumulative_mass_round_trip_is_bit_exact_and_not_normalized(
    tmp_path: Path,
) -> None:
    tree, mass, row, blob = fixture(tmp_path / "mass.gz")
    decoded = decode_mass(blob, tree, row)
    assert mass.tobytes() == decoded.tobytes()
    assert not decoded.flags.writeable
    assert not np.allclose(decoded.sum(axis=1), 1)
    assert decoded[0, 1] == 7
    assert not np.shares_memory(decoded, mass)


@pytest.mark.parametrize(
    "mode",
    [
        "format",
        "dtype",
        "shape",
        "menu",
        "metadata",
        "missing",
        "boolean",
        "negative",
        "nan",
        "extra",
    ],
)
def test_rehashed_but_corrupt_mass_payload_still_fails(
    tmp_path: Path, mode: str
) -> None:
    tree, _, row, blob = fixture(tmp_path / "mass.gz")
    saved = json.loads(gzip.decompress(blob))
    if mode == "format":
        saved["format"] = "wrong"
    elif mode == "dtype":
        saved["dtype"] = "<f4"
    elif mode == "shape":
        saved["shape"][0] += 1
    elif mode == "menu":
        saved["actions"][0].reverse()
    elif mode == "metadata":
        saved["metadata"]["work_label"] += 1
    elif mode == "missing":
        saved["mass"].pop()
    elif mode == "extra":
        saved["extra"] = True
    else:
        saved["mass"][0][0] = dict(boolean=True, negative=-1.0, nan=float("nan"))[mode]
    # Deliberately rehash outer bytes, leaving inner source/weight contracts checked.
    altered = gzip.compress(json.dumps(saved, sort_keys=True).encode(), mtime=0)
    changed = copy.deepcopy(row)
    changed["receipt"].update(
        bytes=len(altered), sha256=hashlib.sha256(altered).hexdigest()
    )
    with pytest.raises((ArithmeticError, ValueError)):
        decode_mass(altered, tree, changed)


@pytest.mark.parametrize("mode", ["hash", "bytes", "mass_hash", "source"])
def test_mass_receipt_changes_are_rejected(tmp_path: Path, mode: str) -> None:
    tree, _, row, blob = fixture(tmp_path / "mass.gz")
    if mode == "source":
        row["source_sha256"] = "0" * 64
    elif mode == "bytes":
        row["receipt"]["bytes"] = float(len(blob))
    else:
        row["receipt"]["sha256" if mode == "hash" else "mass_sha256"] = "0" * 64
    with pytest.raises(ArithmeticError):
        decode_mass(blob, tree, row)


def test_mass_writer_retains_existing_and_partial_outputs(tmp_path: Path) -> None:
    path = tmp_path / "mass.gz"
    tree, mass, _, _ = fixture(path)
    with pytest.raises(FileExistsError):
        write_mass(path, tree, mass, {})
    pending = tmp_path / "another.gz"
    pending.with_suffix(".gz.tmp").write_bytes(b"retained partial")
    with pytest.raises(FileExistsError):
        write_mass(pending, tree, mass, {})
    assert pending.with_suffix(".gz.tmp").read_bytes() == b"retained partial"


def test_mass_padding_illegal_actions_and_overflowing_row_totals_fail() -> None:
    tree = sentinel_tree()
    padding = tree.legal == 0
    assert padding.any()
    for bad in (-0.0, 1.0):
        mass = tree.legal.copy()
        mass[padding] = bad
        with pytest.raises(ValueError):
            pack_mass(tree, mass)
    rows = pack_mass(tree, tree.legal)
    rows[0][0] = True
    with pytest.raises(ArithmeticError):
        unpack_mass(tree, rows)
    with np.errstate(over="ignore"):
        with pytest.raises(ValueError):
            pack_mass(tree, tree.legal * 1e308)


def test_mass_serialization_is_deterministic(tmp_path: Path) -> None:
    _, _, _, first = fixture(tmp_path / "one.gz")
    _, _, _, second = fixture(tmp_path / "two.gz")
    assert first == second
    canonical(json.loads(gzip.decompress(first)))
