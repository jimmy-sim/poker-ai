"""Frozen completed-study inputs for read-only own decision inspection."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation.opponent_learning_admission import native_receipt
from poker_ai.evaluation.opponent_learning_cli import read
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import REAL, WORK, Design
from poker_ai.evaluation.opponent_learning_score import scoring
from poker_ai.evaluation.opponent_learning_sources import build_game
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.river_study import Deadline, digest

CONFIG = "configs/own-opponent-decisions.json"
CONFIG_SHA = "8e09241f9f27b95dc535c1623547cf84d29b628fb5c56a25f3d04dc541dff0f8"
FOLDER = "results/opponent-decisions"
ENTRIES = (
    "scripts/trace_own_opponent_decisions.py",
    "scripts/inspect_own_opponent_decisions.py",
)


def contract(root: Path) -> dict[str, Any]:
    path = root / CONFIG
    if digest(path) != CONFIG_SHA:
        raise ArithmeticError("frozen saved-decision protocol changed")
    config: dict[str, Any] = json.loads(path.read_text())
    json.dumps(config, allow_nan=False)
    return config


def panel(config: dict[str, Any], own: dict[str, Any]) -> list[dict[str, Any]]:
    """Select the complete prospective panel from the complete original grid."""
    design = Design(REAL, WORK)
    design.require_rows("arms", own["arms"])
    design.require_rows("profiles", own["rows"])
    rows = {row["id"]: row for row in own["rows"]}
    selected = []
    for arm in own["arms"]:
        if (
            arm["work_label"] == config["work_label"]
            and arm["readout"] == config["readout"]
        ):
            selected.append(
                dict(
                    coordinate=arm["coordinate"],
                    game=config["games"][arm["coordinate"] // 3],
                    seed=arm["seed"],
                    arm=arm["arm"],
                    row=rows[arm["id"]],
                )
            )
    keys = {(r["game"], r["seed"], r["arm"]) for r in selected}
    expected = {
        (g, s, a)
        for g in config["games"]
        for s in config["seeds"]
        for a in config["arms"]
    }
    if (
        len(selected) != config["expected_profiles"]
        or len(keys) != len(selected)
        or keys != expected
    ):
        raise ArithmeticError("complete24-profile saved decision panel required")
    return selected


def checked(root: Path, config: dict[str, Any], deadline: Deadline) -> dict[str, Any]:
    for name in ("own", "native", "learning_config"):
        path = root / config[name]
        if (
            not path.resolve().is_relative_to(root.resolve())
            or digest(path) != config[name + "_sha256"]
        ):
            raise ArithmeticError("bound saved-decision source input changed")
    own = read(root, root / config["own"], deadline)
    native = native_receipt(
        root, root / config["native"], root / config["own"], own, "audit"
    )
    if own["scope"] != REAL or any(
        data["source_sha256"] != config["historical_source_sha256"]
        for data in (own, native)
    ):
        raise ArithmeticError("completed real own/native source cohort required")
    deadline.check()
    return own


@dataclass(frozen=True)
class Profile:
    coordinate: int
    game: str
    seed: int
    arm: str
    row: dict[str, Any]
    contexts: Contexts
    policy: FloatArray
    fine_policy: FloatArray

    def identity(self) -> dict[str, Any]:
        return dict(
            coordinate=self.coordinate,
            game=self.game,
            seed=self.seed,
            arm=self.arm,
            source_id=self.row["id"],
            policy_sha256=self.row["receipt"]["policy_sha256"],
        )


def profiles(
    root: Path, config: dict[str, Any], own: dict[str, Any], deadline: Deadline
) -> list[Profile]:
    selected = panel(config, own)
    contexts = (build_game(root, 0), build_game(root, 1))
    wanted = {r["row"]["id"]: r for r in selected}
    found: dict[str, Profile] = {}
    path = root / config["own"]
    for row, blob in read_archive(
        path.parent / own["details_file"], own["details_sha256"], own["rows"]
    ):
        deadline.check()
        if row["id"] not in wanted:
            continue
        if row["id"] in found:
            raise ArithmeticError("duplicate selected decision archive member")
        identity = wanted[row["id"]]
        context = contexts[identity["coordinate"] // 3]
        scored = scoring(context, row)
        policy = unpack_policy(scored.partition, decode(blob, scored, row)["policy"])
        fine = scored.expand(policy)
        policy.flags.writeable = fine.flags.writeable = False
        found[row["id"]] = Profile(
            identity["coordinate"],
            identity["game"],
            identity["seed"],
            identity["arm"],
            row,
            context,
            policy,
            fine,
        )
    if set(found) != set(wanted):
        raise ArithmeticError("complete24 saved policy archive members required")
    return [found[r["row"]["id"]] for r in selected]
