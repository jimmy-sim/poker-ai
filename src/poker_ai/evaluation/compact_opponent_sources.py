"""Sealed old OWN controls and new compact contexts, scoring inputs only.

Training workers import compact_opponent_contexts, never this saved-policy
loader. Historical native receipts are authenticated scalar comparison data.
They do not supply strategies, actions, initialization or learning targets.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_fixed_inputs as sampled_parent
from poker_ai.evaluation import opponent_learning_cost as old_cost
from poker_ai.evaluation import opponent_learning_sources as old_sources
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.compact_opponent_boundaries import boundaries, load_contexts
from poker_ai.evaluation.compact_opponent_contexts import build_game, refinement
from poker_ai.evaluation.compact_opponent_contract import (
    contract,
    cost_contract,
    input_pins,
)
from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.evaluation.compact_opponent_projection import lift_mass, lift_policy
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import REAL, WORK, Design
from poker_ai.evaluation.opponent_learning_sources import Opponent
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.river_study import Deadline


@dataclass(frozen=True)
class Sources:
    games: tuple[Contexts, Contexts]
    original: old_sources.Sources
    opponents: tuple[Opponent, ...]
    input_sha256: dict[str, str]
    original_boundaries: tuple[dict[str, Any], ...]
    sampled_parent_replay: dict[str, Any]

    def context(self, coordinate: int) -> Contexts:
        Design(REAL, WORK).coordinate(coordinate)
        return self.games[coordinate // 3]


def load(root: Path, deadline: Deadline) -> Sources:
    with isolated(worker=False):
        return _load(root, deadline)


def _load(root: Path, deadline: Deadline) -> Sources:
    pins = input_pins(root)
    config = contract(root)
    old = old_sources.load(root)
    deadline.check()
    games = (build_game(root, 0), build_game(root, 1))
    for game in (0, 1):
        refinement(old.games[game], games[game])
    if canonical(config["frozen_controls"]) != canonical(
        old_sources.contract(root)["frozen_controls"]
    ):
        raise ArithmeticError("fixed scoring opponent inventory changed")
    # This reader checks original named dependency maps and Git blobs, all raw
    # states/books/journals and native scalar receipts. Old strict checkers are
    # unchanged; added modules are not substituted for their original source.
    replay = sampled_parent.replay_sources(root, False)
    deadline.check()
    sampled = root / "results/compact-sampled/real"
    own = json.loads((sampled / "own.json").read_text())
    contexts = load_contexts(root)
    for game, filename in enumerate(config["spot_files"]):
        for representation, kind in (
            ("exact", "fine"),
            (config["coarse_representation"], "coarse"),
        ):
            c = contexts[filename, representation]
            if tree_digest(c.scoring.partition) != tree_digest(games[game].tree(kind)):
                raise ArithmeticError(
                    "original compact/exact structural context changed"
                )
    peers = boundaries(sampled, own, contexts)
    deadline.check()
    if input_pins(root) != pins:
        raise ArithmeticError("compact scientific inputs changed during loading")
    return Sources(games, old, old.opponents, pins, peers, replay)


def standins(root: Path, sources: Sources, deadline: Deadline) -> old_cost.Standins:
    config = cost_contract(root)
    if {int(k): v for k, v in config["source_label_map"].items()} != old_cost.LABELS:
        raise ArithmeticError("old endpoint map changed in compact cost contract")
    old = old_cost.load(root, sources.original, deadline)
    maps = [refinement(sources.original.games[i], sources.games[i]) for i in (0, 1)]
    members = {}
    for key, member in old.members.items():
        coordinate, kind, _, readout = key
        game = coordinate // 3
        before, after = sources.original.games[game], sources.games[game]
        if kind == "fine":
            values, projection = member.values.copy(), dict(projection="unchanged_fine")
        elif readout in ("uniform", "linear"):
            values, projection = lift_mass(before, after, maps[game], member.values)
        else:
            values = lift_policy(before, after, maps[game], member.values)
            projection = dict(projection="unchanged_policy_lift_to_refining_groups")
        values.flags.writeable = False
        members[key] = old_cost.OldMember(
            values,
            dict(
                original_own_member=member.identity,
                before_values_sha256=array_sha(member.values),
                after_values_sha256=array_sha(values),
                learned_compact_values=False,
                **projection,
            ),
        )
        deadline.check()
    if len(members) != 180:
        raise ArithmeticError("complete180 old own cost source members required")
    return old_cost.Standins(members, sources.context)
