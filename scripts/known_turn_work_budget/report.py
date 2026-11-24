"""Fixed two-known-game matched-work scores and exact decision traces."""

import json
import math
from pathlib import Path
from typing import Any

from medium_dry_b8.report import row_identity
from study_known_turn_work_budget import save
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.report import trace

from known_turn_work_budget.gate import (
    NATIVE,
    OWN,
    SOURCE,
    clean_revision,
    require_archive,
    source_fingerprint,
)
from known_turn_work_budget.plan import (
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    READOUTS,
    context,
    contract,
    paths,
)
from poker_ai.postflop.matrix import MatrixTree

TOLERANCE = 1e-9


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the published known-game rule without a seed-based inference."""
    final = [
        row
        for row in cases
        if row["work_label"] == LABELS[-1] and row["readout"] == "linear_average"
    ]
    if len(final) != 4:
        raise ArithmeticError("four fixed final policies required")
    by_game: dict[str, dict[str, Any]] = {}
    for game in GAMES:
        selected = {
            row["arm"]: row for row in final if row["game"] == game and row["seed"] == 0
        }
        if (
            set(selected) != {CONTROL, CANDIDATE}
            or len([row for row in final if row["game"] == game]) != 2
        ):
            raise ArithmeticError("fixed known-game pair changed")
        control, candidate = selected[CONTROL], selected[CANDIDATE]
        value = candidate["exploitability_fraction_initial_pot"]
        coverage = candidate["whole_coverage"]
        absolute = (
            value <= 0.01
            and value <= 0.025
            and coverage is not None
            and coverage >= 0.95
            and candidate["recall_violations"] == 0
        )
        difference = value - control["exploitability_fraction_initial_pot"]
        by_game[game] = dict(
            control=control["exploitability_fraction_initial_pot"],
            candidate=value,
            candidate_minus_control=difference,
            candidate_absolute_pass=absolute,
            control_absolute_pass=control["exploitability_fraction_initial_pot"] <= 0.01
            and control["whole_coverage"] is not None
            and control["whole_coverage"] >= 0.95
            and control["recall_violations"] == 0,
        )
    wet = [
        row
        for row in cases
        if row["game"] == GAMES[0]
        and row["arm"] == CANDIDATE
        and row["readout"] == "linear_average"
    ]
    if len(wet) != 3 or {row["work_label"] for row in wet} != set(LABELS):
        raise ArithmeticError("wet budget trend grid changed")
    series = {
        row["work_label"]: row["exploitability_fraction_initial_pot"] for row in wet
    }
    trend = (
        series[LABELS[-1]] - series[LABELS[0]] <= -0.005
        and series[LABELS[-1]] - series[LABELS[1]] <= -0.001
    )
    positive = all(
        row["candidate_absolute_pass"] and row["candidate_minus_control"] <= -0.001
        for row in by_game.values()
    )
    return dict(
        classification="positive" if positive else "negative",
        by_game=by_game,
        wet_trend="continuing decline" if trend else "not established",
        wet_candidate_by_work=series,
    )


def paired(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep all twelve matched-work/readout contrasts at seed zero."""
    result = []
    for game in GAMES:
        for work in LABELS:
            for readout in READOUTS:
                selected = [
                    row
                    for row in cases
                    if (row["game"], row["work_label"], row["readout"])
                    == (game, work, readout)
                ]
                if (
                    len(selected) != 2
                    or {row["arm"] for row in selected} != {CONTROL, CANDIDATE}
                    or len({row["actual_node_work"] for row in selected}) != 1
                ):
                    raise ArithmeticError("matched charged work pair changed")
                by_arm = {row["arm"]: row for row in selected}
                a, b = (
                    by_arm[arm]["exploitability_fraction_initial_pot"]
                    for arm in (CONTROL, CANDIDATE)
                )
                result.append(
                    dict(
                        game=game,
                        work_label=work,
                        readout=readout,
                        actual_node_work=selected[0]["actual_node_work"],
                        seed=0,
                        control=a,
                        candidate=b,
                        candidate_minus_control=b - a,
                    )
                )
    return result


def timing(record: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Bind the complete four-path fixed worker grid and resources."""
    if (
        record.get("status") != "completed"
        or record.get("stage") != "study"
        or record.get("assignments") != [[0, 2], [1, 3]]
        or record.get("worker_count") != 2
        or not 0 < record.get("seconds", -1) < 7200
    ):
        raise ArithmeticError("complete capped fixed own grid required")
    rows = [
        item
        for worker in record["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    by_index = {row["index"]: row for row in rows}
    if len(rows) != 4 or set(by_index) != set(range(4)):
        raise ArithmeticError("four distinct path resource records required")
    for spec in paths():
        row = by_index[spec.index]
        if (
            row["path"] != dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
            or row["repeat"] != 0
            or row["captures"] != 6
            or row["final_work"] < LABELS[-1]
            or not 0 < row["whole_path_seconds"]
            or not 0 < row["worker_peak_rss_bytes"] <= 1_500_000_000
        ):
            raise ArithmeticError("fixed own path identity/resource changed")
    return by_index


def report(root: Path, output: Path) -> None:
    """Report all 24 published own/native cases and fixed decision rows."""
    plan = contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
    ):
        require_archive(root, root / stage, status, fingerprint)
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    if (
        native["status"] != "completed"
        or len(native["rows"]) != 24
        or native["maximum_error_chips"] > TOLERANCE
    ):
        raise ArithmeticError("complete 24-case native audit required")
    audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in native["rows"]
    }
    if len(audits) != 24:
        raise ArithmeticError("duplicate native case")
    own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
    resources = timing(own)
    cases: list[dict[str, Any]] = []
    traced: dict[tuple[int, int, str], dict[str, Any]] = {}
    identities: dict[str, list[dict[str, Any]]] = {}
    for spec in paths():
        scoring = context(root, spec.game, spec.arm)
        folder = root / OWN / "study" / f"path{spec.index:02d}"
        summary = replay_path(scoring, folder)
        if (
            summary["path"]
            != dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 6
        ):
            raise ArithmeticError("fixed saved path changed")
        tree = scoring.exact
        if not isinstance(tree, MatrixTree):
            raise ArithmeticError("exact decision tree required")
        if spec.game not in identities:
            identities[spec.game] = [
                row_identity(tree, i) for i in range(len(tree.keys))
            ]
        streets = [row["street"] for row in identities[spec.game]]
        pot = next(
            row["initial_pot_chips"]
            for row in plan["games"]
            if row["name"] == spec.game
        )
        for capture in summary["captures"]:
            meta = capture["metadata"]
            work, readout = meta["work_label"], meta["readout"]
            if work not in LABELS or readout not in READOUTS:
                raise ArithmeticError("unregistered work/readout")
            audit = audits[(spec.index, work, readout)]
            if (
                audit["own_policy_sha256"] != capture["receipt"]["policy_sha256"]
                or audit["native"]["maximum_error_chips"] > TOLERANCE
            ):
                raise ArithmeticError("native scalar/policy mismatch")
            score = capture["score"]["metrics"]["exact_exploitability_chips"]
            support = capture["support"]
            case = dict(
                path_index=spec.index,
                game=spec.game,
                arm=spec.arm,
                seed=0,
                work_label=work,
                readout=readout,
                policy_sha256=capture["receipt"]["policy_sha256"],
                actual_node_work=meta["total_work"],
                overshoot=meta["overshoot"],
                exploitability_chips=score,
                exploitability_fraction_initial_pot=score / pot,
                whole_coverage=None
                if support is None
                else support["whole"]["all"]["uniform_reach_fraction"],
                post_initial_river_coverage=None
                if support is None
                else support["post_warm"]["river"]["uniform_reach_fraction"],
                recall_violations=summary["recall_violations"],
                exact_information_rows=len(tree.keys),
                information_rows=capture["information_rows"],
                table_bytes=2
                * 8
                * capture["information_rows"]
                * capture["padded_width"],
                whole_path_seconds=resources[spec.index]["whole_path_seconds"],
                worker_peak_rss_bytes=resources[spec.index]["worker_peak_rss_bytes"],
                native_maximum_error_chips=audit["native"]["maximum_error_chips"],
            )
            detail = trace(scoring, folder, capture)
            traced[(spec.index, work, readout)] = detail
            case["turn_row_contributions_chips"] = [
                float(value) if label == "TURN" else 0.0
                for value, label in zip(detail["contribution"], streets, strict=True)
            ]
            case["river_row_contributions_chips"] = [
                float(value) if label == "RIVER" else 0.0
                for value, label in zip(detail["contribution"], streets, strict=True)
            ]
            case["turn_contribution_chips"] = math.fsum(
                case["turn_row_contributions_chips"]
            )
            case["river_contribution_chips"] = math.fsum(
                case["river_row_contributions_chips"]
            )
            if abs(
                case["turn_contribution_chips"]
                + case["river_contribution_chips"]
                - score
            ) > TOLERANCE or any(value < -1e-12 for value in detail["contribution"]):
                raise ArithmeticError("nonnegative additive row accounting failed")
            cases.append(case)
    if len(cases) != 24 or len(traced) != 24:
        raise ArithmeticError("fixed case grid incomplete")
    diagnostics = []
    for game in GAMES:
        identities_for_game = identities[game]
        control_index = next(
            spec.index for spec in paths() if spec.game == game and spec.arm == CONTROL
        )
        candidate_index = control_index + 1
        ranked: dict[str, list[int]] = {}
        selected: set[int] = set(
            next(
                row["fixed_decision_rows"]
                for row in plan["games"]
                if row["name"] == game
            )
        )
        for street in ("TURN", "RIVER"):
            vector = traced[(candidate_index, LABELS[-1], "linear_average")][
                "contribution"
            ]
            ranked[street] = sorted(
                (
                    i
                    for i, identity in enumerate(identities_for_game)
                    if identity["street"] == street
                ),
                key=lambda i: (-float(vector[i]), i),
            )[:10]
            if len(ranked[street]) != 10:
                raise ArithmeticError("fewer than ten exact rows on street")
            selected.update(ranked[street])
        for info in sorted(selected):
            identity = identities_for_game[info]
            owner = identity["seat"]
            observations = []
            for index in (control_index, candidate_index):
                for work in LABELS:
                    for readout in READOUTS:
                        detail = traced[(index, work, readout)]
                        seat = detail["traces"][owner]
                        width = len(identity["legal_actions"])
                        observations.append(
                            dict(
                                arm=paths()[index].arm,
                                seed=0,
                                work_label=work,
                                readout=readout,
                                saved_probabilities=detail["expanded"][
                                    info, :width
                                ].tolist(),
                                counterfactual_reach=float(
                                    seat.counterfactual_mass[info]
                                ),
                                saved_prefix_reach=float(seat.saved_reach_mass[info]),
                                alternative_action_values_chips=seat.conditional_values[
                                    info, :width
                                ].tolist(),
                                additive_contribution_chips=float(
                                    seat.losses[info] / 2
                                ),
                            )
                        )
            diagnostics.append(
                dict(
                    game=game,
                    **identity,
                    fixed_diagnosed=info
                    in next(
                        row["fixed_decision_rows"]
                        for row in plan["games"]
                        if row["name"] == game
                    ),
                    candidate_final_rank_within_street=ranked[identity["street"]].index(
                        info
                    )
                    + 1
                    if info in ranked[identity["street"]]
                    else None,
                    observations=observations,
                )
            )
    started: dict[str, Any] = json.loads((root / OWN / "started.json").read_bytes())
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "report.json",
        dict(
            status="completed",
            scope="two previously outcome-inspected known turn-start finite games",
            protocol="docs/known-turn-work-budget.md",
            head=head,
            source_fingerprint=fingerprint,
            runtime=started["runtime"],
            study_seconds=own["seconds"],
            cases=cases,
            checkpoint_contrasts=paired(cases),
            primary=decision(cases),
            diagnostics=diagnostics,
            native_maximum_error_chips=native["maximum_error_chips"],
            uncertainty=(
                "one deterministic seed per arm; no seed confidence interval, "
                "independence or unseen transfer claim"
            ),
            decision_assumptions=(
                "fixed saved opponent and optimized reply continuation; local "
                "values are not causal action swaps or universal poker advice"
            ),
        ),
    )
