"""Replay saved profiles and measure complete fixed-turn continuation controls."""

import argparse
import gzip
import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import numpy as np

from poker_ai.cards import format_card
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_decision_inputs import (
    Profile,
    checked,
    profiles,
)
from poker_ai.evaluation.opponent_decision_inputs import contract as old_contract
from poker_ai.evaluation.opponent_decision_run import BLOCKED, forbidden
from poker_ai.evaluation.opponent_learning_clock import atomic
from poker_ai.evaluation.opponent_learning_score import scoring
from poker_ai.evaluation.turn_continuation_io import (
    CONFIG,
    CONFIG_SHA,
    ENTRIES,
    FOLDER,
    contract,
    prior,
    validate_profiles,
    validate_response,
)
from poker_ai.evaluation.turn_continuation_math import PANELS, continuations
from poker_ai.evaluator import evaluate_best
from poker_ai.postflop.controlled_checkpoints import pack_policy, unpack_policy
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.training.no_limit import NoLimitState
from poker_ai.validation.five_card import source_provenance


def analyse_profile(
    profile: Profile,
    previous: dict[str, Any],
    previous_detail: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    context = scoring(profile.contexts, profile.row)
    fine = cast(MatrixTree, context.exact)
    tolerance = config["absolute_tolerance_chips"]
    streets = []
    for info, node in enumerate(fine.source.representatives):
        state = fine.source.states[node]
        assert state.dealer is not None
        name = state.dealer.street.name
        if name not in ("TURN", "RIVER"):
            raise ArithmeticError("turn-start continuation game required")
        streets.append(name)
        for target in (0, 1):
            if bool(context.river_masks[target][info]) != (
                int(fine.owners[info]) == target and name == "RIVER"
            ):
                raise ArithmeticError("source river mask changes street/seat")
    summaries, details = [], []
    for target in (0, 1):
        result = continuations(context, profile.policy, target, tolerance=tolerance)
        previous_response = previous["responses"][target]
        old = previous_detail["responses"][target]
        if old["target"] != target or previous_response["target"] != target:
            raise ArithmeticError("prior response seat changed")
        old_rows = old["infos"]
        if [r["exact_info"] for r in old_rows] != list(
            np.flatnonzero(fine.owners == target)
        ):
            raise ArithmeticError("prior complete owned-row inventory changed")
        lookup = {r["exact_info"]: r for r in old_rows}
        river = context.river_masks[target]
        for panel, previous_name in (
            (1, "restricted_reply_profile"),
            (2, "exact_reply_profile"),
        ):
            old_reply = unpack_policy(fine, old[previous_name])
            key = "restricted" if panel == 1 else "exact"
            if (
                sha(pack_policy(fine, old_reply))
                != profile.row["reply_sha256"][target][key]
            ):
                raise ArithmeticError("prior full reply fingerprint changed")
            if result.policies[panel][river].tobytes() != old_reply[river].tobytes():
                raise ArithmeticError(
                    "river-only response differs from prior reply slice"
                )
        if (
            sha(pack_policy(fine, result.policies[3]))
            != profile.row["reply_sha256"][target]["exact"]
        ):
            raise ArithmeticError("complete fine response fingerprint changed")
        errors = [
            result.maximum_error,
            abs(result.root_values[0] - previous_response["baseline_value_chips"]),
            abs(result.root_values[3] - previous_response["exact_reply_value_chips"]),
        ]
        rows = []
        for raw_info in np.flatnonzero((fine.owners == target) & ~river):
            info = int(raw_info)
            source = lookup[info]
            count = len(fine.actions[info])
            errors.extend(
                (
                    abs(float(result.support[info]) - source["counterfactual_mass"]),
                    float(
                        np.max(
                            np.abs(
                                result.conditional_values[3][info, :count]
                                - source["conditional_values_chips"]
                            ),
                            initial=0,
                        )
                    ),
                )
            )
            state = fine.source.states[fine.source.representatives[info]]
            assert state.dealer is not None
            observation = state.dealer.observe(target)
            labels = []
            for action in fine.actions[info]:
                move = NoLimitState(state.dealer, fine.source.spot.rules).decode(action)
                labels.append(
                    move.kind.value + ("" if move.amount is None else f" {move.amount}")
                )
            rows.append(
                dict(
                    exact_info=info,
                    abstract_info=int(context.exact_to_partition[info]),
                    hole=[format_card(c) for c in observation.hole_cards],
                    board=[format_card(c) for c in observation.board],
                    street="TURN",
                    hand_category=evaluate_best(
                        observation.hole_cards + observation.board
                    ).category.name,
                    pot=observation.pot,
                    history=[
                        dict(
                            seat=h.seat,
                            street=h.street.name,
                            kind=h.action.kind.value,
                            amount=h.action.amount,
                            chips_paid=h.chips_paid,
                        )
                        for h in observation.history
                    ],
                    actions=labels,
                    saved_probabilities=profile.fine_policy[info, :count].tolist(),
                    support=float(result.support[info]),
                    saved_reach_mass=source["saved_reach_mass"],
                    prior_loss_chips=source["loss_chips"],
                    conditional_action_values_chips={
                        name: q[info, :count].tolist()
                        for name, q in zip(
                            PANELS, result.conditional_values, strict=True
                        )
                    },
                )
            )
        groups = []
        for group in sorted({r["abstract_info"] for r in rows}):
            members = [r for r in rows if r["abstract_info"] == group]
            supported = [r["exact_info"] for r in members if r["support"] > 0]
            if supported:
                groups.append(
                    dict(
                        abstract_info=group,
                        prior_loss_chips=sum(r["prior_loss_chips"] for r in members),
                        infos=supported,
                    )
                )
        groups.sort(key=lambda g: (-g["prior_loss_chips"], g["abstract_info"]))
        response = dict(
            target=target,
            root_values_chips=dict(zip(PANELS, result.root_values, strict=True)),
            root_increments_chips=list(result.increments),
            source_unilateral_gain_chips=previous_response["exact_gain_chips"],
            panel_policy_sha256=dict(
                zip(PANELS, (array_sha(p) for p in result.policies), strict=True)
            ),
            turn_info_ids=[r["exact_info"] for r in rows],
            supported_turn_rows=sum(r["support"] > 0 for r in rows),
            top_turn_groups=groups[: config["top_turn_groups"]],
            maximum_source_accounting_error_chips=max(errors),
        )
        validate_response(response, rows)
        if any(not np.isfinite(e) or e > tolerance for e in errors):
            raise ArithmeticError("continuation source/root/action values changed")
        summaries.append(response)
        details.append(dict(target=target, turn_rows=rows))
    return dict(responses=summaries), dict(responses=details)


def run(root: Path, output: Path, started: float) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing complete/partial continuation output")
    config = contract(root)
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    provenance = source_provenance(root, root / CONFIG, entrypoints=ENTRIES)
    if provenance["dirty"] is not False:
        raise ValueError("publish clean continuation source before reproduction")
    output.mkdir(parents=True)
    summaries: list[dict[str, Any]] = []
    try:
        with ExitStack() as stack:
            for name in BLOCKED:
                stack.enter_context(patch(name, forbidden))
            print(
                "Replaying frozen inputs; learner/reference constructors blocked...",
                flush=True,
            )
            previous = prior(root, config)
            old_config = old_contract(root)
            own = checked(root, old_config, deadline)
            selected = profiles(root, old_config, own, deadline)
            old_by_id = {p["source_id"]: p for p in previous}
            (output / "details").mkdir()
            for profile in selected:
                deadline.check()
                before = (
                    tree_digest(profile.contexts.fine),
                    tree_digest(profile.contexts.coarse),
                    array_sha(profile.policy),
                    array_sha(profile.fine_policy),
                )
                old = old_by_id[profile.row["id"]]
                with gzip.open(
                    root / config["decision_folder"] / old["details_file"], "rt"
                ) as stream:
                    old_detail = json.load(stream)
                summary, detail = analyse_profile(profile, old, old_detail, config)
                if before != (
                    tree_digest(profile.contexts.fine),
                    tree_digest(profile.contexts.coarse),
                    array_sha(profile.policy),
                    array_sha(profile.fine_policy),
                ):
                    raise ArithmeticError(
                        "continuation diagnosis mutated saved game/policy"
                    )
                filename = f"details/{profile.coordinate:02d}-{profile.arm}.json.gz"
                with (output / filename).open("xb") as raw:
                    with gzip.GzipFile(
                        fileobj=raw, mode="wb", filename="", mtime=0
                    ) as stream:
                        stream.write(canonical(dict(**profile.identity(), **detail)))
                summaries.append(
                    dict(**profile.identity(), **summary, details_file=filename)
                )
                atomic(
                    output / "partial.json",
                    dict(
                        status="partial",
                        profiles=summaries,
                        training_performed=False,
                        reference_constructed=False,
                    ),
                )
                print(
                    f"controlled {profile.game}/{profile.seed}/{profile.arm} "
                    f"({len(summaries)}/24)",
                    flush=True,
                )
            validate_profiles(summaries, config)
            prior(root, config)
        if (
            source_provenance(root, root / CONFIG, entrypoints=ENTRIES)["sha256"]
            != provenance["sha256"]
        ):
            raise ArithmeticError("continuation source changed during diagnosis")
        atomic(output / "summary.json", dict(profiles=summaries))
        deadline.check()
        manifest = dict(
            status="complete_fixed_turn_continuations",
            config_sha256=CONFIG_SHA,
            source=provenance,
            source_sha256=sha(provenance["sha256"]),
            decision_manifest_sha256=config["decision_manifest_sha256"],
            profiles=24,
            responses=48,
            root_values=192,
            turn_rows=sum(
                len(r["turn_info_ids"]) for p in summaries for r in p["responses"]
            ),
            maximum_source_accounting_error_chips=max(
                r["maximum_source_accounting_error_chips"]
                for p in summaries
                for r in p["responses"]
            ),
            maximum_seconds=config["maximum_seconds"],
            clock_scope=config["clock_scope"],
            seconds=time.perf_counter() - started,
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            new_independent_audit=False,
            new_agent_default=False,
            fresh_global_admission=False,
            environment=runtime_environment(),
            limits=(
                "Known saved profiles. New continuation calculations have no new "
                "native audit. Conditional row values are not additive root "
                "losses or retraining EV."
            ),
            outputs={
                str(p.relative_to(output)): digest(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        )
        atomic(output / "manifest.json", manifest)
        deadline.check()
        return manifest
    except BaseException as exc:
        atomic(
            output / "failure.json",
            dict(
                status="failed_retained",
                failure=dict(type=type(exc).__name__, message=str(exc)),
                completed_profiles=len(summaries),
                seconds=time.perf_counter() - started,
                training_performed=False,
                reference_constructed=False,
                new_agent_default=False,
                fresh_global_admission=False,
            ),
        )
        raise


def main(root: Path, started: float) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    result = run(root, root / args.output, started)
    print(f"{result['status']}: 24 profiles / 48 conditions / 192 root values")
    return 0
