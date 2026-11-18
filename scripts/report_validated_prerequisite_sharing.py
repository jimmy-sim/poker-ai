"""Render the published failed pair from data only; import no poker code."""

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
EVIDENCE = ROOT / "results/validated-prerequisite-sharing"
SOURCE = "04d19ed4c419d14cbe3fc41ccca1b1df8f3dd62b"
OWN_HEAD = "c9eb71349e973679c00e24be2c8fb6515d94f68d"
PAIR_HEAD = "b47cf8cc6f3228ffa7944539804090daf8a034d5"
BLOCKED = ("poker_ai", "numpy", "numba", "pyspiel", "treys")


class BlockReaders(MetaPathFinder):
    def find_spec(
        self, fullname: str, path: Any, target: Any = None
    ) -> ModuleSpec | None:
        if any(fullname == name or fullname.startswith(name + ".") for name in BLOCKED):
            raise ImportError("reader, numerical and reference imports blocked")
        return None


@contextmanager
def block_readers() -> Iterator[None]:
    if any(
        name == root or name.startswith(root + ".")
        for name in sys.modules
        for root in BLOCKED
    ):
        raise ArithmeticError("reader, numerical or reference module already imported")
    blocker = BlockReaders()
    sys.meta_path.insert(0, blocker)
    try:
        yield
    finally:
        sys.meta_path.remove(blocker)


def members(folder: Path, manifest: dict[str, Any]) -> dict[str, bytes]:
    output: dict[str, bytes] = {}
    listed = manifest["files"]
    entries = (
        ((row["file"], row) for row in listed)
        if isinstance(listed, list)
        else listed.items()
    )
    for name, metadata in entries:
        raw = (folder / name).read_bytes()
        if (
            len(raw) != metadata["bytes"]
            or hashlib.sha256(raw).hexdigest() != metadata["sha256"]
        ):
            raise ArithmeticError("published raw member changed: " + name)
        output[name] = raw
    return output


def render() -> dict[str, Any]:
    source_dir = EVIDENCE / "source-checks"
    own_dir = EVIDENCE / "own"
    failed_dir = EVIDENCE / "failed-pair"
    source_raw = (source_dir / "manifest.json").read_bytes()
    own_raw = (own_dir / "manifest.json").read_bytes()
    failed_raw = (failed_dir / "manifest.json").read_bytes()
    source = json.loads(source_raw)
    own = json.loads(own_raw)
    failed = json.loads(failed_raw)
    if (
        source["status"] != "six_roles_qualified_before_own_proof"
        or source["checked_commit"] != SOURCE
        or own["status"] != "published_own_proof"
        or own["checked_source_commit"] != SOURCE
        or own["proof_head"] != OWN_HEAD
        or failed["status"] != "failed_first_ordinary_child_retained"
        or failed["checked_source_commit"] != SOURCE
        or failed["pair_head"] != PAIR_HEAD
        or failed["own_raw_published_before_pair"] is not True
        or failed["validated_share_child_started"] is not False
        or failed["favorable_retry_performed"] is not False
        or failed["complete_identity_established"] is not False
    ):
        raise ArithmeticError("published gate sequence or outcome changed")
    source_files = members(source_dir, source)
    own_files = members(own_dir, own)
    failed_files = members(failed_dir, failed)
    if (
        len(source_files) != 29
        or set(own_files) != {"child.json", "child.log", "outer.json"}
        or len(failed_files) != 16
        or (failed_dir / "raw/validated_share").exists()
    ):
        raise ArithmeticError("published evidence membership changed")
    own_child = json.loads(own_files["child.json"])
    own_outer = json.loads(own_files["outer.json"])
    rows = own_child["observations"]
    if (
        own_files["child.log"]
        or own_child["status"]
        != "seven_original_loaders_six_validated_substitutions_complete"
        or own_child["head"] != OWN_HEAD
        or own_child["dirty"] is not False
        or (own_child["python"], own_child["numpy"]) != ("3.11.17", "2.4.6")
        or own_child["reference_constructed"] is not False
        or own_child["new_postflop_training_performed"] is not False
        or own_child["saved_own_replay"]["maximum_error_chips"] != 0
        or own_child["saved_own_replay"]["maximum_error_unitless"] != 0
        or (own_child["saved_batch_count"], own_child["saved_row_count"]) != (2, 480)
        or len(rows) != 7
        or [row["kind"] for row in rows] != ["nested"] * 6 + ["direct"]
        or [row["substituted"] for row in rows] != [False] + [True] * 6
        or any(
            row["fresh"] != row["load"] or row["after_archive"] != row["load"]
            for row in rows
        )
        or any(row["after_caller"] != row["load"] for row in rows[:6])
        or own_outer["status"] != "passed"
        or own_outer["returncode"] != 0
        or not 0
        < own_child["elapsed_seconds"]
        < own_outer["outer_elapsed_seconds"]
        < 180
    ):
        raise ArithmeticError("published own proof changed")
    pair = json.loads(failed_files["raw/pair.json"])
    child = json.loads(failed_files["raw/ordinary/child.json"])
    measurement = json.loads(failed_files["raw/ordinary/measurement.json"])
    read = json.loads(failed_files["raw/ordinary/read-1.json"])
    archive = json.loads(failed_files["raw/ordinary/archive-0.json"])
    environment = json.loads(failed_files["environment-check.json"])
    if (
        pair["status"] != "failed_retained"
        or pair["failure_kind"] != "ArithmeticError"
        or pair["order"] != ["ordinary", "validated_share"]
        or pair["measurements"] != [measurement]
        or child["status"] != "failed_retained"
        or child["mode"] != "ordinary"
        or child["head"] != PAIR_HEAD
        or child["dirty"] is not False
        or child["failure"]
        != {
            "type": "PackageNotFoundError",
            "reason": "No package metadata was found for numba",
        }
        or measurement["returncode"] != 1
        or measurement["cap_seconds"] != 900
        or read["status"] != "failed"
        or read["failure_kind"] != "PackageNotFoundError"
        or len(archive["rows"]) != 7
        or [row["kind"] for row in archive["rows"]] != ["nested"] * 6 + ["direct"]
        or failed_files["raw/pair-command.exit"].strip() != b"1"
        or environment["status"] != "post_failure_read_only_environment_check"
        or environment["base311_numba"] != "missing"
        or environment["optional311_numba"] != "0.68.1"
    ):
        raise ArithmeticError("published failed pair changed")
    return {
        "status": "failed_before_validated_share_child",
        "source_manifest_sha256": hashlib.sha256(source_raw).hexdigest(),
        "own_manifest_sha256": hashlib.sha256(own_raw).hexdigest(),
        "failed_pair_manifest_sha256": hashlib.sha256(failed_raw).hexdigest(),
        "own_proof": {
            "runtime": [own_child["python"], own_child["numpy"]],
            "outer_seconds": own_outer["outer_elapsed_seconds"],
            "original_loads": len(rows),
            "donor_substitutions": sum(row["substituted"] for row in rows),
            "saved_rows": own_child["saved_row_count"],
            "maximum_error_chips": own_child["saved_own_replay"]["maximum_error_chips"],
            "maximum_error_unitless": own_child["saved_own_replay"][
                "maximum_error_unitless"
            ],
        },
        "complete_pair": {
            "order": pair["order"],
            "first_child": child["mode"],
            "first_child_seconds": measurement["seconds"],
            "pair_seconds": pair["seconds"],
            "first_child_returncode": measurement["returncode"],
            "first_child_failure": child["failure"],
            "completed_archive_roots": 1,
            "validated_share_child_started": False,
            "complete_identity_established": False,
            "cpu_savings_established": False,
            "favorable_retry_performed": False,
        },
        "post_failure_environment_check": {
            "base311_numba": environment["base311_numba"],
            "optional311_numba": environment["optional311_numba"],
        },
    }


def verify() -> dict[str, Any]:
    with block_readers():
        return render()


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
