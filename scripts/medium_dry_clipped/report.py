"""Data-bound matched-rule strength report with fixed turn/river diagnostics."""

import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

from medium_dry_clipped.capture import replay_path
from medium_dry_clipped.gate import (
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
from medium_dry_clipped.learning import context
from medium_dry_clipped.study import save
from poker_ai.cards import format_card
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.training.no_limit import NoLimitState

TOP_TURN = (2443, 1596, 14)
READOUTS = ("current", "uniform_average", "linear_average")
TOLERANCE = 1e-9


def row_identity(tree: MatrixTree, info: int) -> dict[str, Any]:
    """Describe an exact decision using only acting-seat visible information."""
    state = tree.source.states[tree.source.representatives[info]]
    if state.dealer is None:
        raise ArithmeticError("exact decision lacks dealer state")
    observation = state.dealer.observe(state.actor)
    decoder = NoLimitState(state.dealer, tree.source.spot.rules)
    actions = []
    for action in tree.actions[info]:
        move = decoder.decode(action)
        actions.append(
            move.kind.value + ("" if move.amount is None else f" {move.amount}")
        )
    return dict(
        exact_info=info,
        seat=observation.seat,
        street="TURN" if len(observation.board) == 4 else "RIVER",
        hole=[format_card(card) for card in observation.hole_cards],
        board=[format_card(card) for card in observation.board],
        pot_chips=observation.pot,
        legal_actions=actions,
    )


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply frozen per-spot absolute and paired gates at final linear average."""
    final = [
        r
        for r in cases
        if r["work_label"] == WORK[-1] and r["readout"] == "linear_average"
    ]
    if len(final) != 12:
        raise ArithmeticError("12 fixed final scores required")
    by_game: dict[str, dict[str, Any]] = {}
    for game in GAMES:
        control = [
            r for r in final if r["game"] == game and r["arm"] == "signed_linear"
        ]
        candidate = [
            r for r in final if r["game"] == game and r["arm"] == "clipped_linear"
        ]
        if (
            len(control) != 3
            or [r["seed"] for r in control] != list(SEEDS)
            or [r["seed"] for r in candidate] != list(SEEDS)
        ):
            raise ArithmeticError("fixed paired seed grid changed")
        pairs = [
            c["exploitability_fraction_initial_pot"]
            - b["exploitability_fraction_initial_pot"]
            for b, c in zip(control, candidate, strict=True)
        ]
        values = [r["exploitability_fraction_initial_pot"] for r in candidate]
        passed = (
            median(values) <= 0.01
            and max(values) <= 0.025
            and all(
                r["whole_coverage"] is not None and r["whole_coverage"] >= 0.95
                for r in candidate
            )
            and all(r["recall_violations"] == 0 for r in candidate)
        )
        by_game[game] = dict(
            candidate_by_seed=values,
            control_by_seed=[r["exploitability_fraction_initial_pot"] for r in control],
            candidate_median=median(values),
            candidate_worst=max(values),
            absolute_pass=passed,
            paired_seed_differences=pairs,
            paired_median=median(pairs),
        )
    medium = by_game["new_medium_dry_oop"]
    low = by_game["new_low_wet_ip"]
    classification = (
        "positive"
        if medium["absolute_pass"]
        and low["absolute_pass"]
        and medium["paired_median"] <= -0.001
        and low["paired_median"] <= 0.001
        else "negative"
        if not medium["absolute_pass"]
        or not low["absolute_pass"]
        or medium["paired_median"] >= 0.001
        or low["paired_median"] > 0.001
        else "inconclusive"
    )
    return dict(classification=classification, by_game=by_game)


def report(root: Path, output: Path) -> None:
    """Recompute all scores and fixed decision losses after own/native publication."""
    plan = fixed_contract(root)
    head = clean_head(root)
    require_stage(root, SOURCE, "source_qualified")
    require_stage(root, OWN, "own_published")
    require_stage(root, NATIVE, "native_audited")
    native = json.loads((root / NATIVE / "result.json").read_bytes())
    if native["status"] != "completed" or len(native["rows"]) != 108:
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
    if len(path_rows) != 12 or len(timing) != 12:
        raise ArithmeticError("missing whole-path time or memory")
    cases: list[dict[str, Any]] = []
    for index, game, seed, arm in paths():
        scoring = context(root, game, arm)
        if not isinstance(scoring.exact, MatrixTree):
            raise ArithmeticError("fixed exact tree required")
        exact = scoring.exact
        streets = [row_identity(exact, i)["street"] for i in range(len(exact.keys))]
        folder = root / OWN / "study" / f"path{index:02d}"
        summary = replay_path(scoring, folder)
        if summary["path"] != dict(
            index=index, game=game, seed=seed, arm=arm
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
                / (324 if game == "new_low_wet_ip" else 36),
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
                    for i in (TOP_TURN if game == "new_medium_dry_oop" else ())
                }
                gains = []
                for seat in (0, 1):
                    trace = trace_losses(exact, expanded, seat, tolerance=TOLERANCE)
                    if trace.accounting_error > TOLERANCE:
                        raise ArithmeticError("reply-loss accounting failed")
                    contribution += trace.losses / 2
                    gains.append(trace.gain)
                    for i in selected:
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
                    for i in (TOP_TURN if game == "new_medium_dry_oop" else ())
                }
            cases.append(row)
    if len(cases) != 108 or len(native_rows) != 108:
        raise ArithmeticError("incomplete clipped-regret report grid")
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
