"""Analytic controls for conditional log growth and separate ruin processes."""

import itertools
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.opponent_modeling.policies import profile_value, scripted_policy
from poker_ai.risk.bankroll import (
    ReturnLaw,
    binary_law,
    eventual_ruin,
    finite_ruin,
    own_toy_return_law,
    robust_binary_fraction,
    simulate_fixed_stake,
    simulate_fractional,
)
from poker_ai.toy.games import GameName
from poker_ai.toy.tree import Tree


@pytest.mark.parametrize("p", [0.0, 0.1, 0.5, 0.55, 0.7, 0.99, 1.0])
def test_binary_kelly_analytic(p: float) -> None:
    law = binary_law(p)
    fraction = law.kelly(0.95)
    assert fraction == pytest.approx(min(0.95, max(0, 2 * p - 1)), abs=1e-13)
    assert law.log_growth(fraction) >= -1e-14


def test_general_two_outcome_kelly_and_uncertainty() -> None:
    law = ReturnLaw(np.array([-0.5, 0.2]), np.array([0.2, 0.8]))
    assert law.kelly() == pytest.approx(0.6, abs=1e-12)
    assert robust_binary_fraction(0.45, 0.6) == 0
    assert robust_binary_fraction(0.55, 0.6) == pytest.approx(0.1)
    with pytest.raises(ValueError):
        robust_binary_fraction(0.7, 0.6)
    with pytest.raises(ValueError):
        law.log_growth(1.0)
    with pytest.raises(ValueError):
        ReturnLaw(np.array([-1.1, 1.0]), np.array([0.5, 0.5]))


def test_finite_ruin_against_enumerated_paths() -> None:
    p, start, target, horizon = 0.3, 2, 5, 6
    probability = 0.0
    for changes in itertools.product((-1, 1), repeat=horizon):
        wealth, mass = start, 1.0
        for change in changes:
            mass *= p if change == 1 else 1 - p
            if 0 < wealth < target:
                wealth += change
        probability += mass * (wealth == 0)
    assert finite_ruin(start, target, p, horizon) == pytest.approx(probability)
    assert finite_ruin(1, 2, 0.7, 0) == 0
    assert finite_ruin(1, 2, 0.7, 1) == pytest.approx(0.3)


@pytest.mark.parametrize("p", [0.45, 0.5, 0.55])
def test_eventual_ruin_limits_and_known_formula(p: float) -> None:
    r = (1 - p) / p
    expected = 0.5 if p == 0.5 else (r**10 - r**20) / (1 - r**20)
    assert eventual_ruin(10, 20, p) == pytest.approx(expected)
    assert finite_ruin(10, 20, p, 10000) == pytest.approx(expected, abs=1e-10)
    assert eventual_ruin(0, 20, p) == 1
    assert eventual_ruin(20, 20, p) == 0
    assert 0 <= eventual_ruin(10, 10000, 1e-300) <= 1
    assert 0 <= eventual_ruin(10, 10000, 1 - 1e-15) <= 1


def test_absorption_not_final_wealth_or_fractional_threshold() -> None:
    rng = Generator(PCG64(41))
    result = simulate_fixed_stake(2, 4, 0.0, 3, 10, rng)
    assert result["ruin"]["probability"] == 1
    assert eventual_ruin(2, 4, 1.0) == 0
    assert eventual_ruin(2, 4, 0.0) == 1
    law = ReturnLaw(np.array([-1.0]), np.array([1.0]))
    paths = simulate_fractional(law, 0.5, 3, 10, rng, threshold=0.2)
    assert paths["threshold_crossing"]["probability"] == 1
    assert paths["mean_terminal_log_wealth"] == pytest.approx(math.log(0.125))
    assert paths["maximum_drawdown_quantiles_05_50_95"] == pytest.approx([0.875] * 3)
    assert "impossible" in str(paths["literal_bankruptcy"])
    zero = simulate_fractional(law, 0.0, 3, 10, rng)
    assert zero["mean_terminal_log_wealth"] == 0
    assert zero["threshold_crossing"]["wilson_95"][1] > 0


def test_sticky_returns_preserve_mean_growth_but_change_risk() -> None:
    law, fraction, horizon, paths = binary_law(0.55), 0.1, 100, 5000
    iid = simulate_fractional(law, fraction, horizon, paths, Generator(PCG64(2)))
    sticky = simulate_fractional(
        law, fraction, horizon, paths, Generator(PCG64(3)), persistence=0.8
    )
    for result in (iid, sticky):
        assert abs(
            float(result["mean_terminal_log_wealth"])
            - horizon * law.log_growth(fraction)
        ) < (6 * float(result["se_terminal_log_wealth"]))
    assert sticky["terminal_loss"]["probability"] > iid["terminal_loss"]["probability"]


@pytest.mark.parametrize("game", ["kuhn", "leduc"])
@pytest.mark.parametrize("seat", [0, 1])
def test_own_toy_return_law_exact_ev_and_rake(game: GameName, seat: int) -> None:
    tree = Tree.build(game)
    own, opponent = scripted_policy(tree, "value"), scripted_policy(tree, "aggressive")
    law = own_toy_return_law(tree, own, opponent, seat, 0)
    scale = np.max(np.abs(tree.terminal_values))
    assert law.mean * scale == pytest.approx(profile_value(tree, own, opponent, seat))
    raked = own_toy_return_law(tree, own, opponent, seat, 0.05)
    assert raked.mean < law.mean
    np.testing.assert_array_equal(law.probabilities, raked.probabilities)
    assert np.all(raked.outcomes <= law.outcomes)


def test_tiny_risk_experiment_and_reference_format_rejection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import gzip
    import hashlib
    import json

    from poker_ai.risk import experiment

    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "configs/bankroll-risk.json").read_text())
    config.update({"paths": 20, "horizon": 5, "kelly_multipliers": [0.0, 0.5]})
    config["ruin_control"]["horizon"] = 5
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    profile_path = tmp_path / "own-risk-profiles.json.gz"
    profile: dict[str, Any] = {
        "format": "poker-ai-own-bayesian-risk-profiles-v1",
        "games": {},
    }
    for game in ("kuhn", "leduc"):
        tree = Tree.build(game)
        own, opponent = (
            scripted_policy(tree, "value"),
            scripted_policy(tree, "aggressive"),
        )
        profile["games"][game] = {
            "keys": tree.keys,
            "seat": 0,
            "scenario": "aggressive",
            "seed": 20261203,
            "hands_observed": 1000,
            "opponent": opponent.tolist(),
            "policies": {name: own.tolist() for name in config["toy_policies"]},
        }
    profile_path.write_bytes(gzip.compress(json.dumps(profile).encode()))
    (tmp_path / "opponents.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "artifacts_sha256": {
                    profile_path.name: hashlib.sha256(
                        profile_path.read_bytes()
                    ).hexdigest()
                },
            }
        )
    )
    monkeypatch.setattr(
        experiment, "source_provenance", lambda *args, **kwargs: {"test": True}
    )
    report = experiment.run_experiment(
        root, config_path, profile_path, tmp_path / "risk.json"
    )
    assert report["status"] == "completed" and len(report["rows"]) == 48
    assert report["robust_binary_fraction"] == 0
    for mutation in (
        {"paths": 1},
        {"binary_persistence": [1.0]},
        {"pot_rake_rates": [-0.1]},
        {"toy_scenario": "best_observed"},
    ):
        config_path.write_text(json.dumps({**config, **mutation}))
        with pytest.raises(ValueError):
            experiment.load_config(config_path)
    config_path.write_text(json.dumps(config))
    profile_path.write_bytes(
        gzip.compress(json.dumps({"format": "reference-comparison-only"}).encode())
    )
    with pytest.raises(ValueError, match="only own"):
        experiment.run_experiment(
            root, config_path, profile_path, tmp_path / "bad.json"
        )
