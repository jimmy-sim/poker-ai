"""Fixed-config own-only Bayesian collection and exact evaluation experiment."""

import gzip
import hashlib
import json
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.opponent_modeling.bayes import (
    Evidence,
    Posterior,
    TranscriptModel,
    sample_terminal,
)
from poker_ai.opponent_modeling.policies import (
    guarded_response,
    profile_value,
    root_mixture,
    scripted_policy,
    security,
)
from poker_ai.reproducibility import runtime_environment
from poker_ai.toy.cfr import CFR
from poker_ai.toy.games import GameName
from poker_ai.toy.tree import FloatArray, Tree
from poker_ai.validation.five_card import source_provenance


def load_config(path: Path) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(path.read_text())
    if (
        raw["schema_version"] != 1
        or raw["games"] != ["kuhn", "leduc"]
        or raw["seats"] != [0, 1]
        or raw["blueprint_variant"] != "cfr_plus"
        or raw["hypotheses"] != ["uniform", "calling_station", "aggressive", "value"]
        or raw["scenarios"] != raw["hypotheses"] + ["misspecified", "switching"]
    ):
        raise ValueError("unsupported Bayesian experiment schema")
    for key in ("seeds", "checkpoints"):
        values = raw[key]
        if (
            not isinstance(values, list)
            or not values
            or any(type(v) is not int or v < 0 for v in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError("invalid seed/checkpoint list")
    if raw["checkpoints"] != sorted(raw["checkpoints"]) or raw["checkpoints"][0] != 0:
        raise ValueError("checkpoints must start at zero and increase")
    for key in ("uniform_probability_floor_mass", "security_tolerance"):
        if not np.isfinite(raw[key]) or not 0 < raw[key] <= 1:
            raise ValueError("invalid floor/tolerance")
    if raw["security_tolerance"] > 1e-8:
        raise ValueError("security tolerance too loose")
    budget = raw["security_degradation_budget_ante_chips"]
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("invalid security budget")
    Posterior(np.array(raw["prior"], dtype=np.float64))
    if len(raw["prior"]) != len(raw["hypotheses"]):
        raise ValueError("prior does not match hypothesis family")
    for game in raw["games"]:
        iterations = raw["blueprint_iterations"][game]
        if type(iterations) is not int or iterations < 1:
            raise ValueError("invalid blueprint iterations")
    mixture = raw["misspecified_local_mix"]
    if (
        not mixture
        or any(
            k not in raw["hypotheses"] or not np.isfinite(v) or v < 0
            for k, v in mixture.items()
        )
        or not np.isclose(sum(mixture.values()), 1, atol=1e-12, rtol=0)
    ):
        raise ValueError("invalid misspecified local mixture")
    switch = raw["switching"]
    if (
        switch["before"] not in raw["hypotheses"]
        or switch["after"] not in raw["hypotheses"]
        or type(switch["after_hand"]) is not int
        or switch["after_hand"] not in raw["checkpoints"][1:-1]
    ):
        raise ValueError("switch must be a declared interior checkpoint")
    if not np.isfinite(raw["maximum_seconds"]) or raw["maximum_seconds"] <= 0:
        raise ValueError("invalid experiment time budget")
    return raw


def scenario_policy(
    scenario: str, hand: int, config: dict[str, Any], family: dict[str, FloatArray]
) -> FloatArray:
    if scenario in family:
        return family[scenario]
    if scenario == "misspecified":
        # A fresh local mixture; deliberately not a latent stationary family type.
        return sum(
            (
                weight * family[name]
                for name, weight in config["misspecified_local_mix"].items()
            ),
            start=np.zeros_like(next(iter(family.values()))),
        )
    if scenario != "switching":
        raise ValueError("unknown scenario")
    switch = config["switching"]
    return family[switch["before"] if hand < switch["after_hand"] else switch["after"]]


def run_experiment(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config = load_config(config_path)
    started = time.perf_counter()
    source = source_provenance(
        root, config_path, entrypoints=("scripts/analyze_opponents.py",)
    )
    rows: list[dict[str, Any]] = []
    histories: list[dict[str, Any]] = []
    risk_profiles: dict[str, Any] = {
        "format": "poker-ai-own-bayesian-risk-profiles-v1",
        "games": {},
        "source": source,
        "selection": "first configured seed, seat 0, aggressive, final checkpoint",
    }
    evidence_catalog: dict[str, Any] = {}
    for game_index, game_value in enumerate(config["games"]):
        game = cast(GameName, game_value)
        tree = Tree.build(game)
        solver = CFR(tree, "cfr_plus")
        solver.train(config["blueprint_iterations"][game])
        blueprint = solver.average_policy
        family = {
            name: scripted_policy(tree, name, config["uniform_probability_floor_mass"])
            for name in config["hypotheses"]
        }
        for seat in config["seats"]:
            model = TranscriptModel(tree, tuple(family.values()), seat)
            evidence_catalog[f"{game}:{seat}"] = [
                {"own_card": e.own_card, "board": e.board, "histories": e.histories}
                for e in model.lookup
            ]
            for scenario_index, scenario in enumerate(config["scenarios"]):
                for seed in config["seeds"]:
                    rng = Generator(
                        PCG64(SeedSequence([seed, game_index, seat, scenario_index]))
                    )
                    prior = np.array(config["prior"], dtype=np.float64)
                    posterior = Posterior(prior)
                    observed: list[int] = []
                    current = 0
                    collection: FloatArray | None = None
                    for checkpoint in config["checkpoints"]:
                        if collection is not None:
                            for hand in range(current, checkpoint):
                                if (
                                    time.perf_counter() - started
                                    > config["maximum_seconds"]
                                ):
                                    raise TimeoutError(
                                        "Bayesian experiment budget; no complete report"
                                    )
                                truth = scenario_policy(scenario, hand, config, family)
                                profile = truth.copy()
                                profile[tree.owners == seat] = collection[
                                    tree.owners == seat
                                ]
                                terminal = sample_terminal(tree, profile, rng)
                                evidence = Evidence.from_terminal(terminal, seat)
                                posterior.update(model.likelihood(evidence))
                                observed.append(model.lookup[evidence])
                        current = checkpoint
                        predictive = root_mixture(
                            tree, tuple(family.values()), posterior.weights, 1 - seat
                        )
                        guarded = guarded_response(
                            tree,
                            blueprint,
                            predictive,
                            seat,
                            config["security_degradation_budget_ante_chips"],
                            config["security_tolerance"],
                        )
                        collection = guarded.policy
                        truth = scenario_policy(scenario, checkpoint, config, family)
                        candidate_policies = {
                            "blueprint": blueprint,
                            "unrestricted": guarded.unrestricted,
                            "guarded": guarded.policy,
                        }
                        rows.append(
                            {
                                "game": game,
                                "seat": seat,
                                "scenario": scenario,
                                "seed": seed,
                                "hands_observed": checkpoint,
                                "posterior": posterior.weights.tolist(),
                                "predictive_nll_nats": model.conditional_log_loss(
                                    posterior.weights, blueprint, truth
                                ),
                                "prior_nll_nats": model.conditional_log_loss(
                                    prior, blueprint, truth
                                ),
                                "guarded_fraction": guarded.fraction,
                                "certified_lower_bound": guarded.certified_lower_bound,
                                "policies": {
                                    name: {
                                        "ev_ante_chips": profile_value(
                                            tree, policy, truth, seat
                                        ),
                                        "security_ante_chips": security(
                                            tree, policy, seat
                                        ),
                                    }
                                    for name, policy in candidate_policies.items()
                                },
                            }
                        )
                        if (
                            seat == 0
                            and scenario == "aggressive"
                            and seed == config["seeds"][0]
                            and checkpoint == config["checkpoints"][-1]
                        ):
                            risk_profiles["games"][game] = {
                                "keys": tree.keys,
                                "seat": seat,
                                "scenario": scenario,
                                "seed": seed,
                                "hands_observed": checkpoint,
                                "policies": {
                                    n: p.tolist() for n, p in candidate_policies.items()
                                },
                                "opponent": truth.tolist(),
                            }
                    histories.append(
                        {
                            "game": game,
                            "seat": seat,
                            "scenario": scenario,
                            "seed": seed,
                            "evidence_indices": observed,
                        }
                    )
        print(f"completed Bayesian {game}: both seats, all scenarios/seeds", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    files = {
        "public-transcripts.json.gz": {
            "catalog": evidence_catalog,
            "histories": histories,
        },
        "own-risk-profiles.json.gz": risk_profiles,
    }
    artifacts: dict[str, str] = {}
    for name, data in files.items():
        path = output.parent / name
        path.write_bytes(
            gzip.compress(
                json.dumps(data, sort_keys=True, allow_nan=False).encode(), mtime=0
            )
        )
        artifacts[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report: dict[str, Any] = {
        "status": "completed",
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "rows": rows,
        "artifacts_sha256": artifacts,
        "units": (
            "net ante chips per hand; "
            "conditional public-transcript NLL in natural-log nats"
        ),
        "limits": (
            "finite own toy-policy family; no external strategy or benchmark "
            "learning; exact EV/BR conditional on learned policy, "
            "not estimated Hold'em strength"
        ),
    }
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return report
