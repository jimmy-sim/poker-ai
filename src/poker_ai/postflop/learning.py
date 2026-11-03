"""Own bounded postflop self-play, exact metrics and explicit fallback coverage."""

import gzip
import hashlib
import importlib
import json
import time
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import (
    Encoding,
    IndexedState,
    MatrixTree,
    recall_violations,
)
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    Weighting,
    exact_initial_expectation,
    save_learning_checkpoint,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.toy.analysis import evaluate
from poker_ai.toy.cfr import CFR
from poker_ai.training.mccfr import MCCFR, RootFactory
from poker_ai.validation.five_card import source_provenance

POLICY_FORMAT = "poker-ai-own-postflop-policies-v1"


class FullSolver(Protocol):
    iteration: int
    strategy_sum: FloatArray

    @property
    def average_policy(self) -> FloatArray: ...
    def step(self) -> None: ...


def full_solver(tree: MatrixTree, backend: str) -> FullSolver:
    if backend == "numpy":
        return CFR(tree, "cfr_plus")
    if backend != "fused_numba":
        raise ValueError("unknown full-tree arithmetic backend")
    module = importlib.import_module("poker_ai.postflop.jit_cfr")
    return cast(FullSolver, module.FusedCFRPlus(tree))


def root_factory(tree: MatrixTree) -> RootFactory:
    return lambda rng: IndexedState(tree)


def sampled_average(solver: MCCFR, tree: MatrixTree) -> tuple[FloatArray, FloatArray]:
    """Export without creating unvisited rows or relabeling uniform fallback."""
    policy = tree.normalize(tree.legal)
    trained = np.zeros(len(tree.keys))
    for info, key in enumerate(tree.keys):
        row = solver.rows.get(key)
        if row is None:
            continue
        if row.actions != tree.actions[info]:
            raise ValueError("sampled policy menu mismatch")
        mass = float(row.strategy_sum.sum())
        if mass > 0:
            policy[info, : len(row.actions)] = row.strategy_sum / mass
            trained[info] = 1
    return policy, trained


def decision_mass(tree: MatrixTree, policy: FloatArray) -> FloatArray:
    reaches = tree.chance_reach * tree.reaches(tree.edges(policy)).prod(axis=1)
    mass = np.zeros(len(tree.keys))
    nodes = tree.player >= 0
    np.add.at(mass, tree.information[nodes], reaches[nodes])
    return mass


def score(
    exact: MatrixTree,
    tree: MatrixTree,
    policy: FloatArray,
    trained: FloatArray,
    uniform_mass: FloatArray,
) -> dict[str, Any]:
    deployed = exact.dense_exact(tree.exact_policy(policy))
    metrics = evaluate(exact, deployed)
    active = trained[tree.exact_to_abstract]
    own_mass = decision_mass(exact, deployed)
    return {
        "exploitability_chips": metrics.exploitability,
        "exploitability_pot_fraction": metrics.exploitability / tree.source.spot.pot,
        "value_player_zero_chips": metrics.value_player_zero,
        "best_response_zero_chips": metrics.best_response_zero,
        "best_response_one_chips": metrics.best_response_one,
        "uniform_reach_average_row_coverage": float(
            np.clip(uniform_mass @ active / uniform_mass.sum(), 0.0, 1.0)
        ),
        "own_reach_average_row_coverage": float(
            np.clip(own_mass @ active / own_mass.sum(), 0.0, 1.0)
        ),
        "positive_average_rows": int(trained.sum()),
        "abstract_information_sets": len(tree.keys),
        "exact_information_sets": len(exact.keys),
    }


def acceptance(
    rows: list[dict[str, Any]], config: dict[str, Any], spots: list[str]
) -> dict[str, Any]:
    """Gate only exact-card controls; abstraction failures are diagnostic results."""
    checks = []
    for spot in spots:
        selected = [r for r in rows if r["spot"] == spot and r["encoding"] == "exact"]
        full = [
            r
            for r in selected
            if r["method"] == "full_cfr_plus"
            and r["iteration"] == config["full_tree_checkpoints"][-1]
        ]
        sampled = [
            r
            for r in selected
            if r["method"] == "external"
            and r["iteration"] == config["sampled_checkpoints"][-1]
        ]
        complete = len(full) == 1 and sorted(r["seed"] for r in sampled) == sorted(
            config["seeds"]
        )
        if not complete:
            checks.append(
                {"spot": spot, "passed": False, "reason": "missing exact final rows"}
            )
            continue
        eps = [r["exploitability_pot_fraction"] for r in sampled]
        coverage = min(r["uniform_reach_average_row_coverage"] for r in full + sampled)
        passed = (
            full[0]["exploitability_pot_fraction"]
            <= config["full_tree_exploitability_pot_limit"]
            and float(np.median(eps))
            <= config["sampled_median_exploitability_pot_limit"]
            and max(eps) <= config["sampled_max_exploitability_pot_limit"]
            and coverage >= config["minimum_uniform_reach_average_row_coverage"]
        )
        checks.append(
            {
                "spot": spot,
                "passed": passed,
                "full_final_epsilon_pot": full[0]["exploitability_pot_fraction"],
                "sampled_median_epsilon_pot": float(np.median(eps)),
                "sampled_max_epsilon_pot": max(eps),
                "minimum_uniform_coverage": coverage,
            }
        )
    return {
        "passed": bool(checks) and all(r["passed"] for r in checks),
        "spots": checks,
    }


def run_training(
    root: Path,
    config_path: Path,
    output: Path,
    *,
    phase: str,
    encodings: tuple[Encoding, ...],
) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(config_path.read_text())
    if (
        phase not in ("development", "heldout")
        or not encodings
        or len(set(encodings)) != len(encodings)
    ):
        raise ValueError("invalid postflop phase/encodings")
    if config["schema_version"] != 1 or any(
        e not in config["encodings"] for e in encodings
    ):
        raise ValueError("invalid learning schema/encoding")
    for key in ("full_tree_checkpoints", "sampled_checkpoints", "seeds"):
        values = config[key]
        if (
            not values
            or len(set(values)) != len(values)
            or any(type(v) is not int or v < 1 for v in values)
            or (key != "seeds" and values != sorted(values))
        ):
            raise ValueError("invalid postflop checkpoints/seeds")
    started = time.perf_counter()
    source = source_provenance(
        root, config_path, entrypoints=("scripts/train_postflop.py",)
    )
    rows: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    model = CardAbstraction.load(root / config["model"])
    model_hash = hashlib.sha256((root / config["model"]).read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output.parent / "runs" / output.stem
    failure = None
    names = []
    try:
        for filename in config[phase + "_spots"]:
            spot = load_spot(root / filename)
            names.append(spot.name)
            t = time.perf_counter()
            source_tree = SpotTree.build(spot)
            if len(source_tree.states) > config["maximum_nodes_per_pass"]:
                raise ValueError("materialized tree exceeds target-pass budget")
            exact = MatrixTree.build(source_tree)
            uniform = exact.normalize(exact.legal)
            uniform_mass = decision_mass(exact, uniform)
            shared_setup = time.perf_counter() - t
            for encoding in encodings:
                representation_started = time.perf_counter()
                tree = (
                    exact
                    if encoding == "exact"
                    else MatrixTree.build(source_tree, encoding, model)
                )
                violations = recall_violations(tree)
                if violations:
                    raise ValueError(
                        "representation violates own information/action recall"
                    )
                diagnostics.append(
                    {
                        "spot": spot.name,
                        "encoding": encoding,
                        "nodes": len(tree.player),
                        "information_sets": len(tree.keys),
                        "recall_violations": violations,
                        "initial_uniform_epsilon_pot": evaluate(
                            exact, uniform
                        ).exploitability
                        / spot.pot,
                        "shared_exact_setup_seconds": shared_setup,
                        "representation_build_seconds": time.perf_counter()
                        - representation_started,
                    }
                )
                for method, seed in [("full_cfr_plus", None)] + [
                    ("external", s) for s in config["seeds"]
                ]:
                    full = (
                        full_solver(tree, config.get("full_tree_backend", "numpy"))
                        if method == "full_cfr_plus"
                        else None
                    )
                    weighting = config.get("sampling_weighting", "uniform")
                    if weighting not in ("uniform", "linear"):
                        raise ValueError("invalid sampling weighting")
                    warm = config.get("initial_exact_expectation", False)
                    if type(warm) is not bool:
                        raise ValueError("invalid initialization flag")
                    sampled = (
                        PostflopMCCFR(
                            root_factory(tree),
                            Generator(PCG64(seed)),
                            cast(Weighting, weighting),
                        )
                        if seed is not None
                        else None
                    )
                    if sampled is not None and warm:
                        exact_initial_expectation(sampled, tree)
                    checkpoints = config[
                        "full_tree_checkpoints"
                        if full is not None
                        else "sampled_checkpoints"
                    ]
                    run_started = time.perf_counter()
                    for checkpoint in checkpoints:
                        while (
                            full.iteration
                            if full is not None
                            else cast(MCCFR, sampled).iteration
                        ) < checkpoint:
                            if (
                                time.perf_counter() - started
                                > config["maximum_seconds"]
                            ):
                                raise TimeoutError(
                                    "declared postflop training budget exceeded"
                                )
                            if full is not None:
                                full.step()
                            else:
                                cast(MCCFR, sampled).step()
                        if full is not None:
                            policy = full.average_policy
                            trained = (full.strategy_sum.sum(axis=1) > 0).astype(
                                np.float64
                            )
                            nodes = 2 * full.iteration * len(tree.player)
                        else:
                            assert sampled is not None
                            policy, trained = sampled_average(sampled, tree)
                            nodes = sampled.nodes_visited
                        row = {
                            "spot": spot.name,
                            "encoding": encoding,
                            "method": method,
                            "sampling_weighting": None
                            if sampled is None
                            else sampled.weighting,
                            "full_tree_backend": config.get(
                                "full_tree_backend", "numpy"
                            ),
                            "seed": seed,
                            "iteration": checkpoint,
                            "seconds": time.perf_counter() - run_started,
                            "nodes_visited_or_full_node_equivalent": nodes,
                            "initial_exact_expectation": bool(sampled and warm),
                            "warm_node_equivalent": 0
                            if sampled is None
                            else sampled.warm_node_equivalent,
                            "subsequently_sampled_information_sets": None
                            if sampled is None
                            else len(sampled.sampled_keys),
                            "initial_only_information_sets": 0
                            if sampled is None
                            else len(set(sampled.rows) - sampled.sampled_keys),
                            **score(exact, tree, policy, trained, uniform_mass),
                        }
                        rows.append(row)
                        snapshots.append(
                            {
                                k: row[k]
                                for k in (
                                    "spot",
                                    "encoding",
                                    "method",
                                    "seed",
                                    "iteration",
                                )
                            }
                        )
                        snapshots[-1]["policy"] = tree.exact_policy(policy)
                        if sampled is not None:
                            name = f"{spot.name}-{encoding}-{seed}-{checkpoint}.json"
                            save_learning_checkpoint(
                                sampled,
                                checkpoint_dir / name,
                                config={
                                    "learning": config,
                                    "spot": filename,
                                    "encoding": encoding,
                                    "model_sha256": model_hash,
                                },
                                provenance=source,
                            )
                        print(
                            f"trained: {spot.name}/{encoding}/{method}/{seed} "
                            f"t={checkpoint}; "
                            f"eps/pot={row['exploitability_pot_fraction']:.6g}; "
                            f"coverage={row['uniform_reach_average_row_coverage']:.1%}",
                            flush=True,
                        )
    except (TimeoutError, ValueError) as error:
        failure = {"type": type(error).__name__, "reason": str(error)}
    policy_path = output.with_name(output.stem + "-own-policies.json.gz")
    policy_path.write_bytes(
        gzip.compress(
            json.dumps(
                {"format": POLICY_FORMAT, "policies": snapshots},
                sort_keys=True,
                allow_nan=False,
            ).encode(),
            mtime=0,
        )
    )
    report: dict[str, Any] = {
        "status": "incomplete" if failure else "completed",
        "failure": failure,
        "phase": phase,
        "encodings": encodings,
        "config": config,
        "source": source,
        "model_sha256": model_hash,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "rows": rows,
        "diagnostics": diagnostics,
        "own_policies_file": policy_path.name,
        "own_policies_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "spot_sha256": {
            p: hashlib.sha256((root / p).read_bytes()).hexdigest()
            for p in config[phase + "_spots"]
        },
        "exact_acceptance": acceptance(rows, config, names)
        if "exact" in encodings and failure is None
        else None,
        "scope": (
            "own per-spot training; full-tree CFR+ versus vanilla external-"
            "sampling CFR, different iteration costs; exact restricted-game "
            "NashConv/2, no global strength or zero-shot claim"
        ),
    }
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return report
