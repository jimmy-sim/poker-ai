"""Display one frozen within-partition response row, with visible averaging limits."""

from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.cards import format_card
from poker_ai.evaluation.controlled_reply_inputs import SourcePolicy
from poker_ai.evaluation.controlled_reply_io import read_saved, trace_records
from poker_ai.evaluator import evaluate_best
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.training.no_limit import NoLimitState


def inspect(
    root: Path,
    path: Path,
    *,
    game: str,
    representation: str,
    traversal: str,
    seed: int | None,
    clip: str,
    average: str,
    target: int,
    rank: int,
    native_path: Path | None = None,
) -> dict[str, Any]:
    if (
        type(rank) is not int
        or rank < 1
        or type(target) is not int
        or target not in (0, 1)
    ):
        raise ValueError("choose a positive rank and seat zero or one")
    saved, data = read_saved(root, path)
    audit_path = (
        native_path if native_path is not None else path.with_name("native.json")
    )
    audit_status = "crossed-profile native audit absent; own-trace view only"
    if audit_path.exists():
        import json

        from poker_ai.postflop.pipeline_report import check_source
        from poker_ai.solver_validation.controlled_replies import validate

        native = json.loads(audit_path.read_text())
        check_source(root, native["source"])
        validate(native, saved, path, data)
        audit_status = "crossed-profile native audit verified"

    candidates = [
        p
        for p in data.policies
        if Path(p.case["spot_file"]).stem == game
        and p.case["representation"] == representation
        and p.case["traversal"] == traversal
        and p.case["seed"] == seed
        and p.mode == (clip, average)
    ]
    if len(candidates) != 1:
        raise ValueError("choose a retained source game/mode/seed")
    source: SourcePolicy = candidates[0]
    selected = None
    # Validate the entire archive inventory, including records after the selected one.
    for record in trace_records(path, saved, data):
        if (
            record["summary"]["profile_id"] == source.identifier
            and record["summary"]["target"] == target
        ):
            selected = record
    if selected is None:
        raise ArithmeticError("requested trace missing")
    rows = sorted(selected["rows"], key=lambda row: (-row[1], row[0]))
    if rank > len(rows):
        raise ValueError(f"rank must be at most {len(rows)} owned information rows")
    info, loss, cf, reach, q, choice = rows[rank - 1]
    context = data.context(source.case)
    if not isinstance(context.exact, MatrixTree):
        raise ValueError("card example requires a poker source")
    members = np.flatnonzero(context.exact_to_partition == info)
    representative = int(members[0])
    state = context.exact.source.states[
        context.exact.source.representatives[representative]
    ]
    if state.dealer is None or state.actor != target:
        raise ArithmeticError("representative does not belong to responding seat")
    view = state.dealer.observe(target)
    hand = evaluate_best(view.hole_cards + view.board)
    moves = []
    for action in context.partition.actions[info]:
        decoded = NoLimitState(state.dealer, context.exact.source.spot.rules).decode(
            action
        )
        moves.append(
            decoded.kind.value
            + ("" if decoded.amount is None else f" {decoded.amount}")
        )
    return dict(
        audit_status=audit_status,
        case=source.case,
        source_snapshot_id=source.row["id"],
        target=target,
        info=info,
        rank=rank,
        total_owned_rows=len(rows),
        exact_members=len(members),
        gain_chips=selected["summary"]["gain_chips"],
        street_losses_chips=selected["summary"]["street_losses_chips"],
        loss_chips=loss,
        counterfactual_mass=cf,
        saved_reach_mass=reach,
        actions=moves,
        reply_action=moves[choice],
        saved_probabilities=source.policy[info, : len(moves)].tolist(),
        conditional_values_chips=q,
        street=view.street.name,
        hole=[format_card(c) for c in view.hole_cards],
        board=[format_card(c) for c in view.board],
        hand_category=hand.category.name,
        source_iteration=source.row["iteration"],
        source_work=source.row["total_work"],
    )


def display(row: dict[str, Any]) -> str:
    case = row["case"]
    lines = [
        f"{Path(case['spot_file']).stem}/{case['representation']}; "
        f"{case['traversal']}; {case['regret_rule']}/{case['average_weight']}; "
        f"seed {case['seed']}",
        f"Seat {row['target']}; information row {row['info']}; "
        f"rank {row['rank']}/{row['total_owned_rows']}",
        "Fixed saved opponent; own within-partition reply continuation.",
        "Diagnostic only, not universal poker advice.",
        row["audit_status"],
        f"Source iteration {row['source_iteration']}; "
        f"total node work {row['source_work']:,}",
        f"Unilateral within gain: {row['gain_chips']:.6g} chips; "
        f"row loss: {row['loss_chips']:.6g}",
        f"Street accounting: turn {row['street_losses_chips']['TURN']:.6g}; "
        f"river {row['street_losses_chips']['RIVER']:.6g}",
        f"Example own {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
        f"{row['hand_category']}; {row['street']}",
        f"This shared row has {row['exact_members']} exact members.",
        "Values average all compatible histories, not just these example cards.",
        f"Own reply: {row['reply_action']}; "
        f"saved reach mass {row['saved_reach_mass']:.6g}",
    ]
    for action, probability, q in zip(
        row["actions"],
        row["saved_probabilities"],
        row["conditional_values_chips"],
        strict=True,
    ):
        lines.append(
            f"  {action}: saved probability {probability:.6f}; "
            f"reply-suffix target value {q:.6f} chips"
        )
    return "\n".join(lines)
