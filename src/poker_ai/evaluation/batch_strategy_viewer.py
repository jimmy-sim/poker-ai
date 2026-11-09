"""Read immutable own strategies; L1 is distribution difference, not EV loss."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.cards import format_card
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_inputs import Sources
from poker_ai.evaluation.batch_current_run import read_saved
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.solver_validation.batch_currents import read as read_native
from poker_ai.training.no_limit import NoLimitState

READOUTS = ("current", "uniform_average", "linear_average")


@dataclass(frozen=True)
class Selection:
    game: str
    representation: str
    rule: str
    seed: int
    work: int
    batch: int
    readout: str

    def __post_init__(self) -> None:
        if (
            self.game not in ("dev_low_oop", "dev_medium_oop")
            or self.representation not in ("exact", "texture_range_q8_b8")
            or self.rule not in ("signed", "clipped")
            or type(self.seed) is not int
            or self.seed not in (20261301, 20261302, 20261303)
            or type(self.work) is not int
            or self.work not in (100_000, 1_000_000, 10_000_000)
            or type(self.batch) is not int
            or self.batch not in (1, 4, 16)
            or self.readout not in READOUTS
        ):
            raise ValueError(
                "choose a retained game, encoding, rule, seed/work/batch/readout"
            )


def select(rows: list[dict[str, Any]], request: Selection) -> dict[str, Any]:
    found = []
    for row in rows:
        case = row["case"]
        readout = (
            "current"
            if row.get("variant") == "current"
            else case["average_weight"] + "_average"
        )
        if (
            Path(case["spot_file"]).stem == request.game
            and case["representation"] == request.representation
            and case["regret_rule"] == request.rule
            and case["seed"] == request.seed
            and row["work_label"] == request.work
            and row["batch_size"] == request.batch
            and readout == request.readout
        ):
            found.append(row)
    if len(found) != 1:
        raise ValueError("selection must identify exactly one saved own policy")
    return found[0]


def rank_rows(
    tree: ArrayTree, left: FloatArray, right: FloatArray, seat: int
) -> list[tuple[int, float]]:
    """All owned rows, including unreachable/zero differences; no reach weights."""
    if type(seat) is not int or seat not in (0, 1):
        raise ValueError("choose seat zero or one")
    for policy in (left, right):
        tree.validate_policy(policy)
    difference = np.abs(left - right).sum(axis=1)
    rows = [
        (i, float(difference[i]))
        for i, owner in enumerate(tree.owners)
        if owner == seat
    ]
    return sorted(rows, key=lambda item: (-item[1], item[0]))


@dataclass(frozen=True)
class Comparison:
    context: ScoringContext
    left: dict[str, Any]
    right: dict[str, Any]
    left_policy: FloatArray
    right_policy: FloatArray
    left_request: Selection
    right_request: Selection

    def rows(self, seat: int) -> list[tuple[int, float]]:
        return rank_rows(
            self.context.partition, self.left_policy, self.right_policy, seat
        )


def load(root: Path, left: Selection, right: Selection) -> Comparison:
    # Differences in batch/readout are allowed. Changing the game/information
    # groups, seed or work label cannot be treated as a matched row comparison.
    if (
        left.game,
        left.representation,
        left.rule,
        left.seed,
        left.work,
    ) != (right.game, right.representation, right.rule, right.seed, right.work):
        raise ValueError("compare the same game, encoding, rule, seed and work label")
    path = root / "results/batch-current-diagnosis/own.json"
    saved, sources = read_saved(root, path)
    read_native(root, path.with_name("native.json"), saved, path)
    averages = [r for r in sources.own["rows"] if r["path_index"] < 72]
    rows = [*saved["rows"], *averages]
    a, b = select(rows, left), select(rows, right)
    context = sources.data.base.context(a["case"])
    policies = _policies(path, saved, sources, context, {a["id"], b["id"]})
    return Comparison(context, a, b, policies[a["id"]], policies[b["id"]], left, right)


def _policies(
    path: Path,
    saved: dict[str, Any],
    sources: Sources,
    context: ScoringContext,
    wanted: set[str],
) -> dict[str, FloatArray]:
    result = {}
    for receipt, receipt_path in ((saved, path), (sources.own, sources.own_path)):
        # Verify the full archive inventory/hash even if only one policy is needed.
        for row, blob in read_archive(
            archive_path(receipt_path, receipt["details_file"]),
            receipt["details_sha256"],
            receipt["rows"],
        ):
            if row["id"] in wanted:
                detail = decode(blob, context, row)
                result[row["id"]] = unpack_policy(context.partition, detail["policy"])
    if set(result) != wanted:
        raise ArithmeticError("selected own archive policy missing")
    return result


def example(context: ScoringContext, info: int, seat: int) -> dict[str, Any]:
    if not isinstance(context.exact, MatrixTree):
        raise ValueError("card example requires the saved poker game")
    if type(info) is not int or not 0 <= info < len(context.partition.keys):
        raise ValueError("unknown information row")
    if type(seat) is not int or seat not in (0, 1):
        raise ValueError("choose seat zero or one")
    if context.partition.owners[info] != seat:
        raise ValueError("row belongs to the other seat")
    members = np.flatnonzero(context.exact_to_partition == info)
    if not len(members):
        raise ArithmeticError("shared row has no exact representative")
    exact = int(members[0])
    state = context.exact.source.states[context.exact.source.representatives[exact]]
    if state.dealer is None or state.actor != seat:
        raise ArithmeticError("representative does not belong to selected acting seat")
    view = state.dealer.observe(seat)
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
        hole=[format_card(c) for c in view.hole_cards],
        board=[format_card(c) for c in view.board],
        street=view.street.name,
        pot=state.dealer.pot,
        actions=moves,
        exact_members=len(members),
    )


def display(comparison: Comparison, seat: int, rank: int) -> str:
    rows = comparison.rows(seat)
    if type(rank) is not int or not 1 <= rank <= len(rows):
        raise ValueError(f"choose a rank from 1 to {len(rows)}")
    info, difference = rows[rank - 1]
    view = example(comparison.context, info, seat)
    request = comparison.left_request
    lines = [
        f"{request.game}/{request.representation}; {request.rule}; seed {request.seed}",
        f"Seat {seat}; rank {rank}/{len(rows)}; information row {info}",
        "Verified saved own policies; no training or reference construction.",
        f"Unweighted action-probability L1 difference: {difference:.9f} "
        "(range 0 to 2).",
        "This ranking is not EV loss, reach-weighted importance or poker advice.",
    ]
    for name, row, choice in (
        ("Left", comparison.left, comparison.left_request),
        ("Right", comparison.right, comparison.right_request),
    ):
        lines.append(
            f"{name}: B{choice.batch}/{choice.readout}; snapshot {row['id']}; "
            f"updates {row['iteration']:,}; charged node work {row['total_work']:,}"
        )
    lines.extend(
        [
            "Same work label; actual overshoot and number of updates may differ.",
            f"Representative own {' '.join(view['hole'])}; "
            f"board {' '.join(view['board'])}; {view['street']}; pot {view['pot']}",
            f"Shared row has {view['exact_members']} exact members; "
            "this is one example, not a summary of every member.",
        ]
    )
    for i, move in enumerate(view["actions"]):
        lines.append(
            f"  {move}: left {comparison.left_policy[info, i]:.6f}; "
            f"right {comparison.right_policy[info, i]:.6f}"
        )
    return "\n".join(lines)


def browse(
    comparison: Comparison,
    seat: int,
    rank: int,
    *,
    read: Callable[[str], str] = input,
    write: Callable[[str], object] = print,
) -> None:
    count = len(comparison.rows(seat))
    write(display(comparison, seat, rank))
    while True:
        try:
            command = read("n next, p previous, q quit > ").strip().lower()
        except EOFError:
            return
        if command == "q":
            return
        if command not in ("n", "p"):
            write("Use n, p or q.")
            continue
        rank = max(1, min(count, rank + (1 if command == "n" else -1)))
        write(display(comparison, seat, rank))
