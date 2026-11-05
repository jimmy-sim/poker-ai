"""Frozen ordinary-procedure validation on fresh, independently trained spots."""

import gzip
import json
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.postflop.fresh_cohort import (
    development_gate,
    validate_config,
    verify_freeze,
)
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import (
    decision_mass,
    full_solver,
    root_factory,
    sampled_average,
    score,
)
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.river_study import Deadline, advance_to_work, digest
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    exact_initial_expectation,
    save_learning_checkpoint,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-fresh-learning-v1"
POLICY_FORMAT = "poker-ai-fresh-own-policies-v1"
IDENTITY = ("spot_file", "method", "seed", "node_threshold", "iteration")


def filenames(config: dict[str, Any]) -> list[str]:
    return [f"configs/fresh-spots/{s['name']}.json" for s in config["strata"]]


def acceptance(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Require every fixed cell; thresholds are unchanged and final-only."""
    ids = [
        (
            r["spot_file"],
            r["method"],
            r["seed"],
            r["iteration"] if r["method"] == "full_cfr_plus" else r["node_threshold"],
        )
        for r in rows
    ]
    expected = {
        (p, "external", seed, budget)
        for p in filenames(config)
        for seed in config["training_seeds"]
        for budget in config["total_node_thresholds"]
    }
    expected |= {
        (p, "full_cfr_plus", None, t)
        for p in filenames(config)
        for t in config["full_tree_checkpoints"]
    }
    complete = len(ids) == len(set(ids)) and set(ids) == expected
    checks = []
    for path in filenames(config):
        full = [
            r
            for r in rows
            if r["spot_file"] == path
            and r["method"] == "full_cfr_plus"
            and r["iteration"] == config["full_tree_checkpoints"][-1]
        ]
        final = [
            r
            for r in rows
            if r["spot_file"] == path
            and r["method"] == "external"
            and r["node_threshold"] == config["total_node_thresholds"][-1]
        ]
        if len(full) != 1 or sorted(r["seed"] for r in final) != sorted(
            config["training_seeds"]
        ):
            checks.append(
                {
                    "spot_file": path,
                    "passed": False,
                    "reason": "missing/duplicate final cells",
                }
            )
            continue
        eps = [r["exploitability_pot_fraction"] for r in final]
        coverage = min(r["uniform_reach_average_row_coverage"] for r in full + final)
        checks.append(
            {
                "spot_file": path,
                "full_epsilon_pot": full[0]["exploitability_pot_fraction"],
                "median_epsilon_pot": float(np.median(eps)),
                "max_epsilon_pot": max(eps),
                "minimum_average_coverage": coverage,
                "passed": bool(
                    full[0]["exploitability_pot_fraction"]
                    <= config["full_tree_exploitability_pot_limit"]
                    and np.median(eps)
                    <= config["sampled_median_exploitability_pot_limit"]
                    and max(eps) <= config["sampled_max_exploitability_pot_limit"]
                    and coverage >= config["minimum_uniform_reach_average_row_coverage"]
                ),
            }
        )
    return {
        "complete": complete,
        "passed": complete and all(r["passed"] for r in checks),
        "checks": checks,
    }


def run_validation(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_config(config)
    policy_path = output.with_name(output.stem + "-own-policies.json.gz")
    if output.exists() or policy_path.exists():
        raise FileExistsError("retain prior evidence; use a different output path")
    deadline = Deadline(config["maximum_seconds_total"])
    source = source_provenance(
        root, config_path, entrypoints=("scripts/validate_fresh_games.py",)
    )
    rows: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "started_at_utc": datetime.now(UTC).isoformat(),
        "rows": rows,
        "diagnostics": [],
        "admission": None,
        "spot_sha256": {},
        "package_versions": {
            k: version(k)
            for k in (
                ("numpy", "numba")
                if config["full_tree_backend"] == "fused_numba"
                else ("numpy",)
            )
        },
        "scope": (
            "fresh procedure check; separate per-spot training; "
            "no zero-shot/global strength claim"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)

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
        policy: np.ndarray[Any, np.dtype[np.float64]],
        trained: np.ndarray[Any, np.dtype[np.float64]],
        uniform_mass: np.ndarray[Any, np.dtype[np.float64]],
        fields: dict[str, Any],
    ) -> None:
        row = {
            "spot_file": filename,
            "spot": tree.source.spot.name,
            "encoding": "exact",
            **fields,
            **score(tree, tree, policy, trained, uniform_mass),
        }
        rows.append(row)
        snapshots.append(
            {**{k: row[k] for k in IDENTITY}, "policy": tree.exact_policy(policy)}
        )
        print(
            f"fresh: {row['spot']}/{row['method']}/{row['seed']} "
            f"work={row['total_node_work']} t={row['iteration']} "
            f"epsilon/pot={row['exploitability_pot_fraction']:.7g}",
            flush=True,
        )
        persist()

    try:
        # Admission reads only known development inputs. No fresh tree is built
        # until source/input identity, all selected seeds and native audit pass.
        report["admission"] = development_gate(root, config_path)
        _, freeze = verify_freeze(root, config_path)
        report["freeze_sha256"] = digest(root / config["freeze_file"])
        report["spot_sha256"] = freeze["spot_sha256"]
        persist()
        for filename in filenames(config):
            deadline.check()
            verify_freeze(root, config_path)
            started = time.perf_counter()
            tree = MatrixTree.build(SpotTree.build(load_spot(root / filename)))
            if len(tree.player) > config["maximum_tree_nodes"] or recall_violations(
                tree
            ):
                raise ValueError("fresh tree cap/recall failed")
            if 2 * len(tree.player) >= config["total_node_thresholds"][0]:
                raise ValueError("initial expectation exceeds first work threshold")
            uniform_mass = decision_mass(tree, tree.normalize(tree.legal))
            report["diagnostics"].append(
                {
                    "spot": tree.source.spot.name,
                    "nodes": len(tree.player),
                    "information_sets": len(tree.keys),
                    "setup_seconds": time.perf_counter() - started,
                }
            )
            started = time.perf_counter()
            full = full_solver(tree, config["full_tree_backend"])
            for t in config["full_tree_checkpoints"]:
                while full.iteration < t:
                    deadline.check()
                    full.step()
                record(
                    tree,
                    filename,
                    full.average_policy,
                    (full.strategy_sum.sum(axis=1) > 0).astype(np.float64),
                    uniform_mass,
                    {
                        "method": "full_cfr_plus",
                        "seed": None,
                        "iteration": t,
                        "node_threshold": None,
                        "total_node_work": 2 * t * len(tree.player),
                        "seconds": time.perf_counter() - started,
                        "warm_node_equivalent": 0,
                    },
                )
            for seed in config["training_seeds"]:
                started = time.perf_counter()
                solver = PostflopMCCFR(
                    root_factory(tree), Generator(PCG64(seed)), "linear"
                )
                exact_initial_expectation(solver, tree)
                for budget in config["total_node_thresholds"]:
                    advance_to_work(solver, budget, deadline)
                    policy, trained = sampled_average(solver, tree)
                    total = solver.nodes_visited + solver.warm_node_equivalent
                    if not 0 <= total - budget < 2 * len(tree.player):
                        raise ArithmeticError("invalid full-iteration overshoot")
                    checkpoint = (
                        output.parent
                        / "runs"
                        / output.stem
                        / f"{tree.source.spot.name}-{seed}-{budget}.json"
                    )
                    save_learning_checkpoint(
                        solver,
                        checkpoint,
                        config={
                            "learning": {**config, "sampler": "external"},
                            "spot_file": filename,
                            "spot_sha256": freeze["spot_sha256"][filename],
                        },
                        provenance=source,
                    )
                    visited = np.array(
                        [key in solver.sampled_keys for key in tree.keys],
                        dtype=np.float64,
                    )
                    record(
                        tree,
                        filename,
                        policy,
                        trained,
                        uniform_mass,
                        {
                            "method": "external",
                            "seed": seed,
                            "iteration": solver.iteration,
                            "node_threshold": budget,
                            "total_node_work": total,
                            "overshoot": total - budget,
                            "recursive_visits": solver.nodes_visited,
                            "warm_node_equivalent": solver.warm_node_equivalent,
                            "seconds": time.perf_counter() - started,
                            "subsequently_sampled_information_sets": len(
                                solver.sampled_keys
                            ),
                            "initial_only_information_sets": len(
                                set(solver.rows) - solver.sampled_keys
                            ),
                            "uniform_reach_subsequently_sampled_coverage": float(
                                uniform_mass @ visited / uniform_mass.sum()
                            ),
                            "checkpoint_file": str(
                                checkpoint.relative_to(output.parent)
                            ),
                            "checkpoint_sha256": digest(checkpoint),
                            "checkpoint_visits_sha256": digest(
                                checkpoint.with_suffix(".visits.json")
                            ),
                        },
                    )
        deadline.check()
        verify_freeze(root, config_path)
        report["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        report["status"] = (
            "gate_failed" if report["admission"] is None else "incomplete"
        )
        report["failure"] = {"type": type(error).__name__, "reason": str(error)}
    finally:
        persist()
    return report


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ValueError("partial/non-admitted fresh report cannot be accepted")
    if (
        report["admission"]["status"] != "passed"
        or report["acceptance"] != acceptance(report["rows"], report["config"])
        or not report["acceptance"]["complete"]
    ):
        raise ArithmeticError("admission or complete fresh grid missing/changed")
    policy_path = path.parent / report["own_policies_file"]
    if digest(policy_path) != report["own_policies_sha256"]:
        raise ArithmeticError("fresh own-policy hash mismatch")
    payload = json.loads(gzip.decompress(policy_path.read_bytes()))
    own_ids = {tuple(r[k] for k in IDENTITY) for r in report["rows"]}
    ids = {tuple(r[k] for k in IDENTITY) for r in payload["policies"]}
    if (
        payload["format"] != POLICY_FORMAT
        or ids != own_ids
        or len(ids) != len(payload["policies"])
    ):
        raise ArithmeticError("missing/duplicate fresh own policy")
    return report, payload["policies"]
