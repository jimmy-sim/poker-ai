"""One bounded read-only all-row trace of four published known policies."""

import json
import math
import os
import platform
import resource
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from medium_dry_b8.report import row_identity
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.report import trace

from known_turn_loss_attribution.gate import (
    clean_head,
    require_admission,
    source_fingerprint,
)
from known_turn_loss_attribution.math import summarize
from known_turn_loss_attribution.plan import (
    CANDIDATE,
    CONTROL,
    GAMES,
    READOUT,
    WORK,
    context,
    contract,
)
from poker_ai.postflop.matrix import MatrixTree

TOLERANCE = 1e-9
PARENT_REPORT = Path("results/known-turn-regret-recency/report/report.json")
FOLDERS = {
    (GAMES[0], CONTROL): Path("results/known-wet-turn-mechanism/own/study/path01"),
    (GAMES[1], CONTROL): Path("results/known-turn-exact-mechanism/own/study/path01"),
    (GAMES[0], CANDIDATE): Path("results/known-turn-regret-recency/own/study/path00"),
    (GAMES[1], CANDIDATE): Path("results/known-turn-regret-recency/own/study/path00"),
}


def save(path: Path, value: dict[str, Any]) -> None:
    """Create and durably flush one immutable JSON record."""
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def event(path: Path, value: dict[str, Any]) -> None:
    """Append and flush each partial-progress event."""
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def saved_capture(summary: dict[str, Any]) -> dict[str, Any]:
    """Choose the sole fixed 10m final linear-average snapshot."""
    matches = [
        row
        for row in summary["captures"]
        if row["metadata"]["work_label"] == 10_000_000
        and row["metadata"]["readout"] == READOUT
    ]
    if len(matches) != 1:
        raise ArithmeticError("missing or duplicate published final average")
    saved: dict[str, Any] = matches[0]
    return saved


def observe(detail: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    """Return one saved-opponent, optimized-continuation exact decision."""
    info = int(identity["exact_info"])
    seat = detail["traces"][identity["seat"]]
    count = len(identity["legal_actions"])
    return {
        "saved_probabilities": detail["expanded"][info, :count].tolist(),
        "counterfactual_reach": float(seat.counterfactual_mass[info]),
        "saved_prefix_reach": float(seat.saved_reach_mass[info]),
        "alternative_action_values_chips": seat.conditional_values[
            info, :count
        ].tolist(),
        "additive_contribution_chips": float(seat.losses[info] / 2),
    }


def published_cases(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Bind all four fixed final cases to the already audited report."""
    report = json.loads((root / PARENT_REPORT).read_bytes())
    if report["primary"]["classification"] != "negative" or len(report["cases"]) != 24:
        raise ArithmeticError("published negative parent report changed")
    cases = {
        (row["game"], row["arm"]): row
        for row in report["cases"]
        if row["work_label"] == 10_000_000 and row["readout"] == READOUT
    }
    if set(cases) != {(g, a) for g in GAMES for a in (CONTROL, CANDIDATE)} or any(
        row["seed"] != 0 or row["native_maximum_error_chips"] > TOLERANCE
        for row in cases.values()
    ):
        raise ArithmeticError("published final policy/native grid changed")
    return cases


def run(root: Path, output: Path) -> None:
    """Trace the one fixed four-policy grid and retain all full-row deltas."""
    started_clock = time.monotonic()
    plan = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_admission(root, fingerprint)
    published = published_cases(root)
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "started.json",
        {
            "status": "started",
            "head": head,
            "source_fingerprint": fingerprint,
            "started_utc": datetime.now(UTC).isoformat(),
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "hardware": platform.platform(),
            "cap_seconds": 900,
        },
    )
    events = output / "events.jsonl"
    event(events, {"kind": "started", "head": head})
    try:
        reports = []
        for index, game in enumerate(GAMES):
            scoring = context(root, game)
            tree = scoring.exact
            if (
                not isinstance(tree, MatrixTree)
                or not isinstance(scoring.partition, MatrixTree)
                or not np.array_equal(
                    scoring.partition.exact_to_abstract, np.arange(len(tree.keys))
                )
            ):
                raise ArithmeticError("exact acting key identity changed")
            identities = [row_identity(tree, i) for i in range(len(tree.keys))]
            if {row["street"] for row in identities} != {"TURN", "RIVER"}:
                raise ArithmeticError("fixed turn-start streets changed")
            details = {}
            cases = {}
            for arm in (CONTROL, CANDIDATE):
                folder = root / FOLDERS[(game, arm)]
                summary = replay_path(scoring, folder)
                saved = saved_capture(summary)
                prior = published[(game, arm)]
                if (
                    summary["path"]["index"] != (1 if arm == CONTROL else 0)
                    or summary["path"]["game"] != game
                    or summary["path"]["arm"] != arm
                    or summary["path"]["seed"] != 0
                    or summary["labels"] != [100_000, 1_000_000, 10_000_000]
                    or len(summary["captures"]) != 6
                    or saved["metadata"]["total_work"] != WORK[index]
                    or saved["metadata"]["total_work"] != prior["actual_node_work"]
                    or saved["receipt"]["policy_sha256"] != prior["policy_sha256"]
                    or prior["recall_violations"] != 0
                ):
                    raise ArithmeticError("fixed saved policy path/work/hash changed")
                detail = trace(scoring, folder, saved)
                contribution = np.asarray(detail["contribution"], dtype=np.float64)
                score = saved["score"]["metrics"]["exact_exploitability_chips"]
                if (
                    len(contribution) != len(identities)
                    or not np.all(np.isfinite(contribution))
                    or float(contribution.min(initial=0)) < -1e-12
                    or abs(math.fsum(float(x) for x in contribution) - score)
                    > TOLERANCE
                    or abs(score - prior["exploitability_chips"]) > TOLERANCE
                ):
                    raise ArithmeticError("full row sum or published scalar changed")
                streets = {
                    street: math.fsum(
                        float(contribution[i])
                        for i, ident in enumerate(identities)
                        if ident["street"] == street
                    )
                    for street in ("TURN", "RIVER")
                }
                if any(
                    abs(streets[s] - prior[f"{s.lower()}_contribution_chips"])
                    > TOLERANCE
                    for s in streets
                ):
                    raise ArithmeticError("published street contribution changed")
                raw_name = f"{game}-{arm}-contribution.npz"
                np.savez_compressed(output / raw_name, contribution=contribution)
                with (output / raw_name).open("rb") as raw_stream:
                    os.fsync(raw_stream.fileno())
                case = {
                    "game": game,
                    "arm": arm,
                    "seed": 0,
                    "work_label": 10_000_000,
                    "actual_node_work": WORK[index],
                    "readout": READOUT,
                    "policy_sha256": prior["policy_sha256"],
                    "raw_contribution": raw_name,
                    "exploitability_chips": score,
                    "exploitability_fraction_initial_pot": prior[
                        "exploitability_fraction_initial_pot"
                    ],
                    "street_contribution_chips": streets,
                    "whole_coverage": prior["whole_coverage"],
                    "post_initial_river_coverage": prior["post_initial_river_coverage"],
                    "worker_peak_rss_bytes": prior["worker_peak_rss_bytes"],
                    "whole_path_seconds": prior["whole_path_seconds"],
                    "native_maximum_error_chips": prior["native_maximum_error_chips"],
                }
                save(output / f"{game}-{arm}.json", case)
                event(
                    events,
                    {
                        "kind": "case",
                        "game": game,
                        "arm": arm,
                        "policy_sha256": prior["policy_sha256"],
                    },
                )
                details[arm] = detail
                cases[arm] = case
            ctrl = np.asarray(details[CONTROL]["contribution"], dtype=np.float64)
            cand = np.asarray(details[CANDIDATE]["contribution"], dtype=np.float64)
            streets_report = {}
            selected = set()
            for street in ("TURN", "RIVER"):
                indices = [
                    i for i, ident in enumerate(identities) if ident["street"] == street
                ]
                known = plan["games"][index][
                    f"previously_inspected_{street.lower()}_rows"
                ]
                row = summarize(ctrl, cand, indices, known)
                if (
                    abs(
                        row["net_change_chips"]
                        - (
                            cases[CANDIDATE]["street_contribution_chips"][street]
                            - cases[CONTROL]["street_contribution_chips"][street]
                        )
                    )
                    > TOLERANCE
                ):
                    raise ArithmeticError("paired street delta did not reconcile")
                streets_report[street] = row
                selected.update(row["top_ten_by_delta"])
                selected.update(row["top_ten_by_candidate_gain"])
                selected.update(known)
            delta = (
                cases[CANDIDATE]["exploitability_chips"]
                - cases[CONTROL]["exploitability_chips"]
            )
            if (
                abs(
                    math.fsum(
                        row["net_change_chips"] for row in streets_report.values()
                    )
                    - delta
                )
                > TOLERANCE
            ):
                raise ArithmeticError("paired total delta did not reconcile")
            diagnostics = []
            for info in sorted(selected):
                identity = identities[info]
                diagnostics.append(
                    {
                        **identity,
                        "control": observe(details[CONTROL], identity),
                        "candidate": observe(details[CANDIDATE], identity),
                        "candidate_minus_control_contribution_chips": float(
                            cand[info] - ctrl[info]
                        ),
                    }
                )
            result = {
                "game": game,
                "seed": 0,
                "work_label": 10_000_000,
                "actual_node_work": WORK[index],
                "readout": READOUT,
                "cases": [cases[CONTROL], cases[CANDIDATE]],
                "streets": streets_report,
                "candidate_minus_control_chips": delta,
                "diagnostics": diagnostics,
                "full_row_count": len(identities),
            }
            save(output / f"{game}-report.json", result)
            event(
                events,
                {
                    "kind": "game_complete",
                    "game": game,
                    "rows": len(identities),
                    "selected": len(selected),
                },
            )
            reports.append(result)
        save(
            output / "report.json",
            {
                "status": "completed",
                "head": head,
                "source_fingerprint": fingerprint,
                "games": reports,
                "assumption": (
                    "each arm's saved opponent and optimized best-reply "
                    "continuation; additive decomposition is not a causal "
                    "action swap or universal advice"
                ),
                "uncertainty": (
                    "one deterministic seed on two related outcome-inspected "
                    "known games; no seed confidence or unseen claim"
                ),
                "runtime": {
                    "seconds": time.monotonic() - started_clock,
                    "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    * (1 if sys.platform == "darwin" else 1024),
                },
            },
        )
        event(events, {"kind": "completed", "games": 2, "cases": 4})
    except BaseException as error:
        save(
            output / "failure.json",
            {"status": "failed", "type": type(error).__name__, "detail": str(error)},
        )
        event(
            events,
            {"kind": "failed", "type": type(error).__name__, "detail": str(error)},
        )
        raise
