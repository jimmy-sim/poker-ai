"""Frozen six-control factories; software fixtures share the real array path."""

from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.public_metrics import collision_summary
from poker_ai.postflop.public_range_definition import (
    build_control,
    check_inputs,
    contract,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import evaluate
from poker_ai.toy.tree import Tree


def mass(tree: ArrayTree, policy: FloatArray) -> FloatArray:
    reach = tree.chance_reach * tree.reaches(tree.edges(policy)).prod(axis=1)
    result = np.zeros(len(tree.keys))
    nodes = tree.player >= 0
    np.add.at(result, tree.information[nodes], reach[nodes])
    return result


@dataclass(frozen=True)
class Context:
    spot_file: str
    representation: str
    context_sha256: str
    scoring: ScoringContext
    pot: float
    diagnostics: dict[str, Any]

    @property
    def identity(self) -> dict[str, str]:
        return dict(
            spot_file=self.spot_file,
            representation=self.representation,
            context_sha256=self.context_sha256,
        )

    @property
    def binding(self) -> dict[str, str]:
        return dict(
            **self.identity,
            exact_sha256=tree_digest(self.scoring.exact),
            partition_sha256=tree_digest(self.scoring.partition),
            mapping_sha256=sha(self.scoring.exact_to_partition.tolist()),
        )


def contexts(root: Path, *, software: bool) -> Iterator[Context]:
    """No learner/reference is constructed. All real inputs are pinned first."""
    config = contract(root)
    check_inputs(root, config)
    if software:
        for sign in (1, -1):
            original = Tree.build("kuhn")
            exact: ArrayTree = replace(
                original, terminal_values=sign * original.terminal_values
            )
            for index, name in enumerate(config["representations"]):
                mapping = np.arange(len(exact.keys), dtype=np.int64)
                if index % 2:
                    mapping = mapping[::-1].copy()
                inverse = np.argsort(mapping)
                information = exact.information.copy()
                decision = exact.player >= 0
                information[decision] = mapping[information[decision]]
                partition = replace(
                    exact,
                    keys=tuple(exact.keys[int(i)] for i in inverse),
                    actions=tuple(exact.actions[int(i)] for i in inverse),
                    owners=exact.owners[inverse].copy(),
                    legal=exact.legal[inverse].copy(),
                    information=information,
                )
                # Artificial last-depth decision masks exercise river reporting.
                masks = tuple(
                    np.array(
                        [owner == target for owner in exact.owners], dtype=np.bool_
                    )
                    for target in (0, 1)
                )
                scoring = ScoringContext(
                    exact, partition, mapping, (masks[0], masks[1])
                )
                yield Context(
                    f"software-kuhn-{sign}",
                    name,
                    sha(["software-kuhn", sign]),
                    scoring,
                    2.0,
                    dict(
                        information_sets=len(partition.keys),
                        tree_nodes=len(partition.player),
                        recall_violations=0,
                        menus_compatible=True,
                        key_utf8_bytes=sum(len(k.encode()) for k in partition.keys),
                        dense_regret_average_bytes=2 * partition.legal.nbytes,
                    ),
                )
        return
    model = CardAbstraction.load(root / config["model"])
    for filename in config["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        if len(source.states) > config["full"]["maximum_tree_nodes"]:
            raise ValueError("frozen full-control node cap exceeded")
        exact = MatrixTree.build(source)
        uniform = mass(exact, exact.normalize(exact.legal))
        river = np.array(
            [
                len(source.states[n].dealer.board) == 5  # type: ignore[union-attr]
                for n in source.representatives
            ],
            dtype=np.bool_,
        )
        masks = (river & (exact.owners == 0), river & (exact.owners == 1))
        for name in config["representations"]:
            tree = build_control(source, name, model)
            scoring = ScoringContext(exact, tree, tree.exact_to_abstract, masks)
            yield Context(
                filename,
                name,
                config["contexts"][filename],
                scoring,
                float(source.spot.pot),
                dict(
                    **collision_summary(tree, uniform),
                    tree_nodes=len(tree.player),
                    menus_compatible=True,
                ),
            )


def metrics(context: Context, policy: FloatArray, sums: FloatArray) -> dict[str, Any]:
    """Exact-game scalar metrics and positive-average support, never warm support."""
    exact, partition = context.scoring.exact, context.scoring.partition
    partition.validate_policy(policy)
    if (
        sums.shape != partition.legal.shape
        or not np.isfinite(sums).all()
        or np.any(sums < 0)
        or np.any(sums * (1 - partition.legal))
    ):
        raise ValueError("invalid cumulative average weights")
    deployed = context.scoring.expand(policy)
    evaluated = evaluate(exact, deployed)
    active = (sums.sum(axis=1) > 0)[context.scoring.exact_to_partition]
    uniform = mass(exact, exact.normalize(exact.legal))
    own = mass(exact, deployed)
    river = context.scoring.river_masks[0] | context.scoring.river_masks[1]
    coverage: dict[str, Any] = {}
    for street, mask in (
        ("all", np.ones(len(exact.keys), dtype=np.bool_)),
        ("river", river),
    ):
        for label, weights in (("uniform", uniform), ("own", own)):
            denominator = float(weights[mask].sum())
            coverage[f"{street}_{label}_reach_coverage"] = (
                float(np.clip(weights[mask] @ active[mask] / denominator, 0, 1))
                if denominator > 0
                else None
            )
    return dict(
        value_player_zero_chips=evaluated.value_player_zero,
        best_response_zero_chips=evaluated.best_response_zero,
        best_response_one_chips=evaluated.best_response_one,
        exploitability_chips=evaluated.exploitability,
        exploitability_pot=evaluated.exploitability / context.pot,
        coverage=coverage["all_uniform_reach_coverage"],
        positive_average_rows=int((sums.sum(axis=1) > 0).sum()),
        initialization_work=0,
        support_convention=(
            "positive full-CFR+ average mass; whole=post-warm; no warm stage"
        ),
        **coverage,
    )
