"""Full-size reporting IO benchmark, visibly synthetic and never agent input."""

import csv
import gzip
import importlib
import json
import time
from pathlib import Path
from typing import Any

from poker_ai.postflop.controlled_profile import KEY, cells
from poker_ai.postflop.pipeline_cost import CASE, METRICS
from poker_ai.postflop.river_study import digest

SCOPE = "SYNTHETIC IO CALIBRATION — NOT LEARNING RESULTS"


def planned_rows(
    protocol: dict[str, Any], profiles: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Duplicate old values/policies into planned labels solely to benchmark IO."""
    comparison = protocol["future_comparison"]
    rows, snapshots = [], []
    for index, cell in enumerate(cells(comparison)):
        old = next(
            d
            for d in profiles
            if d["case"]["spot_file"] == cell["spot_file"]
            and d["case"]["representation"] == cell["representation"]
            and d["case"]["training"]
            == ("full" if cell["traversal"] == "full" else "sampled")
            and d["case"]["seed"] == cell["seed"]
        )
        for axis, targets in (
            ("work", comparison["node_work_checkpoints"]),
            ("iteration", comparison["iteration_checkpoints"]),
        ):
            for target in targets:
                row = dict(
                    scope=SCOPE,
                    planned_cell=index,
                    axis=axis,
                    target=target,
                    **{k: cell[k] for k in KEY},
                    source_case=json.dumps(
                        {k: old["case"][k] for k in CASE}, sort_keys=True
                    ),
                    **old["metrics"],
                )
                rows.append(row)
                snapshots.append(
                    dict(
                        scope=SCOPE,
                        planned_cell=index,
                        axis=axis,
                        target=target,
                        source_profile=old,
                    )
                )
    if len(rows) != 840:
        raise ArithmeticError("synthetic IO fixture is not the fixed planned size")
    return rows, snapshots


def render_curves(rows: list[dict[str, Any]], output: Path) -> list[str]:
    """Eight fixed figures: four primary metrics x two separate checkpoint axes."""
    matplotlib = importlib.import_module("matplotlib")

    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")

    groups = sorted({(r["spot_file"], r["representation"]) for r in rows})
    figures = []
    for metric in METRICS[:-1]:
        for axis in ("work", "iteration"):
            fig, axes = plt.subplots(2, 2, figsize=(12, 8), squeeze=False)
            for plot, group in zip(axes.flat, groups, strict=True):
                chosen = [
                    r
                    for r in rows
                    if r["axis"] == axis
                    and (r["spot_file"], r["representation"]) == group
                ]
                for index in sorted({r["planned_cell"] for r in chosen}):
                    line = sorted(
                        [r for r in chosen if r["planned_cell"] == index],
                        key=lambda r: r["target"],
                    )
                    plot.plot(
                        [r["target"] for r in line],
                        [r[metric] for r in line],
                        marker=".",
                        alpha=0.4,
                        linewidth=0.8,
                    )
                if axis == "work":
                    plot.set_xscale("log")
                plot.set_title(f"{Path(group[0]).stem} / {group[1]}", fontsize=9)
                plot.set_xlabel(axis + " label (duplicated old data)")
                plot.set_ylabel("old own-policy chips")
                plot.grid(alpha=0.2)
            fig.suptitle(SCOPE + "\n" + metric, fontsize=11)
            fig.text(
                0.5,
                0.5,
                "DUPLICATE OLD POLICY DATA",
                ha="center",
                rotation=25,
                fontsize=26,
                alpha=0.15,
            )
            fig.tight_layout(rect=(0, 0, 1, 0.93))
            name = metric + "-" + axis + ".png"
            fig.savefig(output / name, dpi=140)
            plt.close(fig)
            figures.append(name)
    return figures


def fixture(
    root: Path, protocol: dict[str, Any], profiles: list[dict[str, Any]], output: Path
) -> dict[str, Any]:
    del root
    started, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True, exist_ok=False)
    rows, snapshots = planned_rows(protocol, profiles)
    # Memory is bounded by sixteen source profiles and one decoded JSONL record.
    encoded = {
        d["index"]: json.dumps(
            d, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        for d in profiles
    }
    path = output / "synthetic-840-profiles.jsonl.gz"
    with (
        path.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream,
    ):
        header = dict(format="poker-ai-synthetic-io-bundle-v1", scope=SCOPE, rows=840)
        stream.write(json.dumps(header, sort_keys=True).encode() + b"\n")
        for snapshot in snapshots:
            metadata = {k: v for k, v in snapshot.items() if k != "source_profile"}
            prefix = json.dumps(
                metadata, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
            stream.write(
                prefix[:-1]
                + b',"source_profile":'
                + encoded[snapshot["source_profile"]["index"]]
                + b"}\n"
            )
    with gzip.open(path, "rt") as stream:
        header = json.loads(next(stream))
        count = 0
        for line in stream:
            record = json.loads(line)
            if record["scope"] != SCOPE:
                raise ArithmeticError("synthetic IO record scope changed")
            count += 1
        if header["scope"] != SCOPE or header["rows"] != 840 or count != 840:
            raise ArithmeticError("synthetic IO round trip changed")
    with (output / "synthetic-rows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    names = [path.name, "synthetic-rows.csv", *render_curves(rows, output)]
    (output / "README.md").write_text(
        "# " + SCOPE + "\n\n840 planned labels duplicate 16 old own profiles.\n"
        "These files benchmark serialization/table/plot cost. They are not new "
        "learning outcomes and cannot establish playing strength.\n"
    )
    names.append("README.md")
    artifacts = {
        name: dict(sha256=digest(output / name), bytes=(output / name).stat().st_size)
        for name in names
    }
    return dict(
        scope=SCOPE,
        rows=840,
        unique_source_profiles=16,
        figures=8,
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu,
        directory=str(output),
        artifacts=artifacts,
    )
