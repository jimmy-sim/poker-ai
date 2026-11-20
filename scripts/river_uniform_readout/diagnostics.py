"""Bounded best-response attribution from final published own policies only."""

import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.cards import format_card
from poker_ai.postflop.collision_diagnosis import conditional_actions
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.postflop.river_study import Deadline
from poker_ai.training.no_limit import NoLimitState
from river_uniform_readout.learning import GAMES, LABELS, SEEDS, context, paths

CONTROL = "linear_average"
CANDIDATE = "uniform_average"
TOLERANCE = 1e-9


def top_infos(
    contributions: np.ndarray[Any, Any],
    support: np.ndarray[Any, Any],
    streets: tuple[str, ...],
    street: str,
    count: int = 3,
) -> list[int]:
    """Rank positive, supported control contributions; tie by exact info index."""
    if (
        contributions.ndim != 1
        or support.shape != contributions.shape
        or len(streets) != len(contributions)
        or not np.all(np.isfinite(contributions))
        or not np.all(np.isfinite(support))
        or np.any(support < 0)
        or street not in ("TURN", "RIVER")
        or count < 1
    ):
        raise ValueError("invalid fixed diagnostic ranking inputs")
    return sorted(
        (
            int(info)
            for info in np.flatnonzero((contributions > 0) & (support > 0))
            if streets[int(info)] == street
        ),
        key=lambda info: (-float(contributions[info]), info),
    )[:count]


def row_identity(tree: MatrixTree, info: int) -> dict[str, Any]:
    """Decode one exact player's own cards, board and public action menu."""
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


def _case(
    root: Path,
    own: Path,
    scoring: Any,
    spec: Any,
    readout: str,
    report_row: dict[str, Any],
    deadline: Deadline,
) -> dict[str, Any]:
    """Trace one bound final policy, checking additive gains against own score."""
    deadline.check()
    folder = own / "study" / f"path{spec.index:02d}"
    summary = json.loads((folder / "summary.json").read_bytes())
    if summary["path"] != vars(spec) or summary["recall_violations"] != 0:
        raise ArithmeticError("saved path identity/recall changed")
    captures = [
        row
        for row in summary["captures"]
        if row["metadata"]["work_label"] == LABELS[-1]
        and row["metadata"]["readout"] == readout
    ]
    if (
        len(captures) != 1
        or captures[0]["receipt"]["policy_sha256"] != report_row["policy_sha256"]
    ):
        raise ArithmeticError("fixed final policy/report binding changed")
    saved = captures[0]
    policy = read_snapshot(
        folder / saved["file"], scoring.partition, saved["receipt"], saved["metadata"]
    )
    exact_policy = scoring.expand(policy)
    tree = scoring.exact
    if not isinstance(tree, MatrixTree) or recall_violations(tree):
        raise ArithmeticError("exact game or recall changed")
    local_values, local_support = conditional_actions(tree, exact_policy)
    traces = []
    for target in (0, 1):
        deadline.check()
        traced = trace_losses(tree, exact_policy, target, tolerance=TOLERANCE)
        response = saved["score"]["responses"][target]
        if (
            response["target"] != target
            or abs(traced.value - response["exact_reply_value_chips"]) > TOLERANCE
            or abs(traced.gain - (traced.value - response["baseline_value_chips"]))
            > TOLERANCE
            or traced.accounting_error > TOLERANCE
            or float(traced.losses.min(initial=0.0)) < -TOLERANCE
        ):
            raise ArithmeticError("best-response attribution accounting changed")
        traces.append(traced)
    exploitability = math.fsum(trace.gain for trace in traces) / 2
    if (
        abs(exploitability - saved["score"]["metrics"]["exact_exploitability_chips"])
        > TOLERANCE
        or abs(exploitability - report_row["exploitability_chips"]) > TOLERANCE
    ):
        raise ArithmeticError("two-seat trace/exploitability identity failed")
    return dict(
        spec=vars(spec),
        readout=readout,
        policy_sha256=saved["receipt"]["policy_sha256"],
        exact_policy=exact_policy,
        local_values=local_values,
        local_support=local_support,
        traces=traces,
        exploitability_chips=exploitability,
    )


def diagnose(
    root: Path,
    own: Path,
    report_rows: list[dict[str, Any]],
    deadline: Deadline,
    events: Path | None = None,
) -> list[dict[str, Any]]:
    """Rank three control nodes per street/spot, show both readouts for all seeds."""
    lookup = {
        (row["game"], row["seed"], row["readout"]): row
        for row in report_rows
        if row["work_label"] == LABELS[-1] and row["readout"] in (CONTROL, CANDIDATE)
    }
    if len(lookup) != len(GAMES) * len(SEEDS) * 2:
        raise ArithmeticError("complete final diagnostic grid required")
    panels = []
    for game in GAMES:
        deadline.check()
        scoring = context(root, game)
        tree = scoring.exact
        if not isinstance(tree, MatrixTree):
            raise ArithmeticError("exact diagnostic game required")
        identities = [row_identity(tree, info) for info in range(len(tree.keys))]
        streets = tuple(row["street"] for row in identities)
        cases = {
            (seed, readout): _case(
                root,
                own,
                scoring,
                next(
                    spec for spec in paths() if spec.game == game and spec.seed == seed
                ),
                readout,
                lookup[(game, seed, readout)],
                deadline,
            )
            for seed in SEEDS
            for readout in (CONTROL, CANDIDATE)
        }
        control = [cases[(seed, CONTROL)] for seed in SEEDS]
        mean_contribution = np.mean(
            np.stack(
                [
                    (case["traces"][0].losses + case["traces"][1].losses) / 2
                    for case in control
                ]
            ),
            axis=0,
        )
        total_support = np.sum(
            np.stack(
                [
                    case["traces"][0].saved_reach_mass
                    + case["traces"][1].saved_reach_mass
                    for case in control
                ]
            ),
            axis=0,
        )
        ranked = {
            street: top_infos(mean_contribution, total_support, streets, street)
            for street in ("TURN", "RIVER")
        }
        decisions = []
        for _street, infos in ranked.items():
            for rank, info in enumerate(infos, start=1):
                identity = identities[info]
                owner = identity["seat"]
                n = len(identity["legal_actions"])
                observations = []
                for seed in SEEDS:
                    for readout in (CONTROL, CANDIDATE):
                        case = cases[(seed, readout)]
                        trace = case["traces"][owner]
                        observations.append(
                            dict(
                                seed=seed,
                                readout=readout,
                                policy_sha256=case["policy_sha256"],
                                saved_probabilities=case["exact_policy"][
                                    info, :n
                                ].tolist(),
                                counterfactual_reach=float(
                                    trace.counterfactual_mass[info]
                                ),
                                saved_prefix_reach=float(trace.saved_reach_mass[info]),
                                local_counterfactual_reach=float(
                                    case["local_support"][info]
                                ),
                                best_reply_suffix_action_values_chips=trace.conditional_values[
                                    info, :n
                                ].tolist(),
                                saved_continuation_action_values_chips=case[
                                    "local_values"
                                ][info, :n].tolist(),
                                additive_exploitability_contribution_chips=float(
                                    trace.losses[info] / 2
                                ),
                            )
                        )
                decisions.append(
                    dict(
                        **identity,
                        rank_within_street=rank,
                        control_mean_contribution_chips=float(mean_contribution[info]),
                        observations=observations,
                    )
                )
        panel = dict(game=game, ranked=ranked, decisions=decisions)
        panels.append(panel)
        if events is not None:
            with events.open("a") as stream:
                stream.write(json.dumps(panel, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
    deadline.check()
    return panels
