"""Report the one failed guarded-skip pair from published data only."""

import hashlib
import json
import subprocess
import sys
import tarfile
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/guarded-prerequisite-skip"
SOURCE = "7fb8f8ae4d2f823c064a55ace78afded64db0d8d"
SOURCE_PUBLIC = "316bfb3601d6eeeac627f3ce1fcf9d0d618bbd1c"
PAIR = "e323279ee48d9d9d5d7c87913d29561d48497fda"
RAW_PUBLIC = "aa3c9c2936e245719ce3edd46927b0e2964ea0df"
PREDECESSOR_IDENTITY = (
    "ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185"
)
GUARDED_IDENTITY = "c8027ef54f60c40b244e8b278e7b8fb186f15f8d4c46894c139cbd28cc3b74b8"
LICENSE = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
BLOCKED = ("poker_ai", "numpy", "numba", "pyspiel", "treys")
WORK_DIFFERENCE = {
    "normalization.reduced_evaluations": (918104, 726200),
    "normalization.requests": (918104, 726200),
    "validation_cache.hits": (8290, 8194),
    "validation_cache.requests": (8316, 8220),
}


class BlockReaders(MetaPathFinder):
    def find_spec(
        self, fullname: str, path: Any, target: Any = None
    ) -> ModuleSpec | None:
        if any(fullname == name or fullname.startswith(name + ".") for name in BLOCKED):
            raise ImportError("poker, numerical and reference imports blocked")
        return None


@contextmanager
def block_readers() -> Iterator[None]:
    if any(
        name == root or name.startswith(root + ".")
        for name in sys.modules
        for root in BLOCKED
    ):
        raise ArithmeticError("poker, numerical or reference module already imported")
    blocker = BlockReaders()
    sys.meta_path.insert(0, blocker)
    try:
        yield
    finally:
        sys.meta_path.remove(blocker)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def committed_at(commit: str, name: str, raw: bytes) -> None:
    original = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
    if original != raw:
        raise ArithmeticError("publication history changed: " + name)


def ancestor(earlier: str, later: str) -> None:
    if (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", earlier, later],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).returncode
        != 0
    ):
        raise ArithmeticError("publication order changed")


def checked_files(folder: Path, listed: list[dict[str, Any]]) -> dict[str, bytes]:
    output: dict[str, bytes] = {}
    for row in listed:
        name = row["file"]
        if (
            not isinstance(name, str)
            or not name
            or name in output
            or Path(name).is_absolute()
            or ".." in Path(name).parts
        ):
            raise ArithmeticError("invalid source-check member")
        raw = (folder / name).read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ArithmeticError("source-check member changed: " + name)
        output[name] = raw
    if len(output) != 35:
        raise ArithmeticError("source-check membership changed")
    return output


def own_files(folder: Path, listed: dict[str, Any]) -> dict[str, bytes]:
    if set(listed) != {"child.json", "child.log", "outer.json"}:
        raise ArithmeticError("own membership changed")
    output: dict[str, bytes] = {}
    for name, row in listed.items():
        raw = (folder / name).read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ArithmeticError("own member changed: " + name)
        output[name] = raw
    return output


def raw_files(folder: Path, manifest: dict[str, Any]) -> dict[str, bytes]:
    compressed = (folder / "raw.tar.gz").read_bytes()
    verifier = (folder / "verify.py.txt").read_bytes()
    if (len(compressed), digest(compressed)) != (
        manifest["archive"]["bytes"],
        manifest["archive"]["sha256"],
    ) or (len(verifier), digest(verifier)) != (
        manifest["verifier"]["bytes"],
        manifest["verifier"]["sha256"],
    ):
        raise ArithmeticError("raw archive or verifier changed")
    listed = manifest["files"]
    if len(listed) != 31:
        raise ArithmeticError("raw membership changed")
    output: dict[str, bytes] = {}
    with tarfile.open(folder / "raw.tar.gz", "r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(listed) or {m.name for m in members} != set(listed):
            raise ArithmeticError("raw tar membership changed")
        for member in members:
            if (
                not member.isfile()
                or member.name in output
                or Path(member.name).is_absolute()
                or ".." in Path(member.name).parts
            ):
                raise ArithmeticError("invalid raw tar member")
            stream = archive.extractfile(member)
            if stream is None:
                raise ArithmeticError("raw member unreadable")
            raw = stream.read()
            expected = listed[member.name]
            if (
                len(raw) != member.size
                or len(raw) != expected["bytes"]
                or digest(raw) != expected["sha256"]
            ):
                raise ArithmeticError("raw member changed: " + member.name)
            output[member.name] = raw
    return output


def differences(left: Any, right: Any, path: str = "") -> dict[str, tuple[Any, Any]]:
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            raise ArithmeticError("identity keys changed at " + path)
        result: dict[str, tuple[Any, Any]] = {}
        for key in sorted(left):
            result.update(
                differences(left[key], right[key], path + "." + key if path else key)
            )
        return result
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise ArithmeticError("identity list length changed at " + path)
        result = {}
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            result.update(differences(a, b, f"{path}[{index}]"))
        return result
    return {} if left == right else {path: (left, right)}


def render(evidence: Path = EVIDENCE, *, publication: bool = True) -> dict[str, Any]:
    source_dir, own_dir, raw_dir = (
        evidence / name for name in ("source-checks", "own", "pair-raw")
    )
    source_raw, own_raw, pair_raw = (
        (folder / "manifest.json").read_bytes()
        for folder in (source_dir, own_dir, raw_dir)
    )
    source, own, pair_manifest = (
        json.loads(raw) for raw in (source_raw, own_raw, pair_raw)
    )
    if (
        source["status"] != "six_roles_qualified_before_guarded_skip_proof"
        or source["checked_commit"] != SOURCE
        or own["status"] != "published_own_proof"
        or own["checked_source_commit"] != SOURCE
        or own["proof_head"] != SOURCE_PUBLIC
        or pair_manifest["status"] != "failed_pair_raw_retained_before_report"
        or pair_manifest["pair_head"] != PAIR
        or pair_manifest["checked_source_commit"] != SOURCE
        or pair_manifest["complete_pair_status"] != "failed_retained"
        or pair_manifest["source_checks_sha256"] != digest(source_raw)
        or pair_manifest["own_proof_sha256"] != digest(own_raw)
    ):
        raise ArithmeticError("published guarded-skip sequence changed")
    source_members = checked_files(source_dir, source["files"])
    own_members = own_files(own_dir, own["files"])
    raw_members = raw_files(raw_dir, pair_manifest)
    if publication:
        ancestor(SOURCE, SOURCE_PUBLIC)
        ancestor(SOURCE_PUBLIC, PAIR)
        ancestor(PAIR, RAW_PUBLIC)
        committed_at(
            SOURCE_PUBLIC,
            str(source_dir.relative_to(ROOT) / "manifest.json"),
            source_raw,
        )
        committed_at(PAIR, str(own_dir.relative_to(ROOT) / "manifest.json"), own_raw)
        for name, raw in source_members.items():
            committed_at(PAIR, str(source_dir.relative_to(ROOT) / name), raw)
        for name, raw in own_members.items():
            committed_at(PAIR, str(own_dir.relative_to(ROOT) / name), raw)
        for name in ("manifest.json", "raw.tar.gz", "verify.py.txt"):
            committed_at(
                RAW_PUBLIC,
                str(raw_dir.relative_to(ROOT) / name),
                (raw_dir / name).read_bytes(),
            )
    preflight = json.loads(raw_members["preflight.json"])
    pair = json.loads(raw_members["raw/pair.json"])
    if (
        preflight["status"] != "optional_runtime_preflight_passed_before_pair"
        or preflight["head"] != PAIR
        or preflight["checked_launcher_commit"] != SOURCE
        or preflight["checked_launcher_manifest_sha256"] != digest(source_raw)
        or preflight["carried_own_manifest_sha256"] != digest(own_raw)
        or preflight["no_reference_constructed_in_preflight"] is not True
        or (
            preflight["installed"]["python"],
            preflight["installed"]["numpy"],
            preflight["installed"]["numba"],
            preflight["installed"]["open_spiel"],
            preflight["installed"]["license_sha256"],
        )
        != ("3.11.17", "2.4.6", "0.68.1", "2.0.2", LICENSE)
        or pair["status"] != "failed_retained"
        or pair["failure_kind"] != "ArithmeticError"
        or pair["order"] != ["ordinary", "guarded_skip"]
        or len(pair["measurements"]) != 2
        or not 0 < pair["seconds"] < 1800
        or b"complete ordinary/guarded-skip identity failed"
        not in raw_members["pair-command.log"]
    ):
        raise ArithmeticError("preflight or failed pair changed")
    children: list[dict[str, Any]] = []
    for index, mode in enumerate(("ordinary", "guarded_skip")):
        child = json.loads(raw_members[f"raw/{mode}/child.json"])
        measurement = json.loads(raw_members[f"raw/{mode}/measurement.json"])
        native = json.loads(raw_members[f"raw/{mode}/native.json"])
        observer = json.loads(raw_members[f"raw/{mode}/observer.json"])
        archives = [
            json.loads(raw_members[f"raw/{mode}/archive-{i}.json"]) for i in range(2)
        ]
        reads = [json.loads(raw_members[f"raw/{mode}/read-{i}.json"]) for i in range(3)]
        identity = child["result"]["identity"]
        if (
            child["status"] != "complete_guarded_skip_pair_child"
            or child["mode"] != mode
            or child["head"] != PAIR
            or child["dirty"] is not False
            or (child["python"], child["environment"]["numpy"]) != ("3.11.17", "2.4.6")
            or child["reference_output_used_in_training"] is not False
            or child["new_postflop_training_performed"] is not False
            or child["archive_roots"] != 2
            or child["original_loads"] != (14 if index == 0 else 2)
            or child["guarded_returns"] != (0 if index == 0 else 12)
            or not 0 < child["seconds"] < 900
            or type(identity["profiles"]) is not list
            or len(identity["profiles"]) != 432
            or type(identity["fixed_conditions"]) is not list
            or len(identity["fixed_conditions"]) != 1152
            or len(identity["worker_summaries"]) != 3
            or identity["reference_actions_exported"] is not False
            or identity["training_performed"] is not False
            or measurement != pair["measurements"][index]
            or measurement["returncode"] != 0
            or measurement["cap_seconds"] != 900
            or native["status"] != "completed_scalar_comparison"
            or native["failure"] is not None
            or len(native["native_batch"]["workers"]) != 3
            or [r["status"] for r in reads] != ["complete"] * 3
            or len(observer["reads"]) != 3
            or len(observer["replays"]) != 3
            or [len(a["rows"]) for a in archives] != [7, 7]
        ):
            raise ArithmeticError("complete child scope changed")
        for archive in archives:
            rows = archive["rows"]
            if (
                [row["kind"] for row in rows] != ["nested"] * 6 + ["direct"]
                or any(row["after_archive"] != row["load"] for row in rows)
                or any(row["after_caller"] != row["load"] for row in rows[:6])
                or [row.get("guarded_return") for row in rows]
                != ([None] * 7 if index == 0 else [False] + [True] * 6)
            ):
                raise ArithmeticError("loader observations changed")
        children.append(child)
    left, right = [child["result"]["identity"] for child in children]
    changed = differences(left, right)
    if (
        children[0]["pid"] == children[1]["pid"]
        or children[0]["input_sha256"] != children[1]["input_sha256"]
        or children[0]["context_identity_sha256"]
        != children[1]["context_identity_sha256"]
        or digest(canonical(left)) != PREDECESSOR_IDENTITY
        or digest(canonical(right)) != GUARDED_IDENTITY
        or changed != WORK_DIFFERENCE
        or pair_manifest["work_identity_difference"]
        != {key: list(value) for key, value in changed.items()}
    ):
        raise ArithmeticError("failed scientific/work identity record changed")
    return {
        "status": "failed_exact_work_identity",
        "source_manifest_sha256": digest(source_raw),
        "own_manifest_sha256": digest(own_raw),
        "raw_pair_manifest_sha256": digest(pair_raw),
        "publication": {
            "source_archive_complete_at_pair_time": True,
            "fresh_own_proof_published_before_reference": True,
            "raw_pair_published_before_report": publication,
            "pair_admissible": False,
        },
        "complete_pair": {
            "order": pair["order"],
            "ordinary_child_seconds": children[0]["seconds"],
            "guarded_child_seconds": children[1]["seconds"],
            "pair_seconds": pair["seconds"],
            "child_cap_seconds": 900,
            "pair_cap_seconds": 1800,
            "archive_roots_each": 2,
            "ordinary_original_loads": 14,
            "guarded_original_loads": 2,
            "guarded_returns": 12,
            "complete_reads_each": 3,
            "reference_workers_each": 3,
            "profile_count": 432,
            "fixed_condition_count": 1152,
            "predecessor_identity_sha256": PREDECESSOR_IDENTITY,
            "guarded_identity_sha256": GUARDED_IDENTITY,
            "context_identity_sha256": children[0]["context_identity_sha256"],
            "scientific_fields_identical_except_work": True,
            "exact_result_and_work_identity": False,
            "work_counter_difference": {
                key: list(value) for key, value in changed.items()
            },
            "reference_output_used_in_training": False,
        },
        "limits": {
            "one_ordered_pair_only": True,
            "no_favorable_retry": True,
            "cpu_savings_established": False,
            "new_strategy_or_training_admitted": False,
        },
    }


def verify(evidence: Path = EVIDENCE, *, publication: bool = True) -> dict[str, Any]:
    with block_readers():
        return render(evidence, publication=publication)


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
