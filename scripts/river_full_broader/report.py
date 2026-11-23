"""Fixed own-versus-own strength report and control-ranked decision traces."""

import json
import math
from pathlib import Path
from statistics import median
from typing import Any

from medium_dry_b8.report import row_identity
from medium_dry_full.capture import replay_path as full_replay
from study_river_full_broader import save

from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import trace_losses
from river_full_broader.control_capture import replay_path as control_replay
from river_full_broader.gate import (
    NATIVE,
    OWN,
    SOURCE,
    clean_revision,
    require_archive,
    source_fingerprint,
)
from river_full_broader.learning import (
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    READOUTS,
    SEEDS,
    context,
    contract,
    paths,
)

TOLERANCE = 1e-9


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply exactly the two-stratum prospective final linear-average rule."""
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
            len(controls) != 3
            or [row["seed"] for row in controls] != list(SEEDS)
            or len(candidates) != 1
            or candidates[0]["seed"] != 0
        ):
            raise ArithmeticError("fixed B4/full comparison grid changed")
        candidate = candidates[0]
        score = candidate["exploitability_fraction_initial_pot"]
        values = [row["exploitability_fraction_initial_pot"] for row in controls]
        contrasts = [score - value for value in values]
        passed = (
            score <= 0.01
            and score <= 0.025
            and candidate["whole_coverage"] is not None
            and candidate["whole_coverage"] >= 0.95
            and candidate["recall_violations"] == 0
        )
        by_game[game] = dict(
            candidate=score,
            control_by_seed=values,
            control_median=median(values),
            control_worst=max(values),
            candidate_minus_each_control=contrasts,
            contrast_median=median(contrasts),
            absolute_pass=passed,
            control_absolute_pass_by_seed=[
                row["exploitability_fraction_initial_pot"] <= 0.01
                and row["exploitability_fraction_initial_pot"] <= 0.025
                and row["whole_coverage"] is not None
                and row["whole_coverage"] >= 0.95
                and row["recall_violations"] == 0
                for row in controls
            ],
        )
    medium, low = (by_game[game] for game in GAMES)
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


def checkpoint_contrasts(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retain every dependent paired contrast at each prespecified work label."""
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
            if (
                len(selected) != 4
                or len(controls) != 3
                or [row["seed"] for row in controls] != list(SEEDS)
                or len(candidates) != 1
            ):
                raise ArithmeticError("fixed checkpoint contrast grid changed")
            candidate = candidates[0]["exploitability_fraction_initial_pot"]
            values = [row["exploitability_fraction_initial_pot"] for row in controls]
            contrasts = [candidate - value for value in values]
            result.append(
                dict(
                    game=game,
                    work_label=work,
                    candidate=candidate,
                    control_by_seed=values,
                    candidate_minus_each_control=contrasts,
                    contrast_median=median(contrasts),
                )
            )
    return result


def timing(record: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Bind all eight serial whole-path wall and peak-memory records."""
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
        raise ArithmeticError("missing fixed whole-path timing")
    for spec in paths():
        row = result[spec.index]
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm)
        if spec.arm == CONTROL:
            expected["seed"] = spec.seed
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


def _trace(scoring: Any, folder: Path, capture: dict[str, Any]) -> dict[str, Any]:
    """Tie additive best-reply gains to one saved own policy, never to reference."""
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
        any(trace.accounting_error > TOLERANCE for trace in traces)
        or abs(math.fsum(trace.gain for trace in traces) / 2 - chips) > TOLERANCE
        or abs(float(contribution.sum()) - chips) > TOLERANCE
    ):
        raise ArithmeticError("saved best-reply contribution identity failed")
    return dict(expanded=expanded, traces=traces, contribution=contribution)


def report(root: Path, output: Path) -> None:
    """Rebuild all fixed metrics and decisions from published own/native bytes."""
    plan = contract(root)
    head = clean_revision(root)
    source = source_fingerprint(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
    ):
        require_archive(root, root / stage, status, source)
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    if native["status"] != "completed" or len(native["rows"]) != 48:
        raise ArithmeticError("complete independent 48-policy audit required")
    audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in native["rows"]
    }
    if len(audits) != 48:
        raise ArithmeticError("duplicate independent audit case")
    resources = timing(json.loads((root / OWN / "result.json").read_bytes()))
    cases: list[dict[str, Any]] = []
    traced: dict[tuple[int, int], dict[str, Any]] = {}
    for spec in paths():
        scoring = context(root, spec.game)
        folder = root / OWN / "study" / f"path{spec.index:02d}"
        replay = full_replay if spec.arm == CANDIDATE else control_replay
        summary = replay(scoring, folder)
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm)
        if spec.arm == CONTROL:
            expected["seed"] = spec.seed
        if (
            summary["path"] != expected
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 6
        ):
            raise ArithmeticError("fixed own path changed")
        pot = json.loads(
            (root / f"configs/river-full-broader-spots/{spec.game}.json").read_bytes()
        )["pot"]
        if not isinstance(pot, (int, float)) or pot <= 0:
            raise ArithmeticError("initial pot invalid")
        for capture in summary["captures"]:
            meta = capture["metadata"]
            work, readout = meta["work_label"], meta["readout"]
            if work not in LABELS or readout not in READOUTS:
                raise ArithmeticError("unregistered work or readout")
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
                seed=spec.seed,
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
                initial_only_river_rows=None
                if support is None
                else support["whole"]["river"]["positive_rows"]
                - support["post_warm"]["river"]["positive_rows"],
                recall_violations=summary["recall_violations"],
                information_rows=capture["information_rows"],
                table_bytes=(2 if spec.arm == CANDIDATE else 4)
                * 8
                * capture["information_rows"]
                * capture["padded_width"],
                whole_path_seconds=resources[spec.index]["whole_path_seconds"],
                worker_peak_rss_bytes=resources[spec.index]["worker_peak_rss_bytes"],
                native_maximum_error_chips=audit["native"]["maximum_error_chips"],
            )
            cases.append(case)
            if readout == "linear_average":
                trace = _trace(scoring, folder, capture)
                traced[(spec.index, work)] = trace
                exact = scoring.exact
                if not isinstance(exact, MatrixTree):
                    raise ArithmeticError("exact street tree required")
                street = [
                    row_identity(exact, i)["street"] for i in range(len(exact.keys))
                ]
                case["turn_contribution_chips"] = math.fsum(
                    float(trace["contribution"][i])
                    for i, label in enumerate(street)
                    if label == "TURN"
                )
                case["river_contribution_chips"] = math.fsum(
                    float(trace["contribution"][i])
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
        scoring = context(root, game)
        tree = scoring.exact
        if not isinstance(tree, MatrixTree):
            raise ArithmeticError("exact decision tree required")
        identities = [row_identity(tree, i) for i in range(len(tree.keys))]
        control_scores = [
            (row["exploitability_fraction_initial_pot"], row["seed"], row["path_index"])
            for row in cases
            if row["game"] == game
            and row["arm"] == CONTROL
            and row["work_label"] == LABELS[-1]
            and row["readout"] == "linear_average"
        ]
        if len(control_scores) != 3:
            raise ArithmeticError("control-only diagnostic ranking grid changed")
        median_control = sorted(control_scores)[1]
        rank_contribution = traced[(median_control[2], LABELS[-1])]["contribution"]
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
                        trace = traced[(spec.index, work)]
                        seat = trace["traces"][owner]
                        count = len(identity["legal_actions"])
                        observations.append(
                            dict(
                                arm=spec.arm,
                                seed=spec.seed,
                                work_label=work,
                                saved_probabilities=trace["expanded"][
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
                        control_median_seed=median_control[1],
                        control_rank_contribution_chips=float(rank_contribution[info]),
                        observations=observations,
                    )
                )
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "report.json",
        dict(
            status="completed",
            scope="two new card/range inputs on known templates",
            protocol=plan["issue"],
            head=head,
            source_fingerprint=source,
            cases=cases,
            checkpoint_contrasts=checkpoint_contrasts(cases),
            primary=primary,
            diagnostics=diagnostics,
            native_maximum_error_chips=max(
                row["native_maximum_error_chips"] for row in cases
            ),
            decision_assumptions=(
                "fixed saved opponent policy and optimal reply continuation; "
                "local values are not universal poker advice"
            ),
        ),
    )
