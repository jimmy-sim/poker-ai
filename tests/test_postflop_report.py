"""Check cross-play seat signs and fail-closed frozen evidence loading."""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import POLICY_FORMAT
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.report import (
    checked_artifacts,
    checked_comparisons,
    crossplay_ev,
    weighted_gap,
)
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]


def test_crossplay_and_gap_self_zero_and_independent_seat_signs() -> None:
    source = SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    tree = MatrixTree.build(source)
    uniform = tree.normalize(tree.legal)
    pure = np.zeros_like(uniform)
    pure[:, 0] = 1
    assert crossplay_ev(tree, uniform, uniform) == 0
    assert weighted_gap(tree, pure, pure) == 0
    assert 0 < weighted_gap(tree, pure, uniform) <= 2
    a, b = tree.exact_policy(pure), tree.exact_policy(uniform)
    first = tuple(
        x if owner == 0 else y for x, y, owner in zip(a, b, tree.owners, strict=True)
    )
    second = tuple(
        x if owner == 1 else y for x, y, owner in zip(a, b, tree.owners, strict=True)
    )
    expected = (source.values(first)[0] - source.values(second)[0]) / 2
    assert crossplay_ev(tree, pure, uniform) == pytest.approx(expected)
    assert crossplay_ev(tree, uniform, pure) == pytest.approx(-expected)


@pytest.mark.parametrize("corruption", ["hash", "missing", "duplicate", "partial"])
def test_frozen_evidence_rejects_changes(tmp_path: Path, corruption: str) -> None:
    row = {
        "spot": "test",
        "encoding": "exact",
        "method": "external",
        "seed": 1,
        "iteration": 1,
    }
    snapshots = [row]
    if corruption == "missing":
        snapshots = []
    if corruption == "duplicate":
        snapshots = [row, row]
    policy = tmp_path / "own.json.gz"
    policy.write_bytes(
        gzip.compress(
            json.dumps({"format": POLICY_FORMAT, "policies": snapshots}).encode(),
            mtime=0,
        )
    )
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps(
            {
                "status": "incomplete" if corruption == "partial" else "completed",
                "own_policies_file": policy.name,
                "own_policies_sha256": "wrong"
                if corruption == "hash"
                else hashlib.sha256(policy.read_bytes()).hexdigest(),
                "rows": [row],
            }
        )
    )
    with pytest.raises((ArithmeticError, ValueError)):
        checked_artifacts(path)


@pytest.mark.parametrize("corruption", [None, "missing", "duplicate", "nan", "epsilon"])
def test_native_comparison_records_require_complete_finite_checks(
    corruption: str | None,
) -> None:
    row = {
        "spot": "test",
        "encoding": "exact",
        "method": "external",
        "seed": 1,
        "iteration": 1,
        "exploitability_chips": 0.5,
    }
    comparison = {
        **row,
        "own_native_value_error": 0.0,
        "own_native_exploitability_error": 0.0,
        "native_exploitability_chips": 0.5,
    }
    checks = [comparison]
    if corruption == "missing":
        checks = []
    elif corruption == "duplicate":
        checks = [comparison, comparison]
    elif corruption == "nan":
        comparison["own_native_value_error"] = float("nan")
    elif corruption == "epsilon":
        comparison["native_exploitability_chips"] = 1.0
    report = {"rows": [row], "config": {"independent_tolerance": 1e-9}}
    independent = {"status": "passed", "comparisons": checks}
    if corruption is None:
        assert checked_comparisons(report, independent) == 1
    else:
        with pytest.raises(ArithmeticError):
            checked_comparisons(report, independent)
