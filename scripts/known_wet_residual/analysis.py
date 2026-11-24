"""One bounded replay of published exact-turn policies and residual losses."""

import json
import math
import os
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from known_wet_turn_mechanism.plan import (
    CANDIDATE,
    CONTROL,
    GAME,
    LABELS,
    READOUTS,
    context,
)
from medium_dry_b8.report import row_identity
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.report import trace

from known_wet_residual.gate import (
    ADMISSION,
    PROOF,
    SOURCE,
    clean_head,
    contract,
    require_archive,
    source_fingerprint,
)
from known_wet_residual.math import rank_street, street_summary
from poker_ai.postflop.matrix import MatrixTree

TOLERANCE = 1e-9
PARENT = Path("results/known-wet-turn-mechanism")


def save(path: Path, value: dict[str, Any]) -> None:
    """Create one complete JSON record without replacing prior evidence."""
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def event(path: Path, value: dict[str, Any]) -> None:
    """Append a durable event after each selected or replayed case."""
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def capture(summary: dict[str, Any], work: int, readout: str) -> dict[str, Any]:
    """Take exactly one predeclared published snapshot, never a substitute."""
    matches = [
        row
        for row in summary["captures"]
        if row["metadata"]["work_label"] == work
        and row["metadata"]["readout"] == readout
    ]
    if len(matches) != 1:
        raise ArithmeticError("missing or duplicate fixed saved policy")
    row: dict[str, Any] = matches[0]
    return row


def parent_cases(root: Path) -> dict[tuple[str, int, str], dict[str, Any]]:
    """Bind all 12 already published own/native/report scalar records."""
    report: dict[str, Any] = json.loads(
        (root / PARENT / "report/report.json").read_bytes()
    )
    if report["primary"]["classification"] != "negative" or len(report["cases"]) != 12:
        raise ArithmeticError("published negative parent report changed")
    cases = {
        (row["arm"], row["work_label"], row["readout"]): row for row in report["cases"]
    }
    expected = {
        (arm, work, readout)
        for arm in (CONTROL, CANDIDATE)
        for work in LABELS
        for readout in READOUTS
    }
    if set(cases) != expected or any(
        row["seed"] != 0
        or row["game"] != GAME
        or row["native_maximum_error_chips"] > TOLERANCE
        for row in cases.values()
    ):
        raise ArithmeticError("published policy/native grid changed")
    return cases


def observation(
    detail: dict[str, Any], identity: dict[str, Any], arm: str, work: int, readout: str
) -> dict[str, Any]:
    """Give conditional saved-opponent action values at one fixed exact row."""
    info = int(identity["exact_info"])
    seat = detail["traces"][identity["seat"]]
    width = len(identity["legal_actions"])
    return dict(
        arm=arm,
        seed=0,
        work_label=work,
        readout=readout,
        saved_probabilities=detail["expanded"][info, :width].tolist(),
        counterfactual_reach=float(seat.counterfactual_mass[info]),
        saved_prefix_reach=float(seat.saved_reach_mass[info]),
        alternative_action_values_chips=seat.conditional_values[info, :width].tolist(),
        additive_contribution_chips=float(seat.losses[info] / 2),
    )


def verify_case(
    detail: dict[str, Any],
    selected: dict[str, list[int]],
    identities: list[dict[str, Any]],
    published: dict[str, Any],
    saved: dict[str, Any],
) -> dict[str, Any]:
    """Reconcile full row/street sums to the published own and native scalar."""
    contribution = detail["contribution"]
    score = saved["score"]["metrics"]["exact_exploitability_chips"]
    if (
        saved["receipt"]["policy_sha256"] != published["policy_sha256"]
        or saved["metadata"]["total_work"] != published["actual_node_work"]
        or abs(score - published["exploitability_chips"]) > TOLERANCE
        or len(contribution) != len(identities)
        or not np.all(np.isfinite(contribution))
        or float(contribution.min(initial=0)) < -1e-12
        or abs(math.fsum(float(x) for x in contribution) - score) > TOLERANCE
    ):
        raise ArithmeticError("published policy or additive score identity changed")
    streets = {
        street: street_summary(contribution, identities, selected[street], street)
        for street in ("TURN", "RIVER")
    }
    if (
        abs(streets["TURN"]["total_chips"] - published["turn_contribution_chips"])
        > TOLERANCE
        or abs(streets["RIVER"]["total_chips"] - published["river_contribution_chips"])
        > TOLERANCE
    ):
        raise ArithmeticError("published street gain changed")
    positive = {}
    for street in ("TURN", "RIVER"):
        positive[street] = sum(
            detail["traces"][identity["seat"]].saved_reach_mass[i] > 0
            for i, identity in enumerate(identities)
            if identity["street"] == street
        )
    return dict(
        street=streets,
        positive_saved_prefix_rows={key: int(value) for key, value in positive.items()},
        exploitability_chips=score,
        actual_node_work=published["actual_node_work"],
        whole_coverage=published["whole_coverage"],
        post_initial_river_coverage=published["post_initial_river_coverage"],
        worker_peak_rss_bytes=published["worker_peak_rss_bytes"],
        whole_path_seconds=published["whole_path_seconds"],
        native_maximum_error_chips=published["native_maximum_error_chips"],
    )


def run(root: Path, output: Path) -> None:
    """Select candidate final rows first, then replay the other fixed policies."""
    plan = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (PROOF, "proof_passed"),
        (ADMISSION, "admitted"),
    ):
        require_archive(root, root / stage, status, fingerprint)
    decision: dict[str, Any] = json.loads(
        (root / ADMISSION / "decision.json").read_bytes()
    )
    if (
        decision["forecast_bound_seconds"] != plan["forecast_bound_seconds"]
        or decision["status"] != "admitted"
    ):
        raise ArithmeticError("separate compute admission changed")
    published = parent_cases(root)
    output.mkdir(parents=True, exist_ok=False)
    started = dict(
        status="started",
        head=head,
        source_fingerprint=fingerprint,
        started_utc=datetime.now(UTC).isoformat(),
        python=sys.version.split()[0],
        numpy=np.__version__,
        hardware=platform.platform(),
        policy_cases=12,
        cap_seconds=900,
    )
    save(output / "started.json", started)
    events = output / "events.jsonl"
    event(events, dict(kind="started", head=head, source_fingerprint=fingerprint))
    try:
        candidate_scoring = context(root, GAME, CANDIDATE)
        tree = candidate_scoring.exact
        partition = candidate_scoring.partition
        if (
            not isinstance(tree, MatrixTree)
            or not isinstance(partition, MatrixTree)
            or not np.array_equal(
                partition.exact_to_abstract, np.arange(len(tree.keys))
            )
        ):
            raise ArithmeticError("candidate exact acting key identity changed")
        identities = [row_identity(tree, info) for info in range(len(tree.keys))]
        if {row["street"] for row in identities} != {"TURN", "RIVER"}:
            raise ArithmeticError("registered turn-start game changed")
        candidate_folder = root / PARENT / "own/study/path01"
        candidate_summary = replay_path(candidate_scoring, candidate_folder)
        final_saved = capture(candidate_summary, LABELS[-1], "linear_average")
        final_detail = trace(candidate_scoring, candidate_folder, final_saved)
        selected = {
            street: rank_street(final_detail["contribution"], identities, street)
            for street in ("TURN", "RIVER")
        }
        if len(set(selected["TURN"] + selected["RIVER"])) != 20:
            raise ArithmeticError("selected exact rows overlap")
        save(
            output / "selection.json",
            dict(
                status="selected",
                selection_policy=dict(
                    arm=CANDIDATE,
                    seed=0,
                    work_label=LABELS[-1],
                    readout="linear_average",
                ),
                selected=selected,
            ),
        )
        event(events, dict(kind="selected", selected=selected))
        diagnostics = {
            info: dict(**identities[info], candidate_rank=rank + 1, observations=[])
            for street in ("TURN", "RIVER")
            for rank, info in enumerate(selected[street])
        }
        cases = []
        for path_index, arm in enumerate((CONTROL, CANDIDATE)):
            scoring = context(root, GAME, arm) if arm == CONTROL else candidate_scoring
            folder = root / PARENT / "own/study" / f"path{path_index:02d}"
            summary = (
                replay_path(scoring, folder) if arm == CONTROL else candidate_summary
            )
            if (
                summary["path"] != dict(index=path_index, game=GAME, arm=arm, seed=0)
                or summary["labels"] != list(LABELS)
                or len(summary["captures"]) != 6
            ):
                raise ArithmeticError("fixed saved path identity changed")
            for work in LABELS:
                for readout in READOUTS:
                    saved = capture(summary, work, readout)
                    detail = (
                        final_detail
                        if arm == CANDIDATE
                        and work == LABELS[-1]
                        and readout == "linear_average"
                        else trace(scoring, folder, saved)
                    )
                    prior = published[(arm, work, readout)]
                    checked = verify_case(detail, selected, identities, prior, saved)
                    raw_name = f"path{path_index:02d}-{work}-{readout}.npz"
                    np.savez_compressed(
                        output / raw_name, contribution=detail["contribution"]
                    )
                    row = dict(
                        arm=arm,
                        seed=0,
                        work_label=work,
                        readout=readout,
                        raw_contribution=raw_name,
                        **checked,
                    )
                    save(output / f"path{path_index:02d}-{work}-{readout}.json", row)
                    event(
                        events,
                        dict(
                            kind="case",
                            arm=arm,
                            work_label=work,
                            readout=readout,
                            raw_contribution=raw_name,
                        ),
                    )
                    cases.append(row)
                    for info in selected["TURN"] + selected["RIVER"]:
                        diagnostics[info]["observations"].append(
                            observation(detail, identities[info], arm, work, readout)
                        )
        if len(cases) != 12 or any(
            len(row["observations"]) != 12 for row in diagnostics.values()
        ):
            raise ArithmeticError("fixed diagnostic grid incomplete")
        final = next(
            row
            for row in cases
            if row["arm"] == CANDIDATE
            and row["work_label"] == LABELS[-1]
            and row["readout"] == "linear_average"
        )
        save(
            output / "report.json",
            dict(
                status="completed",
                scope="one already known outcome-inspected turn-start medium/wet game",
                source_head=head,
                source_fingerprint=fingerprint,
                selection=selected,
                final_candidate_concentration={
                    street: final["street"][street] for street in ("TURN", "RIVER")
                },
                cases=cases,
                diagnostics=[
                    diagnostics[info] for info in selected["TURN"] + selected["RIVER"]
                ],
                assumption=(
                    "fixed saved opponent and optimized best-reply continuation; "
                    "local values are not universal advice or causal action swaps"
                ),
                limitation=(
                    "one deterministic known game; no new training, convergence "
                    "proof, unseen transfer or default promotion"
                ),
            ),
        )
        event(events, dict(kind="completed", cases=12, selected_rows=20))
    except BaseException as error:
        save(
            output / "failure.json",
            dict(status="failed", error=type(error).__name__, detail=str(error)),
        )
        event(
            events, dict(kind="failed", error=type(error).__name__, detail=str(error))
        )
        raise
