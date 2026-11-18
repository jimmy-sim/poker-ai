"""Verify published raw receipts without importing the original poker readers."""

import hashlib
import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/receipt-consumer-mutation/raw"
VERSIONS = {"311": ("3.11.17", "2.4.6"), "312": ("3.12.15", "2.5.4")}
SOURCE = "9b401130c12c1cb7b15afa1f677e4e5fa9174465"
LOCK = "db5529861ae56225daaf8a18513013e52bee88ef667227855b719a7e1364250c"


class BlockPokerReaders(MetaPathFinder):
    def find_spec(
        self, fullname: str, path: Any, target: Any = None
    ) -> ModuleSpec | None:
        if fullname == "poker_ai" or fullname.startswith("poker_ai."):
            raise ImportError("poker readers blocked in data-only report")
        return None


@contextmanager
def block_poker_readers() -> Iterator[None]:
    if any(name == "poker_ai" or name.startswith("poker_ai.") for name in sys.modules):
        raise ArithmeticError("original reader imported during data-only report")
    blocker = BlockPokerReaders()
    sys.meta_path.insert(0, blocker)
    try:
        yield
    finally:
        sys.meta_path.remove(blocker)


def read_verified(name: str, metadata: dict[str, Any]) -> bytes:
    raw = (RAW / name).read_bytes()
    if (
        len(raw) != metadata["bytes"]
        or hashlib.sha256(raw).hexdigest() != metadata["sha256"]
    ):
        raise ArithmeticError(f"raw member changed: {name}")
    return raw


def verify_raw() -> dict[str, Any]:
    if any(name == "poker_ai" or name.startswith("poker_ai.") for name in sys.modules):
        raise ArithmeticError("original reader imported during data-only report")
    manifest = json.loads((RAW / "manifest.json").read_bytes())
    if manifest["published_source_commit"] != SOURCE or set(manifest["files"]) != {
        f"{version}/{name}"
        for version in VERSIONS
        for name in ("child.json", "child.log", "outer.json")
    }:
        raise ArithmeticError("raw archive membership or source changed")
    reports: dict[str, Any] = {}
    prior: dict[str, Any] | None = None
    for version, (python, numpy) in VERSIONS.items():
        members = {
            name: read_verified(
                f"{version}/{name}", manifest["files"][f"{version}/{name}"]
            )
            for name in ("child.json", "child.log", "outer.json")
        }
        child = json.loads(members["child.json"])
        outer = json.loads(members["outer.json"])
        if (
            members["child.log"]
            or child["head"] != SOURCE
            or child["dirty"]
            or child["python"] != python
            or child["numpy"] != numpy
            or child["lock_sha256"] != LOCK
            or child["status"] != "seven_prerequisites_unchanged_through_complete_read"
            or child["saved_status"] != "completed_own_native_pending"
            or child["saved_own_replay"]["status"]
            != "all_batch_profiles_and_raw_observations_replayed"
            or child["saved_own_replay"]["maximum_error_chips"] != 0
            or child["saved_own_replay"]["maximum_error_unitless"] != 0
            or outer["status"] != "passed"
            or outer["returncode"] != 0
            or not outer["child_receipt_present"]
            or not 0 < child["elapsed_seconds"] < outer["outer_elapsed_seconds"] < 180
        ):
            raise ArithmeticError(f"original read or cap failed: {version}")
        rows = child["observations"]
        if len(rows) != 7:
            raise ArithmeticError(f"wrong number of observations: {version}")
        for index, row in enumerate(rows):
            if row["index"] != index or row["kind"] != (
                "nested" if index < 6 else "direct"
            ):
                raise ArithmeticError(f"prerequisite order changed: {version}")
            if row["load"] != row["after_archive"]:
                raise ArithmeticError(f"archive changed prerequisite: {version}")
            if index < 6 and row["load"] != row["after_caller"]:
                raise ArithmeticError(f"receipt changed prerequisite: {version}")
            if index == 6 and row["after_caller"] is not None:
                raise ArithmeticError("direct load has no timing receipt caller")
        if len({json.dumps(row["load"], sort_keys=True) for row in rows}) != 1:
            raise ArithmeticError(f"loaded prerequisites differ: {version}")
        comparable = {
            "own_sha256": child["own_sha256"],
            "input_sha256": child["input_sha256"],
            "saved_source_sha256": child["saved_source_sha256"],
            "saved_own_replay": child["saved_own_replay"],
            "saved_batch_count": child["saved_batch_count"],
            "saved_row_count": child["saved_row_count"],
            "saved_mass_count": child["saved_mass_count"],
            "saved_current_count": child["saved_current_count"],
            "witness": rows[0]["load"],
        }
        if prior is not None and comparable != prior:
            raise ArithmeticError("locked runtimes disagree on archived semantics")
        prior = comparable
        reports[version] = {
            "python": python,
            "numpy": child["numpy"],
            "outer_seconds": outer["outer_elapsed_seconds"],
            "child_seconds": child["elapsed_seconds"],
            "observed_graphs": len(rows),
            "unchanged_nested_caller_checks": 6,
            "unchanged_archive_checks": 7,
            "graph_witness": rows[0]["load"],
        }
    if any(name == "poker_ai" or name.startswith("poker_ai.") for name in sys.modules):
        raise ArithmeticError("original reader imported during data-only report")
    return {
        "status": "passed",
        "raw_manifest_sha256": hashlib.sha256(
            (RAW / "manifest.json").read_bytes()
        ).hexdigest(),
        "runtimes": reports,
    }


def verify() -> dict[str, Any]:
    with block_poker_readers():
        return verify_raw()


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
