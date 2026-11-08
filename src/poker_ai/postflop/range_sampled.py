"""Fixed-work own sampled learning with context-bound frozen checkpoint receipts."""

import gzip
import hashlib
import json
import math
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import (
    decision_mass,
    root_factory,
    sampled_average,
    score,
)
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.public_metrics import collision_summary
from poker_ai.postflop.public_study import peak_rss_bytes, profile
from poker_ai.postflop.range_admission import context_tag, package_versions
from poker_ai.postflop.range_admission import replay as full_replay
from poker_ai.postflop.range_admission import verify_inputs as verify_full_inputs
from poker_ai.postflop.range_admission_report import checked_audit
from poker_ai.postflop.range_protocol import (
    assess_full_metrics,
    assess_sampled_metrics,
    build_representation_control,
    check_inputs,
    validate_protocol,
)
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    exact_initial_expectation,
    load_learning_checkpoint,
    save_learning_checkpoint,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-range-mass-sampled-v1"
POLICY_FORMAT = "poker-ai-range-mass-sampled-own-receipts-v1"
IDENTITY = ("spot_file", "representation", "seed", "node_work_checkpoint")
ENTRYPOINTS = (
    "scripts/study_range_mass.py",
    "scripts/audit_range_sampled.py",
    "scripts/report_range_sampled.py",
)
FULL_STUDY = "results/range-mass-admission/study.json"
FULL_AUDIT = "results/range-mass-admission/independent.json"


def prerequisite(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Replay the prior gate; no frozen policy/reference value enters a learner."""
    report, _, own_error = full_replay(root, root / FULL_STUDY)
    audit = json.loads((root / FULL_AUDIT).read_text())
    native_error = checked_audit(root / FULL_STUDY, report, audit)
    if report["config"] != config or audit["reference"] != {
        "name": "OpenSpiel",
        "version": "2.0.2",
        "license": "Apache-2.0",
    }:
        raise ArithmeticError("full-stage config/reference changed")
    for name, sha in audit["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("full-stage native source changed")
    assessment = assess_full_metrics(
        report["rows"],
        report["diagnostics"],
        audit["comparisons"],
        config,
        check_inputs(root, config),
        elapsed_seconds=report["seconds"],
    )
    if assessment["eligible_for_sampled_comparison"] is not True:
        raise ArithmeticError("full-control prerequisite did not pass")
    return {
        "study_sha256": digest(root / FULL_STUDY),
        "audit_sha256": digest(root / FULL_AUDIT),
        "assessment": assessment,
        "maximum_own_replay_error_chips": own_error,
        "maximum_native_error_chips": native_error,
    }


def expected_grid(config: dict[str, Any]) -> set[tuple[Any, ...]]:
    later = config["later_sampled"]
    return {
        (p, e, s, w)
        for p in config["spot_files"]
        for e in config["representations"]
        for s in later["seeds"]
        for w in later["node_work_checkpoints"]
    }


def assessment(report: dict[str, Any]) -> dict[str, Any]:
    result = assess_sampled_metrics(
        report["rows"],
        [],
        report["full_prerequisite"]["assessment"],
        report["config"],
        report["range_contexts"],
        elapsed_seconds=report["seconds"],
    )
    ids = [tuple(r[k] for k in IDENTITY) for r in report["rows"]]
    result.update(
        own_grid_complete=len(ids) == len(set(ids))
        and set(ids) == expected_grid(report["config"]),
        independent_audit="pending",
    )
    return result


def checkpoint_config(
    report: dict[str, Any], filename: str, name: str
) -> dict[str, Any]:
    return {
        "learning": {
            "sampler": "external",
            "sampling_weighting": "linear",
            "protocol": report["config"],
            "representation": name,
        },
        "spot_file": filename,
        "spot_sha256": report["spot_sha256"][filename],
        **context_tag(name, filename, report["range_contexts"]),
    }


def advance(
    solver: PostflopMCCFR, threshold: int, deadline: Deadline
) -> tuple[int, int]:
    """Return actual work before and inside the first whole iteration crossing W."""
    previous, last = 0, 0
    while solver.nodes_visited + solver.warm_node_equivalent < threshold:
        deadline.check()
        previous = solver.nodes_visited + solver.warm_node_equivalent
        solver.step()
        last = solver.nodes_visited + solver.warm_node_equivalent - previous
    deadline.check()
    if not last:
        raise ArithmeticError("work checkpoint did not require a new whole iteration")
    return previous, last


def run_study(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_protocol(config)
    deadline = Deadline(config["later_sampled"]["maximum_seconds"])
    deadline.started = started
    bundle = output.with_name(output.stem + "-own-receipts.json.gz")
    checkpoints = output.parent / "runs" / output.stem
    if output.exists() or bundle.exists() or checkpoints.exists():
        raise FileExistsError("retain existing study and receipts; choose a new output")
    source = source_provenance(root, config_path, entrypoints=ENTRYPOINTS)
    if source["dirty"] is not False:
        raise ValueError("publish checked code first; use a clean worktree")
    contexts = check_inputs(root, config)
    report: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "source": source,
        "config": config,
        "range_contexts": contexts,
        "model_sha256": config["model_sha256"],
        "spot_sha256": config["spot_sha256"],
        "environment": runtime_environment(),
        "package_versions": package_versions(),
        "started_at_utc": datetime.now(UTC).isoformat(),
        "rows": [],
        "diagnostics": [],
        "seconds": 0.0,
        "full_prerequisite": prerequisite(root, config),
        "fresh_global_admission": False,
        "scope": "known-game fixed-work development; no fresh/global/default change",
        "rss_convention": "process-lifetime high-water; not per-representation cost",
    }
    snapshots: list[dict[str, Any]] = []
    output.parent.mkdir(parents=True, exist_ok=True)

    def persist() -> None:
        encoded = gzip.compress(
            json.dumps(
                {"format": POLICY_FORMAT, "policies": snapshots},
                sort_keys=True,
                allow_nan=False,
            ).encode(),
            mtime=0,
        )
        temporary_bundle = bundle.with_suffix(".tmp")
        temporary_bundle.write_bytes(encoded)
        temporary_bundle.replace(bundle)
        report.update(
            own_receipts_file=bundle.name,
            own_receipts_sha256=digest(bundle),
            seconds=time.perf_counter() - started,
            peak_process_rss_bytes=peak_rss_bytes(),
        )
        report["assessment"] = assessment(report)
        temporary = output.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        temporary.replace(output)

    try:
        persist()
        later = config["later_sampled"]
        model = CardAbstraction.load(root / config["model"])
        for filename in config["spot_files"]:
            deadline.check()
            source_tree = SpotTree.build(load_spot(root / filename))
            if len(source_tree.states) > config["maximum_tree_nodes"]:
                raise ValueError("declared tree-node cap exceeded")
            exact = MatrixTree.build(source_tree)
            uniform = decision_mass(exact, exact.normalize(exact.legal))
            if 2 * len(exact.player) >= later["node_work_checkpoints"][0]:
                raise ValueError(
                    "exact initialization must fit below first work budget"
                )
            for name in config["representations"]:
                setup = time.perf_counter()
                tree = build_representation_control(source_tree, name, model)
                diag = {
                    "spot_file": filename,
                    "representation": name,
                    **context_tag(name, filename, contexts),
                    **collision_summary(tree, uniform),
                    "tree_nodes": len(tree.player),
                    "setup_seconds": time.perf_counter() - setup,
                }
                report["diagnostics"].append(diag)
                if diag["recall_violations"]:
                    raise ArithmeticError("abstract recall violation")
                diag["profiles"] = profile(tree, later, deadline)
                persist()
                for seed in later["seeds"]:
                    cell_started = time.perf_counter()
                    solver = PostflopMCCFR(
                        root_factory(tree), Generator(PCG64(seed)), "linear"
                    )
                    exact_initial_expectation(solver, tree)
                    for threshold in later["node_work_checkpoints"]:
                        previous, last = advance(solver, threshold, deadline)
                        total = solver.nodes_visited + solver.warm_node_equivalent
                        if not (
                            0 < last <= 2 * len(tree.player)
                            and 0 <= total - threshold < last
                        ):
                            raise ArithmeticError("invalid whole-iteration overshoot")
                        cp = (
                            checkpoints
                            / f"{source_tree.spot.name}-{name}-{seed}-{threshold}.json"
                        )
                        save_learning_checkpoint(
                            solver,
                            cp,
                            config=checkpoint_config(report, filename, name),
                            provenance=source,
                        )
                        policy, active = sampled_average(solver, tree)
                        visited = np.array(
                            [k in solver.sampled_keys for k in tree.keys], dtype=float
                        )
                        deployed = exact.dense_exact(tree.exact_policy(policy))
                        own_mass = decision_mass(exact, deployed)
                        row = {
                            "spot_file": filename,
                            "representation": name,
                            "seed": seed,
                            "node_work_checkpoint": threshold,
                            **context_tag(name, filename, contexts),
                            "iteration": solver.iteration,
                            "sampling": "ordinary_external",
                            "weighting": solver.weighting,
                            "initial_exact_expectation": True,
                            "initialization_node_work": solver.warm_node_equivalent,
                            "recursive_node_visits": solver.nodes_visited,
                            "total_node_work": total,
                            "previous_node_work": previous,
                            "last_iteration_node_work": last,
                            "overshoot": total - threshold,
                            "recall_violations": diag["recall_violations"],
                            **score(exact, tree, policy, active, uniform),
                            "uniform_reach_subsequently_sampled_coverage": float(
                                uniform
                                @ visited[tree.exact_to_abstract]
                                / uniform.sum()
                            ),
                            "own_reach_subsequently_sampled_coverage": float(
                                own_mass
                                @ visited[tree.exact_to_abstract]
                                / own_mass.sum()
                            ),
                            "subsequently_sampled_information_sets": len(
                                solver.sampled_keys
                            ),
                            "initial_only_information_sets": len(solver.rows)
                            - len(solver.sampled_keys),
                            "sampled_regret_average_bytes": sum(
                                r.regrets.nbytes + r.strategy_sum.nbytes
                                for r in solver.rows.values()
                            ),
                            "checkpoint_sha256": digest(cp),
                            "visits_sha256": digest(cp.with_suffix(".visits.json")),
                            "seconds_including_initialization": time.perf_counter()
                            - cell_started,
                        }
                        report["rows"].append(row)
                        snapshots.append(
                            {
                                **{k: row[k] for k in IDENTITY},
                                **context_tag(name, filename, contexts),
                                "policy": tree.exact_policy(policy),
                                "average_active": active.astype(int).tolist(),
                                "sampled": visited.astype(int).tolist(),
                                "checkpoint_json": cp.read_text(),
                                "visits_json": cp.with_suffix(
                                    ".visits.json"
                                ).read_text(),
                            }
                        )
                        print(
                            f"range sampled: {source_tree.spot.name}/{name}/{seed} "
                            f"work={total} "
                            f"epsilon/pot={row['exploitability_pot_fraction']:.7g}",
                            flush=True,
                        )
                        persist()
        deadline.check()
        verify_inputs(root, report)
        report["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        report["status"] = "incomplete"
        report["failure"] = {"type": type(error).__name__, "reason": str(error)}
    finally:
        persist()
    return report


def verify_inputs(root: Path, report: dict[str, Any]) -> None:
    verify_full_inputs(root, report)
    saved = report["full_prerequisite"]
    if (
        digest(root / FULL_STUDY) != saved["study_sha256"]
        or digest(root / FULL_AUDIT) != saved["audit_sha256"]
    ):
        raise ArithmeticError("full-control prerequisite changed")


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    json.dumps(report, allow_nan=False)
    expected = assessment(report)
    if (
        report["format"] != FORMAT
        or report["status"] != "completed"
        or report["failure"] is not None
        or report["fresh_global_admission"] is not False
        or report["assessment"] != expected
        or not expected["own_grid_complete"]
        or not expected["context_binding"]
    ):
        raise ArithmeticError("partial/changed sampled grid or stage claim")
    bundle = path.parent / report["own_receipts_file"]
    if digest(bundle) != report["own_receipts_sha256"]:
        raise ArithmeticError("own receipt bundle hash changed")
    payload = json.loads(gzip.decompress(bundle.read_bytes()))
    json.dumps(payload, allow_nan=False)
    ids = [tuple(r[k] for k in IDENTITY) for r in payload["policies"]]
    if (
        payload["format"] != POLICY_FORMAT
        or len(ids) != len(set(ids))
        or set(ids) != expected_grid(report["config"])
    ):
        raise ArithmeticError("missing/duplicate own receipts")
    diag_ids = [(d["spot_file"], d["representation"]) for d in report["diagnostics"]]
    if len(diag_ids) != len(set(diag_ids)) or set(diag_ids) != {
        (p, e)
        for p in report["config"]["spot_files"]
        for e in report["config"]["representations"]
    }:
        raise ArithmeticError("missing/duplicate partition diagnostics")
    return report, payload["policies"]


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report, snapshots = checked_artifacts(path)
    verify_inputs(root, report)
    config = report["config"]
    if prerequisite(root, config) != report["full_prerequisite"]:
        raise ArithmeticError("full-control assessment changed")
    model = CardAbstraction.load(root / config["model"])
    lookup = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    maximum = 0.0
    for filename in config["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        uniform = decision_mass(exact, exact.normalize(exact.legal))
        for name in config["representations"]:
            tree = build_representation_control(source, name, model)
            diag = next(
                d
                for d in report["diagnostics"]
                if (d["spot_file"], d["representation"]) == (filename, name)
            )
            actual_diag = {
                **collision_summary(tree, uniform),
                "tree_nodes": len(tree.player),
                **context_tag(name, filename, report["range_contexts"]),
            }
            if any(diag[k] != v for k, v in actual_diag.items()):
                raise ArithmeticError("partition/context diagnostics changed")
            profiles = diag["profiles"]
            later = config["later_sampled"]
            if (
                sorted(p["repeat"] for p in profiles)
                != list(range(later["profile_repetitions"]))
                or any(
                    p["seed"] != later["seeds"][0]
                    or p["sampled_iterations"] != later["profile_iterations"]
                    or type(p["total_node_work"]) is not int
                    or p["total_node_work"] <= 2 * len(tree.player)
                    or not math.isfinite(p["seconds_including_initialization"])
                    or p["seconds_including_initialization"] < 0
                    for p in profiles
                )
                or len({p["total_node_work"] for p in profiles}) != 1
            ):
                raise ArithmeticError("profile repetitions/work/seed changed")
            for snapshot in snapshots:
                if (snapshot["spot_file"], snapshot["representation"]) != (
                    filename,
                    name,
                ):
                    continue
                row = lookup[tuple(snapshot[k] for k in IDENTITY)]
                if any(
                    type(snapshot[k]) is not int
                    for k in ("seed", "node_work_checkpoint")
                ) or snapshot.get("range_context_sha256") != row.get(
                    "range_context_sha256"
                ):
                    raise ArithmeticError("checkpoint identity/context changed")
                for field, sha in (
                    ("checkpoint_json", "checkpoint_sha256"),
                    ("visits_json", "visits_sha256"),
                ):
                    if hashlib.sha256(snapshot[field].encode()).hexdigest() != row[sha]:
                        raise ArithmeticError("checkpoint/visit receipt hash changed")
                with tempfile.TemporaryDirectory() as temporary:
                    cp = Path(temporary) / "checkpoint.json"
                    cp.write_text(snapshot["checkpoint_json"])
                    cp.with_suffix(".visits.json").write_text(snapshot["visits_json"])
                    solver = load_learning_checkpoint(
                        cp,
                        root_factory(tree),
                        expected_config=checkpoint_config(report, filename, name),
                    )
                core = json.loads(snapshot["checkpoint_json"])
                if (
                    core["source"] != report["source"]
                    or set(solver.rows) != set(tree.keys)
                    or solver.iteration != row["iteration"]
                    or type(row["iteration"]) is not int
                    or solver.warm_node_equivalent != 2 * len(tree.player)
                    or solver.warm_node_equivalent != row["initialization_node_work"]
                    or solver.nodes_visited != row["recursive_node_visits"]
                    or solver.nodes_visited + solver.warm_node_equivalent
                    != row["total_node_work"]
                    or not 0 < row["last_iteration_node_work"] <= 2 * len(tree.player)
                    or row["overshoot"]
                    != row["total_node_work"] - row["node_work_checkpoint"]
                    or not 0 <= row["overshoot"] < row["last_iteration_node_work"]
                    or row["previous_node_work"] + row["last_iteration_node_work"]
                    != row["total_node_work"]
                    or solver.weighting != row["weighting"]
                    or row["sampling"] != "ordinary_external"
                    or row["initial_exact_expectation"] is not True
                    or type(row["recall_violations"]) is not int
                    or row["recall_violations"] != diag["recall_violations"]
                ):
                    raise ArithmeticError(
                        "checkpoint work/source/method receipt changed"
                    )
                policy, active = sampled_average(solver, tree)
                visited = np.array(
                    [k in solver.sampled_keys for k in tree.keys], dtype=float
                )
                if not np.array_equal(
                    exact.dense_exact(tuple(tuple(r) for r in snapshot["policy"])),
                    exact.dense_exact(tree.exact_policy(policy)),
                ):
                    raise ArithmeticError(
                        "frozen policy differs from checkpoint accumulators"
                    )
                if not np.array_equal(
                    active, snapshot["average_active"]
                ) or not np.array_equal(visited, snapshot["sampled"]):
                    raise ArithmeticError("average/visit mask differs from checkpoint")
                deployed = exact.dense_exact(tree.exact_policy(policy))
                own_mass = decision_mass(exact, deployed)
                actual = {
                    **score(exact, tree, policy, active, uniform),
                    "uniform_reach_subsequently_sampled_coverage": float(
                        uniform @ visited[tree.exact_to_abstract] / uniform.sum()
                    ),
                    "own_reach_subsequently_sampled_coverage": float(
                        own_mass @ visited[tree.exact_to_abstract] / own_mass.sum()
                    ),
                    "subsequently_sampled_information_sets": len(solver.sampled_keys),
                    "initial_only_information_sets": len(solver.rows)
                    - len(solver.sampled_keys),
                    "sampled_regret_average_bytes": sum(
                        r.regrets.nbytes + r.strategy_sum.nbytes
                        for r in solver.rows.values()
                    ),
                }
                maximum = max(maximum, *[abs(v - row[k]) for k, v in actual.items()])
    if maximum > config["full_limits"]["independent_tolerance_chips"]:
        raise ArithmeticError("sampled checkpoint/policy metric replay changed")
    verify_inputs(root, report)
    return report, snapshots, maximum
