"""Classify fixed same-path river readouts from published own/native bytes."""

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

from river_uniform_readout.diagnostics import diagnose
from river_uniform_readout.gate import (
    clean_revision,
    require_archive,
    source_fingerprint,
)
from river_uniform_readout.learning import (
    GAMES,
    LABELS,
    READOUTS,
    SEEDS,
    contract,
    paths,
)

from poker_ai.postflop.river_study import Deadline

SOURCE = Path("results/river-uniform-readout/source-checks")
OWN = Path("results/river-uniform-readout/own")
NATIVE = Path("results/river-uniform-readout/native")
CONTROL = "linear_average"
CANDIDATE = "uniform_average"


def path_resources(own: Path) -> dict[int, dict[str, float | int]]:
    """Bind twelve complete construction-through-replay times and peak RSS."""
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
        spec = paths()[row["index"]]
        seconds = row["whole_path_seconds"]
        rss = row["worker_peak_rss_bytes"]
        if (
            row["repeat"] != 0
            or row["path"] != vars(spec)
            or row["captures"] != 9
            or row["final_work"] < LABELS[-1]
            or type(seconds) not in (int, float)
            or not math.isfinite(seconds)
            or seconds <= 0
            or type(rss) is not int
            or rss <= 0
        ):
            raise ArithmeticError("own path timing or identity changed")
        result[spec.index] = dict(whole_path_seconds=float(seconds), peak_rss_bytes=rss)
    return result


def report(root: Path, own: Path, native: Path) -> dict[str, Any]:
    """Retain every readout and apply frozen per-stratum quality/paired gates."""
    audit = json.loads((native / "result.json").read_bytes())
    if audit["status"] != "completed" or len(audit["rows"]) != 108:
        raise ArithmeticError("complete independent 108-profile audit required")
    by_audit = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in audit["rows"]
    }
    if len(by_audit) != 108:
        raise ArithmeticError("duplicate independent scalar row")
    resources_by_path = path_resources(own)
    result: list[dict[str, Any]] = []
    for spec in paths():
        summary = json.loads(
            (own / "study" / f"path{spec.index:02d}" / "summary.json").read_bytes()
        )
        if (
            summary["status"] != "completed"
            or summary["path"] != vars(spec)
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 9
            or summary.get("recall_violations") != 0
        ):
            raise ArithmeticError("own fixed path inventory changed")
        pot = json.loads(
            (
                root / f"configs/river-uniform-readout-spots/{spec.game}.json"
            ).read_bytes()
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
            whole = support["whole"] if support is not None else None
            post = support["post_warm"] if support is not None else None
            result.append(
                dict(
                    game=spec.game,
                    seed=spec.seed,
                    arm=spec.arm,
                    work_label=label,
                    readout=readout,
                    total_node_work=meta["total_work"],
                    overshoot=meta["overshoot"],
                    whole_path_seconds=resources_by_path[spec.index][
                        "whole_path_seconds"
                    ],
                    worker_peak_rss_bytes=resources_by_path[spec.index][
                        "peak_rss_bytes"
                    ],
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
                    initial_only_river_rows=(
                        whole["river"]["positive_rows"] - post["river"]["positive_rows"]
                        if whole is not None and post is not None
                        else None
                    ),
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
        or len({(r["game"], r["seed"], r["work_label"], r["readout"]) for r in result})
        != 108
    ):
        raise ArithmeticError("incomplete fixed comparison grid")
    gates = []
    paired = []
    medians: dict[str, float] = {}
    for game in GAMES:
        for readout in (CONTROL, CANDIDATE):
            selected = sorted(
                (
                    r
                    for r in result
                    if r["game"] == game
                    and r["work_label"] == LABELS[-1]
                    and r["readout"] == readout
                ),
                key=lambda r: r["seed"],
            )
            if [r["seed"] for r in selected] != list(SEEDS):
                raise ArithmeticError("missing fixed primary seeds")
            values = [r["exploitability_fraction_initial_pot"] for r in selected]
            coverages = [
                r["whole_coverage"]["all"]["uniform_reach_fraction"] for r in selected
            ]
            gates.append(
                dict(
                    game=game,
                    readout=readout,
                    median=statistics.median(values),
                    worst=max(values),
                    coverage=coverages,
                    median_pass=statistics.median(values) <= 0.01,
                    worst_pass=max(values) <= 0.025,
                    coverage_pass=all(v is not None and v >= 0.95 for v in coverages),
                    recall_pass=True,
                )
            )
        for seed in SEEDS:
            paired_rows = {
                r["readout"]: r
                for r in result
                if r["game"] == game
                and r["seed"] == seed
                and r["work_label"] == LABELS[-1]
            }
            if set(paired_rows) != set(READOUTS):
                raise ArithmeticError("missing fixed paired seed")
            paired.append(
                dict(
                    game=game,
                    seed=seed,
                    candidate_minus_control_chips=paired_rows[CANDIDATE][
                        "exploitability_chips"
                    ]
                    - paired_rows[CONTROL]["exploitability_chips"],
                    candidate_minus_control_fraction_initial_pot=paired_rows[CANDIDATE][
                        "exploitability_fraction_initial_pot"
                    ]
                    - paired_rows[CONTROL]["exploitability_fraction_initial_pot"],
                )
            )
        medians[game] = statistics.median(
            r["candidate_minus_control_fraction_initial_pot"]
            for r in paired
            if r["game"] == game
        )
    if any(not math.isfinite(value) for value in medians.values()):
        raise ArithmeticError("nonfinite paired median")
    candidate_pass = all(
        gate["median_pass"]
        and gate["worst_pass"]
        and gate["coverage_pass"]
        and gate["recall_pass"]
        for gate in gates
        if gate["readout"] == CANDIDATE
    )
    medium = (medians[GAMES[0]], medians[GAMES[1]])
    guards = (medians[GAMES[2]], medians[GAMES[3]])
    classification = (
        "negative"
        if not candidate_pass
        or any(value >= 0.001 for value in medium)
        or any(value > 0.001 for value in guards)
        else "positive"
        if all(value <= -0.001 for value in medium)
        and all(value <= 0.001 for value in guards)
        else "inconclusive"
    )
    return dict(
        status="completed",
        scope=(
            "four newly selected inputs on known public templates; no global admission"
        ),
        rows=result,
        gates=gates,
        primary_paired=paired,
        primary_spot_medians=medians,
        classification=classification,
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
        raise FileExistsError("retain existing uniform-readout report")
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        result = report(root, root / OWN, root / NATIVE)
        (args.output / "partial-report.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )
        result["representative_decisions"] = diagnose(
            root,
            root / OWN,
            result["rows"],
            Deadline(900),
            args.output / "decision-events.jsonl",
        )
        result["decision_assumptions"] = (
            "Finite restricted game. Additive gains use an exact best response "
            "to the saved opponent policy and optimally continue the responder's "
            "future actions; each seat gain is divided by two. Local alternative "
            "values instead continue both seats under the saved profile. "
            "Neither is universal poker advice."
        )
        (args.output / "report.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )
    except BaseException as error:
        (args.output / "failure.json").write_text(
            json.dumps(
                dict(
                    status="failed_retained",
                    type=type(error).__name__,
                    reason=str(error),
                ),
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )
        raise


if __name__ == "__main__":
    main()
