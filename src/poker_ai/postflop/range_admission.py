"""Context-bound full-control admission; no sampled or global learner."""

import gzip
import json
import time
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import decision_mass, full_solver, score
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.public_metrics import collision_summary
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.postflop.range_protocol import (
    CANDIDATE,
    assess_full_metrics,
    build_representation_control,
    check_inputs,
    validate_protocol,
)
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-range-mass-admission-v1"
POLICY_FORMAT = "poker-ai-range-mass-own-policies-v1"
IDENTITY = ("spot_file", "representation", "iteration")
ENTRYPOINTS = (
    "scripts/admit_range_mass.py",
    "scripts/audit_range_mass.py",
    "scripts/report_range_mass.py",
)


def acceptance(
    rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    config: dict[str, Any],
    contexts: dict[str, str],
    elapsed: float,
) -> dict[str, Any]:
    """Record own-only assessment honestly: no synthetic native measurements."""
    result = assess_full_metrics(
        rows, diagnostics, [], config, contexts, elapsed_seconds=elapsed
    )
    expected = {
        (p, e, t)
        for p in config["spot_files"]
        for e in config["representations"]
        for t in config["full_tree_checkpoints"]
    }
    ids = [tuple(r[k] for k in IDENTITY) for r in rows]
    diag_ids = [(d["spot_file"], d["representation"]) for d in diagnostics]
    complete = (
        len(ids) == len(set(ids))
        and set(ids) == expected
        and len(diag_ids) == len(set(diag_ids))
        and set(diag_ids)
        == {(p, e) for p in config["spot_files"] for e in config["representations"]}
    )
    # The pure assessor requires native rows for a complete overall assessment.
    # Keep that False; expose own-grid completeness as a separate fact.
    result.update(own_grid_complete=complete, independent_audit="pending")
    return result


def context_tag(name: str, filename: str, contexts: dict[str, str]) -> dict[str, Any]:
    return {"range_context_sha256": contexts[filename] if name == CANDIDATE else None}


def run_admission(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_protocol(config)
    deadline = Deadline(config["maximum_full_seconds"])
    deadline.started = started
    policy_path = output.with_name(output.stem + "-own-policies.json.gz")
    if output.exists() or policy_path.exists():
        raise FileExistsError("retain previous admission evidence; use a new output")
    contexts = check_inputs(root, config)
    source = source_provenance(root, config_path, entrypoints=ENTRYPOINTS)
    if source["dirty"] is not False:
        raise ValueError("publish candidate/config first; use a clean worktree")
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "source": source,
        "config": config,
        "range_contexts": contexts,
        "environment": runtime_environment(),
        "started_at_utc": datetime.now(UTC).isoformat(),
        "package_versions": package_versions(),
        "model_sha256": digest(root / config["model"]),
        "spot_sha256": {p: digest(root / p) for p in config["spot_files"]},
        "rows": rows,
        "diagnostics": diagnostics,
        "encoder_version": config["feature_version"],
        "matrix_encoding_for_candidate": "texture_b8",
        "extra_information_key_version": config["feature_version"],
        "rss_convention": (
            "process-lifetime high-water; not isolated per-representation cost"
        ),
        "sampled_learning": "not_run",
        "fresh_global_admission": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)

    def persist() -> None:
        policy_path.write_bytes(
            gzip.compress(
                json.dumps(
                    {"format": POLICY_FORMAT, "policies": policies},
                    sort_keys=True,
                    allow_nan=False,
                ).encode(),
                mtime=0,
            )
        )
        elapsed = time.perf_counter() - deadline.started
        report.update(
            own_policies_file=policy_path.name,
            own_policies_sha256=digest(policy_path),
            seconds=elapsed,
            peak_process_rss_bytes=peak_rss_bytes(),
            acceptance=acceptance(rows, diagnostics, config, contexts, elapsed),
        )
        temporary = output.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        temporary.replace(output)

    try:
        persist()
        model = CardAbstraction.load(root / config["model"])
        for filename in config["spot_files"]:
            deadline.check()
            tree_source = SpotTree.build(load_spot(root / filename))
            if len(tree_source.states) > config["maximum_tree_nodes"]:
                raise ValueError("admission tree cap exceeded")
            exact = MatrixTree.build(tree_source)
            uniform_mass = decision_mass(exact, exact.normalize(exact.legal))
            for name in config["representations"]:
                started = time.perf_counter()
                tree = build_representation_control(tree_source, name, model)
                diagnostic = {
                    "spot_file": filename,
                    "representation": name,
                    **context_tag(name, filename, contexts),
                    **collision_summary(tree, uniform_mass),
                    "tree_nodes": len(tree.player),
                    "setup_seconds": time.perf_counter() - started,
                }
                diagnostics.append(diagnostic)
                if diagnostic["recall_violations"]:
                    raise ValueError("range-mass candidate violates abstract recall")
                solver = full_solver(tree, config["full_tree_backend"])
                for checkpoint in config["full_tree_checkpoints"]:
                    while solver.iteration < checkpoint:
                        deadline.check()
                        solver.step()
                    policy = solver.average_policy
                    active = (solver.strategy_sum.sum(axis=1) > 0).astype(np.float64)
                    row = {
                        "spot_file": filename,
                        "representation": name,
                        "iteration": checkpoint,
                        **context_tag(name, filename, contexts),
                        **score(exact, tree, policy, active, uniform_mass),
                        "total_node_work": 2 * checkpoint * len(tree.player),
                        "seconds_including_setup": time.perf_counter() - started,
                    }
                    rows.append(row)
                    policies.append(
                        {
                            **{k: row[k] for k in IDENTITY},
                            **context_tag(name, filename, contexts),
                            "policy": tree.exact_policy(policy),
                            "average_active": active.astype(int).tolist(),
                        }
                    )
                    print(
                        f"admission: {tree_source.spot.name}/{name} t={checkpoint} "
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
    for name, sha in report["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("range-mass source/config changed")
    config = report["config"]
    if check_inputs(root, config) != report["range_contexts"]:
        raise ArithmeticError("range context changed")
    if (
        digest(root / config["model"]) != report["model_sha256"]
        or report["spot_sha256"] != config["spot_sha256"]
    ):
        raise ArithmeticError("range-mass model/game changed")


def package_versions() -> dict[str, str]:
    result = {}
    for name in ("numpy", "numba"):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = "not installed"
    return result


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    validate_protocol(report["config"])
    json.dumps(report, allow_nan=False)
    expected = acceptance(
        report["rows"],
        report["diagnostics"],
        report["config"],
        report["range_contexts"],
        report["seconds"],
    )
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ValueError("partial admission cannot be accepted")
    if (
        not expected["own_grid_complete"]
        or not expected["context_binding"]
        or report["failure"] is not None
        or report["acceptance"] != expected
        or report["sampled_learning"] != "not_run"
        or report["fresh_global_admission"] is not False
    ):
        raise ArithmeticError("changed/missing admission grid or stage claim")
    policy_path = path.parent / report["own_policies_file"]
    if digest(policy_path) != report["own_policies_sha256"]:
        raise ArithmeticError("admission own-policy hash mismatch")
    payload = json.loads(gzip.decompress(policy_path.read_bytes()))
    ids = [tuple(p[k] for k in IDENTITY) for p in payload["policies"]]
    if (
        payload["format"] != POLICY_FORMAT
        or len(ids) != len(set(ids))
        or set(ids) != {tuple(r[k] for k in IDENTITY) for r in report["rows"]}
    ):
        raise ArithmeticError("missing/duplicate admission policy")
    for snapshot in payload["policies"]:
        if (
            snapshot.get("range_context_sha256")
            != context_tag(
                snapshot["representation"],
                snapshot["spot_file"],
                report["range_contexts"],
            )["range_context_sha256"]
        ):
            raise ArithmeticError("own-policy range context changed")
    return report, payload["policies"]


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report, policies = checked_artifacts(path)
    verify_inputs(root, report)
    model = CardAbstraction.load(root / report["config"]["model"])
    lookup = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    maximum = 0.0
    for filename in report["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        weights = decision_mass(exact, exact.normalize(exact.legal))
        for name in report["config"]["representations"]:
            tree = build_representation_control(source, name, model)
            diag = {**collision_summary(tree, weights), "tree_nodes": len(tree.player)}
            recorded = next(
                d
                for d in report["diagnostics"]
                if d["spot_file"] == filename and d["representation"] == name
            )
            if any(diag[k] != recorded[k] for k in diag):
                raise ArithmeticError("admission diagnostics changed")
            first = np.unique(tree.exact_to_abstract, return_index=True)[1]
            for snapshot in policies:
                if (
                    snapshot["spot_file"] != filename
                    or snapshot["representation"] != name
                ):
                    continue
                row = lookup[tuple(snapshot[k] for k in IDENTITY)]
                dense = exact.dense_exact(
                    tuple(tuple(v for v in r) for r in snapshot["policy"])
                )
                policy = dense[first]
                if not np.array_equal(
                    exact.dense_exact(tree.exact_policy(policy)), dense
                ):
                    raise ArithmeticError("admission policy violates shared rows")
                active = np.asarray(snapshot["average_active"], dtype=np.float64)
                if active.shape != (len(tree.keys),) or not np.all(
                    np.isin(active, (0, 1))
                ):
                    raise ArithmeticError("admission active-row mask invalid")
                actual = score(exact, tree, policy, active, weights)
                maximum = max(maximum, *[abs(actual[k] - row[k]) for k in actual])
                if row["total_node_work"] != 2 * row["iteration"] * len(tree.player):
                    raise ArithmeticError("admission work receipt invalid")
    if maximum > report["config"]["full_limits"]["independent_tolerance_chips"]:
        raise ArithmeticError("admission frozen-policy replay mismatch")
    verify_inputs(root, report)
    return report, policies, maximum
