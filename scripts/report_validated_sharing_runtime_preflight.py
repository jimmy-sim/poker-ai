"""Render the published optional-runtime pair failure from data only."""

import hashlib
import json
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/validated-sharing-runtime-preflight"
OLD_OWN = ROOT / "results/validated-prerequisite-sharing/own/manifest.json"
REPAIR = ROOT / "results/validated-sharing-runtime-preflight/source-check-repair.json"
SOURCE = "0b9ae32b13959371952f8f853d5419d8708de8d1"
PAIR = "c5697efc0fb5d9564ed684e57a5a2bbb1904db5d"
REPAIR_HEAD = "97baaf2fa9c472d66abb77d4ee7cb23ff39c9f98"
MISSING = (
    "results/validated-sharing-runtime-preflight/source-checks/"
    "local/__pycache__/verify-local.py.cpython-313.pyc"
)
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
    """Authenticate every archived byte before interpreting any result."""
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
    """State the failed gate and limits without running any poker reader."""
    source_dir = EVIDENCE / "source-checks"
    failed_dir = EVIDENCE / "failed-pair"
    source_raw = (source_dir / "manifest.json").read_bytes()
    failed_raw = (failed_dir / "manifest.json").read_bytes()
    old_own_raw = OLD_OWN.read_bytes()
    repair_raw = REPAIR.read_bytes()
    source: dict[str, Any] = json.loads(source_raw)
    failed: dict[str, Any] = json.loads(failed_raw)
    old_own: dict[str, Any] = json.loads(old_own_raw)
    repair: dict[str, Any] = json.loads(repair_raw)
    if (
        source["status"] != "six_roles_qualified_before_optional_pair"
        or source["checked_commit"] != SOURCE
        or failed["status"] != "failed_first_ordinary_child_retained"
        or failed["checked_source_commit"] != SOURCE
        or failed["pair_head"] != PAIR
        or failed["old_own_raw_published_before_pair"] is not True
        or failed["source_checks_published_before_pair"] is not True
        or failed["validated_share_child_started"] is not False
        or failed["favorable_retry_performed"] is not False
        or failed["complete_identity_established"] is not False
        or old_own["status"] != "published_own_proof"
        or old_own["checked_source_commit"]
        != "04d19ed4c419d14cbe3fc41ccca1b1df8f3dd62b"
        or repair["status"]
        != "late_missing_source_check_member_published_without_retroactive_admission"
        or repair["member"] != MISSING
        or repair["source_check_manifest_sha256"]
        != hashlib.sha256(source_raw).hexdigest()
        or repair["absent_at_pair_head"] != PAIR
        or repair["absent_at_failed_report_head"]
        != "2066f2c4e16d7fcf185c936f98b42f7f3ac980b5"
        or repair["pair_admissible"] is not False
        or repair["pair_retried"] is not False
    ):
        raise ArithmeticError("published gate sequence or outcome changed")
    missing_raw = (ROOT / MISSING).read_bytes()
    if (
        len(missing_raw) != repair["bytes"]
        or hashlib.sha256(missing_raw).hexdigest() != repair["sha256"]
        or subprocess.run(
            ["git", "cat-file", "-e", PAIR + ":" + MISSING],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).returncode
        == 0
        or subprocess.run(
            ["git", "cat-file", "-e", REPAIR_HEAD + ":" + MISSING],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).returncode
        != 0
    ):
        raise ArithmeticError("late source-check member history changed")
    source_files = members(source_dir, source)
    failed_files = members(failed_dir, failed)
    if len(source_files) != 34 or len(failed_files) != 19:
        raise ArithmeticError("published evidence membership changed")
    preflight = json.loads(failed_files["preflight.json"])
    pair = json.loads(failed_files["raw/pair.json"])
    child = json.loads(failed_files["raw/ordinary/child.json"])
    measurement = json.loads(failed_files["raw/ordinary/measurement.json"])
    native = json.loads(failed_files["raw/ordinary/native.json"])
    observed = json.loads(failed_files["raw/ordinary/observer.json"])
    archives = [
        json.loads(failed_files[f"raw/ordinary/archive-{i}.json"]) for i in range(2)
    ]
    reads = [json.loads(failed_files[f"raw/ordinary/read-{i}.json"]) for i in range(3)]
    if (
        preflight["status"] != "optional_runtime_preflight_passed_before_pair"
        or preflight["head"] != PAIR
        or preflight["checked_launcher_commit"] != SOURCE
        or preflight["carried_own_manifest_sha256"]
        != hashlib.sha256(old_own_raw).hexdigest()
        or (preflight["installed"]["python"], preflight["installed"]["numpy"])
        != ("3.11.17", "2.4.6")
        or (preflight["installed"]["numba"], preflight["installed"]["open_spiel"])
        != ("0.68.1", "2.0.2")
        or preflight["installed"]["license_sha256"]
        != "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
        or pair["status"] != "failed_retained"
        or pair["failure_kind"] != "ArithmeticError"
        or pair["order"] != ["ordinary", "validated_share"]
        or pair["measurements"] != [measurement]
        or not 0 < pair["seconds"] < 1800
        or child["status"] != "failed_retained"
        or child["mode"] != "ordinary"
        or child["head"] != PAIR
        or child["dirty"] is not False
        or child["failure"]
        != {
            "type": "ArithmeticError",
            "reason": "complete reader scope, source or input changed",
        }
        or not 0 < child["seconds"] < 900
        or measurement["returncode"] != 1
        or measurement["cap_seconds"] != 900
        or native["status"] != "completed_scalar_comparison"
        or native["failure"] is not None
        or len(native["profiles"]) != 432
        or len(native["fixed_conditions"]) != 1152
        or type(native["profiles"]) is not list
        or type(native["fixed_conditions"]) is not list
        or len(native["native_batch"]["workers"]) != 3
        or [row["status"] for row in reads] != ["complete"] * 3
        or len(observed["reads"]) != 3
        or len(observed["replays"]) != 3
        or [len(row["rows"]) for row in archives] != [7, 7]
        or failed_files["raw/pair-command.exit"].strip() != b"1"
        or (failed_dir / "raw/validated_share").exists()
    ):
        raise ArithmeticError("published failed pair changed")
    return {
        "status": "failed_pair_with_incomplete_publication_gate",
        "source_manifest_sha256": hashlib.sha256(source_raw).hexdigest(),
        "old_own_manifest_sha256": hashlib.sha256(old_own_raw).hexdigest(),
        "failed_pair_manifest_sha256": hashlib.sha256(failed_raw).hexdigest(),
        "source_check_repair_sha256": hashlib.sha256(repair_raw).hexdigest(),
        "publication": {
            "source_archive_complete_at_pair_time": False,
            "missing_member": MISSING,
            "missing_member_published_later_at": REPAIR_HEAD,
            "pair_admissible": False,
        },
        "complete_pair": {
            "order": pair["order"],
            "first_child": child["mode"],
            "first_child_seconds": measurement["seconds"],
            "pair_seconds": pair["seconds"],
            "first_child_returncode": measurement["returncode"],
            "first_child_failure": child["failure"],
            "completed_archive_roots": len(archives),
            "original_loader_calls": sum(len(row["rows"]) for row in archives),
            "complete_reads": len(reads),
            "reference_workers": len(native["native_batch"]["workers"]),
            "profile_count": len(native["profiles"]),
            "fixed_condition_count": len(native["fixed_conditions"]),
            "profile_value_type": type(native["profiles"]).__name__,
            "condition_value_type": type(native["fixed_conditions"]).__name__,
            "validated_share_child_started": False,
            "complete_identity_established": False,
            "cpu_savings_established": False,
            "favorable_retry_performed": False,
        },
    }


def verify() -> dict[str, Any]:
    with block_readers():
        return render()


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
