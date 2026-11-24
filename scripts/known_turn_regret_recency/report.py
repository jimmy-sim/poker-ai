"""Fixed matched-work report from published candidate and control bytes."""

import json
import math
from pathlib import Path
from typing import Any

from medium_dry_b8.report import row_identity
from study_known_turn_regret_recency import save
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.report import trace

from known_turn_regret_recency.gate import (
    NATIVE,
    OWN,
    SOURCE,
    clean_head,
    historical_controls,
    require_archive,
    source_fingerprint,
)
from known_turn_regret_recency.plan import (
    ARM,
    GAMES,
    LABELS,
    READOUTS,
    context,
    contract,
    paths,
)
from poker_ai.postflop.matrix import MatrixTree

TOLERANCE = 1e-9
CONTROL = "signed_full_exact_turn_river"
ARCHIVES = ("known-wet-turn-mechanism", "known-turn-exact-mechanism")


def absolute(row: dict[str, Any]) -> bool:
    """Apply the unchanged two known-game absolute gates."""
    value = row["exploitability_fraction_initial_pot"]
    return bool(
        math.isfinite(value)
        and value <= 0.01
        and value <= 0.025
        and row["whole_coverage"] is not None
        and row["whole_coverage"] >= 0.95
        and row["recall_violations"] == 0
    )


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify exactly two final deterministic known-game pairs."""
    if len(cases) != 24:
        raise ArithmeticError("24 fixed policies required")
    by_game = {}
    for game in GAMES:
        final = [
            row
            for row in cases
            if row["game"] == game
            and row["work_label"] == LABELS[-1]
            and row["readout"] == "linear_average"
        ]
        if len(final) != 2 or {row["arm"] for row in final} != {CONTROL, ARM}:
            raise ArithmeticError("fixed final pair changed")
        old, new = (
            next(row for row in final if row["arm"] == arm) for arm in (CONTROL, ARM)
        )
        if old["seed"] != 0 or new["seed"] != 0:
            raise ArithmeticError("fixed seed changed")
        delta = (
            new["exploitability_fraction_initial_pot"]
            - old["exploitability_fraction_initial_pot"]
        )
        by_game[game] = dict(
            control=old["exploitability_fraction_initial_pot"],
            candidate=new["exploitability_fraction_initial_pot"],
            candidate_minus_control=delta,
            control_absolute_pass=absolute(old),
            candidate_absolute_pass=absolute(new),
        )
    wet, dry = (by_game[game] for game in GAMES)
    positive = (
        wet["candidate_absolute_pass"]
        and dry["candidate_absolute_pass"]
        and wet["candidate_minus_control"] <= -0.001
        and dry["candidate_minus_control"] <= 0.001
    )
    negative = any(
        not row["candidate_absolute_pass"] or row["candidate_minus_control"] > 0.001
        for row in by_game.values()
    )
    return dict(
        classification="positive"
        if positive
        else "negative"
        if negative
        else "inconclusive",
        by_game=by_game,
    )


def contrasts(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pair both saved readouts at all three exact work crossings."""
    result = []
    for game in GAMES:
        for work in LABELS:
            for readout in READOUTS:
                pair = [
                    row
                    for row in cases
                    if row["game"] == game
                    and row["work_label"] == work
                    and row["readout"] == readout
                ]
                if len(pair) != 2 or {row["arm"] for row in pair} != {CONTROL, ARM}:
                    raise ArithmeticError("fixed work/readout pair changed")
                old, new = (
                    next(row for row in pair if row["arm"] == arm)
                    for arm in (CONTROL, ARM)
                )
                if old["actual_node_work"] != new["actual_node_work"]:
                    raise ArithmeticError("matched work changed")
                result.append(
                    dict(
                        game=game,
                        seed=0,
                        work_label=work,
                        actual_node_work=new["actual_node_work"],
                        readout=readout,
                        control=old["exploitability_fraction_initial_pot"],
                        candidate=new["exploitability_fraction_initial_pot"],
                        candidate_minus_control=(
                            new["exploitability_fraction_initial_pot"]
                            - old["exploitability_fraction_initial_pot"]
                        ),
                    )
                )
    return result


def timing(record: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Bind both whole candidate paths and retained worker RSS."""
    if record.get("status") != "completed" or record.get("assignments") != [[0], [1]]:
        raise ArithmeticError("complete two-worker own study required")
    rows = [
        item
        for worker in record["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    result = {row["index"]: row for row in rows}
    if len(rows) != 2 or len(result) != 2:
        raise ArithmeticError("missing candidate timing")
    for spec in paths():
        row = result[spec.index]
        if (
            row["path"] != dict(index=spec.index, game=spec.game, arm=ARM, seed=0)
            or row["repeat"] != 0
            or row["captures"] != 6
            or row["whole_path_seconds"] <= 0
            or row["worker_peak_rss_bytes"] <= 0
        ):
            raise ArithmeticError("candidate path timing changed")
    return result


def observation(identity: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    """Saved opponent and optimized continuation, for one fixed exact row."""
    info = identity["exact_info"]
    seat = detail["traces"][identity["seat"]]
    count = len(identity["legal_actions"])
    return dict(
        saved_probabilities=detail["expanded"][info, :count].tolist(),
        counterfactual_reach=float(seat.counterfactual_mass[info]),
        saved_prefix_reach=float(seat.saved_reach_mass[info]),
        alternative_action_values_chips=seat.conditional_values[info, :count].tolist(),
        additive_contribution_chips=float(seat.losses[info] / 2),
    )


def report(root: Path, output: Path) -> None:
    """Require all published archives before replaying their 24 policies."""
    plan = contract(root)
    head = clean_head(root)
    source = source_fingerprint(root)
    historical_controls(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
    ):
        require_archive(root, root / stage, status, source)
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in native["rows"]
    }
    if (
        native["status"] != "completed"
        or len(native["rows"]) != 12
        or len(audits) != 12
    ):
        raise ArithmeticError("fixed candidate independent audit missing")
    own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
    resources = timing(own)
    cases: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for spec in paths():
        scoring = context(root, spec.game)
        tree = scoring.exact
        if not isinstance(tree, MatrixTree):
            raise ArithmeticError("exact matrix tree required")
        item = plan["inputs"][spec.index]
        old_root = root / "results" / ARCHIVES[spec.index]
        old_report: dict[str, Any] = json.loads(
            (old_root / "report/report.json").read_bytes()
        )
        old_cases = {
            (row["work_label"], row["readout"]): row
            for row in old_report["cases"]
            if row["arm"] == CONTROL
        }
        if len(old_cases) != 6:
            raise ArithmeticError("six immutable control policies required")
        if (
            old_cases[(LABELS[-1], "linear_average")][
                "exploitability_fraction_initial_pot"
            ]
            != item["control_final_linear_exploitability_fraction_pot"]
        ):
            raise ArithmeticError("frozen final control score changed")
        fixed = item["fixed_turn_rows"] + item["fixed_river_rows"]
        if len(set(fixed)) != len(fixed):
            raise ArithmeticError("duplicate fixed decision row")
        identities = {info: row_identity(tree, info) for info in fixed}
        decisions: dict[int, dict[str, Any]] = {
            info: dict(**identity, observations=[])
            for info, identity in identities.items()
        }
        for arm, folder, path_index in (
            (CONTROL, old_root / "own/study/path01", 1),
            (ARM, root / OWN / "study" / f"path{spec.index:02d}", spec.index),
        ):
            summary = replay_path(scoring, folder)
            if (
                summary["path"]
                != dict(index=path_index, game=spec.game, arm=arm, seed=0)
                or summary["labels"] != list(LABELS)
                or len(summary["captures"]) != 6
            ):
                raise ArithmeticError("saved path identity changed")
            for capture in summary["captures"]:
                meta = capture["metadata"]
                work, readout = meta["work_label"], meta["readout"]
                if work not in LABELS or readout not in READOUTS:
                    raise ArithmeticError("unregistered saved checkpoint")
                score = capture["score"]["metrics"]["exact_exploitability_chips"]
                support = capture["support"]
                detail = trace(scoring, folder, capture)
                case = dict(
                    path_index=path_index,
                    game=spec.game,
                    seed=0,
                    arm=arm,
                    work_label=work,
                    readout=readout,
                    policy_sha256=capture["receipt"]["policy_sha256"],
                    actual_node_work=meta["total_work"],
                    overshoot=meta["overshoot"],
                    exploitability_chips=score,
                    exploitability_fraction_initial_pot=score / 36,
                    seat_best_reply_gain_chips=[
                        float(item.gain) for item in detail["traces"]
                    ],
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
                    whole_path_seconds=(
                        old_cases[(work, readout)]["whole_path_seconds"]
                        if arm == CONTROL
                        else resources[spec.index]["whole_path_seconds"]
                    ),
                    worker_peak_rss_bytes=(
                        old_cases[(work, readout)]["worker_peak_rss_bytes"]
                        if arm == CONTROL
                        else resources[spec.index]["worker_peak_rss_bytes"]
                    ),
                    native_maximum_error_chips=(
                        old_cases[(work, readout)]["native_maximum_error_chips"]
                        if arm == CONTROL
                        else audits[(spec.index, work, readout)]["native"][
                            "maximum_error_chips"
                        ]
                    ),
                )
                if arm == CONTROL:
                    old = old_cases[(work, readout)]
                    if (
                        old["policy_sha256"] != case["policy_sha256"]
                        or abs(old["exploitability_chips"] - score) > TOLERANCE
                        or old["actual_node_work"] != case["actual_node_work"]
                    ):
                        raise ArithmeticError("immutable control report mismatch")
                elif (
                    audits[(spec.index, work, readout)]["own_policy_sha256"]
                    != case["policy_sha256"]
                    or case["native_maximum_error_chips"] > TOLERANCE
                ):
                    raise ArithmeticError("candidate native scalar/policy mismatch")
                streets = [
                    row_identity(tree, i)["street"] for i in range(len(tree.keys))
                ]
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
                    raise ArithmeticError("street gains do not sum")
                cases.append(case)
                for info, identity in identities.items():
                    decisions[info]["observations"].append(
                        dict(
                            arm=arm,
                            seed=0,
                            work_label=work,
                            readout=readout,
                            **observation(identity, detail),
                        )
                    )
        diagnostics.extend(dict(game=spec.game, **decisions[info]) for info in fixed)
    paired = contrasts(cases)
    verdict = decision(cases)
    output.mkdir(parents=True, exist_ok=False)
    started: dict[str, Any] = json.loads((root / OWN / "started.json").read_bytes())
    save(
        output / "report.json",
        dict(
            status="completed",
            head=head,
            source_fingerprint=source,
            protocol="docs/known-turn-regret-recency.md",
            runtime=started["runtime"],
            study_seconds=own["seconds"],
            cases=cases,
            checkpoint_contrasts=paired,
            primary=verdict,
            diagnostics=diagnostics,
            wet_top_two_turn_contribution_chips={
                arm: sum(
                    row["additive_contribution_chips"]
                    for entry in diagnostics
                    if entry["game"] == GAMES[0] and entry["exact_info"] in (1611, 4041)
                    for row in entry["observations"]
                    if row["arm"] == arm
                    and row["work_label"] == LABELS[-1]
                    and row["readout"] == "linear_average"
                )
                for arm in (CONTROL, ARM)
            },
            uncertainty=(
                "one deterministic seed per known outcome-inspected game; "
                "no seed confidence or unseen claim"
            ),
            decision_assumptions=(
                "each saved opponent policy and optimized reply continuation; "
                "values are not universal poker advice"
            ),
        ),
    )
