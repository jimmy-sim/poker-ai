"""Check saved boundary arithmetic and source bytes without executing poker work.

CPU is OS-reported process or reaped-descendant CPU, never a wall partition.
Matching receipts do not establish a causal speedup or rerun archived math.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from card_clock_support import check_record

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/reader-boundary-reconciliation.json"
SCOPE = "SAVED_BOUNDARY_BOOKKEEPING_NOT_REPLAY_OR_CAUSAL_RUNTIME_EVIDENCE"
REAL = "OLD_OWN_OPPONENT_COST_STANDINS_NO_NEW_TRAINING"
TINY = "FICTIONAL_SIGNAL_GAMES_OWN_OPPONENT_SOFTWARE_NOT_HOLDEM"
OLD = "results/card-audit-clock-trace/pair"
NEW = "results/complete-reader-helper-trace/pair"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(root: Path, name: str) -> Path:
    path = root / name
    if (
        Path(name).is_absolute()
        or ".." in Path(name).parts
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ArithmeticError("input/source path must stay within the repository")
    if path.is_symlink() or not path.is_file():
        raise ArithmeticError("input/source must be a regular retained file")
    return path


def load_inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    expected = {
        *(
            f"{OLD}/{arm}/{name}.json"
            for arm in ("uncached", "cached")
            for name in ("child", "parent-resource-reads")
        ),
        *(f"{NEW}/{arm}/child.json" for arm in ("control", "observed")),
    }
    if (
        set(config) != {"format", "scope", "inputs"}
        or type(config["format"]) is not int
        or config["format"] != 1
        or config["scope"] != SCOPE
        or set(config["inputs"]) != expected
    ):
        raise ArithmeticError("exact six-input saved-data contract required")
    result = {}
    for name, sha in config["inputs"].items():
        path = local_path(root, name)
        if digest(path) != sha:
            raise ArithmeticError(f"retained input changed: {name}")
        result[name] = json.loads(path.read_text())
    return config, result


def boundary(row: dict[str, Any], pid: int, label: str) -> dict[str, Any]:
    check_record(row)
    if type(pid) is not int or row["before"]["pid"] != pid:
        raise ArithmeticError("boundary must belong to its recorded parent process")
    clocks = row["interval"]["clocks"]
    child = row["interval"]["resources"]["reaped_child_usage"]["delta"]
    return dict(
        label=label,
        pid=pid,
        wall_seconds=clocks["perf_seconds"],
        own_process_cpu_seconds=clocks["process_cpu_seconds"],
        reaped_child_user_seconds=child["ru_utime"],
        reaped_child_system_seconds=child["ru_stime"],
    )


def reconcile(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    """Compare recorded identities, not fresh mathematical or runtime results."""
    rows = []
    old_sources = []
    new_sources = []
    summaries = []
    own_hashes = []
    for arm in ("uncached", "cached"):
        child = inputs[f"{OLD}/{arm}/child.json"]
        reads = inputs[f"{OLD}/{arm}/parent-resource-reads.json"]["reads"]
        if (
            child["status"] != "complete_card_clock_trace"
            or child["mode"] != arm
            or len(reads) != 3
        ):
            raise ArithmeticError(
                "complete historical arm with exactly three reads required"
            )
        pid = child["child_before"]["pid"]
        if child["body_before"]["pid"] != pid:
            raise ArithmeticError("historical parent process changed")
        old_sources.append(child["source"]["sha256"])
        own_hashes.append(child["identity"]["own_sha256"])
        computed = child["identity"]["computed_replays"]
        if len(computed) != 3:
            raise ArithmeticError("all three historical computed receipts required")
        for i, (read, phase, scope) in enumerate(
            zip(reads, ("tiny", "initial", "final"), (TINY, REAL, REAL), strict=True)
        ):
            if (
                read["status"] != "complete"
                or read["scope"] != scope
                or computed[i]["scope"] != scope
                or read["before"] != read["observation"]["before"]
            ):
                raise ArithmeticError("historical read scope/order/boundary changed")
            rows.append(boundary(read["observation"], pid, f"{arm}/{phase}"))
            if i:
                summaries.append(computed[i]["computed"])
    for arm in ("control", "observed"):
        child = inputs[f"{NEW}/{arm}/child.json"]
        if (
            child["status"] != "complete"
            or child["mode"] != arm
            or child["target_before"] != child["target_observation"]["before"]
            or child["witness"]["reader_scope"] != REAL
        ):
            raise ArithmeticError(
                "complete standalone read and matching boundary required"
            )
        rows.append(
            boundary(child["target_observation"], child["pid"], f"standalone/{arm}")
        )
        new_sources.append(child["source"]["sha256"])
        summaries.append(child["witness"]["computed_replay"])
        own_hashes.append(child["witness"]["own_sha256"])
    old, new = old_sources[0], new_sources[0]
    if (
        old_sources[1] != old
        or new_sources[1] != new
        or len(old) != 390
        or len(new) != 398
        or any(new.get(name) != sha for name, sha in old.items())
    ):
        raise ArithmeticError("historical source maps must agree and remain unchanged")
    for name, sha in new.items():
        if digest(local_path(root, name)) != sha:
            raise ArithmeticError(f"historical source bytes changed: {name}")
    if len(set(own_hashes)) != 1 or any(s != summaries[0] for s in summaries[1:]):
        raise ArithmeticError(
            "recorded real archive identities or computed summaries differ"
        )
    return dict(
        scope=SCOPE,
        boundary_count=len(rows),
        recorded_real_summaries_compared=len(summaries),
        recorded_real_summaries_equal=True,
        recorded_own_sha256=own_hashes[0],
        historical_source_files=390,
        current_source_files_checked=398,
        rows=rows,
        cause_identified=False,
        poker_training_performed=False,
        mathematical_archive_replay_performed=False,
        long_run_admitted=False,
    )


def report(root: Path) -> dict[str, Any]:
    config, inputs = load_inputs(root)
    return dict(
        **reconcile(root, inputs),
        input_sha256=config["inputs"],
        config_sha256=digest(root / CONFIG),
        implementation_sha256=digest(root / "scripts/reconcile_reader_boundaries.py"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="fresh JSON output; never overwrite evidence"
    )
    args = parser.parse_args()
    saved = report(ROOT)
    text = json.dumps(saved, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            stream.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()
