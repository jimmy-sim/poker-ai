"""Exact valid-state parity, including padded rounding and per-pass invalidation."""

from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_training import ControlledTrainer, Rules, Weight
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_policy import RowPolicyTrainer
from poker_ai.postflop.row_profile import assert_equal, parity
from poker_ai.postflop.training_isolation import SPOTS, sentinel_tree
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]
CLIPS: tuple[Literal["signed", "clipped"], ...] = ("signed", "clipped")
WEIGHTS: tuple[Weight, ...] = ("uniform", "linear")
RULES = [Rules(c, r, a) for c, r, a in product(CLIPS, WEIGHTS, WEIGHTS)]


@pytest.mark.parametrize("width", [3, 8, 17, 44, 65])
def test_padded_row_reduction_is_byte_identical(width: int) -> None:
    original = sentinel_tree()
    extra = width - original.legal.shape[1]
    tree = replace(
        original,
        children=np.pad(original.children, ((0, 0), (0, extra))),
        valid=np.pad(original.valid, ((0, 0), (0, extra))),
        chance_edges=np.pad(original.chance_edges, ((0, 0), (0, extra))),
        legal=np.pad(original.legal, ((0, 0), (0, extra))),
    )
    solver = RowPolicyTrainer(tree, Generator(PCG64(72)))
    rng = Generator(PCG64(19))
    solver.regrets[:] = (
        rng.normal(size=tree.legal.shape)
        * 10.0 ** rng.integers(-200, 200, size=tree.legal.shape)
        * tree.legal
    )
    expected = solver.current_policy
    for info in range(len(tree.keys)):
        assert solver._policy_row(info).tobytes() == expected[info].tobytes()
    solver.regrets[:] = -tree.legal
    for info in range(len(tree.keys)):
        assert (
            solver._policy_row(info).tobytes() == solver.current_policy[info].tobytes()
        )
    solver.regrets[0, 0] = np.nan
    with pytest.raises(ValueError, match="visited"):
        solver._policy_row(0)


@pytest.mark.parametrize("rules", RULES)
@pytest.mark.parametrize("warm", [False, True])
def test_exact_state_rng_and_work_each_iteration(rules: Rules, warm: bool) -> None:
    tree = sentinel_tree()
    a = ControlledTrainer(tree, Generator(PCG64(211)), rules=rules)
    b = RowPolicyTrainer(tree, Generator(PCG64(211)), rules=rules)
    if warm:
        a.initialize_exact()
        b.initialize_exact()
    for _ in range(32):
        before = b.row_evaluations
        a.step()
        b.step()
        assert_equal(a, b)
        assert b.row_evaluations - before == sum(b.last_pass_rows)
        assert 0 < sum(b.last_pass_rows) <= 2 * len(tree.keys)
    b.regrets[0, 0] += 1
    with pytest.raises(ArithmeticError, match="regrets"):
        assert_equal(a, b)


def test_step_avoids_global_policy_export_and_instances_do_not_share_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = sentinel_tree()
    solver = RowPolicyTrainer(tree, Generator(PCG64(2)))
    untouched = RowPolicyTrainer(tree, Generator(PCG64(2)))
    solver.initialize_exact()

    def forbidden(self: ControlledTrainer) -> FloatArray:
        raise AssertionError("global policy requested inside sampled step")

    with monkeypatch.context() as patch:
        patch.setattr(ControlledTrainer, "current_policy", property(forbidden))
        solver.step()
    assert solver.row_evaluations > 0 and untouched.row_evaluations == 0
    with pytest.raises(ValueError, match="external"):
        RowPolicyTrainer(tree, Generator(PCG64(2)), traversal="full").step()


def test_real_game_prefixes_all_rules_both_representations() -> None:
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    for path in SPOTS:
        source = SpotTree.build(load_spot(ROOT / path))
        for name in ("exact", "texture_range_q8_b8"):
            tree = build_representation_control(source, name, model)
            for rules in RULES:
                cell = dict(
                    spot_file=path,
                    representation=name,
                    traversal="external",
                    regret_rule=rules.regret_rule,
                    regret_weight=rules.regret_weight,
                    average_weight=rules.average_weight,
                    seed=20261301,
                    bridge="common",
                )
                rows = parity(tree, cell, [1, 2, 4], Deadline(30))
                assert [r["iteration"] for r in rows] == [1, 2, 4]
