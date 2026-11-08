"""Stream source-bound OWN checkpoint files; reference strategies cannot enter."""

import base64
import gzip
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.controlled_checkpoints import FORMAT, unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest

FORMAT_ARCHIVE = "poker-ai-controlled-own-checkpoints-jsonl-v1"


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(blob: bytes, context: ScoringContext, row: dict[str, Any]) -> dict[str, Any]:
    receipt = row["receipt"]
    if (
        len(blob) != receipt["bytes"]
        or hashlib.sha256(blob).hexdigest() != receipt["sha256"]
    ):
        raise ArithmeticError("own snapshot bytes changed")
    saved: dict[str, Any] = json.loads(gzip.decompress(blob))
    tree = context.partition
    if (
        set(saved) != {"format", "dtype", "shape", "actions", "metadata", "policy"}
        or saved["format"] != FORMAT
        or saved["dtype"] != "<f8"
        or not same(saved["shape"], list(tree.legal.shape))
        or not same(saved["actions"], [list(menu) for menu in tree.actions])
        or sha(saved["metadata"]) != row["metadata_sha256"]
    ):
        raise ArithmeticError("own snapshot schema/metadata/menu changed")
    policy = unpack_policy(tree, saved["policy"])
    if (
        hashlib.sha256(np.asarray(policy, dtype="<f8").tobytes()).hexdigest()
        != receipt["policy_sha256"]
    ):
        raise ArithmeticError("own policy fingerprint changed")
    metadata = saved["metadata"]
    if any(
        not same(metadata[k], row[k])
        for k in row
        if k not in {"receipt", "metadata_sha256", "file", "seconds", "cpu_seconds"}
    ):
        raise ArithmeticError("own scalar row differs from snapshot")
    return dict(**metadata, policy=saved["policy"])


def write_archive(output: Path, scratch: Path, rows: list[dict[str, Any]]) -> str:
    if output.exists():
        raise FileExistsError("retain own checkpoint archive")
    temporary = output.with_suffix(".tmp")
    with (
        temporary.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as stream,
    ):
        stream.write(
            canonical(dict(format=FORMAT_ARCHIVE, snapshots=len(rows))) + b"\n"
        )
        for row in rows:
            blob = (scratch / row["file"]).read_bytes()
            if hashlib.sha256(blob).hexdigest() != row["receipt"]["sha256"]:
                raise ArithmeticError("own snapshot changed before archiving")
            stream.write(
                canonical(
                    dict(id=row["id"], blob=base64.b64encode(blob).decode("ascii"))
                )
                + b"\n"
            )
    temporary.replace(output)
    return digest(output)


def read_archive(
    path: Path, expected_sha: str, rows: list[dict[str, Any]]
) -> Iterator[tuple[dict[str, Any], bytes]]:
    if digest(path) != expected_sha:
        raise ArithmeticError("own checkpoint archive hash changed")
    with gzip.open(path, "rt") as stream:
        header = json.loads(next(stream))
        if not same(header, dict(format=FORMAT_ARCHIVE, snapshots=len(rows))):
            raise ArithmeticError("own archive inventory changed")
        for row in rows:
            line = stream.readline()
            if not line:
                raise ArithmeticError("own archive truncated")
            item = json.loads(line)
            if item["id"] != row["id"]:
                raise ArithmeticError("own archive order/identity changed")
            yield row, base64.b64decode(item["blob"], validate=True)
        if stream.read():
            raise ArithmeticError("own archive has extra snapshots")
