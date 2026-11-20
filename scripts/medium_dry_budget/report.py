"""Data-bound own strength report with fixed turn/river reply-loss readouts."""

import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from river_generalization.capture import replay_path
from river_generalization.learning import context
from river_generalization_diagnosis.analysis import row_identity

from medium_dry_budget.gate import (
    GAME,
    NATIVE,
    OWN,
    SOURCE,
    WORK,
    clean_head,
    fixed_contract,
    paths,
    require_stage,
)
from medium_dry_budget.study import save
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import trace_losses

TOP_TURN = (2443, 1596, 14)
READOUTS = ("current", "uniform_average", "linear_average")
TOLERANCE = 1e-9


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify only preregistered final linear-average matched paths."""
    final = [
        r
        for r in cases
        if r["work_label"] == WORK[-1] and r["readout"] == "linear_average"
    ]
    if len(final) != 6:
        raise ArithmeticError("six fixed final scores required")
    control = [r for r in final if r["arm"] == "texture_range_q8_b8"]
    candidate = [r for r in final if r["arm"] == "q8_turn_exact_river"]
    if [r["seed"] for r in control] != [r["seed"] for r in candidate] or len(
        control
    ) != 3:
        raise ArithmeticError("fixed paired seed grid changed")
    pairs = [
        c["exploitability_fraction_initial_pot"]
        - b["exploitability_fraction_initial_pot"]
        for b, c in zip(control, candidate, strict=True)
    ]
    values = [r["exploitability_fraction_initial_pot"] for r in candidate]
    coverage = [r["whole_coverage"] for r in candidate]
    passed = (
        median(values) <= 0.01
        and max(values) <= 0.025
        and min(coverage) >= 0.95
        and all(r["recall_violations"] == 0 for r in candidate)
    )
    paired = median(pairs)
    classification = (
        "positive"
        if passed and paired <= -0.001
        else "negative"
        if not passed or paired >= 0.001
        else "inconclusive"
    )
    return dict(
        classification=classification,
        candidate_median=median(values),
        candidate_worst=max(values),
        paired_seed_differences=pairs,
        paired_median=paired,
        candidate_absolute_pass=passed,
        control_median=median(
            r["exploitability_fraction_initial_pot"] for r in control
        ),
        control_worst=max(r["exploitability_fraction_initial_pot"] for r in control),
        control_absolute_pass=(
            median(r["exploitability_fraction_initial_pot"] for r in control) <= 0.01
            and max(r["exploitability_fraction_initial_pot"] for r in control) <= 0.025
            and min(r["whole_coverage"] for r in control) >= 0.95
            and all(r["recall_violations"] == 0 for r in control)
        ),
    )


def report(root: Path, output: Path) -> None:
    """Recompute all scores and fixed decision losses after own/native publication."""
    plan = fixed_contract(root)
    head = clean_head(root)
    require_stage(root, SOURCE, "source_qualified")
    require_stage(root, OWN, "own_published")
    require_stage(root, NATIVE, "native_audited")
    native = json.loads((root / NATIVE / "result.json").read_bytes())
    if native["status"] != "completed" or len(native["rows"]) != 54:
        raise ArithmeticError("complete independent audit required")
    native_rows = {
        (r["path_index"], r["work_label"], r["readout"]): r for r in native["rows"]
    }
    own_result = json.loads((root / OWN / "result.json").read_bytes())
    if own_result.get("status") != "completed" or own_result.get("worker_count") != 3:
        raise ArithmeticError("complete fixed own worker cohort required")
    path_rows = [
        item
        for worker in own_result["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    timing = {row["index"]: row for row in path_rows}
    if len(path_rows) != 6 or len(timing) != 6:
        raise ArithmeticError("missing whole-path time or memory")
    cases: list[dict[str, Any]] = []
    for index, seed, arm in paths():
        scoring = context(root, GAME, arm)
        if not isinstance(scoring.exact, MatrixTree):
            raise ArithmeticError("fixed exact tree required")
        exact = scoring.exact
        streets = [row_identity(exact, i)["street"] for i in range(len(exact.keys))]
        folder = root / OWN / "study" / f"path{index:02d}"
        summary = replay_path(scoring, folder)
        if summary["path"] != dict(
            index=index, game=GAME, seed=seed, arm=arm
        ) or summary["labels"] != list(WORK):
            raise ArithmeticError("fixed own path changed")
        for capture in summary["captures"]:
            meta = capture["metadata"]
            work, readout = meta["work_label"], meta["readout"]
            if work not in WORK or readout not in READOUTS:
                raise ArithmeticError("unregistered budget capture")
            audit = native_rows[(index, work, readout)]
            if (
                audit["own_policy_sha256"] != capture["receipt"]["policy_sha256"]
                or audit["native"]["maximum_error_chips"] > TOLERANCE
            ):
                raise ArithmeticError("native/own policy or scalar mismatch")
            metrics = capture["score"]["metrics"]
            chips = metrics["exact_exploitability_chips"]
            row: dict[str, Any] = dict(
                path_index=index,
                seed=seed,
                arm=arm,
                work_label=work,
                readout=readout,
                policy_sha256=capture["receipt"]["policy_sha256"],
                actual_node_work=meta["total_work"],
                overshoot=meta["overshoot"],
                exploitability_chips=chips,
                exploitability_fraction_initial_pot=chips / 36,
                information_rows=capture["information_rows"],
                four_float64_table_bytes=4
                * 8
                * capture["information_rows"]
                * capture["padded_width"],
                whole_coverage=None
                if capture["support"] is None
                else capture["support"]["whole"]["all"]["uniform_reach_fraction"],
                post_initial_coverage=None
                if capture["support"] is None
                else capture["support"]["post_warm"]["river"]["uniform_reach_fraction"],
                recall_violations=summary["recall_violations"],
                native_maximum_error_chips=audit["native"]["maximum_error_chips"],
                whole_path_seconds=timing[index]["whole_path_seconds"],
                worker_peak_rss_bytes=timing[index]["worker_peak_rss_bytes"],
                initial_only_river_rows=None
                if capture["support"] is None
                else capture["support"]["whole"]["river"]["positive_rows"]
                - capture["support"]["post_warm"]["river"]["positive_rows"],
            )
            if readout == "linear_average":
                policy = read_snapshot(
                    folder / capture["file"],
                    scoring.partition,
                    capture["receipt"],
                    meta,
                )
                expanded = scoring.expand(policy)
                contribution = np.zeros(len(exact.keys), dtype=np.float64)
                selected = {
                    i: dict(
                        identity=row_identity(exact, i),
                        saved_probabilities=expanded[
                            i, : len(exact.actions[i])
                        ].tolist(),
                        seats=[],
                    )
                    for i in TOP_TURN
                }
                gains = []
                for seat in (0, 1):
                    trace = trace_losses(exact, expanded, seat, tolerance=TOLERANCE)
                    if trace.accounting_error > TOLERANCE:
                        raise ArithmeticError("reply-loss accounting failed")
                    contribution += trace.losses / 2
                    gains.append(trace.gain)
                    for i in TOP_TURN:
                        if selected[i]["identity"]["seat"] == seat:
                            selected[i]["seats"].append(
                                dict(
                                    seat=seat,
                                    counterfactual_reach=float(
                                        trace.counterfactual_mass[i]
                                    ),
                                    saved_prefix_reach=float(trace.saved_reach_mass[i]),
                                    alternative_action_values_chips=trace.conditional_values[
                                        i, : len(exact.actions[i])
                                    ].tolist(),
                                    additive_contribution_chips=float(
                                        trace.losses[i] / 2
                                    ),
                                )
                            )
                if (
                    abs(math.fsum(gains) / 2 - chips) > TOLERANCE
                    or abs(float(contribution.sum()) - chips) > TOLERANCE
                ):
                    raise ArithmeticError(
                        "turn/river contributions do not sum to exploitability"
                    )
                row["turn_contribution_chips"] = float(
                    contribution[np.array(streets) == "TURN"].sum()
                )
                row["river_contribution_chips"] = float(
                    contribution[np.array(streets) == "RIVER"].sum()
                )
                row["fixed_turn_rows"] = {
                    str(i): dict(
                        **selected[i], contribution_chips=float(contribution[i])
                    )
                    for i in TOP_TURN
                }
            cases.append(row)
    if len(cases) != 54 or len(native_rows) != 54:
        raise ArithmeticError("incomplete budget report grid")
    result = dict(
        status="completed",
        scope=plan["question"],
        head=head,
        cases=cases,
        primary=decision(cases),
        native_maximum_error_chips=native["maximum_error_chips"],
    )
    output.mkdir(parents=True, exist_ok=False)
    save(output / "report.json", result)
