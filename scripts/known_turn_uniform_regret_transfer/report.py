"""Fixed four-game matched-work report and preregistered decision rows."""

import json
import math
from pathlib import Path
from statistics import median
from typing import Any

from medium_dry_b8.report import row_identity
from river_generalization.gate import require_archive
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.report import trace

from known_turn_uniform_regret_transfer.gate import (
    NATIVE,
    OWN,
    clean_head,
    require_own,
    source_fingerprint,
)
from known_turn_uniform_regret_transfer.native import save
from known_turn_uniform_regret_transfer.plan import (
    ARM,
    GAMES,
    LABELS,
    MAX_RSS,
    READOUTS,
    context,
    contract,
    paths,
)
from poker_ai.postflop.matrix import MatrixTree

PRIOR_OWN = Path("results/known-turn-collision-medium-transfer/own")
PRIOR_REPORT = Path("results/known-turn-collision-medium-transfer/report/report.json")
FIXED_ROWS = Path("results/known-mixture-residual-map/report/report.json")
PRIOR_ARM = "signed_full_exact_turn_river"
TOLERANCE = 1e-9


def timing(record: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Bind the exact four-path capped worker grid and resource records."""
    if (
        record.get("status") != "completed"
        or record.get("stage") != "study"
        or record.get("worker_count") != 2
        or record.get("assignments") != [list(range(0, 4, 2)), list(range(1, 4, 2))]
        or not 0 < record.get("seconds", -1) < 7200
    ):
        raise ArithmeticError("complete capped candidate own grid required")
    rows = [
        item
        for worker in record["workers"]
        for message in worker["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    by_index = {row["index"]: row for row in rows}
    if len(rows) != 4 or set(by_index) != set(range(4)):
        raise ArithmeticError("four candidate resource records required")
    for spec in paths():
        row = by_index[spec.index]
        if (
            row["path"] != dict(index=spec.index, game=spec.game, arm=ARM, seed=0)
            or row["repeat"] != 0
            or row["captures"] != 6
            or row["final_work"] != 40_205_562
            or not 0 < row["whole_path_seconds"]
            or not 0 < row["worker_peak_rss_bytes"] < MAX_RSS
        ):
            raise ArithmeticError("candidate path resource identity changed")
    return by_index


def paired(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep every 10m/20m/40m current and average paired score."""
    contrasts = []
    for game in GAMES:
        for work in LABELS:
            for readout in READOUTS:
                pair = [
                    row
                    for row in cases
                    if (row["game"], row["work_label"], row["readout"])
                    == (game, work, readout)
                ]
                if (
                    len(pair) != 2
                    or {row["arm"] for row in pair} != {PRIOR_ARM, ARM}
                    or len({row["actual_node_work"] for row in pair}) != 1
                ):
                    raise ArithmeticError("fixed matched-work policy pair changed")
                by_arm = {row["arm"]: row for row in pair}
                a = by_arm[PRIOR_ARM]["exploitability_fraction_initial_pot"]
                b = by_arm[ARM]["exploitability_fraction_initial_pot"]
                contrasts.append(
                    dict(
                        game=game,
                        work_label=work,
                        readout=readout,
                        actual_node_work=pair[0]["actual_node_work"],
                        seed=0,
                        control=a,
                        candidate=b,
                        candidate_minus_control=b - a,
                    )
                )
    return contrasts


def decision(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the unchanged absolute/paired PR116 gates to four final means."""
    final = [
        row
        for row in cases
        if row["work_label"] == LABELS[-1] and row["readout"] == "linear_average"
    ]
    if len(final) != 8:
        raise ArithmeticError("eight final matched policies required")
    by_game = {}
    for game in GAMES:
        pair = [row for row in final if row["game"] == game]
        if len(pair) != 2 or {row["arm"] for row in pair} != {PRIOR_ARM, ARM}:
            raise ArithmeticError("fixed final pair changed")
        controls = {row["arm"]: row for row in pair}
        control, candidate = controls[PRIOR_ARM], controls[ARM]
        value = candidate["exploitability_fraction_initial_pot"]
        delta = value - control["exploitability_fraction_initial_pot"]
        absolute = (
            value <= 0.01
            and value <= 0.025
            and candidate["whole_coverage"] is not None
            and candidate["whole_coverage"] >= 0.95
            and candidate["recall_violations"] == 0
        )
        by_game[game] = dict(
            control=control["exploitability_fraction_initial_pot"],
            candidate=value,
            candidate_minus_control=delta,
            candidate_absolute_pass=absolute,
        )
    improved = [
        game
        for game, row in by_game.items()
        if row["candidate_minus_control"] <= -0.001
    ]
    positive = (
        all(row["candidate_absolute_pass"] for row in by_game.values())
        and len(improved) >= 3
        and any("dry" in game for game in improved)
        and any("wet" in game for game in improved)
        and all(row["candidate_minus_control"] <= 0.001 for row in by_game.values())
    )
    negative = any(
        not row["candidate_absolute_pass"] or row["candidate_minus_control"] > 0.001
        for row in by_game.values()
    )
    deltas = [row["candidate_minus_control"] for row in by_game.values()]
    return dict(
        classification="positive"
        if positive
        else "negative"
        if negative
        else "inconclusive",
        by_game=by_game,
        paired_delta_min=min(deltas),
        paired_delta_median=median(deltas),
        paired_delta_max=max(deltas),
        candidate_worst=max(row["candidate"] for row in by_game.values()),
    )


def observation(
    detail: dict[str, Any], info: int, owner: int, width: int
) -> dict[str, Any]:
    """Keep saved-policy and fixed-opponent best-reply values for one row."""
    seat = detail["traces"][owner]
    return dict(
        saved_probabilities=detail["expanded"][info, :width].tolist(),
        counterfactual_reach=float(seat.counterfactual_mass[info]),
        saved_prefix_reach=float(seat.saved_reach_mass[info]),
        alternative_action_values_chips=seat.conditional_values[info, :width].tolist(),
        additive_contribution_chips=float(seat.losses[info] / 2),
    )


def report(root: Path, output: Path) -> None:
    """Read complete own/native evidence and all fixed PR119 selected rows."""
    contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_own(root, fingerprint)
    require_archive(root, root / NATIVE, "native_audited", fingerprint)
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    if (
        native["status"] != "completed"
        or len(native["rows"]) != 24
        or native["maximum_error_chips"] > TOLERANCE
    ):
        raise ArithmeticError("complete 24-case candidate reference audit required")
    audits = {
        (row["path_index"], row["work_label"], row["readout"]): row
        for row in native["rows"]
    }
    if len(audits) != 24:
        raise ArithmeticError("duplicate reference case")
    own = json.loads((root / OWN / "result.json").read_bytes())
    resources = timing(own)
    prior = json.loads((root / PRIOR_REPORT).read_bytes())
    controls = [row for row in prior["cases"] if row["arm"] == PRIOR_ARM]
    if len(controls) != 24:
        raise ArithmeticError("24 pinned old controls missing")
    fixed = json.loads((root / FIXED_ROWS).read_bytes())
    cases: list[dict[str, Any]] = controls.copy()
    diagnostics: list[dict[str, Any]] = []
    for spec in paths():
        scoring = context(root, spec.game)
        if not isinstance(scoring.exact, MatrixTree) or len(scoring.exact.keys) != 8340:
            raise ArithmeticError("fixed exact decision tree changed")
        streets = [
            row_identity(scoring.exact, info)["street"]
            for info in range(len(scoring.exact.keys))
        ]
        folder = root / OWN / "study" / f"path{spec.index:02d}"
        summary = replay_path(scoring, folder)
        if (
            summary["path"] != dict(index=spec.index, game=spec.game, arm=ARM, seed=0)
            or summary["labels"] != list(LABELS)
            or len(summary["captures"]) != 6
        ):
            raise ArithmeticError("fixed candidate capture path changed")
        chosen = next(
            row["selected_decisions"]
            for row in fixed["cases"]
            if row["game"] == spec.game
        )
        expected_count = (10, 10, 12, 10)[spec.index]
        infos = [row["exact_info"] for row in chosen]
        if len(infos) != expected_count or len(set(infos)) != expected_count:
            raise ArithmeticError("fixed PR119 decision row selection changed")
        selected = {
            info: dict(
                game=spec.game, **row_identity(scoring.exact, info), observations=[]
            )
            for info in infos
        }
        for row in chosen:
            identity = selected[row["exact_info"]]
            if any(
                identity[key] != row[key]
                for key in ("board", "hole", "seat", "street", "legal_actions")
            ):
                raise ArithmeticError("published PR119 decision identity changed")
        prior_folder = root / PRIOR_OWN / "study" / f"path{2 * spec.index + 1:02d}"
        prior_summary = replay_path(scoring, prior_folder)
        if (
            prior_summary["path"]
            != dict(index=2 * spec.index + 1, game=spec.game, arm=PRIOR_ARM, seed=0)
            or len(prior_summary["captures"]) != 6
        ):
            raise ArithmeticError("pinned prior exact-turn control path changed")
        for arm, captures, source_folder in (
            (PRIOR_ARM, prior_summary["captures"], prior_folder),
            (ARM, summary["captures"], folder),
        ):
            for capture in captures:
                meta = capture["metadata"]
                work, readout = meta["work_label"], meta["readout"]
                if work not in LABELS or readout not in READOUTS:
                    raise ArithmeticError("unregistered saved policy")
                detail = trace(scoring, source_folder, capture)
                if arm == ARM:
                    audit = audits[(spec.index, work, readout)]
                    if (
                        audit["own_policy_sha256"]
                        != capture["receipt"]["policy_sha256"]
                        or audit["native"]["maximum_error_chips"] > TOLERANCE
                    ):
                        raise ArithmeticError("candidate native policy/scalar mismatch")
                    chip_value = capture["score"]["metrics"][
                        "exact_exploitability_chips"
                    ]
                    contributions = detail["contribution"]
                    turn = math.fsum(
                        float(value)
                        for value, street in zip(contributions, streets, strict=True)
                        if street == "TURN"
                    )
                    river = math.fsum(
                        float(value)
                        for value, street in zip(contributions, streets, strict=True)
                        if street == "RIVER"
                    )
                    if abs(turn + river - chip_value) > TOLERANCE:
                        raise ArithmeticError("candidate turn/river accounting failed")
                    support = capture["support"]
                    cases.append(
                        dict(
                            path_index=spec.index,
                            game=spec.game,
                            arm=ARM,
                            seed=0,
                            work_label=work,
                            readout=readout,
                            policy_sha256=capture["receipt"]["policy_sha256"],
                            actual_node_work=meta["total_work"],
                            overshoot=meta["overshoot"],
                            exploitability_chips=chip_value,
                            exploitability_fraction_initial_pot=chip_value / 36,
                            whole_coverage=None
                            if support is None
                            else support["whole"]["all"]["uniform_reach_fraction"],
                            post_initial_river_coverage=None
                            if support is None
                            else support["post_warm"]["river"][
                                "uniform_reach_fraction"
                            ],
                            recall_violations=summary["recall_violations"],
                            information_rows=capture["information_rows"],
                            table_bytes=2
                            * 8
                            * capture["information_rows"]
                            * capture["padded_width"],
                            whole_path_seconds=resources[spec.index][
                                "whole_path_seconds"
                            ],
                            worker_peak_rss_bytes=resources[spec.index][
                                "worker_peak_rss_bytes"
                            ],
                            native_maximum_error_chips=audit["native"][
                                "maximum_error_chips"
                            ],
                            turn_contribution_chips=turn,
                            river_contribution_chips=river,
                        )
                    )
                for info in infos:
                    identity = selected[info]
                    identity["observations"].append(
                        dict(
                            arm=arm,
                            seed=0,
                            work_label=work,
                            readout=readout,
                            **observation(
                                detail,
                                info,
                                identity["seat"],
                                len(identity["legal_actions"]),
                            ),
                        )
                    )
        diagnostics.extend(selected[info] for info in infos)
    if (
        len(cases) != 48
        or len(diagnostics) != 42
        or any(len(row["observations"]) != 12 for row in diagnostics)
    ):
        raise ArithmeticError("fixed case/decision grid incomplete")
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "report.json",
        dict(
            status="completed",
            scope=(
                "four already inspected dependent collision-containing medium OOP games"
            ),
            protocol="docs/known-turn-uniform-regret-transfer.md",
            head=head,
            source_fingerprint=fingerprint,
            study_seconds=own["seconds"],
            cases=cases,
            checkpoint_contrasts=paired(cases),
            primary=decision(cases),
            diagnostics=diagnostics,
            native_maximum_error_chips=native["maximum_error_chips"],
            uncertainty=(
                "one deterministic path per arm/input, dependent known games; "
                "no seed interval, unseen transfer or full-game claim"
            ),
            decision_assumptions=(
                "each saved policy has its own fixed saved opponent and optimized "
                "reply continuation; row values are diagnostic, not causal swaps "
                "or universal advice"
            ),
        ),
    )
