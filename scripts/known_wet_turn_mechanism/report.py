"""Fixed known-case paired strength and control-ranked decision report."""

import json
import math
from pathlib import Path
from typing import Any

from medium_dry_b8.report import row_identity
from study_known_wet_turn_mechanism import save
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.report import trace

from known_wet_turn_mechanism.gate import (
    NATIVE,
    OWN,
    SOURCE,
    clean_revision,
    require_archive,
    source_fingerprint,
)
from known_wet_turn_mechanism.plan import (
    CANDIDATE,
    CONTROL,
    GAME,
    LABELS,
    PROTOCOL,
    READOUTS,
    SPOT,
    context,
    contract,
    paths,
)
from poker_ai.postflop.matrix import MatrixTree

TOLERANCE = 1e-9


def absolute(row: dict[str, Any]) -> bool:
    """Use unchanged one-path 0.01/0.025-pot, coverage and recall gates."""
    value = row["exploitability_fraction_initial_pot"]
    return bool(
        value <= 0.01
        and value <= 0.025
        and row["whole_coverage"] is not None
        and row["whole_coverage"] >= 0.95
        and row["recall_violations"] == 0
    )


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify the fixed final deterministic pair without seed inference."""
    final = [
        row
        for row in cases
        if row["work_label"] == LABELS[-1] and row["readout"] == "linear_average"
    ]
    if len(final) != 2 or {row["arm"] for row in final} != {CONTROL, CANDIDATE}:
        raise ArithmeticError("two fixed final policies required")
    by_arm = {row["arm"]: row for row in final}
    control, candidate = by_arm[CONTROL], by_arm[CANDIDATE]
    if any(row["game"] != GAME or row["seed"] != 0 for row in final):
        raise ArithmeticError("known-case identity changed")
    delta = (
        candidate["exploitability_fraction_initial_pot"]
        - control["exploitability_fraction_initial_pot"]
    )
    passed = absolute(candidate)
    return dict(
        classification="positive"
        if passed and delta <= -0.001
        else "negative"
        if not passed or delta > 0.001
        else "inconclusive",
        control=control["exploitability_fraction_initial_pot"],
        candidate=candidate["exploitability_fraction_initial_pot"],
        candidate_minus_control=delta,
        control_absolute_pass=absolute(control),
        candidate_absolute_pass=passed,
    )


def timing(record: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Bind both fixed path wall times and peak worker memory."""
    if (
        record.get("status") != "completed"
        or record.get("stage") != "study"
        or record.get("assignments") != [[0], [1]]
    ):
        raise ArithmeticError("complete fixed own pair required")
    rows = [
        item
        for worker in record["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    result = {row["index"]: row for row in rows}
    if len(rows) != 2 or len(result) != 2:
        raise ArithmeticError("missing fixed pair timing")
    for spec in paths():
        row = result[spec.index]
        expected = dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
        if (
            row["path"] != expected
            or row["repeat"] != 0
            or row["captures"] != 6
            or row["final_work"] < LABELS[-1]
            or not math.isfinite(row["whole_path_seconds"])
            or row["whole_path_seconds"] <= 0
            or row["worker_peak_rss_bytes"] <= 0
        ):
            raise ArithmeticError("own timing or path identity changed")
    return result


def paired_contrasts(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Report both saved readouts at every fixed matched-work crossing."""
    contrasts = []
    for work in LABELS:
        for readout in READOUTS:
            pair = [
                row
                for row in cases
                if row["work_label"] == work and row["readout"] == readout
            ]
            if len(pair) != 2 or {row["arm"] for row in pair} != {CONTROL, CANDIDATE}:
                raise ArithmeticError("fixed checkpoint pair changed")
            selected = {row["arm"]: row for row in pair}
            a, b = (
                selected[CONTROL]["exploitability_fraction_initial_pot"],
                selected[CANDIDATE]["exploitability_fraction_initial_pot"],
            )
            contrasts.append(
                dict(
                    work_label=work,
                    readout=readout,
                    seed=0,
                    control=a,
                    candidate=b,
                    candidate_minus_control=b - a,
                )
            )
    return contrasts


def report(root: Path, output: Path) -> None:
    """Build fixed report only from published own and independent audit bytes."""
    contract(root)
    head = clean_revision(root)
    source = source_fingerprint(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
    ):
        require_archive(root, root / stage, status, source)
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    if native["status"] != "completed" or len(native["rows"]) != 12:
        raise ArithmeticError("complete 12-policy independent audit required")
    audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in native["rows"]
    }
    if len(audits) != 12:
        raise ArithmeticError("duplicate independent audit case")
    own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
    resources = timing(own)
    pot = json.loads((root / SPOT).read_bytes())["pot"]
    if pot != 36:
        raise ArithmeticError("registered initial pot changed")
    cases: list[dict[str, Any]] = []
    traced: dict[tuple[int, int, str], dict[str, Any]] = {}
    for spec in paths():
        scoring = context(root, GAME, spec.arm)
        folder = root / OWN / "study" / f"path{spec.index:02d}"
        summary = replay_path(scoring, folder)
        expected = dict(index=spec.index, game=GAME, arm=spec.arm, seed=0)
        if (
            summary["path"] != expected
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 6
        ):
            raise ArithmeticError("fixed own path changed")
        tree = scoring.exact
        if not isinstance(tree, MatrixTree):
            raise ArithmeticError("exact tree required")
        streets = [row_identity(tree, i)["street"] for i in range(len(tree.keys))]
        for capture in summary["captures"]:
            meta = capture["metadata"]
            work, readout = meta["work_label"], meta["readout"]
            if work not in LABELS or readout not in READOUTS:
                raise ArithmeticError("unregistered checkpoint or readout")
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
                game=GAME,
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
            cases.append(case)
            detail = trace(scoring, folder, capture)
            traced[(spec.index, work, readout)] = detail
            for street in ("TURN", "RIVER"):
                case[f"{street.lower()}_contribution_chips"] = math.fsum(
                    float(detail["contribution"][i])
                    for i, label in enumerate(streets)
                    if label == street
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
    if len(cases) != 12 or len(traced) != 12:
        raise ArithmeticError("fixed own comparison grid incomplete")
    contrasts = paired_contrasts(cases)
    scoring = context(root, GAME, CONTROL)
    tree = scoring.exact
    if not isinstance(tree, MatrixTree):
        raise ArithmeticError("exact decision tree required")
    identities = [row_identity(tree, i) for i in range(len(tree.keys))]
    contribution = traced[(0, LABELS[-1], "linear_average")]["contribution"]
    control_partition = scoring.partition
    if not isinstance(control_partition, MatrixTree):
        raise ArithmeticError("control partition must be a matrix tree")
    groups: dict[int, list[int]] = {}
    for info, identity in enumerate(identities):
        if identity["street"] == "TURN":
            groups.setdefault(
                int(control_partition.exact_to_abstract[info]), []
            ).append(info)
    collided_infos = {
        info for members in groups.values() if len(members) > 1 for info in members
    }
    if (
        len(collided_infos) != 12
        or sum(len(members) > 1 for members in groups.values()) != 6
    ):
        raise ArithmeticError("frozen known-wet turn collision inventory changed")
    selected_infos: set[int] = set()
    ranked: dict[str, list[int]] = {}
    for street in ("TURN", "RIVER"):
        ranked[street] = sorted(
            (
                i
                for i, identity in enumerate(identities)
                if identity["street"] == street
            ),
            key=lambda i: (-float(contribution[i]), i),
        )[:3]
        if len(ranked[street]) != 3:
            raise ArithmeticError("fewer than three decision nodes on street")
        selected_infos.update(ranked[street])
    ranked_collided = sorted(
        collided_infos, key=lambda i: (-float(contribution[i]), i)
    )[:3]
    selected_infos.update(ranked_collided)
    diagnostics = []
    for info in sorted(selected_infos):
        identity = identities[info]
        owner = identity["seat"]
        observations = []
        for spec in paths():
            for work in LABELS:
                for readout in READOUTS:
                    detail = traced[(spec.index, work, readout)]
                    seat = detail["traces"][owner]
                    count = len(identity["legal_actions"])
                    observations.append(
                        dict(
                            arm=spec.arm,
                            seed=0,
                            work_label=work,
                            readout=readout,
                            saved_probabilities=detail["expanded"][
                                info, :count
                            ].tolist(),
                            counterfactual_reach=float(seat.counterfactual_mass[info]),
                            saved_prefix_reach=float(seat.saved_reach_mass[info]),
                            alternative_action_values_chips=seat.conditional_values[
                                info, :count
                            ].tolist(),
                            additive_contribution_chips=float(seat.losses[info] / 2),
                        )
                    )
        diagnostics.append(
            dict(
                **identity,
                control_collided_turn_rank=(
                    ranked_collided.index(info) + 1 if info in ranked_collided else None
                ),
                control_rank_within_street=(
                    ranked[identity["street"]].index(info) + 1
                    if info in ranked[identity["street"]]
                    else None
                ),
                control_rank_contribution_chips=float(contribution[info]),
                observations=observations,
            )
        )
    output.mkdir(parents=True, exist_ok=False)
    started: dict[str, Any] = json.loads((root / OWN / "started.json").read_bytes())
    save(
        output / "report.json",
        dict(
            status="completed",
            scope="one structurally inspected known medium/wet finite game",
            protocol=PROTOCOL.as_posix(),
            head=head,
            source_fingerprint=source,
            runtime=started["runtime"],
            study_seconds=own["seconds"],
            cases=cases,
            checkpoint_contrasts=contrasts,
            primary=decision(cases),
            diagnostics=diagnostics,
            native_maximum_error_chips=max(
                row["native_maximum_error_chips"] for row in cases
            ),
            uncertainty=(
                "one deterministic seed per arm; no seed-based confidence "
                "interval or unseen generalization"
            ),
            decision_assumptions=(
                "fixed saved opponent policy and optimized reply continuation; "
                "local values are not universal poker advice"
            ),
        ),
    )
