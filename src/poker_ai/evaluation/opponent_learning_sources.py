"""Pinned own games, original B4 barriers and frozen own evaluation controls.

Training workers call build_game only: no saved opponent or reference policy is
an input to a learner. The parent loads frozen OWN controls for scoring only.
Historical native receipts are checked data, never native strategy targets.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.evaluation import batch_current_inputs as historical
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.evaluation.frozen_batch_inputs import paths as old_paths
from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import GAMES, REAL, WORK, Design
from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree

CONFIG = "configs/own-opponent-learning.json"
CONFIG_SHA = "e567981a76e2d1ec07d5828d8e36ed6cc4cc9207954c13cb1c181b900f8ea084"
COST_CONFIG = "configs/own-opponent-cost-standins.json"
COST_CONFIG_SHA = "13828f6f7ba0678a73575b6e625039850ba7967c2ef384d2823d977554cde03b"


def cost_contract(root: Path) -> dict[str, Any]:
    if digest(root / COST_CONFIG) != COST_CONFIG_SHA:
        raise ArithmeticError("prospective own cost stand-in contract changed")
    saved: dict[str, Any] = json.loads((root / COST_CONFIG).read_text())
    if saved["parent_config"] != CONFIG or saved["parent_sha256"] != CONFIG_SHA:
        raise ArithmeticError("cost stand-in parent contract changed")
    return saved


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective own-opponent learning contract changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return result


def input_pins(root: Path) -> dict[str, str]:
    pins: dict[str, str] = contract(root)["input_sha256"]
    if any(digest(root / p) != h for p, h in pins.items()):
        raise ArithmeticError("fixed own-opponent learning input bytes changed")
    return dict(pins)


def build_game(root: Path, game: int) -> Contexts:
    """Real structural factory, no learner, saved policy or native construction."""
    if type(game) is not int or game not in (0, 1):
        raise ValueError("choose one of the two prospective known games")
    config = contract(root)
    for path in (GAMES[game], config["model"]):
        if digest(root / path) != config["input_sha256"][path]:
            raise ArithmeticError("own game/model bytes changed")
    source = SpotTree.build(load_spot(root / GAMES[game]))
    fine = MatrixTree.build(source)
    coarse = build_representation_control(
        source,
        config["coarse_representation"],
        CardAbstraction.load(root / config["model"]),
    )
    river = (river_mask(fine, 0), river_mask(fine, 1))
    return Contexts.build(fine, coarse, coarse.exact_to_abstract, river)


@dataclass(frozen=True)
class Opponent:
    identifier: str
    game: int
    policy: FloatArray  # Always expanded to the legal fine game; never a learner input.
    source_policy_sha256: str
    fine_policy_sha256: str
    replies: tuple[Reply, Reply]


def frozen_opponent(
    contexts: Contexts,
    identifier: str,
    game: int,
    fine_policy: FloatArray,
    source_policy_sha256: str,
) -> Opponent:
    tree = contexts.fine
    tree.validate_policy(fine_policy)
    policy = fine_policy.copy()
    policy.flags.writeable = False
    replies = []
    for target in (0, 1):
        result = trace_losses(tree, policy, target, tolerance=1e-9)
        owned = np.flatnonzero(tree.owners == target)
        reply = Reply(
            target, result.value, tuple(int(result.profile[i].argmax()) for i in owned)
        )
        if reply.apply(tree, policy).tobytes() != result.profile.tobytes():
            raise ArithmeticError(
                "own fixed reply choices changed their achieved policy"
            )
        replies.append(reply)
    return Opponent(
        identifier,
        game,
        policy,
        source_policy_sha256,
        array_sha(policy),
        (replies[0], replies[1]),
    )


@dataclass(frozen=True)
class Sources:
    games: tuple[Contexts, Contexts]
    historical: historical.Sources
    opponents: tuple[Opponent, ...]
    input_sha256: dict[str, str]
    original_boundaries: tuple[dict[str, Any], ...]

    def context(self, coordinate: int) -> Contexts:
        Design(REAL, WORK).coordinate(coordinate)
        return self.games[coordinate // 3]


def boundaries(archived: historical.Sources) -> tuple[dict[str, Any], ...]:
    """All original coarse/fine signed B4 controls, including current/books bits."""
    design = Design(REAL, WORK)
    original_paths = old_paths(archived.own["config"])
    result = []
    for index in range(30):
        path = design.path(index)
        if path["path_kind"] not in ("coarse0", "fine"):
            continue
        encoding = "exact" if path["path_kind"] == "fine" else "texture_range_q8_b8"
        chosen = [
            i
            for i, p in enumerate(original_paths)
            if p["batch_size"] == 4
            and p["representation"] == encoding
            and p["regret_rule"] == "signed"
            and p["seed"] == path["seed"]
            and p["spot_file"] == path["spot_file"]
        ]
        if len(chosen) != 1:
            raise ArithmeticError(
                "original B4 coordinate must identify one archived path"
            )
        original = chosen[0]
        for label in WORK:
            selected = {
                name: [
                    r
                    for r in archived.own[name]
                    if r["path_index"] == original and r["work_label"] == label
                ]
                for name in ("rows", "currents", "masses")
            }
            if tuple(len(selected[n]) for n in selected) != (2, 1, 2):
                raise ArithmeticError("original B4 readout/book inventory incomplete")
            current = selected["currents"][0]
            shared = (
                "iteration",
                "previous_work",
                "total_work",
                "last_iteration_visits",
                "initialization_visits",
                "sampled_traversals",
                "guard_sha256",
                "current_sha256",
            )
            average = selected["rows"][0]
            if any(
                not same(average[k], other[k])
                for other in selected["rows"]
                for k in shared
            ):
                raise ArithmeticError("original B4 average readouts changed endpoint")
            if current["guard_sha256"] != average["guard_sha256"]:
                raise ArithmeticError("original B4 current endpoint changed")
            result.append(
                dict(
                    path_index=index,
                    original_path_index=original,
                    work_label=label,
                    **{k: average[k] for k in shared},
                    readouts={
                        r["case"]["average_weight"]: dict(
                            policy_sha256=r["receipt"]["policy_sha256"],
                            state_sha256=r["state_sha256"],
                        )
                        for r in selected["rows"]
                    },
                    mass_sha256={
                        r["case"]["average_weight"]: r["receipt"]["mass_sha256"]
                        for r in selected["masses"]
                    },
                    current_policy_sha256=current["receipt"]["policy_sha256"],
                )
            )
    if len(result) != 36:
        raise ArithmeticError("all36 original B4 boundaries required")
    return tuple(result)


def load(root: Path) -> Sources:
    pins = input_pins(root)
    config = contract(root)
    archived = historical.load(root)
    games = (build_game(root, 0), build_game(root, 1))
    opponents = []
    wanted = {r["id"]: r for r in config["frozen_controls"]}
    seen = set()
    for source in full_sources(archived.data):
        identifier = source.identifier
        if identifier in seen or identifier not in wanted:
            raise ArithmeticError("frozen own opponent inventory changed")
        seen.add(identifier)
        expected = wanted[identifier]
        if (
            not same(source.case, expected["case"])
            or array_sha(source.policy) != expected["policy_sha256"]
        ):
            raise ArithmeticError("frozen own opponent source policy changed")
        game = GAMES.index(source.case["spot_file"])
        context = archived.data.base.context(source.case)
        if tree_digest(context.exact) != tree_digest(games[game].fine):
            raise ArithmeticError("frozen own opponent describes a different fine game")
        expected_tree = (
            games[game].fine
            if source.case["representation"] == "exact"
            else games[game].coarse
        )
        if tree_digest(context.partition) != tree_digest(expected_tree):
            raise ArithmeticError("original own coarse/fine information groups changed")
        expanded = context.expand(source.policy)
        opponents.append(
            frozen_opponent(
                games[game], identifier, game, expanded, expected["policy_sha256"]
            )
        )
    if seen != set(wanted) or any(
        sum(p.game == g for p in opponents) != 8 for g in (0, 1)
    ):
        raise ArithmeticError("all eight frozen own opponents per game required")
    if input_pins(root) != pins:
        raise ArithmeticError("own source inputs changed during loading")
    return Sources(games, archived, tuple(opponents), pins, boundaries(archived))


def verify_boundaries(
    design: Design,
    captures: list[dict[str, Any]],
    masses: list[dict[str, Any]],
    expected: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Original-runtime B4 guard/work/current/average/book barrier, not a score."""
    if design.scope != REAL or design.labels != WORK:
        raise ValueError("original poker B4 barrier requires the real fixed design")
    design.require_rows("captures", captures)
    design.require_rows("masses", masses)
    wanted = {(i, w) for i in range(30) if i % 5 in (0, 4) for w in WORK}
    if (
        len(expected) != 36
        or {(r["path_index"], r["work_label"]) for r in expected} != wanted
    ):
        raise ArithmeticError("complete36 original B4 barriers required")
    by_id = {r["id"]: r for r in captures + masses}
    fields = (
        "iteration",
        "previous_work",
        "total_work",
        "last_iteration_visits",
        "initialization_visits",
        "sampled_traversals",
        "guard_sha256",
        "current_sha256",
    )
    for peer in expected:
        i, work = peer["path_index"], peer["work_label"]
        current = by_id[design.raw(i, work, "current")["id"]]
        if any(not same(current[k], peer[k]) for k in fields) or (
            current["receipt"]["policy_sha256"] != peer["current_policy_sha256"]
        ):
            raise ArithmeticError(
                "ordinary B4 current/work/guard no longer matches archive"
            )
        for weight in ("uniform", "linear"):
            row = by_id[design.raw(i, work, weight + "_average")["id"]]
            mass = by_id[design.mass(i, work, weight)["id"]]
            original = peer["readouts"][weight]
            if (
                any(not same(row[k], peer[k]) for k in fields)
                or row["state_sha256"] != original["state_sha256"]
                or row["receipt"]["policy_sha256"] != original["policy_sha256"]
                or mass["receipt"]["mass_sha256"] != peer["mass_sha256"][weight]
                or mass["guard_sha256"] != peer["guard_sha256"]
            ):
                raise ArithmeticError(
                    "ordinary B4 average/book bits no longer match archive"
                )
    return dict(
        original_work_boundaries=36,
        original_policy_bits=108,
        original_ledger_bits=72,
        status="all_original_B4_boundaries_match_exactly",
    )
