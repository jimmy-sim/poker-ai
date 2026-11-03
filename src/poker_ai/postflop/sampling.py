"""Own sampling controls: iteration weighting and one exact initial expectation."""

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from numpy.random import Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.training.checkpoint import load_checkpoint, save_checkpoint
from poker_ai.training.mccfr import MCCFR, RootFactory, Row, external_updates

Weighting = Literal["uniform", "linear"]


class PostflopMCCFR(MCCFR):
    """External sampling with optional raw linear regrets/averages and visit audit.

    Linear R accumulates sum_t t*delta_t, equivalent up to common positive scale
    to the full-tree Linear CFR recurrence. Both regret and averaging increments
    receive t; no clipping. Conditional expectation is preserved by deterministic
    scaling. Pure uniform weighting preserves the original sampled trajectory.
    """

    def __init__(
        self,
        root_factory: RootFactory,
        rng: Generator,
        weighting: Weighting = "uniform",
    ) -> None:
        if weighting not in ("uniform", "linear"):
            raise ValueError("unknown sampling weighting")
        super().__init__(root_factory, rng, method="external")
        self.weighting = weighting
        self.sampled_keys: set[str] = set()
        self.warm_node_equivalent = 0
        self._collect_visits = False

    def _row(self, key: str, actions: tuple[int, ...]) -> Row:
        if self._collect_visits:
            self.sampled_keys.add(key)
        return super()._row(key, actions)

    def step(self) -> None:
        t = self.iteration + 1
        weight = float(t) if self.weighting == "linear" else 1.0

        def select(probabilities: FloatArray) -> int:
            return int(self.rng.choice(len(probabilities), p=probabilities))

        self._collect_visits = True
        try:
            for target in (0, 1):
                updates = external_updates(
                    self.root_factory(self.rng), target, self.policy, select
                )
                for key, delta in updates.regrets.items():
                    self.rows[key].regrets += weight * delta
                for key, mass in updates.averages.items():
                    self.rows[key].strategy_sum += weight * mass
                self.nodes_visited += updates.visited
        finally:
            self._collect_visits = False
        self.iteration = t


def exact_initial_expectation(solver: PostflopMCCFR, tree: ArrayTree) -> None:
    """Integrate the uniform policy's simultaneous initial updates over all worlds.

    This is one own-game expected iteration, not reference supervision. Expected
    simple external averaging for each player equals sum chance*own_reach*sigma
    over its histories. All rows get an actual regret and averaging calculation.
    Subsequent iterations alternate normally. Initial-only rows remain separately
    identified; this finite full-tree operation does not scale to global Hold'em.
    """
    if solver.iteration or solver.rows:
        raise ValueError("initial expectation requires an empty solver")
    policy = tree.normalize(tree.legal)
    edges = tree.edges(policy)
    reaches = tree.reaches(edges)
    values = tree.values(edges)
    regrets, averages = np.zeros_like(tree.legal), np.zeros_like(tree.legal)
    for target in (0, 1):
        nodes = np.flatnonzero(tree.player == target)
        infos = tree.information[nodes]
        advantage = (values[tree.children[nodes]] - values[nodes, None]) * tree.valid[
            nodes
        ]
        advantage *= 1 if target == 0 else -1
        cf = tree.chance_reach[nodes] * reaches[nodes, 1 - target]
        np.add.at(regrets, infos, cf[:, None] * advantage)
        mass = tree.chance_reach[nodes] * reaches[nodes, target]
        np.add.at(averages, infos, mass[:, None] * policy[infos])
    for info, key in enumerate(tree.keys):
        n = len(tree.actions[info])
        solver.rows[key] = Row(
            tree.actions[info], regrets[info, :n].copy(), averages[info, :n].copy()
        )
    solver.iteration = 1
    solver.warm_node_equivalent = 2 * len(tree.player)


def save_learning_checkpoint(
    solver: PostflopMCCFR,
    path: Path,
    *,
    config: dict[str, Any],
    provenance: dict[str, Any],
) -> None:
    save_checkpoint(solver, path, config=config, provenance=provenance)
    visits = {
        "format": "poker-ai-own-postflop-visits-v1",
        "core_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "weighting": solver.weighting,
        "sampled_keys": sorted(solver.sampled_keys),
        "warm_node_equivalent": solver.warm_node_equivalent,
    }
    path.with_suffix(".visits.json").write_text(
        json.dumps(visits, sort_keys=True) + "\n"
    )


def load_learning_checkpoint(
    path: Path, root_factory: RootFactory, *, expected_config: dict[str, Any]
) -> PostflopMCCFR:
    """Restore weighting AND visit audit; a mismatched/incomplete pair is rejected."""
    core = load_checkpoint(path, root_factory, expected_config=expected_config)
    visits = json.loads(path.with_suffix(".visits.json").read_text())
    if (
        set(visits)
        != {
            "format",
            "core_sha256",
            "weighting",
            "sampled_keys",
            "warm_node_equivalent",
        }
        or visits["format"] != "poker-ai-own-postflop-visits-v1"
        or visits["core_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest()
        or visits["weighting"] not in ("uniform", "linear")
    ):
        raise ValueError("invalid own learning checkpoint visit metadata")
    keys = visits["sampled_keys"]
    if (
        not isinstance(keys, list)
        or any(not isinstance(k, str) or k not in core.rows for k in keys)
        or len(set(keys)) != len(keys)
        or type(visits["warm_node_equivalent"]) is not int
        or visits["warm_node_equivalent"] < 0
    ):
        raise ValueError("invalid sampled visit keys/cost")
    expected_weighting = expected_config["learning"].get(
        "sampling_weighting", "uniform"
    )
    if visits["weighting"] != expected_weighting:
        raise ValueError("learning checkpoint weighting mismatch")
    result = PostflopMCCFR(root_factory, core.rng, cast(Weighting, visits["weighting"]))
    result.epsilon = core.epsilon
    result.rows, result.iteration, result.nodes_visited = (
        core.rows,
        core.iteration,
        core.nodes_visited,
    )
    result.sampled_keys, result.warm_node_equivalent = (
        set(keys),
        visits["warm_node_equivalent"],
    )
    return result
