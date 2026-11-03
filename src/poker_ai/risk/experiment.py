"""Fixed-seed risk simulations, analytic controls and own-only toy return laws."""

import gzip
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.reproducibility import runtime_environment
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
from poker_ai.validation.five_card import source_provenance


def load_config(path: Path) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(path.read_text())
    if raw["schema_version"] != 1:
        raise ValueError("invalid risk schema")
    for key in ("seed", "paths", "horizon"):
        if type(raw[key]) is not int or raw[key] < (0 if key == "seed" else 2):
            raise ValueError("invalid risk seed/sample size/horizon")
    if not 0 < raw["kelly_cap"] < 1:
        raise ValueError("invalid Kelly cap")
    for key in ("threshold_initial_wealth_fraction", "drawdown_threshold"):
        if not 0 < raw[key] < 1:
            raise ValueError("invalid risk threshold")
    for key, upper, inclusive in (
        ("binary_true_win_probabilities", 1.0, True),
        ("binary_persistence", 1.0, False),
        ("pot_rake_rates", 0.1, True),
    ):
        values = raw[key]
        if (
            not values
            or len(set(values)) != len(values)
            or any(
                not np.isfinite(x) or x < 0 or (x > upper if inclusive else x >= upper)
                for x in values
            )
        ):
            raise ValueError("invalid risk sensitivity grid")
    multipliers = raw["kelly_multipliers"]
    if (
        not multipliers
        or len(set(multipliers)) != len(multipliers)
        or any(not np.isfinite(x) or x < 0 for x in multipliers)
    ):
        raise ValueError("invalid fractional multiplier grid")
    binary_law(raw["binary_estimated_win_probability"])
    robust_binary_fraction(
        raw["uncertain_win_probability_interval"][0],
        raw["uncertain_win_probability_interval"][1],
        raw["kelly_cap"],
    )
    if raw["toy_policies"] != ["blueprint", "guarded", "unrestricted"]:
        raise ValueError("requires all declared own-policy risk controls")
    if raw["toy_seat"] != 0 or raw["toy_scenario"] != "aggressive":
        raise ValueError(
            "requires predeclared toy selection, not an outcome-selected policy"
        )
    ruin = raw["ruin_control"]
    if type(ruin["horizon"]) is not int or ruin["horizon"] < 1:
        raise ValueError("invalid ruin horizon")
    for p in ruin["win_probabilities"]:
        eventual_ruin(ruin["start"], ruin["target"], p)
    return raw


def compress_law(law: ReturnLaw) -> ReturnLaw:
    outcomes, inverse = np.unique(law.outcomes, return_inverse=True)
    mass = np.zeros(len(outcomes))
    np.add.at(mass, inverse, law.probabilities)
    active = mass > 0
    return ReturnLaw(outcomes[active], mass[active])


def run_experiment(
    root: Path, config_path: Path, own_profile_path: Path, output: Path
) -> dict[str, Any]:
    config = load_config(config_path)
    source = source_provenance(
        root, config_path, entrypoints=("scripts/analyze_bankroll.py",)
    )
    profiles = json.loads(gzip.decompress(own_profile_path.read_bytes()))
    if profiles.get("format") != "poker-ai-own-bayesian-risk-profiles-v1":
        raise ValueError(
            "only own Bayesian profile format accepted; no reference strategies"
        )
    parent_report_path = own_profile_path.parent / "opponents.json"
    parent_report = json.loads(parent_report_path.read_text())
    if (
        parent_report["status"] != "completed"
        or parent_report["artifacts_sha256"][own_profile_path.name]
        != hashlib.sha256(own_profile_path.read_bytes()).hexdigest()
    ):
        raise ValueError(
            "own profile provenance/bytes do not match completed own experiment"
        )
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []

    def simulate(
        law: ReturnLaw, fraction: float, seed_parts: list[int], persistence: float
    ) -> dict[str, Any]:
        return simulate_fractional(
            law,
            fraction,
            config["horizon"],
            config["paths"],
            Generator(PCG64(SeedSequence([config["seed"], *seed_parts]))),
            config["threshold_initial_wealth_fraction"],
            config["drawdown_threshold"],
            persistence,
        )

    estimated = binary_law(config["binary_estimated_win_probability"]).kelly(
        config["kelly_cap"]
    )
    for p_index, p in enumerate(config["binary_true_win_probabilities"]):
        law = binary_law(p)
        for dependence_index, persistence in enumerate(config["binary_persistence"]):
            for multiplier in config["kelly_multipliers"]:
                fraction = min(config["kelly_cap"], multiplier * estimated)
                rows.append(
                    {
                        "domain": "synthetic_binary",
                        "true_p": p,
                        "estimated_p": config["binary_estimated_win_probability"],
                        "persistence": persistence,
                        "kelly_multiplier": multiplier,
                        "fraction": fraction,
                        "true_iid_optimal_fraction": law.kelly(config["kelly_cap"]),
                        "expected_log_growth_per_step": law.log_growth(fraction),
                        "simulation": simulate(
                            law, fraction, [0, p_index, dependence_index], persistence
                        ),
                    }
                )
    for game_index, game in enumerate(("kuhn", "leduc")):
        data = profiles["games"][game]
        if (
            data["seat"] != config["toy_seat"]
            or data["scenario"] != config["toy_scenario"]
            or data["seed"] != config["toy_training_history_seed"]
            or data["hands_observed"] != config["toy_checkpoint"]
        ):
            raise ValueError("own toy profile does not match predeclared selection")
        tree = Tree.build(cast(GameName, game))
        if list(tree.keys) != data["keys"]:
            raise ValueError("own toy profile encoding mismatch")
        opponent = np.array(data["opponent"], dtype=np.float64)
        for policy_index, name in enumerate(config["toy_policies"]):
            own = np.array(data["policies"][name], dtype=np.float64)
            for fee_index, fee in enumerate(config["pot_rake_rates"]):
                law = compress_law(
                    own_toy_return_law(tree, own, opponent, config["toy_seat"], fee)
                )
                optimum = law.kelly(config["kelly_cap"])
                for multiplier in config["kelly_multipliers"]:
                    fraction = min(config["kelly_cap"], multiplier * optimum)
                    rows.append(
                        {
                            "domain": "own_toy",
                            "game": game,
                            "policy": name,
                            "pot_rake_rate": fee,
                            "persistence": 0.0,
                            "kelly_multiplier": multiplier,
                            "fraction": fraction,
                            "law_outcomes": law.outcomes.tolist(),
                            "law_probabilities": law.probabilities.tolist(),
                            "normalized_mean_return": law.mean,
                            "conditional_optimal_fraction": optimum,
                            "expected_log_growth_per_step": law.log_growth(fraction),
                            "simulation": simulate(
                                law,
                                fraction,
                                [1, game_index, policy_index, fee_index],
                                0.0,
                            ),
                        }
                    )
        print(
            f"completed bankroll {game}: all own policies, fees and fractions",
            flush=True,
        )
    controls = []
    ruin = config["ruin_control"]
    alpha = 0.001 / len(ruin["win_probabilities"])
    tolerance = math.sqrt(math.log(2 / alpha) / (2 * config["paths"]))
    for i, p in enumerate(ruin["win_probabilities"]):
        exact = finite_ruin(ruin["start"], ruin["target"], p, ruin["horizon"])
        simulation = simulate_fixed_stake(
            ruin["start"],
            ruin["target"],
            p,
            ruin["horizon"],
            config["paths"],
            Generator(PCG64(SeedSequence([config["seed"], 2, i]))),
        )
        error = abs(simulation["ruin"]["probability"] - exact)
        if error > tolerance:
            raise ArithmeticError(
                "fixed-stake Monte Carlo disagrees with exact finite-horizon control"
            )
        controls.append(
            {
                "p": p,
                "exact_finite_horizon_ruin": exact,
                "eventual_ruin": eventual_ruin(ruin["start"], ruin["target"], p),
                "simulation": simulation,
                "absolute_error": error,
                "acceptance_tolerance": tolerance,
                "family_alpha": 0.001,
            }
        )
    report = {
        "status": "completed",
        "config": config,
        "source": source,
        "own_profile_sha256": hashlib.sha256(own_profile_path.read_bytes()).hexdigest(),
        "own_experiment_sha256": hashlib.sha256(
            parent_report_path.read_bytes()
        ).hexdigest(),
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "rows": rows,
        "ruin_controls": controls,
        "robust_binary_fraction": robust_binary_fraction(
            config["uncertain_win_probability_interval"][0],
            config["uncertain_win_probability_interval"][1],
            config["kelly_cap"],
        ),
        "dependence": (
            "independent paths within each cell; same random return "
            "paths reused across fraction multipliers; "
            "rows are not independent pooled observations"
        ),
        "limits": (
            "known/assumed synthetic and own toy return laws; no empirical "
            "real-world positive edge, financial advice or learned benchmark strategy"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return report
