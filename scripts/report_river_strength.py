"""Reproduce all river-strength metrics from published own and native rows."""

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

from river_strength.gate import (
    ARMS,
    GAMES,
    LABELS,
    READOUTS,
    SEEDS,
    clean_revision,
    contract,
    require_archive,
    source_fingerprint,
)

SOURCE = Path("results/river-strength/source-checks")
OWN = Path("results/river-strength/own")
NATIVE = Path("results/river-strength/native")


@dataclass(frozen=True)
class ReportPath:
    index: int
    game: str
    seed: int
    arm: str


def report_paths() -> tuple[ReportPath, ...]:
    return tuple(
        ReportPath(index, game, seed, arm)
        for index, (game, seed, arm) in enumerate(product(GAMES, SEEDS, ARMS))
    )


def path_times(own: Path) -> dict[int, float]:
    """Bind the twelve complete construction-through-replay path timings."""
    record = json.loads((own / "result.json").read_bytes())
    if (
        record.get("status") != "completed"
        or record.get("stage") != "study"
        or record.get("worker_count") != 3
        or record.get("assignments") != [list(range(i, 12, 3)) for i in range(3)]
    ):
        raise ArithmeticError("complete fixed own study record required")
    rows = []
    for worker in record["workers"]:
        done = [message for message in worker["messages"] if message["kind"] == "done"]
        if len(done) != 1 or worker["exitcode"] != 0:
            raise ArithmeticError("own study worker incomplete")
        rows.extend(done[0]["summary"]["summaries"])
    if len(rows) != 12 or {row["index"] for row in rows} != set(range(12)):
        raise ArithmeticError("own path timing grid incomplete")
    result = {}
    for row in rows:
        spec = report_paths()[row["index"]]
        seconds = row["whole_path_seconds"]
        if (
            row["repeat"] != 0
            or row["path"]
            != dict(index=spec.index, game=spec.game, seed=spec.seed, arm=spec.arm)
            or row["captures"] != 9
            or row["final_work"] < LABELS[-1]
            or type(seconds) not in (int, float)
            or not math.isfinite(seconds)
            or seconds <= 0
        ):
            raise ArithmeticError("own path timing or identity changed")
        result[spec.index] = float(seconds)
    return result


def report(root: Path, own: Path, native: Path) -> dict[str, Any]:
    """Keep all 108 profiles and apply each declared historical gate separately."""
    audit = json.loads((native / "result.json").read_bytes())
    if audit["status"] != "completed" or len(audit["rows"]) != 108:
        raise ArithmeticError("complete independent 108-scalar audit required")
    by_audit = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in audit["rows"]
    }
    if len(by_audit) != 108:
        raise ArithmeticError("duplicate independent scalar row")
    seconds_by_path = path_times(own)
    result: list[dict[str, Any]] = []
    for spec in report_paths():
        summary = json.loads(
            (own / "study" / f"path{spec.index:02d}" / "summary.json").read_bytes()
        )
        if (
            summary["status"] != "completed"
            or summary["path"]
            != dict(index=spec.index, game=spec.game, seed=spec.seed, arm=spec.arm)
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 9
            or summary.get("recall_violations") != 0
        ):
            raise ArithmeticError("own fixed path inventory changed")
        pot = json.loads(
            (root / f"configs/learning-spots/{spec.game}.json").read_bytes()
        )["pot"]
        for row in summary["captures"]:
            meta = row["metadata"]
            label, readout = meta["work_label"], meta["readout"]
            if label not in LABELS or readout not in READOUTS:
                raise ArithmeticError("outside fixed work/readout grid")
            native_row = by_audit[(spec.index, label, readout)]
            if (
                native_row["own_policy_sha256"] != row["receipt"]["policy_sha256"]
                or not math.isfinite(native_row["native"]["maximum_error_chips"])
                or native_row["native"]["maximum_error_chips"] > 1e-9
            ):
                raise ArithmeticError("independent scalar binding/tolerance changed")
            metrics = row["score"]["metrics"]
            support = row["support"]
            post = support["post_warm"] if support is not None else None
            whole = support["whole"] if support is not None else None
            initial_only = (
                whole["river"]["positive_rows"] - post["river"]["positive_rows"]
                if post is not None and whole is not None
                else None
            )
            result.append(
                dict(
                    game=spec.game,
                    seed=spec.seed,
                    arm=spec.arm,
                    work_label=label,
                    readout=readout,
                    total_node_work=meta["total_work"],
                    whole_path_seconds=seconds_by_path[spec.index],
                    overshoot=meta["overshoot"],
                    exploitability_chips=metrics["exact_exploitability_chips"],
                    exploitability_fraction_initial_pot=metrics[
                        "exact_exploitability_chips"
                    ]
                    / pot,
                    within_partition_gain_chips=metrics["within_partition_gain_chips"],
                    extra_information_gap_chips=metrics["extra_information_gap_chips"],
                    exact_prefix_river_only_gain_chips=metrics[
                        "river_only_gain_exact_prefix_chips"
                    ],
                    whole_coverage=whole,
                    post_warm_coverage=post,
                    initial_only_river_rows=initial_only,
                    information_rows=row["information_rows"],
                    tree_nodes=row["tree_nodes"],
                    table_bytes=row["information_rows"] * row["padded_width"] * 4 * 8,
                    policy_sha256=row["receipt"]["policy_sha256"],
                    maximum_native_error_chips=native_row["native"][
                        "maximum_error_chips"
                    ],
                )
            )
    if (
        len(result) != 108
        or len(
            {
                (r["game"], r["seed"], r["arm"], r["work_label"], r["readout"])
                for r in result
            }
        )
        != 108
    ):
        raise ArithmeticError("incomplete fixed comparison grid")
    gates = []
    for game in GAMES:
        for arm in ARMS:
            primary = sorted(
                (
                    r
                    for r in result
                    if r["game"] == game
                    and r["arm"] == arm
                    and r["work_label"] == LABELS[-1]
                    and r["readout"] == "linear_average"
                ),
                key=lambda r: r["seed"],
            )
            if [r["seed"] for r in primary] != list(SEEDS):
                raise ArithmeticError("missing fixed primary seeds")
            values = [r["exploitability_fraction_initial_pot"] for r in primary]
            coverages = [
                r["whole_coverage"]["all"]["uniform_reach_fraction"] for r in primary
            ]
            gates.append(
                dict(
                    game=game,
                    arm=arm,
                    median=statistics.median(values),
                    worst=max(values),
                    coverage=coverages,
                    median_pass=statistics.median(values) <= 0.01,
                    worst_pass=max(values) <= 0.025,
                    coverage_pass=all(v is not None and v >= 0.95 for v in coverages),
                )
            )
    paired = []
    for seed in SEEDS:
        selected = {
            r["arm"]: r
            for r in result
            if r["game"] == "dev_medium_oop"
            and r["seed"] == seed
            and r["work_label"] == LABELS[-1]
            and r["readout"] == "linear_average"
        }
        paired.append(
            dict(
                seed=seed,
                candidate_minus_control_chips=selected[ARMS[1]]["exploitability_chips"]
                - selected[ARMS[0]]["exploitability_chips"],
                candidate_minus_control_fraction_initial_pot=selected[ARMS[1]][
                    "exploitability_fraction_initial_pot"
                ]
                - selected[ARMS[0]]["exploitability_fraction_initial_pot"],
            )
        )
    median = statistics.median(
        r["candidate_minus_control_fraction_initial_pot"] for r in paired
    )
    if not math.isfinite(median):
        raise ArithmeticError("nonfinite paired median")
    return dict(
        status="completed",
        scope="two known games, no fresh/global admission",
        rows=result,
        gates=gates,
        primary_paired=paired,
        primary_median_candidate_minus_control_fraction_initial_pot=median,
        primary_direction="positive"
        if median < 0
        else "negative"
        if median > 0
        else "tie",
        native_maximum_error_chips=max(r["maximum_native_error_chips"] for r in result),
        zero_recall_violations_pass=True,
        native_scalar_tolerance_chips=1e-9,
        native_scalar_gate_pass=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    contract(root)
    clean_revision(root)
    fingerprint = source_fingerprint(root)
    for folder, status in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
    ):
        require_archive(root, root / folder, status, fingerprint)
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain existing river-strength report")
    result = report(root, root / OWN, root / NATIVE)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
