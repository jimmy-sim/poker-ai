"""Exclusive function costs and direct mean callers; no strength/forecast claims."""

import importlib
import json
import math
from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.river_study import digest

FIGURES = ("function-self.png", "mean-direct-callees.png")


def frame_label(row: dict[str, Any]) -> str:
    label = f"{Path(row['file']).name}:{row['line']} {row['name']}"
    if row["file"].startswith("<"):
        label += "(" + ",".join(row["arguments"][:4]) + ")#" + row["code_sha256"][:8]
    return label


def tables(
    saved: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    cases = []
    functions = []
    callers = []
    for row in saved["rows"]:
        point = row["endpoint"]
        path = point["path"]
        common = dict(index=row["index"], source_index=row["source_index"], **path)
        cases.append(
            dict(
                **common,
                mode=row["mode"],
                whole_measure_seconds=row["whole_measure_seconds"],
                setup_and_warm_seconds=point["setup_and_warm_seconds"],
                incremental_seconds=point["incremental_seconds"],
                cpu_seconds=point["cpu_seconds"],
                iteration=point["iteration"],
                total_work=point["total_work"],
                incremental_visits=point["incremental_visits"],
                sampled_traversals=point["sampled_traversals"],
                guard_sha256=point["guard_sha256"],
                uniform_readout_sha256=point["readout_sha256"]["uniform"],
                linear_readout_sha256=point["readout_sha256"]["linear"],
                function_self_total_seconds=row["stats"]["total_self_seconds"]
                if row["stats"]
                else None,
            )
        )
        if row["stats"] is None:
            continue
        stats = row["stats"]
        by_id = {f["id"]: f for f in stats["functions"]}
        for f in stats["functions"]:
            functions.append(
                dict(
                    **common,
                    **f,
                    self_percent_of_instrumented_profile=100
                    * f["self_seconds"]
                    / stats["total_self_seconds"]
                    if stats["total_self_seconds"]
                    else None,
                )
            )
        for edge in stats["callers"]:
            callers.append(
                dict(
                    **common,
                    **edge,
                    caller_label=frame_label(by_id[edge["caller"]]),
                    callee_label=frame_label(by_id[edge["callee"]]),
                )
            )
    return cases, functions, callers


def aggregates(functions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in functions:
        groups.setdefault((row["batch_size"], row["code_id"]), []).append(row)
    result = []
    for (batch, identifier), rows in sorted(groups.items()):
        result.append(
            dict(
                batch_size=batch,
                id=identifier,
                label=frame_label(rows[0]),
                self_seconds=math.fsum(r["self_seconds"] for r in rows),
                cumulative_seconds=math.fsum(r["cumulative_seconds"] for r in rows),
                total_calls=sum(r["total_calls"] for r in rows),
            )
        )
    return result


def mean_children(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[float]] = {}
    labels = {}
    for row in rows:
        if row["mode"] != "instrumented":
            continue
        batch = row["endpoint"]["path"]["batch_size"]
        stats = row["stats"]
        by_id = {f["id"]: f for f in stats["functions"]}
        parent = [
            f
            for f in stats["functions"]
            if f["file"] == "src/poker_ai/postflop/frozen_batches.py"
            and f["name"] == "mean_updates"
        ]
        for f in parent:
            key = batch, "mean-self"
            labels[key] = "mean_updates own self time"
            grouped.setdefault(key, []).append(f["self_seconds"])
            for edge in stats["callers"]:
                if edge["caller"] != f["id"]:
                    continue
                key = batch, by_id[edge["callee"]]["code_id"]
                callee = by_id[edge["callee"]]
                label = frame_label(callee)
                if (
                    callee["file"] == "src/poker_ai/postflop/frozen_batches.py"
                    and callee["name"] == "<genexpr>"
                ):
                    label += " (includes traversal)"
                labels[key] = label
                grouped.setdefault(key, []).append(edge["cumulative_seconds"])
    return [
        dict(batch_size=b, id=i, label=labels[b, i], seconds=math.fsum(values))
        for (b, i), values in sorted(grouped.items())
    ]


def figures(
    output: Path,
    functions: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    scope: str,
) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    aggregate = aggregates(functions)
    fig, axes = plt.subplots(1, 3, figsize=(23, 8), layout="constrained")
    for ax, batch in zip(axes, (1, 4, 16), strict=True):
        chosen = sorted(
            (r for r in aggregate if r["batch_size"] == batch),
            key=lambda r: r["self_seconds"],
        )[-12:]
        ax.barh(range(len(chosen)), [r["self_seconds"] for r in chosen])
        ax.set_yticks(range(len(chosen)), [r["label"][:65] for r in chosen], fontsize=8)
        ax.set_title(f"B{batch}: all eight first-seed paths")
        ax.set_xlabel("Summed instrumented self seconds")
        ax.grid(axis="x", alpha=0.25)
    fig.suptitle(
        scope + "Whole measurement: exclusive costs; "
        "sums across cases are not elapsed stage time"
    )
    fig.savefig(output / FIGURES[0], dpi=140)
    plt.close(fig)
    children = mean_children(rows)
    size = max(sum(r["batch_size"] == b for r in children) for b in (4, 16))
    fig, axes = plt.subplots(
        1, 2, figsize=(23, max(7, size * 0.3 + 2)), layout="constrained"
    )
    for ax, batch in zip(axes, (4, 16), strict=True):
        chosen = sorted(
            (r for r in children if r["batch_size"] == batch),
            key=lambda r: r["seconds"],
        )
        ax.barh(range(len(chosen)), [r["seconds"] for r in chosen], color="C1")
        ax.set_yticks(range(len(chosen)), [r["label"][:85] for r in chosen], fontsize=8)
        ax.set_title(f"B{batch}: mean self and every direct callee")
        ax.set_xlabel("Summed instrumented seconds at the mean caller level")
        ax.grid(axis="x", alpha=0.25)
    fig.suptitle(
        scope + "Generator child includes traversal; "
        "do not add cumulative times from other levels"
    )
    fig.savefig(output / FIGURES[1], dpi=140)
    plt.close(fig)


def write_report(
    saved: dict[str, Any], output: Path, *, plots: bool = True
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    cases, functions, callers = tables(saved)
    if len(cases) != 48 or not functions or not callers:
        raise ArithmeticError("cost report grid incomplete")
    for name, values in (
        ("cases.csv", cases),
        ("functions.csv", functions),
        ("callers.csv", callers),
    ):
        write_csv(output / name, values)
    scope = (
        "SOFTWARE FIXTURE, NOT POKER RESULTS; "
        if saved.get("scope", "").startswith("EXPLICIT")
        else ""
    )
    lines = [
        "# Batch function costs",
        "",
        scope or "Known first-seed cost diagnosis only.",
        "Whole old measurement includes trainer setup/warm, observations and hashes.",
        "Tree/context preparation is outside these function profiles "
        "and inside the stage cap.",
        "Self times may be aggregated as instrumented work; cumulative times overlap.",
        "The mean consumes a traversal generator: "
        "inclusive mean cost is not validation-only cost.",
        "No EV/strength score, optimizer, new forecast or long-study admission.",
        "",
    ]
    aggregate = aggregates(functions)
    for batch in (1, 4, 16):
        lines.extend(
            [
                f"## B{batch}: top function self costs",
                "",
                "| Function | Total calls | Self seconds | "
                "Inclusive seconds (overlap) |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in sorted(
            (r for r in aggregate if r["batch_size"] == batch),
            key=lambda r: r["self_seconds"],
            reverse=True,
        )[:15]:
            label = row["label"].replace("|", "/")
            lines.append(
                f"| {label} | {row['total_calls']} | "
                f"{row['self_seconds']:.9f} | {row['cumulative_seconds']:.9f} |"
            )
        lines.append("")
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    if plots:
        figures(output, functions, saved["rows"], scope)
    names = ("cases.csv", "functions.csv", "callers.csv", "tables.md")
    result = dict(
        paths=24,
        endpoints=48,
        instrumented_profiles=24,
        function_rows=len(functions),
        caller_rows=len(callers),
        numerical_sha256={n: digest(output / n) for n in names},
        figures=list(FIGURES) if plots else [],
        scope="cost only, no strength/optimizer/forecast/admission",
    )
    (output / "summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    return result
