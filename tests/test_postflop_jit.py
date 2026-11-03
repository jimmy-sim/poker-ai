"""Explicit IEEE arithmetic, independently implemented scalar versus JIT controls."""

import itertools
from pathlib import Path
from typing import Any

import numpy as np
import pytest

numba: Any = pytest.importorskip("numba")

from poker_ai.postflop.game import load_spot  # noqa: E402
from poker_ai.postflop.jit_cfr import FMA, FusedCFRPlus  # noqa: E402
from poker_ai.postflop.matrix import MatrixTree  # noqa: E402
from poker_ai.postflop.tree import SpotTree  # noqa: E402
from poker_ai.solver_validation.arithmetic import ScalarCFRPlus  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def medium_tree() -> MatrixTree:
    return MatrixTree.build(
        SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json"))
    )


def test_fused_intrinsic_has_single_rounding() -> None:
    def probe(a: float, b: float, c: float) -> float:
        return float(FMA(a, b, c))

    compiled = numba.njit(fastmath=False)(probe)
    a, b = 1.0 + 2.0**-27, 1.0 - 2.0**-27
    assert a * b - 1.0 == 0
    assert compiled(a, b, -1.0) == -(2.0**-54)


@pytest.mark.parametrize("arithmetic", list(itertools.product((False, True), repeat=3)))
def test_jit_scalar_agree_for_all_contraction_modes(
    medium_tree: MatrixTree,
    arithmetic: tuple[bool, bool, bool],
) -> None:
    values, regrets, averages = arithmetic
    scalar = ScalarCFRPlus(
        medium_tree, fused_values=values, fused_regrets=regrets, fused_averages=averages
    )
    compiled = FusedCFRPlus(
        medium_tree, fused_values=values, fused_regrets=regrets, fused_averages=averages
    )
    for _ in range(3):
        scalar.step()
        compiled.step()
        np.testing.assert_array_equal(
            np.concatenate(scalar.average_policy),
            np.concatenate(medium_tree.exact_policy(compiled.average_policy)),
        )
        np.testing.assert_array_equal(
            np.concatenate(scalar.regrets),
            np.concatenate(
                [
                    compiled.regrets[i, : len(menu)]
                    for i, menu in enumerate(medium_tree.actions)
                ]
            ),
        )


def test_fused_control_has_independently_checked_value_and_br(
    medium_tree: MatrixTree,
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.solver_validation.reference import Reference
    from poker_ai.toy.analysis import evaluate

    compiled = FusedCFRPlus(medium_tree)
    compiled.train(16)
    reference = Reference(medium_tree.source)
    policy = medium_tree.exact_policy(compiled.average_policy)
    assert evaluate(
        medium_tree, compiled.average_policy
    ).exploitability == pytest.approx(reference.exploitability(policy), abs=1e-9)
    assert evaluate(
        medium_tree, compiled.average_policy
    ).value_player_zero == pytest.approx(reference.value(policy), abs=1e-9)
