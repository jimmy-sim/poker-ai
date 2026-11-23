"""Data-bound full-pass versus immutable B4 result and fixed river trace."""

import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from medium_dry_b8.report import row_identity
from medium_dry_clipped.capture import replay_path as replay_control
from medium_dry_clipped.gate import NATIVE as CONTROL_NATIVE_STAGE
from medium_dry_clipped.gate import OWN as CONTROL_OWN_STAGE
from medium_dry_clipped.gate import require_stage as require_control_stage
from medium_dry_clipped.learning import context as control_context

from medium_dry_full.capture import READOUTS
from medium_dry_full.capture import replay_path as replay_candidate
from medium_dry_full.gate import (
    ARM,
    CONTROL_ARM,
    GAMES,
    NATIVE,
    OWN,
    SEEDS,
    SOURCE,
    WORK,
    clean_head,
    fixed_contract,
    paths,
    require_stage,
)
from medium_dry_full.learning import context as candidate_context
from medium_dry_full.study import save
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import trace_losses

TOP_TURN = (2443, 1596, 14)
TOP_RIVER = (1806, 640)
TOLERANCE = 1e-9


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify one deterministic candidate against three fixed B4 controls."""
    final = [
        row
        for row in cases
        if row["work_label"] == WORK[-1] and row["readout"] == "linear_average"
    ]
    if len(final) != 8:
        raise ArithmeticError("eight fixed final scores required")
    by_game: dict[str, dict[str, Any]] = {}
    for game in GAMES:
        controls = [
            row for row in final if row["game"] == game and row["arm"] == CONTROL_ARM
        ]
        candidates = [row for row in final if row["game"] == game and row["arm"] == ARM]
        if (
            len(controls) != 3
            or [row["seed"] for row in controls] != list(SEEDS)
            or len(candidates) != 1
            or candidates[0]["seed"] is not None
        ):
            raise ArithmeticError("fixed candidate/control grid changed")
        candidate = candidates[0]
        score = candidate["exploitability_fraction_initial_pot"]
        control_values = [
            row["exploitability_fraction_initial_pot"] for row in controls
        ]
        contrasts = [score - value for value in control_values]
        passed = (
            score <= 0.01
            and score <= 0.025
            and candidate["whole_coverage"] is not None
            and candidate["whole_coverage"] >= 0.95
            and candidate["recall_violations"] == 0
        )
        by_game[game] = dict(
            candidate=score,
            control_by_seed=control_values,
            control_median=median(control_values),
            control_worst=max(control_values),
            candidate_minus_each_control=contrasts,
            contrast_median=median(contrasts),
            absolute_pass=passed,
        )
    medium = by_game["new_medium_dry_oop"]
    low = by_game["new_low_wet_ip"]
    classification = (
        "positive"
        if medium["absolute_pass"]
        and low["absolute_pass"]
        and medium["contrast_median"] <= -0.001
        and low["contrast_median"] <= 0.001
        else "negative"
        if not medium["absolute_pass"]
        or not low["absolute_pass"]
        or medium["contrast_median"] >= 0.001
        or low["contrast_median"] > 0.001
        else "inconclusive"
    )
    return dict(classification=classification, by_game=by_game)


def _timing(result: dict[str, Any], expected: int) -> dict[int, dict[str, Any]]:
    rows = [
        item
        for worker in result["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    timing = {row["index"]: row for row in rows}
    if (
        result.get("status") != "completed"
        or len(rows) != expected
        or len(timing) != expected
    ):
        raise ArithmeticError("missing fixed whole-path timing")
    return timing


def report(root: Path, output: Path) -> None:
    """Replay published own/control bytes and audit fixed best-reply losses."""
    plan = fixed_contract(root)
    head = clean_head(root)
    require_stage(root, SOURCE, "source_qualified")
    require_stage(root, OWN, "own_published")
    require_stage(root, NATIVE, "native_audited")
    require_control_stage(root, CONTROL_OWN_STAGE, "own_published")
    require_control_stage(root, CONTROL_NATIVE_STAGE, "native_audited")
    candidate_native = json.loads((root / NATIVE / "result.json").read_bytes())
    control_native = json.loads(
        (root / CONTROL_NATIVE_STAGE / "result.json").read_bytes()
    )
    if (
        candidate_native["status"] != "completed"
        or len(candidate_native["rows"]) != 12
        or control_native["status"] != "completed"
        or len(control_native["rows"]) != 108
    ):
        raise ArithmeticError("complete independent audits required")
    candidate_audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in candidate_native["rows"]
    }
    control_audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in control_native["rows"]
    }
    candidate_timing = _timing(json.loads((root / OWN / "result.json").read_bytes()), 2)
    control_timing = _timing(
        json.loads((root / CONTROL_OWN_STAGE / "result.json").read_bytes()), 12
    )
    cases: list[dict[str, Any]] = []
    specs = [
        (
            CONTROL_ARM,
            (0 if game == GAMES[0] else 6) + 2 * SEEDS.index(seed),
            game,
            seed,
        )
        for game in GAMES
        for seed in SEEDS
    ] + [(ARM, index, game, None) for index, game, _ in paths()]
    for arm, path_index, game, seed in specs:
        control = arm == CONTROL_ARM
        folder = (
            root
            / (CONTROL_OWN_STAGE if control else OWN)
            / "study"
            / f"path{path_index:02d}"
        )
        scoring = (
            control_context(root, game, CONTROL_ARM)
            if control
            else candidate_context(root, game, ARM)
        )
        replay = replay_control if control else replay_candidate
        audits = control_audits if control else candidate_audits
        timing = control_timing[path_index] if control else candidate_timing[path_index]
        if not isinstance(scoring.exact, MatrixTree):
            raise ArithmeticError("fixed exact tree required")
        exact = scoring.exact
        streets = [row_identity(exact, i)["street"] for i in range(len(exact.keys))]
        summary = replay(scoring, folder)
        expected_path = (
            dict(index=path_index, game=game, seed=seed, arm=arm)
            if control
            else dict(index=path_index, game=game, arm=arm)
        )
        if summary["path"] != expected_path or summary["labels"] != list(WORK):
            raise ArithmeticError("fixed own path changed")
        selected = [
            item
            for item in summary["captures"]
            if item["metadata"]["readout"] in READOUTS
        ]
        if len(selected) != len(WORK) * len(READOUTS):
            raise ArithmeticError("missing fixed current/linear readouts")
        for capture in selected:
            meta = capture["metadata"]
            work, readout = meta["work_label"], meta["readout"]
            if work not in WORK or readout not in READOUTS:
                raise ArithmeticError("unregistered work/readout")
            audit = audits[(path_index, work, readout)]
            if (
                audit["own_policy_sha256"] != capture["receipt"]["policy_sha256"]
                or audit["native"]["maximum_error_chips"] > TOLERANCE
            ):
                raise ArithmeticError("native/own policy or scalar mismatch")
            chips = capture["score"]["metrics"]["exact_exploitability_chips"]
            support = capture["support"]
            row: dict[str, Any] = dict(
                path_index=path_index,
                game=game,
                seed=seed,
                arm=arm,
                work_label=work,
                readout=readout,
                policy_sha256=capture["receipt"]["policy_sha256"],
                actual_node_work=meta["total_work"],
                overshoot=meta["overshoot"],
                exploitability_chips=chips,
                exploitability_fraction_initial_pot=chips
                / (324 if game == GAMES[0] else 36),
                information_rows=capture["information_rows"],
                trainable_table_bytes=(4 if control else 2)
                * 8
                * capture["information_rows"]
                * capture["padded_width"],
                whole_coverage=None
                if support is None
                else support["whole"]["all"]["uniform_reach_fraction"],
                post_initial_coverage=None
                if support is None
                else support["post_warm"]["river"]["uniform_reach_fraction"],
                recall_violations=summary["recall_violations"],
                native_maximum_error_chips=audit["native"]["maximum_error_chips"],
                whole_path_seconds=timing["whole_path_seconds"],
                worker_peak_rss_bytes=timing["worker_peak_rss_bytes"],
                initial_only_river_rows=None
                if support is None
                else support["whole"]["river"]["positive_rows"]
                - support["post_warm"]["river"]["positive_rows"],
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
                fixed = {
                    i: dict(
                        identity=row_identity(exact, i),
                        saved_probabilities=expanded[
                            i, : len(exact.actions[i])
                        ].tolist(),
                        seats=[],
                    )
                    for i in ((*TOP_TURN, *TOP_RIVER) if game == GAMES[1] else ())
                }
                gains = []
                for acting_seat in (0, 1):
                    trace = trace_losses(
                        exact, expanded, acting_seat, tolerance=TOLERANCE
                    )
                    if trace.accounting_error > TOLERANCE:
                        raise ArithmeticError("reply-loss accounting failed")
                    contribution += trace.losses / 2
                    gains.append(trace.gain)
                    for info in fixed:
                        if fixed[info]["identity"]["seat"] == acting_seat:
                            fixed[info]["seats"].append(
                                dict(
                                    seat=acting_seat,
                                    counterfactual_reach=float(
                                        trace.counterfactual_mass[info]
                                    ),
                                    saved_prefix_reach=float(
                                        trace.saved_reach_mass[info]
                                    ),
                                    alternative_action_values_chips=trace.conditional_values[
                                        info, : len(exact.actions[info])
                                    ].tolist(),
                                    additive_contribution_chips=float(
                                        trace.losses[info] / 2
                                    ),
                                )
                            )
                if (
                    abs(math.fsum(gains) / 2 - chips) > TOLERANCE
                    or abs(float(contribution.sum()) - chips) > TOLERANCE
                ):
                    raise ArithmeticError("street contributions do not sum")
                row["turn_contribution_chips"] = float(
                    contribution[np.array(streets) == "TURN"].sum()
                )
                row["river_contribution_chips"] = float(
                    contribution[np.array(streets) == "RIVER"].sum()
                )
                row["fixed_turn_rows"] = {
                    str(info): dict(
                        **fixed[info], contribution_chips=float(contribution[info])
                    )
                    for info in (TOP_TURN if game == GAMES[1] else ())
                }
                row["fixed_river_rows"] = {
                    str(info): dict(
                        **fixed[info], contribution_chips=float(contribution[info])
                    )
                    for info in (TOP_RIVER if game == GAMES[1] else ())
                }
            cases.append(row)
    if len(cases) != 48 or len(candidate_audits) != 12:
        raise ArithmeticError("incomplete candidate/control report grid")
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "report.json",
        dict(
            status="completed",
            scope=plan["question"],
            head=head,
            cases=cases,
            primary=decision(cases),
            native_maximum_error_chips=max(
                candidate_native["maximum_error_chips"],
                control_native["maximum_error_chips"],
            ),
        ),
    )
