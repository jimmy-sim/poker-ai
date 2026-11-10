"""Browse one verified same-update pair; row L1 is not EV loss or importance."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_strategy_viewer import example, rank_rows
from poker_ai.evaluation.matched_update_data import OWN, READOUTS, SEEDS, Data, load
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.river_study import digest


@dataclass(frozen=True)
class Selection:
    game: str = "dev_medium_oop"
    representation: str = "texture_range_q8_b8"
    rule: str = "signed"
    seed: int = 20261301
    batch: int = 4
    readout: str = "linear_average"

    def __post_init__(self) -> None:
        if (
            self.game not in ("dev_low_oop", "dev_medium_oop")
            or self.representation not in ("exact", "texture_range_q8_b8")
            or self.rule not in ("signed", "clipped")
            or self.readout not in READOUTS
            or type(self.seed) is not int
            or self.seed not in SEEDS
            or type(self.batch) is not int
            or self.batch not in (4, 16)
        ):
            raise ValueError("choose a declared game/encoding/rule/seed/batch/readout")


def select(
    saved: dict[str, Any], request: Selection
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = {r["id"]: r for r in saved["rows"]}
    found = []
    for pair in saved["self_pairs"]:
        row = rows[pair["planned_prefix_id"]]
        case = row["case"]
        if (
            Path(case["spot_file"]).stem == request.game
            and case["representation"] == request.representation
            and case["regret_rule"] == request.rule
            and case["seed"] == request.seed
            and row["comparison_batch_size"] == request.batch
            and pair["readout"] == request.readout
        ):
            found.append((pair, row))
    if len(found) != 1:
        raise ArithmeticError(
            "selection must identify exactly one complete matched pair"
        )
    return found[0]


@dataclass(frozen=True)
class Comparison:
    context: ScoringContext
    request: Selection
    left: dict[str, Any]
    right: dict[str, Any]
    left_policy: FloatArray
    right_policy: FloatArray
    pot: float

    def rows(self, seat: int) -> list[tuple[int, float]]:
        return rank_rows(
            self.context.partition, self.left_policy, self.right_policy, seat
        )


def from_data(data: Data, request: Selection) -> Comparison:
    pair, left = select(data.own, request)
    right = data.right[pair["reused_profile_id"]]
    if not left["iteration"] == right["iteration"] == pair["target_iteration"]:
        raise ArithmeticError(
            "both saved strategies must have exactly the target updates"
        )
    context = data.sources.context(left["path_index"])
    root = data.root
    own_path = root / OWN
    if request.readout == "current":
        other_path = root / "results/batch-current-diagnosis/own.json"
        if (
            digest(other_path)
            != data.own["source_inputs"][str(other_path.relative_to(root))]
        ):
            raise ArithmeticError("saved current source changed during browsing load")
        other = json.loads(other_path.read_text())
    else:
        other_path = data.sources.archived.own_path
        other = data.sources.archived.own
    chosen = {left["id"]: left, right["id"]: right}
    policies = {}
    for path, receipt in ((own_path, data.own), (other_path, other)):
        for row, blob in read_archive(
            archive_path(path, receipt["details_file"]),
            receipt["details_sha256"],
            receipt["rows"],
        ):
            if row["id"] in chosen:
                if row["id"] in policies:
                    raise ArithmeticError("duplicate selected archive identity")
                policy = unpack_policy(
                    context.partition,
                    decode(blob, context, chosen[row["id"]])["policy"],
                )
                policy.flags.writeable = False
                policies[row["id"]] = policy
    if set(policies) != set(chosen):
        raise ArithmeticError("selected own policy archive missing")
    return Comparison(
        context,
        request,
        left,
        right,
        policies[left["id"]],
        policies[right["id"]],
        data.pots[left["case"]["spot_file"]],
    )


def load_pair(
    root: Path, request: Selection, progress: Callable[[str], object] = print
) -> Comparison:
    data = load(root, progress)
    progress("Loading the two selected saved policies; this does not run a learner.")
    return from_data(data, request)


def display(comparison: Comparison, seat: int, rank: int) -> str:
    rows = comparison.rows(seat)
    if type(rank) is not int or not 1 <= rank <= len(rows):
        raise ValueError(f"choose a rank from 1 to {len(rows)}")
    info, distance = rows[rank - 1]
    view = example(comparison.context, info, seat)
    r = comparison.request
    a = comparison.left
    b = comparison.right
    lines = [
        f"{r.game}/{r.representation}; {r.rule}; seed {r.seed}; {r.readout}",
        f"Matched updates: {a['iteration']:,} for BOTH strategies.",
        f"B1 prefix: {a['total_work']:,} node visits; B{r.batch}: {b['total_work']:,}.",
        f"B1/batch actual work ratio: {a['total_work'] / b['total_work']:.6f}.",
        "These are the same update count, with unequal computational work.",
        f"Seat {seat}; rank {rank}/{len(rows)}; information row {info}.",
        f"Unweighted action-probability L1: {distance:.9f} (range 0 to 2).",
        "L1 is not EV loss, reach-weighted importance or poker advice.",
    ]
    for label, row in (("B1 prefix", a), (f"B{r.batch}", b)):
        value = row["metrics"]["exact_exploitability_chips"]
        lines.append(
            f"{label} self-profile exact exploitability: {value:.9f} chips "
            f"({100 * value / comparison.pot:.6f}% initial pot)."
        )
    lines += [
        f"Own {' '.join(view['hole'])}; board {' '.join(view['board'])}; "
        f"{view['street']}; pot {view['pot']}.",
        f"Shared row has {view['exact_members']} exact members; this is one example.",
    ]
    for i, move in enumerate(view["actions"]):
        lines.append(
            f"  {move}: B1 {comparison.left_policy[info, i]:.6f}; "
            f"B{r.batch} {comparison.right_policy[info, i]:.6f}"
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
        rank = min(count, rank + 1) if command == "n" else max(1, rank - 1)
        write(display(comparison, seat, rank))
