"""Immutable source-bound own checkpoint files; no reference input path."""

import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.compact_full_context import Context, metrics
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.public_range_definition import CONFIG, check_inputs, contract
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

FORMAT = "compact-full-own-v1"
SNAPSHOT = "compact-full-own-checkpoint-v1"
IDENTITY = ("spot_file", "representation", "iteration")
ENTRYPOINTS = ("scripts/validate_compact_full.py",)


def atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def source(root: Path, *, clean: bool) -> dict[str, Any]:
    if not Path(__file__).resolve().is_relative_to((root / "src").resolve()):
        raise ArithmeticError("imported runner is outside the stated checkout")
    result = source_provenance(root, root / CONFIG, entrypoints=ENTRYPOINTS)
    if clean and result["dirty"] is not False:
        raise ValueError("publish tested source and use a clean worktree")
    result["fingerprint"] = sha(result["sha256"])
    return result


def check_source(root: Path, saved: dict[str, Any]) -> None:
    if (
        source(root, clean=False)["fingerprint"] != saved["fingerprint"]
        or sha(saved["sha256"]) != saved["fingerprint"]
    ):
        raise ArithmeticError("compact full source/config fingerprint changed")
    commit_sources(root, saved["git_commit"], saved["sha256"])
    check_inputs(root, contract(root))


def commit_sources(root: Path, commit: str, hashes: dict[str, str]) -> None:
    """Bind the recorded commit with one Git inventory, avoiding a process/file."""
    raw = subprocess.check_output(
        ["git", "-C", str(root), "ls-tree", "-r", "-z", commit]
    )
    blobs = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, git_name = entry.split(b"\t", 1)
        mode, kind, git_oid = metadata.split()
        if kind == b"blob" and mode in (b"100644", b"100755"):
            blobs[git_name.decode()] = git_oid.decode()
    for name, checksum in hashes.items():
        content = (root / name).read_bytes()
        # This repository uses Git's SHA-1 object format. SHA-256 above remains
        # the scientific content binding; SHA-1 here identifies the Git object.
        oid = hashlib.sha1(
            b"blob " + str(len(content)).encode() + b"\0" + content
        ).hexdigest()
        if hashlib.sha256(content).hexdigest() != checksum or blobs.get(name) != oid:
            raise ArithmeticError(
                "tested/recorded commit source differs from current source"
            )


def published(root: Path, path: Path) -> str:
    """Require the exact bytes in fetched origin's current research branch.

    This checks Git objects, not a remote execution attestation. The operator
    must push/fetch the publication checkpoint before calling it.
    """
    relative = str(path.resolve().relative_to(root.resolve()))
    branch = subprocess.check_output(
        ["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"], text=True
    ).strip()
    ref = "origin/" + branch
    blob = subprocess.check_output(
        ["git", "-C", str(root), "show", f"{ref}:{relative}"]
    )
    if blob != path.read_bytes():
        raise ArithmeticError("publish exact own/admission bytes before comparison")
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", ref], text=True
    ).strip()


def checked_array(saved: Any, tree_shape: tuple[int, ...]) -> FloatArray:
    # np.asarray silently accepts booleans/strings: reject before conversion.
    if (
        not isinstance(saved, list)
        or any(not isinstance(r, list) for r in saved)
        or any(type(x) not in (int, float) for r in saved for x in r)
    ):
        raise ValueError("checkpoint arrays require numeric rows, not booleans/strings")
    array = np.asarray(saved, dtype=np.float64)
    if array.shape != tree_shape or not np.isfinite(array).all():
        raise ValueError("checkpoint array shape/finiteness changed")
    return array


def capture(
    context: Context,
    iteration: int,
    policy: FloatArray,
    sums: FloatArray,
    regrets: FloatArray,
) -> dict[str, Any]:
    if type(iteration) is not int or iteration < 1:
        raise ValueError("positive integer full iteration required")
    tree = context.scoring.partition
    tree.validate_policy(policy)
    for array in (sums, regrets):
        if (
            array.shape != tree.legal.shape
            or not np.isfinite(array).all()
            or np.any(array < 0)
            or np.any(array * (1 - tree.legal))
        ):
            raise ValueError("nonnegative finite legal CFR+ tables required")
    if not np.allclose(tree.normalize(sums), policy, atol=1e-15, rtol=0):
        raise ArithmeticError("policy is not the normalized linear strategy sum")
    return dict(
        format=SNAPSHOT,
        **context.binding,
        iteration=iteration,
        total_node_work=2 * iteration * len(tree.player),
        actions=[list(a) for a in tree.actions],
        policy=policy.tolist(),
        strategy_sum=sums.tolist(),
        regrets=regrets.tolist(),
        metrics=metrics(context, policy, sums),
    )


def write_snapshot(path: Path, saved: dict[str, Any]) -> dict[str, Any]:
    if path.exists() or path.is_symlink():
        raise FileExistsError("retain previous own checkpoint")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(gzip.compress(canonical(saved), mtime=0))
    temporary.replace(path)
    return dict(file=path.name, sha256=digest(path), bytes=path.stat().st_size)


def decode(context: Context, saved: dict[str, Any]) -> dict[str, Any]:
    expected_keys = set(context.binding) | {
        "format",
        "iteration",
        "total_node_work",
        "actions",
        "policy",
        "strategy_sum",
        "regrets",
        "metrics",
    }
    if set(saved) != expected_keys or saved["format"] != SNAPSHOT:
        raise ValueError("own checkpoint schema changed")
    if any(saved[k] != v for k, v in context.binding.items()):
        raise ArithmeticError("checkpoint context/tree/mapping binding changed")
    shape = context.scoring.partition.legal.shape
    recomputed = capture(
        context,
        saved["iteration"],
        checked_array(saved["policy"], shape),
        checked_array(saved["strategy_sum"], shape),
        checked_array(saved["regrets"], shape),
    )
    if canonical(saved) != canonical(recomputed):
        raise ArithmeticError("checkpoint actions/work/metrics/average changed")
    return recomputed


def load_snapshot(directory: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    name = receipt["file"]
    if (
        type(name) is not str
        or Path(name).name != name
        or not name.endswith(".json.gz")
    ):
        raise ValueError("checkpoint must be a local file name")
    path = directory / name
    if (
        path.is_symlink()
        or path.stat().st_size != receipt["bytes"]
        or digest(path) != receipt["sha256"]
    ):
        raise ArithmeticError("checkpoint bytes/hash changed")
    result: dict[str, Any] = json.loads(gzip.decompress(path.read_bytes()))
    return result


def inventory(saved: dict[str, Any], config: dict[str, Any]) -> None:
    software = saved["software_only"]
    if type(software) is not bool:
        raise ValueError("software marker must be boolean")
    spots = (
        ["software-kuhn-1", "software-kuhn--1"] if software else config["spot_files"]
    )
    layouts = {(s, r) for s in spots for r in config["representations"]}
    expected = {(s, r, t) for s, r in layouts for t in config["full"]["checkpoints"]}
    ids = [tuple(r[k] for k in IDENTITY) for r in saved["rows"]]
    partitions = [(r["spot_file"], r["representation"]) for r in saved["partitions"]]
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or len(ids) != len(set(ids))
        or set(ids) != expected
        or len(partitions) != len(set(partitions))
        or set(partitions) != layouts
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
    ):
        raise ArithmeticError(
            "complete unique 72-policy/12-layout own inventory required"
        )
    for row in saved["rows"]:
        if type(row["iteration"]) is not int:
            raise ValueError("strict integer checkpoint required")
    files = [r["snapshot"]["file"] for r in saved["rows"]]
    if len(set(files)) != len(files):
        raise ArithmeticError("checkpoint file reused")


def array_sha(array: FloatArray) -> str:
    return hashlib.sha256(np.asarray(array, dtype="<f8").tobytes()).hexdigest()
