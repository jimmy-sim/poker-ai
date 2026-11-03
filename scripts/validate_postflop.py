"""Reproduce five restricted postflop comparisons and preregistered ablations."""

import argparse
import csv
import gzip
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.solver_validation.comparison import (
    compare,
    compile_agent,
    information_reach,
    prepare_contexts,
    weighted_gap,
)
from poker_ai.solver_validation.controls import verify_card_worlds
from poker_ai.solver_validation.reference import Reference, SpotTree
from poker_ai.solver_validation.reporting import markdown_table, plot, primary_summary
from poker_ai.solver_validation.spots import load_spot
from poker_ai.validation.five_card import source_provenance


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compressed_json(path: Path, value: object) -> None:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    path.write_bytes(gzip.compress(payload.encode(), mtime=0))


def load_config(path: Path) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(path.read_text())
    required = {
        "schema_version",
        "spot_files",
        "reference",
        "agent_training_config",
        "primary_buckets",
        "primary_iteration",
        "agent_seeds",
        "mapping_episode_seed",
        "reach_weights",
        "action_gap",
        "ev_units",
        "numerical_tolerance",
        "primary_projection_mass_limit",
        "heatmap_spot",
        "max_total_tree_nodes",
        "limitations",
    }
    if (
        set(raw) != required
        or type(raw["schema_version"]) is not int
        or raw["schema_version"] != 1
    ):
        raise ValueError("invalid postflop comparison config")
    ref = raw["reference"]
    if set(ref) != {
        "package",
        "version",
        "algorithm",
        "iteration_schedule",
        "target_exploitability_pot_fraction",
        "required_consecutive_converged",
    }:
        raise ValueError("invalid reference settings")
    if (ref["package"], ref["version"], ref["algorithm"]) != (
        "open_spiel",
        "2.0.2",
        "native CFRPlusSolver",
    ) or importlib.metadata.version("open_spiel") != ref["version"]:
        raise ValueError("requires the audited OpenSpiel version/algorithm")
    schedule = ref["iteration_schedule"]
    if (
        not schedule
        or schedule != sorted(set(schedule))
        or any(type(t) is not int or t < 1 for t in schedule)
    ):
        raise ValueError("invalid reference iteration schedule")
    if type(ref["required_consecutive_converged"]) is not int or not 2 <= ref[
        "required_consecutive_converged"
    ] <= len(schedule):
        raise ValueError("require at least two converged reference checkpoints")
    for number in (
        ref["target_exploitability_pot_fraction"],
        raw["numerical_tolerance"],
    ):
        if type(number) not in (int, float) or not np.isfinite(number) or number <= 0:
            raise ValueError("invalid convergence/numerical tolerance")
    if not 5 <= len(raw["spot_files"]) <= 10 or len(set(raw["spot_files"])) != len(
        raw["spot_files"]
    ):
        raise ValueError("declare 5–10 distinct spots")
    return raw


def load_agents(
    root: Path, training: dict[str, Any], config: dict[str, Any]
) -> list[tuple[dict[str, Any], OwnNoLimitAgent]]:
    expected = json.loads((root / config["agent_training_config"]).read_text())
    if training["status"] != "completed" or training["config"] != expected:
        raise ValueError("own training must complete with the declared config")
    if expected["seeds"] != config["agent_seeds"]:
        raise ValueError("agent seed sets differ")
    agents = []
    models: dict[str, Any] = {}
    observed = set()
    for row in training["rows"]:
        path = Path(row["checkpoint"])
        if sha(path) != row["checkpoint_sha256"]:
            raise ValueError("own checkpoint fingerprint mismatch")
        if sha(root / row["model"]) != training["model_sha256"][row["model"]]:
            raise ValueError("own model fingerprint mismatch")
        if row["method"] != "external":
            raise ValueError("this ablation declares external sampling only")
        buckets = int(Path(row["model"]).stem.rsplit("-", 1)[1])
        key = (buckets, row["seed"], row["iteration"])
        if key in observed:
            raise ValueError("duplicate own ablation profile")
        observed.add(key)
        agent = OwnNoLimitAgent.load(path, root / row["model"])
        # Same immutable model; deterministic feature-cache results shared across
        # seeds/checkpoints. No reference inputs enter that cache or the agent.
        agent.model = models.setdefault(row["model"], agent.model)
        metadata = {
            "buckets": buckets,
            "seed": row["seed"],
            "iteration": row["iteration"],
            "checkpoint_sha256": row["checkpoint_sha256"],
            "model": row["model"],
        }
        agents.append((metadata, agent))
    expected_keys = {
        (int(Path(m).stem.rsplit("-", 1)[1]), s, t)
        for m in expected["models"]
        for s in expected["seeds"]
        for t in expected["checkpoints"]
    }
    if observed != expected_keys:
        raise ValueError("own ablation is missing a declared profile")
    return agents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--training-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_config(args.config)
    source = source_provenance(
        root, args.config, entrypoints=("scripts/validate_postflop.py",)
    )
    training = json.loads(args.training_report.read_text())
    output = args.output.parent
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    agents = load_agents(root, training, config)
    results = []
    artifacts = []
    heatmap: dict[str, Any] = {}
    total_nodes = 0
    for spot_file in config["spot_files"]:
        tick = time.perf_counter()
        spot = load_spot(root / spot_file)
        controls = verify_card_worlds(spot)
        tree = SpotTree.build(spot)
        total_nodes += len(tree.states)
        if total_nodes > config["max_total_tree_nodes"]:
            raise ValueError("spot set exceeded total tree budget")
        reference = Reference(tree)
        trace = []
        consecutive = 0
        previous = None
        prior = None
        target = config["reference"]["target_exploitability_pot_fraction"] * spot.pot
        for iteration in config["reference"]["iteration_schedule"]:
            reference.train_to(iteration)
            policy = reference.policy()
            exploit = reference.exploitability(policy)
            trace.append({"iteration": iteration, "exploitability": exploit})
            consecutive = consecutive + 1 if exploit <= target else 0
            if consecutive >= config["reference"]["required_consecutive_converged"]:
                prior = previous
                break
            previous = policy
        if (
            consecutive < config["reference"]["required_consecutive_converged"]
            or prior is None
        ):
            raise ArithmeticError(
                f"reference convergence gate failed: {spot.name}: {trace}"
            )
        mass = information_reach(tree, policy)
        stability = weighted_gap(prior, policy, mass, list(range(len(tree.keys))))
        reference_path = output / f"{spot.name}-reference.json.gz"
        compressed_json(
            reference_path,
            {
                "format": "poker-ai-reference-comparison-only-v1",
                "spot_sha256": sha(root / spot_file),
                "efg_sha256": hashlib.sha256(tree.efg().encode()).hexdigest(),
                "solver": config["reference"],
                "iteration": reference.iteration,
                "exploitability": exploit,
                "information_keys": tree.keys,
                "menus": tree.menus,
                "policy": policy,
            },
        )
        artifacts.append(reference_path)
        contexts = prepare_contexts(tree, agents[0][1], config["mapping_episode_seed"])
        comparisons = []
        heatmap_runs = []
        for metadata, agent in agents:
            primary = (
                metadata["buckets"] == config["primary_buckets"]
                and metadata["iteration"] == config["primary_iteration"]
            )
            compiled = compile_agent(tree, agent, contexts)
            if (
                compiled.projection_mass > config["primary_projection_mass_limit"]
                or compiled.shadow_changes
            ):
                raise ArithmeticError(
                    "matched-grid comparison changed public ledger/actions"
                )
            result = compare(
                tree,
                reference,
                policy,
                compiled,
                tolerance=config["numerical_tolerance"],
                detailed=primary,
            )
            if primary:
                details = {
                    "metadata": metadata,
                    "decision_rows": result.pop("decision_rows"),
                    "node_frequencies": result.pop("node_frequencies"),
                    "conditioning": (
                        "same reference joint-reach beliefs for both "
                        "continuation EVs/frequencies"
                    ),
                }
                detail_path = (
                    output / f"{spot.name}-seed{metadata['seed']}-nodes.json.gz"
                )
                compressed_json(detail_path, details)
                artifacts.append(detail_path)
                result["details_file"] = detail_path.name
                if spot.name == config["heatmap_spot"]:
                    heatmap_runs.append(
                        [
                            row
                            for row in details["decision_rows"]
                            if row["owner"] == spot.hero
                            and len(row["public_state"]["history"]) == len(spot.prefix)
                        ]
                    )
            comparisons.append(dict(metadata, **result))
        if heatmap_runs:
            first = heatmap_runs[0]
            classes = [row["hand_class"] for row in first]
            if len(set(classes)) != len(classes):
                raise ValueError(
                    "heatmap root needs one configured combo per hand class"
                )
            heatmap = {
                "spot": spot.name,
                "classes": classes,
                "actions": [
                    kind if amount is None else f"raise-to {amount}"
                    for kind, amount in first[0]["actions"]
                ],
                "reference": [row["reference_probabilities"] for row in first],
                "own": np.mean(
                    [
                        [row["own_probabilities"] for row in rows]
                        for rows in heatmap_runs
                    ],
                    axis=0,
                ).tolist(),
            }
        result_spot = {
            "name": spot.name,
            "config": json.loads((root / spot_file).read_text()),
            "config_sha256": sha(root / spot_file),
            "pot": spot.pot,
            "nodes": len(tree.states),
            "information_sets": len(tree.keys),
            "controls": controls,
            "reference_iterations": reference.iteration,
            "reference_exploitability": exploit,
            "reference_target": target,
            "reference_trace": trace,
            "reference_stability_action_gap": stability,
            "reference_file": reference_path.name,
            "comparisons": comparisons,
            "seconds": time.perf_counter() - tick,
        }
        results.append(result_spot)
        print(
            f"{spot.name}: {len(tree.states):,} nodes; "
            f"reference t={reference.iteration}, "
            f"exploit/pot={exploit / spot.pot:.6g}; "
            f"compared {len(comparisons)} own profiles",
            flush=True,
        )
    cpu = platform.processor()
    if platform.system() == "Darwin":
        cpu = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "passed",
        "config": config,
        "source": source,
        "training_source": training["source"],
        "training_report_sha256": sha(args.training_report),
        "spots": results,
        "heatmap": heatmap,
        "seconds": time.perf_counter() - started,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_model": cpu,
            "logical_cpus": os.cpu_count(),
            "numpy": np.__version__,
            "open_spiel": importlib.metadata.version("open_spiel"),
            "treys": importlib.metadata.version("treys"),
        },
    }
    summary = primary_summary(report)
    report["primary_summary"] = summary
    table = output / "postflop-summary.md"
    table.write_text(markdown_table(summary))
    artifacts.append(table)
    csv_path = output / "postflop-summary.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    artifacts.append(csv_path)
    artifacts.extend(plot(report, output))
    report["artifacts_sha256"] = {p.name: sha(p) for p in artifacts}
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(f"passed: {len(results)} turn subgames; report: {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
