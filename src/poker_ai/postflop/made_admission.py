"""Bounded full-control admission for ONE prospective made-category candidate."""

import gzip
import json
import math
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.made_category import MadeCategoryAbstraction
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import decision_mass, full_solver, score
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.public_metrics import collision_summary
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-made-category-admission-v1"
POLICY_FORMAT = "poker-ai-made-category-own-policies-v1"
REPRESENTATIONS = ["exact", "public_b8", "texture_b8", "texture_made_b8"]
IDENTITY = ("spot_file", "representation", "iteration")
ENTRYPOINTS = (
    "scripts/admit_made_category.py",
    "scripts/audit_made_category.py",
    "scripts/report_made_category.py",
)


def build_representation(
    source: SpotTree, name: str, model: CardAbstraction
) -> MatrixTree:
    if name == "exact":
        return MatrixTree.build(source)
    if name == "public_b8":
        return MatrixTree.build(source, "public_b8", model)
    if name == "texture_b8":
        return MatrixTree.build(source, "texture_b8", model)
    if name == "texture_made_b8":
        richer = MadeCategoryAbstraction(model.models, model.config)
        return MatrixTree.build(source, "texture_b8", richer)
    raise ValueError("unknown made-category admission representation")


def validate_config(config: dict[str, Any]) -> None:
    if (
        config["schema_version"] != 1
        or config["stage"] != "full_control_admission"
        or config["candidate"] != "texture_made_b8"
        or config["representations"] != REPRESENTATIONS
        or config["full_tree_backend"] not in ("fused_numba", "numpy")
        or not config["spot_files"]
        or len(set(config["spot_files"])) != len(config["spot_files"])
        or config["later_sampled_comparison"]["status"] != "not_run_in_this_block"
    ):
        raise ValueError("invalid fixed made-category admission design")
    checkpoints = config["full_tree_checkpoints"]
    if (
        not checkpoints
        or checkpoints != sorted(set(checkpoints))
        or any(type(v) is not int or v < 1 for v in checkpoints)
        or not math.isfinite(config["maximum_seconds"])
        or config["maximum_seconds"] <= 0
        or type(config["maximum_tree_nodes"]) is not int
        or config["maximum_tree_nodes"] < 1
    ):
        raise ValueError("invalid admission checkpoints/budget")
    limits = config["limits"]
    if (
        set(limits)
        != {
            "exact_full_exploitability_pot",
            "candidate_full_excess_pot",
            "candidate_information_sets_relative_to_public_b8",
            "minimum_uniform_reach_average_coverage",
            "maximum_recall_violations",
            "independent_tolerance_chips",
        }
        or any(not math.isfinite(v) or not 0 <= v <= 1 for v in limits.values())
        or limits["maximum_recall_violations"] != 0
        or not 0 < limits["independent_tolerance_chips"] <= 1e-8
    ):
        raise ValueError("invalid admission limits")


def acceptance(
    rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    ids = [tuple(r[k] for k in IDENTITY) for r in rows]
    expected = {
        (p, e, t)
        for p in config["spot_files"]
        for e in config["representations"]
        for t in config["full_tree_checkpoints"]
    }
    diag_ids = [(r["spot_file"], r["representation"]) for r in diagnostics]
    complete = (
        len(ids) == len(set(ids))
        and set(ids) == expected
        and len(diag_ids) == len(set(diag_ids))
        and set(diag_ids)
        == {(p, e) for p in config["spot_files"] for e in config["representations"]}
    )
    checks = []
    limits = config["limits"]
    for path in config["spot_files"]:
        final = {
            r["representation"]: r
            for r in rows
            if r["spot_file"] == path
            and r["iteration"] == config["full_tree_checkpoints"][-1]
        }
        diag = {r["representation"]: r for r in diagnostics if r["spot_file"] == path}
        if set(final) != set(config["representations"]) or set(diag) != set(
            config["representations"]
        ):
            checks.append(
                {
                    "spot_file": path,
                    "passed": False,
                    "reason": "missing final cells/diagnostics",
                }
            )
            continue
        exact, candidate = final["exact"], final[config["candidate"]]
        excess = (
            candidate["exploitability_pot_fraction"]
            - exact["exploitability_pot_fraction"]
        )
        ratio = (
            diag[config["candidate"]]["information_sets"]
            / diag["public_b8"]["information_sets"]
        )
        criteria = {
            "exact_accuracy": exact["exploitability_pot_fraction"]
            <= limits["exact_full_exploitability_pot"],
            "candidate_full_excess": excess <= limits["candidate_full_excess_pot"],
            "candidate_compression": ratio
            <= limits["candidate_information_sets_relative_to_public_b8"],
            "recall": all(r["recall_violations"] == 0 for r in diag.values()),
            "average_coverage": min(
                r["uniform_reach_average_row_coverage"] for r in final.values()
            )
            >= limits["minimum_uniform_reach_average_coverage"],
        }
        checks.append(
            {
                "spot_file": path,
                "criteria": criteria,
                "passed": bool(all(criteria.values())),
                "candidate_full_excess_pot": excess,
                "candidate_row_ratio": ratio,
            }
        )
    return {
        "complete": complete,
        "own_full_control_gate_passed": complete and all(r["passed"] for r in checks),
        "checks": checks,
        "independent_audit_required": True,
        "sampled_learning": "not_run",
        "fresh_global_admission": False,
    }


def run_admission(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_config(config)
    policy_path = output.with_name(output.stem + "-own-policies.json.gz")
    if output.exists() or policy_path.exists():
        raise FileExistsError("retain previous admission evidence; use a new output")
    if digest(root / config["diagnosis_file"]) != config["diagnosis_sha256"]:
        raise ArithmeticError("declared diagnosis evidence changed")
    source = source_provenance(root, config_path, entrypoints=ENTRYPOINTS)
    if source["dirty"] is not False:
        raise ValueError("publish candidate/config first; use a clean worktree")
    deadline = Deadline(config["maximum_seconds"])
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "source": source,
        "config": config,
        "environment": runtime_environment(),
        "started_at_utc": datetime.now(UTC).isoformat(),
        "package_versions": {
            name: version(name)
            for name in (
                ("numpy", "numba")
                if config["full_tree_backend"] == "fused_numba"
                else ("numpy",)
            )
        },
        "model_sha256": digest(root / config["model"]),
        "spot_sha256": {p: digest(root / p) for p in config["spot_files"]},
        "rows": rows,
        "diagnostics": diagnostics,
        "encoder_version": "texture+made-category-history-v1",
        "matrix_encoding_for_candidate": "texture_b8",
        "extra_information_key_version": "made-category-history-v1",
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
        report.update(
            own_policies_file=policy_path.name,
            own_policies_sha256=digest(policy_path),
            seconds=time.perf_counter() - deadline.started,
            peak_process_rss_bytes=peak_rss_bytes(),
            acceptance=acceptance(rows, diagnostics, config),
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
                tree = build_representation(tree_source, name, model)
                diagnostic = {
                    "spot_file": filename,
                    "representation": name,
                    **collision_summary(tree, uniform_mass),
                    "setup_seconds": time.perf_counter() - started,
                }
                diagnostics.append(diagnostic)
                if diagnostic["recall_violations"]:
                    raise ValueError("made-category candidate violates abstract recall")
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
                        **score(exact, tree, policy, active, uniform_mass),
                        "total_node_work": 2 * checkpoint * len(tree.player),
                        "seconds_including_setup": time.perf_counter() - started,
                    }
                    rows.append(row)
                    policies.append(
                        {
                            **{k: row[k] for k in IDENTITY},
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
            raise ArithmeticError("made-category source/config changed")
    config = report["config"]
    if (
        digest(root / config["model"]) != report["model_sha256"]
        or digest(root / config["diagnosis_file"]) != config["diagnosis_sha256"]
    ):
        raise ArithmeticError("made-category model/diagnosis changed")
    if any(digest(root / p) != sha for p, sha in report["spot_sha256"].items()):
        raise ArithmeticError("made-category game changed")


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    validate_config(report["config"])
    json.dumps(report, allow_nan=False)
    expected = acceptance(report["rows"], report["diagnostics"], report["config"])
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ValueError("partial admission cannot be accepted")
    if (
        not expected["complete"]
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
            tree = build_representation(source, name, model)
            diag = collision_summary(tree, weights)
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
    if maximum > report["config"]["limits"]["independent_tolerance_chips"]:
        raise ArithmeticError("admission frozen-policy replay mismatch")
    return report, policies, maximum
