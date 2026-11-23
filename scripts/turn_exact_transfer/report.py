"""Fixed paired full-work strength report and control-ranked decision traces."""

import json
import math
from pathlib import Path
from typing import Any

from medium_dry_b8.report import row_identity
from study_turn_exact_transfer import save

from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import trace_losses
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.gate import (
    NATIVE,
    OWN,
    SOURCE,
    clean_revision,
    require_archive,
    require_inventory,
    source_fingerprint,
)
from turn_exact_transfer.learning import (
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    READOUTS,
    context,
    contract,
    paths,
)

TOLERANCE = 1e-9
THRESHOLD = 0.001


def absolute(row: dict[str, Any]) -> bool:
    """Apply the unchanged 0.01/0.025-pot, coverage and recall rules."""
    value = row["exploitability_fraction_initial_pot"]
    return bool(
        value <= 0.01
        and value <= 0.025
        and row["whole_coverage"] is not None
        and row["whole_coverage"] >= 0.95
        and row["recall_violations"] == 0
    )


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify only the prospectively fixed four deterministic spot pairs."""
    final = [
        row
        for row in cases
        if row["work_label"] == LABELS[-1] and row["readout"] == "linear_average"
    ]
    if len(final) != 8:
        raise ArithmeticError("eight fixed final policies required")
    by_game: dict[str, dict[str, Any]] = {}
    for game in GAMES:
        controls = [
            row for row in final if row["game"] == game and row["arm"] == CONTROL
        ]
        candidates = [
            row for row in final if row["game"] == game and row["arm"] == CANDIDATE
        ]
        if (
            len(controls) != 1
            or len(candidates) != 1
            or any(row["seed"] != 0 for row in controls + candidates)
        ):
            raise ArithmeticError("fixed paired full-work grid changed")
        control, candidate = controls[0], candidates[0]
        delta = (
            candidate["exploitability_fraction_initial_pot"]
            - control["exploitability_fraction_initial_pot"]
        )
        by_game[game] = dict(
            known_mechanistic=game == GAMES[0],
            control=control["exploitability_fraction_initial_pot"],
            candidate=candidate["exploitability_fraction_initial_pot"],
            candidate_minus_control=delta,
            control_absolute_pass=absolute(control),
            candidate_absolute_pass=absolute(candidate),
        )
    known, medium_dry, medium_wet, low_wet = (by_game[game] for game in GAMES)
    new = (medium_dry, medium_wet, low_wet)
    positive = (
        all(row["candidate_absolute_pass"] for row in new)
        and known["candidate_minus_control"] <= -THRESHOLD
        and any(
            row["candidate_minus_control"] <= -THRESHOLD
            for row in (medium_dry, medium_wet)
        )
        and all(
            row["candidate_minus_control"] <= THRESHOLD
            for row in (medium_dry, medium_wet)
        )
        and low_wet["candidate_minus_control"] <= THRESHOLD
    )
    negative = any(not row["candidate_absolute_pass"] for row in new) or any(
        row["candidate_minus_control"] > THRESHOLD for row in by_game.values()
    )
    return dict(
        classification="positive"
        if positive
        else "negative"
        if negative
        else "inconclusive",
        by_game=by_game,
    )


def checkpoint_contrasts(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep every deterministic paired difference at all fixed work labels."""
    result = []
    for game in GAMES:
        for work in LABELS:
            selected = [
                row
                for row in cases
                if row["game"] == game
                and row["work_label"] == work
                and row["readout"] == "linear_average"
            ]
            controls = [row for row in selected if row["arm"] == CONTROL]
            candidates = [row for row in selected if row["arm"] == CANDIDATE]
            if len(selected) != 2 or len(controls) != 1 or len(candidates) != 1:
                raise ArithmeticError("fixed checkpoint pair changed")
            control = controls[0]["exploitability_fraction_initial_pot"]
            candidate = candidates[0]["exploitability_fraction_initial_pot"]
            result.append(
                dict(
                    game=game,
                    work_label=work,
                    seed=0,
                    control=control,
                    candidate=candidate,
                    candidate_minus_control=candidate - control,
                )
            )
    return result


def timing(record: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Bind all eight fixed whole-path wall and peak-memory records."""
    if (
        record.get("status") != "completed"
        or record.get("stage") != "study"
        or record.get("assignments") != [list(range(i, 8, 3)) for i in range(3)]
    ):
        raise ArithmeticError("complete fixed own study required")
    rows = [
        item
        for worker in record["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    result = {row["index"]: row for row in rows}
    if len(rows) != 8 or len(result) != 8:
        raise ArithmeticError("missing fixed path timing")
    for spec in paths():
        row = result[spec.index]
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm, seed=spec.seed)
        if (
            row["path"] != expected
            or row["repeat"] != 0
            or row["captures"] != 6
            or row["final_work"] < LABELS[-1]
            or not math.isfinite(row["whole_path_seconds"])
            or row["whole_path_seconds"] <= 0
            or row["worker_peak_rss_bytes"] <= 0
        ):
            raise ArithmeticError("own path timing or identity changed")
    return result


def trace(scoring: Any, folder: Path, capture: dict[str, Any]) -> dict[str, Any]:
    """Tie additive best-reply gains to own policy, never to reference output."""
    tree = scoring.exact
    if not isinstance(tree, MatrixTree):
        raise ArithmeticError("exact finite tree required")
    policy = read_snapshot(
        folder / capture["file"],
        scoring.partition,
        capture["receipt"],
        capture["metadata"],
    )
    expanded = scoring.expand(policy)
    traces = [
        trace_losses(tree, expanded, seat, tolerance=TOLERANCE) for seat in (0, 1)
    ]
    chips = capture["score"]["metrics"]["exact_exploitability_chips"]
    contribution = (traces[0].losses + traces[1].losses) / 2
    if (
        any(item.accounting_error > TOLERANCE for item in traces)
        or abs(math.fsum(item.gain for item in traces) / 2 - chips) > TOLERANCE
        or abs(float(contribution.sum()) - chips) > TOLERANCE
    ):
        raise ArithmeticError("saved best-reply contribution identity failed")
    return dict(expanded=expanded, traces=traces, contribution=contribution)


def report(root: Path, output: Path) -> None:
    """Build the fixed result from complete published own/native bytes."""
    plan, _ = contract(root)
    head = clean_revision(root)
    source = source_fingerprint(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
    ):
        require_archive(root, root / stage, status, source)
    inventory = require_inventory(root, source)
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    if native["status"] != "completed" or len(native["rows"]) != 48:
        raise ArithmeticError("complete independent 48-policy audit required")
    audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in native["rows"]
    }
    if len(audits) != 48:
        raise ArithmeticError("duplicate independent audit case")
    own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
    resources = timing(own)
    cases: list[dict[str, Any]] = []
    traced: dict[tuple[int, int], dict[str, Any]] = {}
    for spec in paths():
        scoring = context(root, spec.game, spec.arm)
        folder = root / OWN / "study" / f"path{spec.index:02d}"
        summary = replay_path(scoring, folder)
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
        if (
            summary["path"] != expected
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 6
        ):
            raise ArithmeticError("fixed own path changed")
        spot = (
            root / "configs/river-full-broader-spots/full_new_medium_dry_oop.json"
            if spec.game == GAMES[0]
            else root / f"configs/turn-exact-transfer-spots/{spec.game}.json"
        )
        pot = json.loads(spot.read_bytes())["pot"]
        if not isinstance(pot, (int, float)) or pot <= 0:
            raise ArithmeticError("initial pot invalid")
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
                raise ArithmeticError("independent scalar/policy mismatch")
            score = capture["score"]["metrics"]["exact_exploitability_chips"]
            support = capture["support"]
            case = dict(
                path_index=spec.index,
                game=spec.game,
                known_mechanistic=spec.game == GAMES[0],
                seed=0,
                arm=spec.arm,
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
                exact_information_rows=len(scoring.exact.keys),
                information_rows=capture["information_rows"],
                table_bytes=2
                * 8
                * capture["information_rows"]
                * capture["padded_width"],
                whole_path_seconds=resources[spec.index]["whole_path_seconds"],
                worker_peak_rss_bytes=resources[spec.index]["worker_peak_rss_bytes"],
                native_maximum_error_chips=audit["native"]["maximum_error_chips"],
            )
            cases.append(case)
            if readout == "linear_average":
                detail = trace(scoring, folder, capture)
                traced[(spec.index, work)] = detail
                exact = scoring.exact
                if not isinstance(exact, MatrixTree):
                    raise ArithmeticError("exact street tree required")
                street = [
                    row_identity(exact, i)["street"] for i in range(len(exact.keys))
                ]
                case["turn_contribution_chips"] = math.fsum(
                    float(detail["contribution"][i])
                    for i, label in enumerate(street)
                    if label == "TURN"
                )
                case["river_contribution_chips"] = math.fsum(
                    float(detail["contribution"][i])
                    for i, label in enumerate(street)
                    if label == "RIVER"
                )
                if (
                    abs(
                        case["turn_contribution_chips"]
                        + case["river_contribution_chips"]
                        - score
                    )
                    > TOLERANCE
                ):
                    raise ArithmeticError("street contributions do not sum")
    if len(cases) != 48 or len(traced) != 24:
        raise ArithmeticError("fixed own comparison grid incomplete")
    primary = decision(cases)
    diagnostics = []
    for game in GAMES:
        scoring = context(root, game, CONTROL)
        tree = scoring.exact
        if not isinstance(tree, MatrixTree):
            raise ArithmeticError("exact decision tree required")
        identities = [row_identity(tree, i) for i in range(len(tree.keys))]
        control_spec = next(
            spec for spec in paths() if spec.game == game and spec.arm == CONTROL
        )
        rank_contribution = traced[(control_spec.index, LABELS[-1])]["contribution"]
        selected = {
            street: sorted(
                (
                    i
                    for i, identity in enumerate(identities)
                    if identity["street"] == street
                ),
                key=lambda i: (-float(rank_contribution[i]), i),
            )[:3]
            for street in ("TURN", "RIVER")
        }
        for _street, infos in selected.items():
            if len(infos) != 3:
                raise ArithmeticError("fewer than three decision nodes on street")
            for rank, info in enumerate(infos, start=1):
                identity = identities[info]
                owner = identity["seat"]
                observations = []
                for spec in paths():
                    if spec.game != game:
                        continue
                    for work in LABELS:
                        detail = traced[(spec.index, work)]
                        seat = detail["traces"][owner]
                        count = len(identity["legal_actions"])
                        observations.append(
                            dict(
                                arm=spec.arm,
                                seed=0,
                                work_label=work,
                                saved_probabilities=detail["expanded"][
                                    info, :count
                                ].tolist(),
                                counterfactual_reach=float(
                                    seat.counterfactual_mass[info]
                                ),
                                saved_prefix_reach=float(seat.saved_reach_mass[info]),
                                alternative_action_values_chips=seat.conditional_values[
                                    info, :count
                                ].tolist(),
                                additive_contribution_chips=float(
                                    seat.losses[info] / 2
                                ),
                            )
                        )
                diagnostics.append(
                    dict(
                        **identity,
                        rank_within_street=rank,
                        control_rank_contribution_chips=float(rank_contribution[info]),
                        observations=observations,
                    )
                )
    output.mkdir(parents=True, exist_ok=False)
    started: dict[str, Any] = json.loads((root / OWN / "started.json").read_bytes())
    save(
        output / "report.json",
        dict(
            status="completed",
            scope=(
                "one known mechanistic and three new card/range inputs "
                "on known templates"
            ),
            protocol=plan["issue"],
            head=head,
            source_fingerprint=source,
            runtime=started["runtime"],
            study_seconds=own["seconds"],
            cases=cases,
            checkpoint_contrasts=checkpoint_contrasts(cases),
            primary=primary,
            inventory=inventory["spots"],
            diagnostics=diagnostics,
            native_maximum_error_chips=max(
                row["native_maximum_error_chips"] for row in cases
            ),
            uncertainty=(
                "one deterministic seed per arm; paired spot contrasts are dependent "
                "and not a seed-based confidence interval"
            ),
            decision_assumptions=(
                "fixed saved opponent policy and optimized reply continuation; "
                "local values are not universal poker advice"
            ),
        ),
    )
