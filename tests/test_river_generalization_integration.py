"""The fixed new inputs bind unchanged representations and old source bytes."""

import sys
from pathlib import Path

from poker_ai.postflop.matrix import MatrixTree, recall_violations

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from river_generalization.gate import (  # noqa: E402
    ARMS,
    CONFIG_SHA256,
    GAMES,
    contract,
    source_files,
    source_fingerprint,
)
from river_generalization.learning import context  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_contract_and_historical_source_binding() -> None:
    config = contract(ROOT)
    assert config["seeds"] == [20261371, 20261372, 20261373]
    assert len(CONFIG_SHA256) == 64
    files = source_files(ROOT)
    assert "scripts/river_strength/representation.py" in files
    assert "scripts/river_generalization/selection.py" in files
    assert "configs/river-generalization-freeze.json" in files
    assert all(f"configs/river-generalization-spots/{g}.json" in files for g in GAMES)
    assert len(source_fingerprint(ROOT)) == 64


def test_all_frozen_spot_arms_build_with_recall_and_tree_bounds() -> None:
    for game in GAMES:
        rows = []
        for arm in ARMS:
            scoring = context(ROOT, game, arm)
            assert len(scoring.exact.player) <= 200_000
            assert isinstance(scoring.partition, MatrixTree)
            assert recall_violations(scoring.partition) == 0
            rows.append(len(scoring.partition.keys))
        assert rows[1] > rows[0]
