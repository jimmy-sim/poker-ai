"""Bounded own river study; reference outputs are never training inputs."""

import gzip
import hashlib
import json
import math
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import (
    decision_mass,
    full_solver,
    root_factory,
    sampled_average,
    score,
)
from poker_ai.postflop.matrix import IndexedState, MatrixTree, recall_violations
from poker_ai.postflop.river_sampling import (
    RiverIntegratedMCCFR,
    integrated_external_updates,
    is_hidden_river,
)
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    exact_initial_expectation,
    save_learning_checkpoint,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.training.mccfr import external_updates
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-river-study-v1"
POLICY_FORMAT = "poker-ai-river-study-own-policies-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_config(config: dict[str, Any]) -> None:
    """Reject ambiguous cells, invalid budgets and unsupported estimator choices."""
    if (
        config["schema_version"] != 1
        or config["encoding"] != "exact"
        or config["variants"] != ["external", "river_integrated"]
        or config["sampling_weighting"] != "linear"
        or config["initial_exact_expectation"] is not True
        or config["candidate_selected_before_results"] != "river_integrated"
    ):
        raise ValueError("unsupported river study design")
    for key in ("training_seeds", "total_node_thresholds", "full_tree_checkpoints"):
        values = config[key]
        if (
            not values
            or any(type(v) is not int or v < 1 for v in values)
            or len(set(values)) != len(values)
            or (key != "training_seeds" and values != sorted(values))
        ):
            raise ValueError("invalid seeds/checkpoints")
    panel = config["frozen_panel"]
    if (
        panel["policies"] != ["uniform", "own_full_cfr_plus_256"]
        or panel["targets"] != [0, 1]
        or not panel["seeds"]
        or len(set(panel["seeds"])) != len(panel["seeds"])
        or any(type(s) is not int or s < 1 for s in panel["seeds"])
        or set(panel["seeds"]) & set(config["training_seeds"])
        or type(panel["passes_per_seed_target_policy_variant"]) is not int
        or panel["passes_per_seed_target_policy_variant"] < 2
        or 256 not in config["full_tree_checkpoints"]
        or not config["spot_files"]
        or len(set(config["spot_files"])) != len(config["spot_files"])
        or config["maximum_tree_nodes"] < 1
        or not math.isfinite(config["maximum_seconds_total"])
        or config["maximum_seconds_total"] <= 0
        or not 0 < config["independent_tolerance_chips"] <= 1e-8
    ):
        raise ValueError("invalid frozen panel/budget")


def expected_updates(
    tree: MatrixTree, policy: FloatArray, target: int
) -> tuple[FloatArray, FloatArray]:
    """Full expectation of ONE frozen external target pass, without t weighting.

    Regret excludes target reach; simple opponent averaging excludes target
    reach as its actions enumerate. Chance supplies its full reach to both.
    This is a direct tree calculation, separate from either sampled traversal.
    """
    if target not in (0, 1):
        raise ValueError("invalid target")
    tree.validate_policy(policy)
    edges = tree.edges(policy)
    reach, values = tree.reaches(edges), tree.values(edges)
    regret, average = np.zeros_like(policy), np.zeros_like(policy)
    nodes = np.flatnonzero(tree.player == target)
    infos = tree.information[nodes]
    delta = (values[tree.children[nodes]] - values[nodes, None]) * tree.valid[nodes]
    cf = tree.chance_reach[nodes] * reach[nodes, 1 - target]
    np.add.at(regret, infos, cf[:, None] * delta * (1 if target == 0 else -1))
    nodes = np.flatnonzero(tree.player == 1 - target)
    infos = tree.information[nodes]
    mass = tree.chance_reach[nodes] * reach[nodes, 1 - target]
    np.add.at(average, infos, mass[:, None] * policy[infos])
    return regret, average


def squared_error(
    updates: dict[str, FloatArray],
    expected: FloatArray,
    lookup: dict[str, int],
    mask: np.ndarray[Any, np.dtype[np.bool_]],
) -> float:
    """Squared L2 over selected legal entries; unvisited increments are zero."""
    result = float(np.square(expected[mask]).sum())
    for key, value in updates.items():
        info = lookup[key]
        if mask[info]:
            truth = expected[info, : len(value)]
            result += float(value @ value - 2 * value @ truth)
    if result < -1e-7:
        raise ArithmeticError("negative squared update error")
    return max(0.0, result)


class Deadline:
    def __init__(self, seconds: float) -> None:
        self.started = time.perf_counter()
        self.seconds = seconds

    def check(self) -> None:
        if time.perf_counter() - self.started >= self.seconds:
            raise TimeoutError("declared total river-study wall-time cap exceeded")


def frozen_panel(
    tree: MatrixTree,
    policy: FloatArray,
    label: str,
    config: dict[str, Any],
    deadline: Deadline,
    rows: list[dict[str, Any]],
) -> None:
    """Retain per-seed means/SDs; independent frozen draws, no policy updates."""
    lookup = {key: i for i, key in enumerate(tree.keys)}
    all_infos = np.ones(len(tree.keys), dtype=np.bool_)
    turn = np.array(
        [
            len(tree.source.states[n].dealer.board) == 4  # type: ignore[union-attr]
            for n in tree.source.representatives
        ],
        dtype=np.bool_,
    )
    policy_hash = hashlib.sha256(policy.tobytes()).hexdigest()

    def frozen(key: str, actions: tuple[int, ...]) -> FloatArray:
        info = lookup[key]
        if actions != tree.actions[info]:
            raise ValueError("frozen policy action mismatch")
        return policy[info, : len(actions)]

    panel = config["frozen_panel"]
    for target in panel["targets"]:
        regret, average = expected_updates(tree, policy, target)
        for variant in config["variants"]:
            for seed in panel["seeds"]:
                rng = Generator(PCG64(seed))

                def select(probabilities: FloatArray, rng: Generator = rng) -> int:
                    return int(rng.choice(len(probabilities), p=probabilities))

                errors = []
                started = time.perf_counter()
                for _ in range(panel["passes_per_seed_target_policy_variant"]):
                    deadline.check()
                    update = (
                        external_updates(IndexedState(tree), target, frozen, select)
                        if variant == "external"
                        else integrated_external_updates(
                            IndexedState(tree), target, frozen, select, is_hidden_river
                        )
                    )
                    errors.append(
                        [
                            squared_error(update.regrets, regret, lookup, all_infos),
                            squared_error(update.regrets, regret, lookup, turn),
                            squared_error(update.averages, average, lookup, all_infos),
                            float(update.visited),
                        ]
                    )
                data = np.asarray(errors)
                mean = data.mean(axis=0)
                rows.append(
                    {
                        "spot": tree.source.spot.name,
                        "policy": label,
                        "policy_sha256": policy_hash,
                        "target": target,
                        "variant": variant,
                        "seed": seed,
                        "passes": len(errors),
                        "regret_mse_all": float(mean[0]),
                        "regret_mse_turn": float(mean[1]),
                        "average_mse_all": float(mean[2]),
                        "mean_node_visits": float(mean[3]),
                        "regret_mse_times_cost": float(mean[0] * mean[3]),
                        "turn_regret_mse_times_cost": float(mean[1] * mean[3]),
                        "average_mse_times_cost": float(mean[2] * mean[3]),
                        "sample_sd": data.std(axis=0, ddof=1).tolist(),
                        "seconds": time.perf_counter() - started,
                    }
                )
                print(
                    f"frozen: {tree.source.spot.name}/{label}/{target}/"
                    f"{variant}/{seed}",
                    flush=True,
                )


def advance_to_work(solver: PostflopMCCFR, threshold: int, deadline: Deadline) -> None:
    """Finish an iteration across a threshold; count warm and recursive work."""
    while solver.warm_node_equivalent + solver.nodes_visited < threshold:
        deadline.check()
        solver.step()
    deadline.check()


def acceptance(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Require the complete declared grid; candidate remains preselected."""
    identities = [
        (r["spot_file"], r["method"], r["seed"], r["node_threshold"]) for r in rows
    ]
    expected = {
        (spot, method, seed, threshold)
        for spot in config["spot_files"]
        for method in config["variants"]
        for seed in config["training_seeds"]
        for threshold in config["total_node_thresholds"]
    } | {(spot, "full_cfr_plus", None, None) for spot in config["spot_files"]}
    # Full controls have multiple iterations; check them separately.
    actual = set(identities)
    full = [r for r in rows if r["method"] == "full_cfr_plus"]
    controls_complete = all(
        sorted(r["iteration"] for r in full if r["spot_file"] == spot)
        == config["full_tree_checkpoints"]
        for spot in config["spot_files"]
    )
    samples = [i for i in identities if i[1] != "full_cfr_plus"]
    complete = (
        actual == expected and len(samples) == len(set(samples)) and controls_complete
    )
    checks = []
    for spot in config["spot_files"]:
        controls = [
            r
            for r in full
            if r["spot_file"] == spot
            and r["iteration"] == config["full_tree_checkpoints"][-1]
        ]
        for method in config["variants"]:
            final = [
                r
                for r in rows
                if r["spot_file"] == spot
                and r["method"] == method
                and r["node_threshold"] == config["total_node_thresholds"][-1]
            ]
            if len(controls) != 1 or sorted(r["seed"] for r in final) != sorted(
                config["training_seeds"]
            ):
                checks.append(
                    {
                        "spot_file": spot,
                        "variant": method,
                        "passed": False,
                        "reason": "missing/duplicate final rows",
                    }
                )
                continue
            eps = [r["exploitability_pot_fraction"] for r in final]
            cover = min(
                r["uniform_reach_average_row_coverage"] for r in final + controls
            )
            checks.append(
                {
                    "spot_file": spot,
                    "variant": method,
                    "full_epsilon_pot": controls[0]["exploitability_pot_fraction"],
                    "median_epsilon_pot": float(np.median(eps)),
                    "max_epsilon_pot": max(eps),
                    "minimum_coverage": cover,
                    "passed": bool(
                        controls[0]["exploitability_pot_fraction"]
                        <= config["full_tree_exploitability_pot_limit"]
                        and np.median(eps)
                        <= config["sampled_median_exploitability_pot_limit"]
                        and max(eps) <= config["sampled_max_exploitability_pot_limit"]
                        and cover
                        >= config["minimum_uniform_reach_average_row_coverage"]
                    ),
                }
            )
    return {
        "complete": complete,
        "checks": checks,
        "candidate_passed": complete
        and all(r["passed"] for r in checks if r["variant"] == "river_integrated"),
    }


def run_study(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_config(config)
    if output.exists():
        raise FileExistsError("retain existing study evidence; choose a new output")
    deadline = Deadline(config["maximum_seconds_total"])
    source = source_provenance(
        root, config_path, entrypoints=("scripts/study_river_integration.py",)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    policy_path = output.with_name(output.stem + "-own-policies.json.gz")
    if policy_path.exists():
        raise FileExistsError("retain existing frozen policies")
    rows: list[dict[str, Any]] = []
    panels: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "package_versions": {
            name: version(name)
            for name in (
                ("numpy", "numba")
                if config["full_tree_backend"] == "fused_numba"
                else ("numpy",)
            )
        },
        "spot_sha256": {p: digest(root / p) for p in config["spot_files"]},
        "rows": rows,
        "frozen_panel": panels,
        "diagnostics": diagnostics,
        "scope": (
            "known-development restricted turn games; "
            "no fresh hold-out/global strength claim"
        ),
    }

    def persist() -> None:
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
        report.update(
            seconds=time.perf_counter() - deadline.started,
            own_policies_file=policy_path.name,
            own_policies_sha256=digest(policy_path),
            acceptance=acceptance(rows, config),
        )
        temporary = output.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        temporary.replace(output)

    def record(
        tree: MatrixTree,
        filename: str,
        policy: FloatArray,
        trained: FloatArray,
        uniform_mass: FloatArray,
        fields: dict[str, Any],
    ) -> None:
        row = {
            "spot": tree.source.spot.name,
            "spot_file": filename,
            "encoding": "exact",
            **fields,
            **score(tree, tree, policy, trained, uniform_mass),
        }
        rows.append(row)
        snapshots.append(
            {
                **{
                    k: row[k]
                    for k in (
                        "spot",
                        "spot_file",
                        "method",
                        "seed",
                        "iteration",
                        "node_threshold",
                    )
                },
                "policy": tree.exact_policy(policy),
            }
        )
        print(
            f"learning: {row['spot']}/{row['method']}/{row['seed']} "
            f"work={row['total_node_work']} t={row['iteration']} "
            f"eps/pot={row['exploitability_pot_fraction']:.7g}",
            flush=True,
        )
        persist()

    try:
        persist()
        names: set[str] = set()
        for filename in config["spot_files"]:
            deadline.check()
            setup = time.perf_counter()
            spot = load_spot(root / filename)
            if spot.name in names or len(spot.board) != 4:
                raise ValueError("duplicate spot name or unsupported street")
            names.add(spot.name)
            tree = MatrixTree.build(SpotTree.build(spot))
            if len(tree.player) > config["maximum_tree_nodes"] or recall_violations(
                tree
            ):
                raise ValueError("tree cap or perfect-recall guard failed")
            if 2 * len(tree.player) >= config["total_node_thresholds"][0]:
                raise ValueError("initial expectation must fit below first threshold")
            uniform = tree.normalize(tree.legal)
            uniform_mass = decision_mass(tree, uniform)
            diagnostics.append(
                {
                    "spot": spot.name,
                    "nodes": len(tree.player),
                    "information_sets": len(tree.keys),
                    "setup_seconds": time.perf_counter() - setup,
                }
            )
            full_started = time.perf_counter()
            full = full_solver(tree, config["full_tree_backend"])
            for checkpoint in config["full_tree_checkpoints"]:
                while full.iteration < checkpoint:
                    deadline.check()
                    full.step()
                policy = full.average_policy
                record(
                    tree,
                    filename,
                    policy,
                    (full.strategy_sum.sum(axis=1) > 0).astype(np.float64),
                    uniform_mass,
                    {
                        "method": "full_cfr_plus",
                        "seed": None,
                        "iteration": checkpoint,
                        "node_threshold": None,
                        "total_node_work": 2 * checkpoint * len(tree.player),
                        "seconds": time.perf_counter() - full_started,
                        "warm_node_equivalent": 0,
                    },
                )
                if checkpoint == 256:
                    frozen_panel(tree, uniform, "uniform", config, deadline, panels)
                    frozen_panel(
                        tree, policy, "own_full_cfr_plus_256", config, deadline, panels
                    )
                    persist()
                    # Control timing excludes the frozen-panel work.
                    full_started = time.perf_counter() - cast(
                        float, rows[-1]["seconds"]
                    )
            for variant in config["variants"]:
                for seed in config["training_seeds"]:
                    started = time.perf_counter()
                    cls = (
                        PostflopMCCFR if variant == "external" else RiverIntegratedMCCFR
                    )
                    solver = cls(root_factory(tree), Generator(PCG64(seed)), "linear")
                    exact_initial_expectation(solver, tree)
                    for threshold in config["total_node_thresholds"]:
                        advance_to_work(solver, threshold, deadline)
                        policy, trained = sampled_average(solver, tree)
                        total = solver.warm_node_equivalent + solver.nodes_visited
                        if not 0 <= total - threshold < 2 * len(tree.player):
                            raise ArithmeticError("unbounded work overshoot")
                        checkpoint = (
                            output.parent
                            / "runs"
                            / output.stem
                            / f"{spot.name}-{variant}-{seed}-{threshold}.json"
                        )
                        save_learning_checkpoint(
                            solver,
                            checkpoint,
                            config={
                                "learning": {**config, "sampler": variant},
                                "spot_file": filename,
                                "spot_sha256": report["spot_sha256"][filename],
                            },
                            provenance=source,
                        )
                        visited = np.array(
                            [k in solver.sampled_keys for k in tree.keys],
                            dtype=np.float64,
                        )
                        record(
                            tree,
                            filename,
                            policy,
                            trained,
                            uniform_mass,
                            {
                                "method": variant,
                                "seed": seed,
                                "iteration": solver.iteration,
                                "node_threshold": threshold,
                                "total_node_work": total,
                                "overshoot": total - threshold,
                                "recursive_visits": solver.nodes_visited,
                                "warm_node_equivalent": solver.warm_node_equivalent,
                                "seconds": time.perf_counter() - started,
                                "checkpoint_file": str(
                                    checkpoint.relative_to(output.parent)
                                ),
                                "checkpoint_sha256": digest(checkpoint),
                                "checkpoint_visits_sha256": digest(
                                    checkpoint.with_suffix(".visits.json")
                                ),
                                "subsequently_sampled_information_sets": len(
                                    solver.sampled_keys
                                ),
                                "initial_only_information_sets": len(
                                    set(solver.rows) - solver.sampled_keys
                                ),
                                "uniform_reach_subsequently_sampled_coverage": float(
                                    uniform_mass @ visited / uniform_mass.sum()
                                ),
                            },
                        )
        deadline.check()
        report["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        report["status"] = "incomplete"
        report["failure"] = {"type": type(error).__name__, "reason": str(error)}
    finally:
        persist()
    return report
