"""All-profile fixed-opponent tables and descriptive decomposition figures."""

import csv
import importlib
import json
import statistics
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_fixed_inputs as inputs
from poker_ai.evaluation.compact_fixed_clock import measurement
from poker_ai.evaluation.compact_fixed_run import replay, validate_native
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_run import runtime
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.river_study import digest


def csv_file(path: Path, rows: list[dict[str, Any]]) -> None:
    if path.exists():
        raise FileExistsError("retain diagnostic table")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(root: Path, op: Path, np: Path, out: Path, started: float) -> dict[str, Any]:
    if out.exists():
        raise FileExistsError("retain diagnostic report")
    saved: dict[str, Any] = dict(
        format="compact-fixed-report-v1",
        status="running",
        failure=None,
        source=inputs.source(root),
        runtime=runtime(),
        new_training=False,
        actual_admission=False,
        fresh_global_admission=False,
    )
    try:
        own = json.loads(op.read_text())
        native = json.loads(np.read_text())
        if own["scope"] != "real":
            raise ValueError("software aliases cannot give poker diagnostic results")
        measurement(op, "own")
        measurement(np, "native")
        saved["replay"] = replay(root, op)
        inputs.check_source(root, native["source"])
        validate_native(
            own, native, digest(op), inputs.config(root)["native_reference"]
        )
        for path in (op, np):
            files.published(root, path)
        contexts = {
            (p.context.spot_file, p.context.representation): p.context
            for p in inputs.pairs(root, False)
        }
        rows = []
        targets: list[dict[str, Any]] = []
        for row in own["rows"]:
            pot = contexts[row["spot_file"], row["representation"]].pot
            identity = {k: row[k] for k in inputs.FIELDS}
            rows.append(
                dict(
                    **identity,
                    initial_pot_chips=pot,
                    **row["metrics"],
                    exact_pot=row["metrics"]["exact_exploitability_chips"] / pot,
                    within_pot=row["metrics"]["within_partition_gain_chips"] / pot,
                    information_pot=row["metrics"]["extra_information_gap_chips"] / pot,
                )
            )
            targets.extend(
                dict(**identity, initial_pot_chips=pot, **target)
                for target in row["responses"]
            )
        conditions = [
            dict(
                row,
                own_S_to_F_gain_pot=row["own_S_to_F_gain_chips"]
                / contexts[row["spot_file"], row["representation"]].pot,
            )
            for row in own["fixed_opponent_conditions"]
        ]
        out.parent.mkdir(parents=True, exist_ok=True)
        artifacts = [
            out.parent / "profiles.csv",
            out.parent / "targets.csv",
            out.parent / "fixed-opponents.csv",
        ]
        for path, data in zip(artifacts, (rows, targets, conditions), strict=True):
            csv_file(path, data)
        matplotlib = importlib.import_module("matplotlib")
        matplotlib.use("Agg")
        plt = importlib.import_module("matplotlib.pyplot")
        base = contract(root)
        reps = base["representations"]
        spots = base["spot_files"]
        figure, axes = plt.subplots(1, 2, figsize=(15, 6))
        for axis, spot in zip(axes, spots, strict=True):
            labels = []
            for j, rep in enumerate(reps):
                for offset, mode in enumerate(("SS", "FF")):
                    selected = [
                        r
                        for r in rows
                        if r["spot_file"] == spot
                        and r["representation"] == rep
                        and r["mixture"] == mode
                    ]
                    w = 100 * statistics.mean(r["within_pot"] for r in selected)
                    i = 100 * statistics.mean(r["information_pot"] for r in selected)
                    x = 2 * j + offset
                    axis.bar(
                        x,
                        w,
                        color="tab:blue",
                        label="Within saved groups" if x == 0 else None,
                    )
                    axis.bar(
                        x,
                        i,
                        bottom=w,
                        color="tab:orange",
                        label="Extra information" if x == 0 else None,
                    )
                    labels.append(rep + "\n" + mode)
            axis.set_xticks(range(12), labels, rotation=65, ha="right", fontsize=7)
            axis.set_title(Path(spot).stem)
            axis.set_ylabel("Mean exploitability contribution (% initial pot)")
            axis.grid(axis="y", alpha=0.2)
        axes[0].legend()
        figure.suptitle(
            "Saved self profiles: three-seed means; SS/FF opponents differ, "
            "not a causal abstraction floor"
        )
        figure.tight_layout()
        plot = out.parent / "decomposition.png"
        if plot.exists():
            raise FileExistsError("retain diagnostic figure")
        figure.savefig(plot, dpi=150)
        plt.close(figure)
        artifacts.append(plot)
        figure, axes = plt.subplots(2, 2, figsize=(14, 8))
        for axis, (spot, target) in zip(
            axes.flat, [(s, t) for s in spots for t in (0, 1)], strict=True
        ):
            for offset, opp in enumerate(("S", "F")):
                positions = [j + (offset - 0.5) * 0.35 for j in range(len(reps))]
                means = []
                low = []
                high = []
                for rep in reps:
                    values = [
                        100 * r["own_S_to_F_gain_pot"]
                        for r in conditions
                        if r["spot_file"] == spot
                        and r["representation"] == rep
                        and r["target"] == target
                        and r["opponent_source"] == opp
                    ]
                    m = statistics.mean(values)
                    means.append(m)
                    low.append(m - min(values))
                    high.append(max(values) - m)
                axis.bar(
                    positions,
                    means,
                    width=0.35,
                    yerr=[low, high],
                    label=opp + " opponent (fixed)",
                    capsize=2,
                )
            axis.axhline(0, color="black", linewidth=0.7)
            axis.set_xticks(range(len(reps)), reps, rotation=35, ha="right", fontsize=7)
            axis.set_title(Path(spot).stem + f", target {target}")
            axis.set_ylabel("Own S to F EV gain (% initial pot)")
            axis.grid(axis="y", alpha=0.2)
        axes.flat[0].legend()
        figure.suptitle(
            "Frozen opponents: means and three-seed range; "
            "not confidence intervals or retraining gains"
        )
        figure.tight_layout()
        plot = out.parent / "fixed-opponents.png"
        if plot.exists():
            raise FileExistsError("retain diagnostic figure")
        figure.savefig(plot, dpi=150)
        plt.close(figure)
        artifacts.append(plot)
        table = out.parent / "tables.md"
        lines = [
            "# Frozen own-opponent diagnosis",
            "",
            "All144logical profiles and288target rows are retained in the CSV files.",
            "SS = both sampled; FF = both full. "
            "Means below are descriptive across three paired seeds.",
            "FF aliases repeat one saved full profile. Opponents differ between SS/FF.",
            "The original sampled accuracy gate remains FAILED; "
            "no new training or admission.",
            "",
            "| Game | Representation | Mode | Mean exact % pot | "
            "Within | Extra information |",
            "|---|---|---|---:|---:|---:|",
        ]
        for spot in spots:
            for rep in reps:
                for mode in ("SS", "SF", "FS", "FF"):
                    selected = [
                        r
                        for r in rows
                        if r["spot_file"] == spot
                        and r["representation"] == rep
                        and r["mixture"] == mode
                    ]
                    values = [
                        100 * statistics.mean(r[k] for r in selected)
                        for k in ("exact_pot", "within_pot", "information_pot")
                    ]
                    lines.append(
                        "| "
                        + " | ".join(
                            [Path(spot).stem, rep, mode, *[f"{v:.9g}" for v in values]]
                        )
                        + " |"
                    )
        with table.open("x") as stream:
            stream.write("\n".join(lines) + "\n")
        artifacts.append(table)
        if time.perf_counter() - started >= 900:
            raise TimeoutError("complete diagnostic report cap")
        saved.update(
            status="completed",
            inputs=[inputs.bound(root, op), inputs.bound(root, np)],
            profiles=144,
            targets=288,
            conditions=144,
            artifacts=[inputs.bound(root, p) for p in artifacts],
            maximum_native_error_chips=max(
                r["maximum_error_chips"] for r in native["comparisons"]
            ),
            maximum_identity_error_chips=own["replay"]["maximum_identity_error_chips"],
            limits=(
                "Known saved policies; paired/repeated sources; "
                "different work and training conventions; shared exported mechanics; "
                "no universal floor or causal sampling/global strength claim"
            ),
        )
        inputs.check_source(root, saved["source"])
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        saved["seconds"] = time.perf_counter() - started
        files.atomic(out, saved)
    return saved
