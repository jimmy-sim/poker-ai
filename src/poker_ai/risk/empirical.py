"""Conditional whole-deal-block resampling of measured OWN baseline matches."""

import csv
import gzip
import hashlib
import io
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.reproducibility import runtime_environment
from poker_ai.risk.bankroll import ReturnLaw, binary_law, simulate_fractional
from poker_ai.validation.five_card import source_provenance

OWN_OPPONENTS = ("random", "always_call", "always_raise", "tight_aggressive", "equity")


def confidence_sizing(
    mean_gross: float,
    loss_bound: float,
    fee: float,
    independent_deals: int,
    family_size: int,
    alpha: float,
    cap: float,
) -> tuple[float, float]:
    """One-sided familywise mean lower bound and worst-law log-growth sizing.

    Gross cluster mean is in [-loss_bound,loss_bound]. A constant fee shifts the
    lower bound without changing its width. Normalize by loss_bound+fee, enclosing
    net returns in [-1,1]. The chord below concave ln(1+f*x) makes the +/-1 law
    with mean m the worst law of mean >=m. Its nonnegative Kelly fraction is m.
    One mean bound covers every specified nonnegative constant fee for that bot.
    This is conditional research analysis; it does not alter the poker policy.
    """
    if (
        not all(math.isfinite(x) for x in (mean_gross, loss_bound, fee, alpha, cap))
        or loss_bound <= 0
        or abs(mean_gross) > loss_bound
        or fee < 0
        or type(independent_deals) is not int
        or independent_deals < 2
        or type(family_size) is not int
        or family_size < 1
        or not 0 < alpha < 1
        or not 0 < cap < 1
    ):
        raise ValueError("invalid bounded-mean confidence problem")
    half = (
        2
        * loss_bound
        * math.sqrt(math.log(family_size / alpha) / (2 * independent_deals))
    )
    lower = mean_gross - fee - half
    m = max(-1.0, min(1.0, lower / (loss_bound + fee)))
    return lower, binary_law((1 + m) / 2).kelly(cap)


def read_own_blocks(
    report_path: Path, names: list[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read only the five own-bot raw files; reject external opponent selection."""
    if tuple(names) != OWN_OPPONENTS:
        raise ValueError(
            "requires all five own baselines; external outputs are excluded"
        )
    report = json.loads(report_path.read_text())
    if report["status"] != "completed" or report["mode"] != "main":
        raise ValueError("requires complete measured main match study")
    config = report["config"]
    n = config["main_deals"]
    seeds = config["agent_seeds"]
    if n < 2 or len(set(seeds)) != len(seeds) or not seeds:
        raise ValueError("invalid measured independent-deal/policy count")
    loss_bound = float(max(config["rules"]["stacks"]))
    blocks: dict[str, Any] = {}
    for name in names:
        selected = [r for r in report["results"] if r["opponent"] == name]
        if len(selected) != 1 or selected[0]["status"] != "completed":
            raise ValueError("missing/duplicate own-baseline results")
        row = selected[0]
        path = report_path.parent / row["raw_file"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["raw_sha256"]:
            raise ArithmeticError("measured own-baseline raw file changed")
        matrix = np.zeros((n, len(seeds), 2))
        seen: set[tuple[int, int, int]] = set()
        for hand in csv.DictReader(io.StringIO(gzip.decompress(raw).decode())):
            deal, seed, seat, profit = (
                int(hand[key])
                for key in ("deal", "agent_seed", "own_seat", "profit_chips")
            )
            if (
                not 0 <= deal < n
                or seed not in seeds
                or seat not in (0, 1)
                or abs(profit) > loss_bound
                or (deal, seed, seat) in seen
            ):
                raise ArithmeticError("duplicate/invalid measured own hand")
            seen.add((deal, seed, seat))
            matrix[deal, seeds.index(seed), seat] = profit
        if len(seen) != n * len(seeds) * 2:
            raise ArithmeticError("missing measured own hand; no prefix resampling")
        values = matrix.mean(axis=(1, 2))
        if not np.isclose(
            values.mean(),
            row["primary_inference"]["mean_chips_per_hand"],
            atol=1e-12,
            rtol=0,
        ):
            raise ArithmeticError(
                "measured block mean differs from original evaluation"
            )
        blocks[name] = {
            "values": values,
            "raw_sha256": row["raw_sha256"],
            "independent_deals": n,
            "hands_per_block": len(seeds) * 2,
            "loss_bound_chips_per_hand": loss_bound,
        }
    return config, blocks


def load_config(path: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(path.read_text())
    if config["schema_version"] != 1 or tuple(config["opponents"]) != OWN_OPPONENTS:
        raise ValueError("invalid empirical risk schema/own-opponent selection")
    for key in ("seed", "paths", "horizon_blocks"):
        if type(config[key]) is not int or config[key] < (0 if key == "seed" else 2):
            raise ValueError("invalid empirical simulation dimensions")
    if config["sizing"] != ["half_plugin", "full_plugin", "confidence_robust"]:
        raise ValueError("requires all predeclared sizing controls")
    fees = config["flat_fee_bb_per_100_hands"]
    if (
        not fees
        or len(set(fees)) != len(fees)
        or any(not math.isfinite(f) or f < 0 for f in fees)
    ):
        raise ValueError("invalid hypothetical constant fee grid")
    if not all(
        0 < config[key] < 1
        for key in (
            "kelly_cap",
            "family_alpha",
            "threshold_initial_wealth_fraction",
            "drawdown_threshold",
        )
    ):
        raise ValueError("invalid empirical confidence/risk parameters")
    return config


def run_experiment(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config = load_config(config_path)
    match_path = root / config["match_report"]
    source = source_provenance(
        root, config_path, entrypoints=("scripts/analyze_empirical_bankroll.py",)
    )
    match_config, blocks = read_own_blocks(match_path, config["opponents"])
    bb = match_config["rules"]["big_blind"]
    started = time.perf_counter()
    rows = []
    measured = []
    for opponent_index, name in enumerate(config["opponents"]):
        block = blocks[name]
        gross = block["values"]
        measured.append(
            {
                "opponent": name,
                "independent_deals": len(gross),
                "hands_per_block": block["hands_per_block"],
                "mean_chips_per_hand": float(gross.mean()),
                "variance_of_block_mean_chips_squared": float(gross.var(ddof=1)),
                "raw_sha256": block["raw_sha256"],
            }
        )
        for fee_index, rate in enumerate(config["flat_fee_bb_per_100_hands"]):
            fee = rate * bb / 100
            unit = block["loss_bound_chips_per_hand"] + fee
            law = ReturnLaw((gross - fee) / unit, np.full(len(gross), 1 / len(gross)))
            plugin = law.kelly(config["kelly_cap"])
            lower, robust = confidence_sizing(
                float(gross.mean()),
                block["loss_bound_chips_per_hand"],
                fee,
                len(gross),
                len(config["opponents"]),
                config["family_alpha"],
                config["kelly_cap"],
            )
            for sizing in config["sizing"]:
                fraction = {
                    "half_plugin": plugin / 2,
                    "full_plugin": plugin,
                    "confidence_robust": robust,
                }[sizing]
                simulation = simulate_fractional(
                    law,
                    fraction,
                    config["horizon_blocks"],
                    config["paths"],
                    Generator(
                        PCG64(SeedSequence([config["seed"], opponent_index, fee_index]))
                    ),
                    config["threshold_initial_wealth_fraction"],
                    config["drawdown_threshold"],
                )
                rows.append(
                    {
                        "opponent": name,
                        "fee_bb_per_100_hands": rate,
                        "sizing": sizing,
                        "fraction": fraction,
                        "plugin_optimal_fraction": plugin,
                        "confidence_robust_fraction": robust,
                        "measured_net_mbb_per_hand": law.mean * unit / bb * 1000,
                        "familywise_lower_net_mbb_per_hand": lower / bb * 1000,
                        "normalized_maximum_loss_unit_chips_per_hand": unit,
                        "expected_log_growth_per_block": law.log_growth(fraction),
                        "simulation": simulation,
                    }
                )
        print(f"completed measured bankroll: {name}; all fixed fees/sizing", flush=True)
    report = {
        "status": "completed",
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "input_match_report_sha256": hashlib.sha256(
            match_path.read_bytes()
        ).hexdigest(),
        "measured": measured,
        "rows": rows,
        "units": (
            "each synthetic bankroll step is a six-hand duplicate-deal "
            "block, not one hand"
        ),
        "limits": (
            "conditional empirical resampling, not independent strength "
            "validation; fixed illustrative fees, not real-site pot rake; "
            "uncertainty fraction is separate from fitted-law optimum"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return report
