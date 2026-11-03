"""Preserve duplicate clusters, distinguish fitted returns and mean uncertainty."""

import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.risk.empirical import (
    OWN_OPPONENTS,
    confidence_sizing,
    read_own_blocks,
    run_experiment,
)


def synthetic_matches(directory: Path) -> Path:
    results = []
    for name in OWN_OPPONENTS:
        stream = io.StringIO()
        writer = csv.DictWriter(
            stream, fieldnames=["deal", "agent_seed", "own_seat", "profit_chips"]
        )
        writer.writeheader()
        for deal in (0, 1):
            for seed in (11, 12, 13):
                for seat in (0, 1):
                    writer.writerow(
                        {
                            "deal": deal,
                            "agent_seed": seed,
                            "own_seat": seat,
                            "profit_chips": 6 if deal == 0 else -4,
                        }
                    )
        path = directory / f"{name}.csv.gz"
        path.write_bytes(gzip.compress(stream.getvalue().encode()))
        results.append(
            {
                "opponent": name,
                "status": "completed",
                "raw_file": path.name,
                "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "primary_inference": {"mean_chips_per_hand": 1.0},
            }
        )
    path = directory / "matches.json"
    path.write_text(
        json.dumps(
            {
                "status": "completed",
                "mode": "main",
                "results": results,
                "config": {
                    "main_deals": 2,
                    "agent_seeds": [11, 12, 13],
                    "rules": {"stacks": [10, 10], "big_blind": 2},
                },
            }
        )
    )
    return path


def test_block_aggregation_and_no_external_selection(tmp_path: Path) -> None:
    path = synthetic_matches(tmp_path)
    _, blocks = read_own_blocks(path, list(OWN_OPPONENTS))
    for row in blocks.values():
        np.testing.assert_array_equal(row["values"], [6.0, -4.0])
        assert row["hands_per_block"] == 6
        assert row["independent_deals"] == 2
        assert row["values"].var(ddof=1) == 50
    with pytest.raises(ValueError, match="external"):
        read_own_blocks(path, [*OWN_OPPONENTS, "openspiel_ismcts"])
    report = json.loads(path.read_text())
    report["results"][0]["raw_sha256"] = "changed"
    path.write_text(json.dumps(report))
    with pytest.raises(ArithmeticError, match="changed"):
        read_own_blocks(path, list(OWN_OPPONENTS))


def test_missing_measured_hand_never_becomes_a_zero_profit(tmp_path: Path) -> None:
    path = synthetic_matches(tmp_path)
    report = json.loads(path.read_text())
    raw_path = tmp_path / report["results"][0]["raw_file"]
    lines = gzip.decompress(raw_path.read_bytes()).splitlines(keepends=True)
    raw_path.write_bytes(gzip.compress(b"".join(lines[:-1])))
    report["results"][0]["raw_sha256"] = hashlib.sha256(
        raw_path.read_bytes()
    ).hexdigest()
    path.write_text(json.dumps(report))
    with pytest.raises(ArithmeticError, match="missing"):
        read_own_blocks(path, list(OWN_OPPONENTS))


def test_confidence_robust_sizing_and_constant_fee_shift() -> None:
    lower, fraction = confidence_sizing(0.1, 1.0, 0.0, 100000, 5, 0.05, 0.95)
    assert lower == pytest.approx(0.1 - 2 * math.sqrt(math.log(100) / 200000))
    assert fraction == pytest.approx(lower)
    fee_lower, fee_fraction = confidence_sizing(0.1, 1.0, 0.02, 100000, 5, 0.05, 0.95)
    assert fee_lower == pytest.approx(lower - 0.02)
    assert fee_fraction == pytest.approx(fee_lower / 1.02)
    assert confidence_sizing(0.1, 1.0, 0.0, 10, 5, 0.05, 0.95)[1] == 0
    with pytest.raises(ValueError):
        confidence_sizing(0.1, 1.0, -0.1, 10, 5, 0.05, 0.95)


def test_empirical_tiny_run_and_fitted_positive_is_not_an_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.risk import empirical

    root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] = json.loads(
        (root / "configs/empirical-bankroll.json").read_text()
    )
    config.update(
        {
            "match_report": str(synthetic_matches(tmp_path)),
            "paths": 20,
            "horizon_blocks": 4,
        }
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(
        empirical, "source_provenance", lambda *args, **kwargs: {"test": True}
    )
    report = run_experiment(root, config_path, tmp_path / "report.json")
    assert report["status"] == "completed" and len(report["rows"]) == 45
    assert all(r["confidence_robust_fraction"] == 0 for r in report["rows"])
    assert all(r["plugin_optimal_fraction"] > 0 for r in report["rows"])
    assert all(
        r["variance_of_block_mean_chips_squared"] == 50 for r in report["measured"]
    )
