"""Source-bound validation-only recall reuse; historical src stays unchanged.

The pinned original predicate consumes five structural fields, not policies or
payoffs. Hash every request; retain only successful stable proofs. This private
experimental adapter is not a production or scientific-admission integration.
"""

import hashlib
import importlib
import importlib.util
import json
import os
import struct
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np

from poker_ai.finite import ArrayTree
from poker_ai.postflop.learning_artifacts import sha

CONFIG = "configs/recall-proof-cache.json"
CONFIG_SHA = "f78198c7570fe21f0164cec8303207ac840bc804d26163946fd1a98a1c1dc09b"
ENTRY = "scripts/compare_recall_cache.py"
SUPPORT = "scripts/recall_cache_support.py"
FOLDER = "results/recall-proof-cache"


def geometry(tree: ArrayTree, version: str) -> str | None:
    """Exact field/dtype/shape/C-byte framing; unsupported types fall back.

    Includes padded children and every level conservatively. Boolean/integer
    ndarrays are the typed tree domain; subclasses and other dtypes are not
    certified. Stable single-threaded data during the call is required, as for
    the original predicate. Between-call mutation always changes the key.
    """
    if type(tree.levels) is not tuple:
        return None
    values = [
        (n, getattr(tree, n)) for n in ("children", "valid", "player", "information")
    ]
    values.extend((f"levels/{i}", a) for i, a in enumerate(tree.levels))
    h = hashlib.sha256(b"recall-geometry-v1\0" + version.encode())
    for name, value in values:
        if type(value) is not np.ndarray or value.dtype.kind not in "biu":
            return None
        header = json.dumps(
            [name, value.dtype.str, value.shape], separators=(",", ":")
        ).encode()
        raw = value.tobytes(order="C")
        h.update(struct.pack("<Q", len(header)))
        h.update(header)
        h.update(struct.pack("<Q", len(raw)))
        h.update(raw)
    return h.hexdigest()


class RecallProofs:
    """Equivalent predicate for stable typed trees; never caches a rejection."""

    def __init__(
        self, original: Callable[[ArrayTree], None], version: str, *, enabled: bool
    ) -> None:
        if len(version) != 64 or any(c not in "0123456789abcdef" for c in version):
            raise ValueError("pinned validator SHA256 required")
        self.original, self.version, self.enabled = original, version, enabled
        self.proven: set[str] = set()
        self.requests = self.traversals = self.hits = self.rejections = (
            self.fallbacks
        ) = 0

    def __call__(self, tree: ArrayTree) -> None:
        self.requests += 1
        key = geometry(tree, self.version) if self.enabled else None
        if key is not None and key in self.proven:
            self.hits += 1
            return
        self.traversals += 1
        if self.enabled and key is None:
            self.fallbacks += 1
        try:
            self.original(tree)
        except BaseException:
            self.rejections += 1
            raise
        if key is not None:
            if geometry(tree, self.version) != key:
                self.rejections += 1
                raise ValueError("tree geometry changed during validation")
            self.proven.add(key)

    def summary(self) -> dict[str, Any]:
        return dict(
            requests=self.requests,
            original_traversals=self.traversals,
            hits=self.hits,
            rejections=self.rejections,
            fallbacks=self.fallbacks,
            successful_proofs=len(self.proven),
            enabled=self.enabled,
        )


def profile_tool(root: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "_recall_original_profile", root / "scripts/profile_compact_replay.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract(root: Path) -> dict[str, Any]:
    p = profile_tool(root)
    if p.digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective recall-cache contract changed")
    saved: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return saved


def source(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.validation.five_card import source_provenance

    p = profile_tool(root)
    c = contract(root)
    _, old = p.preflight(root)
    if p.digest(root / c["validator_file"]) != c["validator_sha256"]:
        raise ArithmeticError("original recall checker changed")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    current["sha256"].update(old["sha256"])
    current["fingerprint"] = sha(current["sha256"])
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


def checked(root: Path, current: dict[str, Any]) -> None:
    from poker_ai.evaluation.compact_opponent_admission import published
    from poker_ai.evaluation.diagnostic_receipts import checks

    p = profile_tool(root)
    _, dependency = p.preflight(root)
    p.checked(root, dependency)
    path = root / FOLDER / "checks.json"
    checks(root, path, current)
    published(root, path)
    for row in json.loads(path.read_text())["checks"]:
        published(root, root / row["log"]["file"])


@contextmanager
def hooks(c: dict[str, Any], *, enabled: bool) -> Iterator[RecallProofs]:
    modules = [importlib.import_module(name.rsplit(".", 1)[0]) for name in c["hooks"]]
    original = vars(modules[0])["require_recall"]
    if any(vars(m)["require_recall"] is not original for m in modules):
        raise ArithmeticError("recall hook no longer names the original function")
    cache = RecallProofs(original, c["validator_sha256"], enabled=enabled)
    with ExitStack() as stack:
        for m in modules:
            stack.enter_context(patch.object(m, "require_recall", cache))
        yield cache


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    from poker_ai.evaluation.compact_opponent_guard import isolated
    from poker_ai.postflop.river_study import Deadline
    from poker_ai.reproducibility import runtime_environment

    p = profile_tool(root)
    saved: dict[str, Any] = dict(
        status="running",
        mode=mode,
        poker_training_performed=False,
        reference_constructed=False,
        admission_evidence=False,
    )
    receipt = output / "child.json"
    p.atomic(receipt, saved)
    try:
        c, current = source(root)
        checked(root, current)
        saved.update(
            source=current, config_sha256=p.digest(root / CONFIG), scope=c["scope"]
        )
        p.atomic(receipt, saved)
        deadline = Deadline(c["maximum_child_seconds"])
        deadline.started = origin
        with isolated(worker=False), hooks(c, enabled=mode == "cached") as cache:
            actual = p.read_with_actual(root, root / c["baseline_own"], deadline)
        saved["identity"] = p.identity(
            actual["own"], p.contract(root), actual["computed_replay"]
        )
        saved["cache"] = cache.summary()
        if saved["cache"]["requests"] != c["expected_requests_per_mode"]:
            raise ArithmeticError("full registered recall request inventory changed")
        after_c, after = source(root)
        if after_c != c or after["sha256"] != current["sha256"]:
            raise ArithmeticError("cache experiment source/input changed")
        saved.update(
            status="complete_saved_replay",
            environment=runtime_environment(),
            seconds=time.perf_counter() - origin,
        )
        p.atomic(receipt, saved)
        deadline.check()
        return 0
    except BaseException as exc:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(exc).__name__, message=str(exc)),
        )
        p.atomic(receipt, saved)
        raise


def pair_identity(uncached: dict[str, Any], cached: dict[str, Any]) -> dict[str, Any]:
    p = json.dumps
    if (
        uncached["status"] != "complete_saved_replay"
        or cached["status"] != "complete_saved_replay"
        or uncached["mode"] != "uncached"
        or cached["mode"] != "cached"
        or p(uncached["identity"], sort_keys=True, allow_nan=False)
        != p(cached["identity"], sort_keys=True, allow_nan=False)
        or uncached["source"]["sha256"] != cached["source"]["sha256"]
        or uncached["config_sha256"] != cached["config_sha256"]
    ):
        raise ArithmeticError("complete uncached/cached replay identity changed")
    a, b = uncached["cache"], cached["cache"]
    for row in (a, b):
        if set(row) != {
            "requests",
            "original_traversals",
            "hits",
            "rejections",
            "fallbacks",
            "successful_proofs",
            "enabled",
        }:
            raise ArithmeticError("complete cache counter fields required")
        if any(type(row[k]) is not int or row[k] < 0 for k in row if k != "enabled"):
            raise ArithmeticError("cache counters must be nonnegative integers")
        if row["requests"] != row["original_traversals"] + row["hits"]:
            raise ArithmeticError("cache request accounting changed")
    if (
        a["requests"] != b["requests"]
        or a["original_traversals"] != a["requests"]
        or a["enabled"] is not False
        or b["enabled"] is not True
        or b["hits"] <= 0
        or b["original_traversals"] >= a["original_traversals"]
        or a["rejections"] != 0
        or b["rejections"] != 0
        or a["successful_proofs"] != 0
        or a["fallbacks"] != 0
        or b["successful_proofs"] != b["original_traversals"] - b["fallbacks"]
    ):
        raise ArithmeticError("cache proof/traversal counters changed")
    return dict(
        status="same_complete_replay_with_reused_proofs", identity=uncached["identity"]
    )


def main(root: Path) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stop-at", required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/recall-proof-cache/pair")
    )
    parser.add_argument(
        "--_mode", choices=("uncached", "cached"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    if args._mode:
        return child(
            root,
            args._mode,
            args.output,
            float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"]),
        )
    p = profile_tool(root)
    c = contract(root)
    cutoff = datetime.fromisoformat(args.stop_at.replace("Z", "+00:00"))
    reserve = (
        c["maximum_pair_seconds"]
        + c["final_ci_reserve_seconds"]
        + c["save_reserve_seconds"]
    )
    if cutoff.tzinfo is None or (cutoff - datetime.now(UTC)).total_seconds() < reserve:
        raise TimeoutError("full pair, final CI and save reserves do not fit cutoff")
    output = root / args.output
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain complete/partial cache experiment")
    output.mkdir(parents=True)
    started = time.perf_counter()
    saved: dict[str, Any] = dict(
        status="running", order=c["order"], measurements=[], admission_evidence=False
    )
    p.atomic(output / "pair.json", saved)
    try:
        for mode in c["order"]:
            remaining = c["maximum_pair_seconds"] - (time.perf_counter() - started)
            if remaining <= 0:
                raise TimeoutError("shared cache pair clock exhausted")
            destination = output / mode
            m = p.supervise(
                [
                    sys.executable,
                    str(root / ENTRY),
                    "--output",
                    str(destination),
                    "--stop-at",
                    args.stop_at,
                    "--_mode",
                    mode,
                ],
                destination,
                min(c["maximum_child_seconds"], remaining),
            )
            saved["measurements"].append(m)
            p.atomic(output / "pair.json", saved)
            if (
                m["returncode"] != 0
                or not 0 < m["seconds"] < c["maximum_child_seconds"]
            ):
                raise ArithmeticError("complete cache comparison child failed its cap")
        a, b = [
            json.loads((output / mode / "child.json").read_text())
            for mode in c["order"]
        ]
        saved.update(pair_identity(a, b), seconds=time.perf_counter() - started)
        saved["narrow_wall_time_pass"] = (
            saved["measurements"][1]["seconds"] < saved["measurements"][0]["seconds"]
        )
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("cache pair exceeded its shared cap")
        p.atomic(output / "pair.json", saved)
    except BaseException as exc:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(exc).__name__, message=str(exc)),
        )
        p.atomic(output / "pair.json", saved)
        raise
    print(
        saved["status"]
        + f"; narrow_wall_time_pass={saved['narrow_wall_time_pass']}"
        + "; no production integration or admission"
    )
    return 0 if saved["narrow_wall_time_pass"] else 2
