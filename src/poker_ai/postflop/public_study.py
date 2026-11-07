"""Own fixed-work public-board study; retain complete grids and negative results."""

import gzip
import json
import resource
import sys
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import (
    decision_mass,
    full_solver,
    root_factory,
    sampled_average,
    score,
)
from poker_ai.postflop.matrix import Encoding, MatrixTree
from poker_ai.postflop.public_metrics import (
    IDENTITY,
    acceptance,
    collision_summary,
    validate_config,
)
from poker_ai.postflop.river_study import Deadline, advance_to_work, digest
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    exact_initial_expectation,
    save_learning_checkpoint,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-public-board-study-v1"
POLICY_FORMAT = "poker-ai-public-board-own-policies-v1"
ENTRYPOINTS = (
    "scripts/study_public_boards.py",
    "scripts/audit_public_boards.py",
    "scripts/report_public_boards.py",
)


def peak_rss_bytes() -> int:
    """Process-lifetime high-water RSS, NOT a per-cell incremental memory cost."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def verify_inputs(root: Path, report: dict[str, Any]) -> None:
    """Bind offline replay to original source, config, model and game inputs."""
    for name, sha in report["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("public-board source/config identity mismatch")
    if digest(root / report["config"]["model"]) != report["model_sha256"]:
        raise ArithmeticError("public-board model identity mismatch")
    if any(digest(root / p) != sha for p, sha in report["spot_sha256"].items()):
        raise ArithmeticError("public-board game identity mismatch")


def profile(
    tree: MatrixTree, config: dict[str, Any], deadline: Deadline
) -> list[dict[str, Any]]:
    """Repeat the same fixed-seed traversal; fresh solvers never feed study runs."""
    rows = []
    for repeat in range(config["profile_repetitions"]):
        started = time.perf_counter()
        solver = PostflopMCCFR(
            root_factory(tree), Generator(PCG64(config["seeds"][0])), "linear"
        )
        exact_initial_expectation(solver, tree)
        for _ in range(config["profile_iterations"]):
            deadline.check()
            solver.step()
        rows.append(
            {
                "repeat": repeat,
                "seed": config["seeds"][0],
                "sampled_iterations": config["profile_iterations"],
                "total_node_work": solver.nodes_visited + solver.warm_node_equivalent,
                "seconds_including_initialization": time.perf_counter() - started,
                "peak_process_rss_bytes": peak_rss_bytes(),
            }
        )
    return rows


def run_study(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_config(config)
    policy_path = output.with_name(output.stem + "-own-policies.json.gz")
    checkpoint_dir = output.parent / "runs" / output.stem
    if output.exists() or policy_path.exists() or checkpoint_dir.exists():
        raise FileExistsError(
            "retain existing study/policies/checkpoints; use a new output"
        )
    source = source_provenance(root, config_path, entrypoints=ENTRYPOINTS)
    if source["dirty"] is not False:
        raise ValueError("publish checked code/config first; run from a clean worktree")
    deadline = Deadline(config["maximum_seconds"])
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "package_versions": {
            k: version(k)
            for k in (
                ("numpy", "numba")
                if config["full_tree_backend"] == "fused_numba"
                else ("numpy",)
            )
        },
        "model_sha256": digest(root / config["model"]),
        "spot_sha256": {p: digest(root / p) for p in config["development_spots"]},
        "rows": rows,
        "diagnostics": diagnostics,
        "scope": "known bounded development games; no fresh/global upgrade claim",
        "rss_convention": (
            "process-lifetime high-water mark; cumulative, not per-cell cost"
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
            peak_process_rss_bytes=peak_rss_bytes(),
            own_policies_file=policy_path.name,
            own_policies_sha256=digest(policy_path),
            acceptance=acceptance(rows, diagnostics, config),
        )
        temporary = output.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        temporary.replace(output)

    def record(
        exact: MatrixTree,
        tree: MatrixTree,
        filename: str,
        policy: FloatArray,
        active: FloatArray,
        uniform_mass: FloatArray,
        fields: dict[str, Any],
        visited: FloatArray | None = None,
    ) -> None:
        row = {
            "spot": tree.source.spot.name,
            "spot_file": filename,
            "encoding": tree.encoding,
            **fields,
            **score(exact, tree, policy, active, uniform_mass),
            "peak_process_rss_bytes": peak_rss_bytes(),
        }
        if visited is not None:
            deployed = exact.dense_exact(tree.exact_policy(policy))
            own_mass = decision_mass(exact, deployed)
            row.update(
                uniform_reach_subsequently_sampled_coverage=float(
                    uniform_mass @ visited[tree.exact_to_abstract] / uniform_mass.sum()
                ),
                own_reach_subsequently_sampled_coverage=float(
                    own_mass @ visited[tree.exact_to_abstract] / own_mass.sum()
                ),
            )
        rows.append(row)
        snapshots.append(
            {
                **{k: row[k] for k in IDENTITY},
                "policy": tree.exact_policy(policy),
                "average_active": active.astype(int).tolist(),
                "sampled": None if visited is None else visited.astype(int).tolist(),
            }
        )
        print(
            f"public-board: {row['spot']}/{tree.encoding}/"
            f"{row['method']}/{row['seed']} "
            f"work={row['total_node_work']} t={row['iteration']} "
            f"eps/pot={row['exploitability_pot_fraction']:.7g}",
            flush=True,
        )
        persist()

    try:
        persist()
        model = CardAbstraction.load(root / config["model"])
        names: set[str] = set()
        for filename in config["development_spots"]:
            deadline.check()
            started = time.perf_counter()
            spot = load_spot(root / filename)
            if spot.name in names or len(spot.board) != 4:
                raise ValueError("duplicate game name or unsupported starting street")
            names.add(spot.name)
            source_tree = SpotTree.build(spot)
            if len(source_tree.states) > config["maximum_nodes_per_game"]:
                raise ValueError("declared tree cap exceeded")
            exact = MatrixTree.build(source_tree)
            uniform_mass = decision_mass(exact, exact.normalize(exact.legal))
            setup_seconds = time.perf_counter() - started
            if 2 * len(exact.player) >= config["sampled_node_checkpoints"][0]:
                raise ValueError("initialization must fit below first work checkpoint")
            for encoding in config["encodings"]:
                started = time.perf_counter()
                tree = (
                    exact
                    if encoding == "exact"
                    else MatrixTree.build(source_tree, cast(Encoding, encoding), model)
                )
                diagnostic = {
                    "spot": spot.name,
                    "spot_file": filename,
                    "encoding": encoding,
                    **collision_summary(tree, uniform_mass),
                    "shared_exact_setup_seconds": setup_seconds,
                    "representation_seconds": time.perf_counter() - started,
                }
                diagnostics.append(diagnostic)
                if diagnostic["recall_violations"]:
                    raise ValueError("representation violates abstract perfect recall")
                diagnostic["profiles"] = profile(tree, config, deadline)
                print(
                    f"profile: {spot.name}/{encoding}; "
                    f"{config['profile_repetitions']} repeats",
                    flush=True,
                )
                persist()
                started = time.perf_counter()
                full = full_solver(tree, config["full_tree_backend"])
                for checkpoint in config["full_tree_checkpoints"]:
                    while full.iteration < checkpoint:
                        deadline.check()
                        full.step()
                    record(
                        exact,
                        tree,
                        filename,
                        full.average_policy,
                        (full.strategy_sum.sum(axis=1) > 0).astype(np.float64),
                        uniform_mass,
                        {
                            "method": "full_cfr_plus",
                            "seed": None,
                            "iteration": checkpoint,
                            "node_threshold": None,
                            "warm_node_equivalent": 0,
                            "total_node_work": 2 * checkpoint * len(tree.player),
                            "seconds": time.perf_counter() - started,
                        },
                    )
                for seed in config["seeds"]:
                    started = time.perf_counter()
                    solver = PostflopMCCFR(
                        root_factory(tree), Generator(PCG64(seed)), "linear"
                    )
                    exact_initial_expectation(solver, tree)
                    for threshold in config["sampled_node_checkpoints"]:
                        advance_to_work(solver, threshold, deadline)
                        total = solver.nodes_visited + solver.warm_node_equivalent
                        if not 0 <= total - threshold < 2 * len(tree.player):
                            raise ArithmeticError(
                                "invalid full-iteration work overshoot"
                            )
                        checkpoint_path = (
                            checkpoint_dir
                            / f"{spot.name}-{encoding}-{seed}-{threshold}.json"
                        )
                        save_learning_checkpoint(
                            solver,
                            checkpoint_path,
                            config={
                                "learning": {
                                    **config,
                                    "sampler": "external",
                                    "encoding": encoding,
                                },
                                "spot_file": filename,
                                "spot_sha256": report["spot_sha256"][filename],
                            },
                            provenance=source,
                        )
                        visited = np.array(
                            [k in solver.sampled_keys for k in tree.keys],
                            dtype=np.float64,
                        )
                        policy, active = sampled_average(solver, tree)
                        record(
                            exact,
                            tree,
                            filename,
                            policy,
                            active,
                            uniform_mass,
                            {
                                "method": "external",
                                "seed": seed,
                                "iteration": solver.iteration,
                                "node_threshold": threshold,
                                "total_node_work": total,
                                "warm_node_equivalent": solver.warm_node_equivalent,
                                "recursive_visits": solver.nodes_visited,
                                "overshoot": total - threshold,
                                "seconds": time.perf_counter() - started,
                                "sampled_regret_average_bytes": sum(
                                    r.regrets.nbytes + r.strategy_sum.nbytes
                                    for r in solver.rows.values()
                                ),
                                "subsequently_sampled_information_sets": len(
                                    solver.sampled_keys
                                ),
                                "initial_only_information_sets": len(solver.rows)
                                - len(solver.sampled_keys),
                                "checkpoint_file": str(
                                    checkpoint_path.relative_to(output.parent)
                                ),
                                "checkpoint_sha256": digest(checkpoint_path),
                                "checkpoint_visits_sha256": digest(
                                    checkpoint_path.with_suffix(".visits.json")
                                ),
                            },
                            visited,
                        )
        deadline.check()
        verify_inputs(root, report)
        report["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        report["status"] = "incomplete"
        report["failure"] = {"type": type(error).__name__, "reason": str(error)}
    finally:
        persist()
    return report


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    validate_config(report["config"])
    json.dumps(report, allow_nan=False)
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ValueError("partial public-board study cannot be accepted")
    expected = acceptance(report["rows"], report["diagnostics"], report["config"])
    if report["acceptance"] != expected or not expected["complete"]:
        raise ArithmeticError("missing/duplicate or changed public-board grid/gate")
    for diagnostic in report["diagnostics"]:
        profiles = diagnostic["profiles"]
        if sorted(p["repeat"] for p in profiles) != list(
            range(report["config"]["profile_repetitions"])
        ):
            raise ArithmeticError("missing/duplicate profile repetitions")
        if any(
            p["sampled_iterations"] != report["config"]["profile_iterations"]
            or p["seed"] != report["config"]["seeds"][0]
            for p in profiles
        ):
            raise ArithmeticError("changed profile budget/seed")
    policy_path = path.parent / report["own_policies_file"]
    if digest(policy_path) != report["own_policies_sha256"]:
        raise ArithmeticError("public-board own-policy hash mismatch")
    payload = json.loads(gzip.decompress(policy_path.read_bytes()))
    json.dumps(payload, allow_nan=False)
    ids = [tuple(p[k] for k in IDENTITY) for p in payload["policies"]]
    row_ids = {tuple(r[k] for k in IDENTITY) for r in report["rows"]}
    if (
        payload["format"] != POLICY_FORMAT
        or len(ids) != len(set(ids))
        or set(ids) != row_ids
    ):
        raise ArithmeticError("missing/duplicate frozen public-board policies")
    return report, cast(list[dict[str, Any]], payload["policies"])
