"""Measure exact-information aliases inside the restricted spot sample only."""

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.solver_validation.gaps import normalized_weights
from poker_ai.solver_validation.reference import Policy, SpotTree


def aliases(
    keys: Sequence[str], menus: Sequence[tuple[int, ...]], mass: Sequence[float]
) -> dict[str, int | float]:
    if len(keys) != len(menus) or len(keys) != len(mass) or not keys:
        raise ValueError("aligned nonempty abstraction keys/menus/mass required")
    weights = normalized_weights(np.asarray(mass, dtype=np.float64), len(keys))
    groups: dict[str, list[int]] = defaultdict(list)
    for info, key in enumerate(keys):
        groups[key].append(info)
    for members in groups.values():
        if any(menus[i] != menus[members[0]] for i in members):
            raise ValueError("abstraction merged incompatible action menus")
    merged = [members for members in groups.values() if len(members) > 1]
    return {
        "exact_information_sets": len(keys),
        "abstract_information_sets": len(groups),
        "merged_groups": len(merged),
        "information_sets_in_merged_groups": sum(map(len, merged)),
        "reference_reach_in_merged_groups": float(
            sum(weights[members].sum() for members in merged) / weights.sum()
        ),
    }


def check_model(
    tree: SpotTree, model: CardAbstraction, policy: Policy
) -> dict[str, Any]:
    keys = []
    for node in tree.representatives:
        state = tree.states[node]
        assert state.dealer is not None
        keys.append(model.information(state.dealer.observe(state.actor)))
    mass = np.zeros(len(tree.keys))
    for node, reach in enumerate(tree.reaches(policy)):
        info = tree.information[node]
        if info >= 0:
            mass[info] += reach
    return aliases(keys, tree.menus, mass.tolist())
