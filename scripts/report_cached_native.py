"""Render the complete native audit profile; saved diagnostics, never training."""

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/report_cached_native.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed_parts(
    whole: float, reads: list[dict[str, Any]], batch: float
) -> dict[str, float]:
    """Disjoint elapsed intervals; never mix child CPU into an elapsed stack."""
    if len(reads) != 3:
        raise ArithmeticError("three complete mathematical reads required")
    values = [whole, batch, *[r["whole_read_wall_seconds"] for r in reads]]
    if any(
        type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in values
    ):
        raise ArithmeticError("positive finite complete clocks required")
    other = whole - batch - sum(r["whole_read_wall_seconds"] for r in reads)
    if other < -1e-9:
        raise ArithmeticError("overlapping or incomplete wall-time accounting")
    return dict(
        tiny_proof_read=reads[0]["whole_read_wall_seconds"],
        initial_own_read=reads[1]["whole_read_wall_seconds"],
        reference_worker_batch=batch,
        final_own_read=reads[2]["whole_read_wall_seconds"],
        other_elapsed=max(0.0, other),
    )


def metric_identity(child: dict[str, Any]) -> None:
    """Never relabel a CPU-timer or other source's frames as elapsed values."""
    from profile_cached_native_wall import CONFIG_SHA

    source = child.get("source")
    if (
        child.get("scope")
        != "DIAGNOSTIC_COMPLETE_NATIVE_ELAPSED_STACK_PROFILE_NOT_ADMISSION"
        or child.get("config_sha256") != CONFIG_SHA
        or not isinstance(source, dict)
        or source.get("fingerprint")
        != "7fdfe7db600b65c945fb93384e1eb30643474e547492202bf8436f880d2afa5c"
    ):
        raise ArithmeticError("elapsed-stack instrument source and units required")


def gather(folder: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from profile_cached_native_wall import show

    from poker_ai.evaluation.batch_cost_stats import validate

    pair = json.loads((folder / "pair.json").read_text())
    for mode in ("plain", "profile"):
        metric_identity(json.loads((folder / mode / "child.json").read_text()))
    show(folder)  # Authenticates complete pair/source/raw hashes/exact identity.
    rows = []
    for mode, measurement in zip(pair["order"], pair["measurements"], strict=True):
        child = json.loads((folder / mode / "child.json").read_text())
        native = json.loads((folder / mode / "native.json").read_text())
        reads = json.loads((folder / mode / "read-phases.json").read_text())["phases"]
        batch = native["native_batch"]
        workers = []
        for worker in batch["workers"]:
            done = next(m for m in worker["messages"] if m.get("kind") == "done")
            workers.append(
                dict(
                    slot=worker["slot"],
                    body_wall_seconds=done["seconds"],
                    body_cpu_seconds=done["cpu_seconds"],
                    scope="worker body only; excludes worker startup/imports",
                )
            )
        rows.append(
            dict(
                mode=mode,
                whole_wall_seconds=measurement["seconds"],
                parent_body_cpu_seconds=child["parent_body_cpu_seconds"],
                elapsed_parts=elapsed_parts(
                    measurement["seconds"], reads, batch["seconds"]
                ),
                complete_reads=reads,
                workers=workers,
                raw_worker_batch_clock={
                    k: v
                    for k, v in batch.items()
                    if k not in ("workers", "assignments")
                },
                scope="one ordered diagnostic copy; no new learning or admission",
            )
        )
    with gzip.open(folder / "profile/functions-callers.json.gz", "rt") as stream:
        stats = json.load(stream)
    validate(stats)
    return rows, stats


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ArithmeticError("nonempty complete export required")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render(folder: Path, output: Path) -> dict[str, Any]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.reproducibility import runtime_environment
    from poker_ai.validation.five_card import source_provenance

    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous diagnostic report")
    rows, stats = gather(folder)
    output.mkdir(parents=True)
    child = json.loads((folder / "plain/child.json").read_text())
    source: dict[str, Any] = dict(
        source_provenance(
            ROOT,
            ROOT / "configs/compact-native-wall-profile.json",
            entrypoints=(ENTRY,),
        )
    )
    source["sha256"].update(child["source"]["sha256"])
    source["fingerprint"] = sha(source["sha256"])
    commit_sources(ROOT, source["git_commit"], source["sha256"])
    summary = dict(
        scope="DIAGNOSTIC_COMPLETE_NATIVE_ELAPSED_STACK_REPORT_NOT_ADMISSION",
        training_performed=False,
        admission_evidence=False,
        modes=rows,
        raw_frames=stats["frame_count"],
        raw_edges=stats["edge_count"],
        total_profiled_parent_elapsed_self_seconds=stats["total_self_seconds"],
        timer=(
            "cProfile built-in elapsed timer; per-frame times include waits; "
            "boundary CPU is separate"
        ),
        source=source,
        environment=runtime_environment(),
    )
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(
        output / "elapsed-parts.csv",
        [
            dict(mode=r["mode"], part=k, wall_seconds=v)
            for r in rows
            for k, v in r["elapsed_parts"].items()
        ],
    )
    write_csv(
        output / "workers.csv",
        [dict(mode=r["mode"], **worker) for r in rows for worker in r["workers"]],
    )
    write_csv(output / "all-parent-functions.csv", stats["functions"])
    write_csv(output / "all-parent-callers.csv", stats["callers"])
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(16, 6), layout="constrained")
    labels = {
        "tiny_proof_read": "Tiny proof read",
        "initial_own_read": "Initial own read",
        "reference_worker_batch": "Reference workers",
        "final_own_read": "Final own read",
        "other_elapsed": "Other elapsed work",
    }
    left = [0.0, 0.0]
    for part, label in labels.items():
        heights = [r["elapsed_parts"][part] for r in rows]
        axes[0].barh(["Ordinary", "Profiled"], heights, left=left, label=label)
        left = [a + b for a, b in zip(left, heights, strict=True)]
    axes[0].set_xlabel("Complete elapsed seconds")
    axes[0].set_title("Full audit path; required replays retained")
    axes[0].legend(loc="lower right", fontsize=9)
    largest = sorted(stats["functions"], key=lambda r: r["self_seconds"], reverse=True)[
        :8
    ]
    names = [
        f"{r['qualname']}\n{r['file'].split('/')[-1]}:{r['line']} "
        f"[entry {r['entry_index']}]"
        for r in largest
    ]
    axes[1].barh(names, [r["self_seconds"] for r in largest], color="#396ab1")
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Parent elapsed self seconds (waits included)")
    axes[1].set_title("Elapsed stack functions; full inventory retained")
    axes[1].tick_params(axis="y", labelsize=8)
    for axis in axes:
        axis.grid(axis="x", alpha=0.2)
        axis.set_axisbelow(True)
    figure.suptitle(
        "One complete saved audit: diagnostic only, no training or budget admission",
        fontsize=14,
    )
    figure.savefig(output / "audit-costs.png", dpi=160)
    plt.close(figure)
    inputs = {
        str(p.relative_to(ROOT)): digest(p) for p in folder.rglob("*") if p.is_file()
    }
    outputs = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
    manifest = dict(
        inputs=inputs,
        outputs=outputs,
        source=source,
        scope=(
            "post-measurement reporting; excluded from original profile clocks, "
            "no new numerical audit/training"
        ),
    )
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("results/compact-native-wall-profile/pair")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/compact-native-wall-profile/report"),
    )
    args = parser.parse_args()
    summary = render(ROOT / args.input, ROOT / args.output)
    print(
        f"Exported {summary['raw_frames']} functions and {summary['raw_edges']} "
        "callers; diagnostic report only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
