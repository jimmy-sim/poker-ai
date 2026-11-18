"""Render only published prerequisite-audit receipts; never load a game."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/prerequisite-identity/raw"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(output: Path, raw: Path = RAW) -> None:
    """Recheck raw hashes, then export a deterministic two-runtime summary."""
    if output.exists():
        raise FileExistsError("retain earlier prerequisite report")
    manifest: dict[str, Any] = json.loads((raw / "manifest.json").read_text())
    if manifest["source_commit"] != "f009c1d5896612adc14dd2694f04a97e9d248205":
        raise ArithmeticError("unexpected archived audit source")
    for row in manifest["files"]:
        path = raw / row["file"]
        if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ArithmeticError("raw prerequisite member changed")
    subprocess.run(
        [sys.executable, str(raw / "verify.py.txt"), str(raw)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    calls: list[dict[str, Any]] = []
    runtimes: list[dict[str, Any]] = []
    for minor in ("311", "312"):
        child: dict[str, Any] = json.loads((raw / minor / "child.json").read_text())
        outer: dict[str, Any] = json.loads((raw / minor / "outer.json").read_text())
        observations = child["observations"]
        if (
            child["status"] != "seven_identical_fresh_disjoint_prerequisites"
            or outer["status"] != "passed"
            or len(observations) != 7
        ):
            raise ArithmeticError("incomplete archived prerequisite audit")
        runtimes.append(
            dict(
                python=child["python"],
                numpy=child["numpy"],
                hardware=child["hardware"],
                source_commit=child["head"],
                outer_elapsed_seconds=outer["outer_elapsed_seconds"],
                child_elapsed_seconds=child["elapsed_seconds"],
                child_parent_cpu_seconds=child["parent_cpu_seconds"],
                complete_witness=observations[0]["witness"],
                semantic_sha256=observations[0]["semantic_sha256"],
                mutable_nodes_per_fresh_graph=observations[0]["mutable_count"],
                arrays_per_fresh_graph=observations[0]["array_count"],
                pinned_inputs=len(child["input_sha256"]),
            )
        )
        calls.extend(dict(python=child["python"], **row) for row in observations)
    if (
        len({row["complete_witness"] for row in runtimes}) != 1
        or len({row["semantic_sha256"] for row in runtimes}) != 1
    ):
        raise ArithmeticError("cross-runtime prerequisite identity changed")
    summary = dict(
        status="seven_fresh_outputs_identical_and_disjoint_on_both_runtimes",
        source_commit=manifest["source_commit"],
        raw_manifest_sha256=sha(raw / "manifest.json"),
        runtime_count=2,
        calls_per_runtime=7,
        within_runtime_complete_graph_equal=True,
        cross_runtime_complete_graph_equal=True,
        fresh_mutable_storage_disjoint_verified_by_producer=True,
        reused_result_safety_in_complete_reader_proven=False,
        cost_saving_estimated=False,
        new_training_or_real_trajectory=False,
        runtimes=runtimes,
    )
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (output / "calls.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "python",
                "index",
                "witness",
                "semantic_sha256",
                "mutable_count",
                "array_count",
                "elapsed_seconds",
                "parent_cpu_seconds",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(calls)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: report_prerequisite_identity.py OUTPUT")
    report(Path(sys.argv[1]).resolve())


if __name__ == "__main__":
    main()
