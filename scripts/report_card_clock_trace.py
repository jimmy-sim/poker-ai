"""Report complete audit resource observations without performance admission."""

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from card_clock_support import check_record
from profile_compact_replay import digest
from report_cached_native import elapsed_parts, write_csv
from trace_card_audit import CONFIG, CONFIG_SHA, show

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/report_card_clock_trace.py"
SOURCE = "be647d36e87d7173cf20a36a3e5d9b9ff6dee581a5bdb8bf98c06a0292e6ef9e"


def measured(child: dict[str, Any]) -> None:
    if (
        child.get("config_sha256") != CONFIG_SHA
        or child.get("source", {}).get("fingerprint") != SOURCE
        or child.get("scope")
        != "RESOURCE_DIAGNOSTIC_COMPLETE_SAVED_AUDIT_NOT_PERFORMANCE_ADMISSION"
        or child.get("status") != "complete_card_clock_trace"
        or child.get("admission_evidence") is not False
    ):
        raise ArithmeticError("registered complete resource diagnostic required")


def exports(
    mode: str, name: str, row: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    check_record(row)
    observation = row["interval"]
    before = row["before"]
    clock = dict(
        mode=mode,
        interval=name,
        pid=before["pid"],
        **observation["clocks"],
        scope=observation["scope"],
    )
    counters: list[dict[str, Any]] = []
    peaks = []
    for kind, resource in observation["resources"].items():
        counters.extend(
            dict(
                mode=mode,
                interval=name,
                pid=before["pid"],
                resource_scope=kind,
                counter=k,
                delta=v,
                zero_does_not_prove_absence=True,
            )
            for k, v in resource["delta"].items()
        )
        peaks.append(
            dict(
                mode=mode,
                interval=name,
                pid=before["pid"],
                resource_scope=kind,
                peak_before=resource["peak_rss_before"],
                peak_after=resource["peak_rss_after"],
                rss_unit=resource["rss_unit"],
                cumulative_peak_not_interval_allocation=True,
            )
        )
    return clock, counters, peaks


def gather(
    folder: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    children = [
        json.loads((folder / m / "child.json").read_text())
        for m in ("uncached", "cached")
    ]
    for child in children:
        measured(child)
    show(ROOT, folder)
    pair = json.loads((folder / "pair.json").read_text())
    modes = []
    clocks = []
    counters: list[dict[str, Any]] = []
    peaks = []
    for mode, m, child in zip(
        pair["order"], pair["measurements"], children, strict=True
    ):
        native = json.loads((folder / mode / "native.json").read_text())
        reads = json.loads((folder / mode / "read-phases.json").read_text())["phases"]
        modes.append(
            dict(
                mode=mode,
                whole_elapsed_seconds=m["seconds"],
                parent_body_cpu_seconds=child["parent_body_cpu_seconds"],
                elapsed_parts=elapsed_parts(
                    m["seconds"], reads, native["native_batch"]["seconds"]
                ),
                idle_control=child["idle_control"],
                card_cache=child["card_cache"],
            )
        )
        rows = [
            ("parent_post_import_prewrite", child["child_observation"]),
            ("parent_body", child["body_observation"]),
        ]
        phases = json.loads((folder / mode / "parent-resource-reads.json").read_text())[
            "reads"
        ]
        rows.extend((f"own_read_{i}", r["observation"]) for i, r in enumerate(phases))
        rows.extend(
            (
                f"worker_{i}",
                json.loads(
                    (
                        folder / mode / "worker-telemetry" / f"worker-{i}.json"
                    ).read_text()
                )["observation"],
            )
            for i in range(3)
        )
        for name, row in rows:
            a, b, c = exports(mode, name, row)
            clocks.append(a)
            counters.extend(b)
            peaks.extend(c)
    return modes, clocks, counters, peaks


def render(folder: Path, output: Path) -> dict[str, Any]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.reproducibility import runtime_environment
    from poker_ai.validation.five_card import source_provenance

    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous resource report")
    modes, clocks, counters, peaks = gather(folder)
    measured_source = json.loads((folder / "uncached/child.json").read_text())["source"]
    source: dict[str, Any] = dict(
        source_provenance(
            ROOT, ROOT / CONFIG, entrypoints=(ENTRY, "scripts/report_cached_native.py")
        )
    )
    source["sha256"].update(measured_source["sha256"])
    source["fingerprint"] = sha(source["sha256"])
    commit_sources(ROOT, source["git_commit"], source["sha256"])
    summary = dict(
        scope="POSTHOC_RESOURCE_OBSERVATIONS_NOT_PERFORMANCE_ADMISSION",
        source=source,
        environment=runtime_environment(),
        modes=modes,
        clock_intervals=len(clocks),
        counter_rows=len(counters),
        peak_rows=len(peaks),
        admission_evidence=False,
        production_integrated=False,
        poker_training_performed=False,
        old_registered_timing_failure_preserved=True,
        cached_elapsed_lower_observed=modes[1]["whole_elapsed_seconds"]
        < modes[0]["whole_elapsed_seconds"],
        limitations=(
            "ONE ordered pair under an explicit idle-prevention request; "
            "assertion state not independently audited. Parent interval excludes "
            "imports/final write. Snapshots nearby, not atomic; CPU is not additive "
            "wall time; parallel worker CPU is not summed; OS zero counters may "
            "be unsupported; peaks cumulative per process with explicit units. "
            "No causal attribution, population runtime, memory savings, stronger "
            "agent or budget permit."
        ),
    )
    output.mkdir(parents=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(output / "clocks.csv", clocks)
    write_csv(output / "resource-counters.csv", counters)
    write_csv(output / "peak-rss.csv", peaks)
    write_csv(
        output / "elapsed-parts.csv",
        [
            dict(mode=r["mode"], part=k, elapsed_seconds=v)
            for r in modes
            for k, v in r["elapsed_parts"].items()
        ],
    )
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    figure, axes = plt.subplots(1, 3, figsize=(18, 6), layout="constrained")
    labels = {
        "tiny_proof_read": "Tiny proof read",
        "initial_own_read": "Initial own read",
        "reference_worker_batch": "Reference workers",
        "final_own_read": "Final own read",
        "other_elapsed": "Other elapsed",
    }
    left = [0.0, 0.0]
    for part, label in labels.items():
        values = [r["elapsed_parts"][part] for r in modes]
        axes[0].bar(["Uncached", "Cached"], values, bottom=left, label=label)
        left = [a + b for a, b in zip(left, values, strict=True)]
    axes[0].set(
        ylabel="Whole-command elapsed seconds", title="All mandatory stages retained"
    )
    axes[0].legend(fontsize=8)
    for axis, prefix, names in (
        (axes[1], "own_read_", ("Tiny", "Initial", "Final")),
        (axes[2], "worker_", ("0", "1", "2")),
    ):
        chosen = [
            r
            for mode in ("uncached", "cached")
            for i in range(3)
            for r in clocks
            if r["mode"] == mode and r["interval"] == prefix + str(i)
        ]
        for offset, key, label in (
            (-0.18, "perf_seconds", "Elapsed"),
            (0.18, "process_cpu_seconds", "Process CPU"),
        ):
            axis.bar(
                [i + offset for i in range(6)],
                [r[key] for r in chosen],
                width=0.36,
                label=label,
            )
        axis.set(
            xticks=list(range(6)),
            xticklabels=[name + " " + m for m in ("U", "C") for name in names],
            ylabel="Seconds at matching boundaries",
            title="Own-read intervals"
            if prefix == "own_read_"
            else "Individual reference workers",
        )
        axis.tick_params(axis="x", rotation=35)
        axis.legend(fontsize=8)
    figure.suptitle(
        "One saved diagnostic pair: U uncached, C cached; "
        "CPU is separate from elapsed; no performance admission"
    )
    figure.savefig(output / "resource-clocks.png", dpi=160)
    plt.close(figure)
    (output / "manifest.json").write_text(
        json.dumps(
            dict(
                input_sha256={
                    str(p.relative_to(folder)): digest(p)
                    for p in folder.rglob("*")
                    if p.is_file()
                },
                output_sha256={
                    p.name: digest(p) for p in output.iterdir() if p.is_file()
                },
                original_inputs_retained=True,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pair", type=Path, default=Path("results/card-audit-clock-trace/pair")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/card-audit-clock-trace/report"),
    )
    a = parser.parse_args()
    saved = render(ROOT / a.pair, ROOT / a.output)
    print(
        json.dumps(
            dict(
                intervals=saved["clock_intervals"],
                counters=saved["counter_rows"],
                peaks=saved["peak_rows"],
                scope=saved["scope"],
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
