"""Recompute posterior odds and all exact metrics from censored retained evidence."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from poker_ai.opponent_modeling.bayes import TranscriptModel
from poker_ai.opponent_modeling.experiment import scenario_policy
from poker_ai.opponent_modeling.policies import (
    guarded_response,
    profile_value,
    root_mixture,
    scripted_policy,
    security,
)
from poker_ai.toy.cfr import CFR
from poker_ai.toy.games import GameName
from poker_ai.toy.tree import Tree


def audit(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text())
    if report["status"] != "completed":
        raise ValueError("cannot accept partial Bayesian experiment")
    for name, digest in report["artifacts_sha256"].items():
        if hashlib.sha256((path.parent / name).read_bytes()).hexdigest() != digest:
            raise ArithmeticError("own Bayesian artifact bytes changed")
    transcripts = json.loads(
        gzip.decompress((path.parent / "public-transcripts.json.gz").read_bytes())
    )
    config = report["config"]
    rows = {
        (r["game"], r["seat"], r["scenario"], r["seed"], r["hands_observed"]): r
        for r in report["rows"]
    }
    expected = (
        len(config["games"])
        * len(config["seats"])
        * len(config["scenarios"])
        * len(config["seeds"])
        * len(config["checkpoints"])
    )
    if len(rows) != len(report["rows"]) or len(rows) != expected:
        raise ArithmeticError("duplicate/missing Bayesian checkpoint row")
    histories = {
        (h["game"], h["seat"], h["scenario"], h["seed"]): h
        for h in transcripts["histories"]
    }
    if len(histories) != len(transcripts["histories"]) or len(
        histories
    ) != expected // len(config["checkpoints"]):
        raise ArithmeticError("duplicate/missing public history")
    max_posterior_error, checked = 0.0, 0
    for game in config["games"]:
        tree = Tree.build(cast(GameName, game))
        solver = CFR(tree, "cfr_plus")
        solver.train(config["blueprint_iterations"][game])
        blueprint = solver.average_policy
        family = {
            name: scripted_policy(tree, name, config["uniform_probability_floor_mass"])
            for name in config["hypotheses"]
        }
        prior = np.array(config["prior"], dtype=np.float64)
        for seat in config["seats"]:
            model = TranscriptModel(tree, tuple(family.values()), seat)
            expected_catalog = [
                {"own_card": e.own_card, "board": e.board, "histories": e.histories}
                for e in model.lookup
            ]
            if (
                json.loads(json.dumps(expected_catalog))
                != transcripts["catalog"][f"{game}:{seat}"]
            ):
                raise ArithmeticError(
                    "public evidence catalog changed or contains extra data"
                )
            for scenario in config["scenarios"]:
                for seed in config["seeds"]:
                    indices = histories[game, seat, scenario, seed]["evidence_indices"]
                    if len(indices) != config["checkpoints"][-1] or any(
                        type(i) is not int or not 0 <= i < len(model.lookup)
                        for i in indices
                    ):
                        raise ArithmeticError("invalid censored transcript indices")
                    for checkpoint in config["checkpoints"]:
                        # Batch log likelihoods, independent of online update order.
                        positive = prior > 0
                        logs = np.full(prior.shape, -np.inf)
                        logs[positive] = np.log(prior[positive])
                        if checkpoint:
                            logs += np.log(model.likelihoods[indices[:checkpoint]]).sum(
                                axis=0
                            )
                        weights = np.exp(logs - logs.max())
                        weights /= weights.sum()
                        row = rows[game, seat, scenario, seed, checkpoint]
                        error = float(np.max(np.abs(weights - row["posterior"])))
                        max_posterior_error = max(max_posterior_error, error)
                        if error > 1e-11:
                            raise ArithmeticError(
                                "posterior does not replay from censored evidence"
                            )
                        # Use the original online vector for exact policy tie behavior.
                        online = np.array(row["posterior"], dtype=np.float64)
                        predictive = root_mixture(
                            tree, tuple(family.values()), online, 1 - seat
                        )
                        guarded = guarded_response(
                            tree,
                            blueprint,
                            predictive,
                            seat,
                            config["security_degradation_budget_ante_chips"],
                            config["security_tolerance"],
                        )
                        truth = scenario_policy(scenario, checkpoint, config, family)
                        expected_metrics = {
                            "predictive_nll_nats": model.conditional_log_loss(
                                online, blueprint, truth
                            ),
                            "prior_nll_nats": model.conditional_log_loss(
                                prior, blueprint, truth
                            ),
                            "guarded_fraction": guarded.fraction,
                            "certified_lower_bound": guarded.certified_lower_bound,
                        }
                        for key, value in expected_metrics.items():
                            if not np.isclose(row[key], value, atol=1e-12, rtol=0):
                                raise ArithmeticError(f"Bayesian metric changed: {key}")
                        for name, policy in (
                            ("blueprint", blueprint),
                            ("unrestricted", guarded.unrestricted),
                            ("guarded", guarded.policy),
                        ):
                            metric = row["policies"][name]
                            if (
                                abs(
                                    metric["ev_ante_chips"]
                                    - profile_value(tree, policy, truth, seat)
                                )
                                > 1e-12
                                or abs(
                                    metric["security_ante_chips"]
                                    - security(tree, policy, seat)
                                )
                                > 1e-12
                            ):
                                raise ArithmeticError(
                                    "exact response EV/security does not replay"
                                )
                        checked += 1
    return {
        "status": "passed",
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "checkpoint_rows": checked,
        "public_histories": len(histories),
        "observed_hands": sum(len(h["evidence_indices"]) for h in histories.values()),
        "max_batch_online_posterior_error": max_posterior_error,
        "scope": (
            "posterior odds and exact metrics replay; simulated hidden "
            "cards/payoffs are absent from learner evidence"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/extensions/opponents.json")
    )
    args = parser.parse_args()
    result = audit(args.report)
    (args.report.parent / "opponent-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"passed: {result['checkpoint_rows']} exact rows and "
        f"{result['observed_hands']} censored hand observations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
