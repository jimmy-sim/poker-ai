"""Project the fixed post-hoc panel from fully checked saved policies only.

Poker replay, native schemas, gaps and source checks use the frozen libraries.
This experiment-specific entrypoint joins those records and renders CSV/plots;
it never trains, constructs a reference, selects a seed or changes a strategy.
"""

import argparse
import csv
import importlib
import itertools
import json
import math
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

from poker_ai.evaluation.matched_update_lifecycle import measured
from poker_ai.evaluation.private_prefix_admission import native_journal
from poker_ai.evaluation.private_prefix_pairs import metric_difference
from poker_ai.evaluation.private_prefix_read import read
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.private_prefix import validate
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/private-prefix-diagnosis.json"
CONFIG_SHA = "403ee1ef1b02f6fbc63c53e1851953f065e01b7673fc632b82e40b0bc9d8b90c"
COORD = ("game", "representation", "readout", "work_label", "seed")


def panel(
    config: dict[str, Any], own: dict[str, Any], pots: dict[str, float]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expected = set(
        itertools.product(
            config["games"],
            config["representations"],
            config["readouts"],
            config["work_labels"],
            config["seeds"],
        )
    )
    selected = {}
    for row in own["rows"]:
        case = row["case"]
        if (
            row["batch_size"] != config["batch_size"]
            or case["regret_rule"] != config["regret_rule"]
        ):
            continue
        key = (
            Path(case["spot_file"]).stem,
            case["representation"],
            row["readout"],
            row["work_label"],
            case["seed"],
        )
        if any(
            type(v) is not int
            for v in (row["batch_size"], row["work_label"], case["seed"])
        ):
            raise ArithmeticError("integer diagnostic coordinates required")
        if key not in expected or key in selected:
            raise ArithmeticError("changed/duplicate diagnostic candidate coordinate")
        selected[key] = row
    if set(selected) != expected:
        raise ArithmeticError("complete108 candidate diagnostic panel required")
    baseline = {r["id"]: r for r in own["baseline_rows"]}
    pairs = {(p["candidate_id"], p["baseline_kind"]): p for p in own["self_pairs"]}
    if len(baseline) != len(own["baseline_rows"]) or len(pairs) != len(
        own["self_pairs"]
    ):
        raise ArithmeticError("duplicate saved baseline/pair identity")
    points, differences = [], []
    for key, candidate in sorted(selected.items()):
        common = dict(zip(COORD, key, strict=True))
        pot = pots[common["game"]]
        if type(pot) not in (int, float) or not math.isfinite(pot) or pot <= 0:
            raise ArithmeticError("finite positive diagnostic pot required")
        roles = {"stratified": candidate}
        for kind in config["baseline_kinds"]:
            pair = pairs[candidate["id"], kind]
            peer = baseline[pair["baseline_id"]]
            roles[kind] = peer
            delta = metric_difference(peer["metrics"], candidate["metrics"])
            if delta != pair["baseline_minus_candidate_chips"]:
                raise ArithmeticError("saved paired gap changed")
            differences.append(
                dict(
                    **common,
                    baseline_kind=kind,
                    baseline_id=peer["id"],
                    candidate_id=candidate["id"],
                    baseline_iterations=peer["iteration"],
                    candidate_iterations=candidate["iteration"],
                    baseline_work=peer["total_work"],
                    candidate_work=candidate["total_work"],
                    **{
                        k.removesuffix("_chips") + "_pct_pot": 100 * delta[k] / pot
                        for k in config["metrics"]
                    },
                )
            )
        for role in config["roles"]:
            row = roles[role]
            metrics = row["metrics"]
            metric_difference(metrics, metrics)  # Existing finite/self-zero checks.
            error = abs(
                metrics["exact_exploitability_chips"]
                - metrics["within_partition_gain_chips"]
                - metrics["extra_information_gap_chips"]
            )
            if error > 1e-9:
                raise ArithmeticError(
                    "total differs from within+extra; river is separate"
                )
            coverage = row.get("coverage")
            support = {
                a + "_" + b: (
                    coverage[a]["all"]["row_fraction"]
                    if b == "row_coverage"
                    else coverage[a]["river"]["uniform_reach_fraction"]
                )
                if coverage
                else None
                for a in ("whole", "post_warm")
                for b in ("row_coverage", "river_reach_coverage")
            }
            points.append(
                dict(
                    **common,
                    role=role,
                    id=row["id"],
                    actual_work=row["total_work"],
                    iteration=row["iteration"],
                    initialization_visits=row.get("initialization_visits"),
                    sampled_traversals=row.get("sampled_traversals"),
                    **support,
                    **{
                        k.removesuffix("_chips") + "_pct_pot": 100 * metrics[k] / pot
                        for k in config["metrics"]
                    },
                )
            )
    if (
        len(points) != config["expected_profile_points"]
        or len(differences) != config["expected_paired_points"]
    ):
        raise ArithmeticError("complete324/216 diagnostic output required")
    if any(
        not math.isfinite(v)
        for row in (*points, *differences)
        for k, v in row.items()
        if k.endswith("_pct_pot")
    ):
        raise ArithmeticError("nonfinite normalized diagnostic metric")
    return points, differences


def groups(
    rows: list[dict[str, Any]], label: str, config: dict[str, Any]
) -> list[dict[str, Any]]:
    keys = (*COORD[:-1], label)
    values = [k.removesuffix("_chips") + "_pct_pot" for k in config["metrics"]]
    result = []
    for key, raw_peers in itertools.groupby(
        sorted(rows, key=lambda r: tuple(r[k] for k in keys)),
        key=lambda r: tuple(r[k] for k in keys),
    ):
        peers = list(raw_peers)
        if (
            any(type(r["seed"]) is not int for r in peers)
            or sorted(r["seed"] for r in peers) != config["seeds"]
        ):
            raise ArithmeticError("all three fixed seeds required in every group")
        if any(not math.isfinite(r[field]) for r in peers for field in values):
            raise ArithmeticError("nonfinite diagnostic group")
        result.append(
            dict(
                zip(keys, key, strict=True),
                seeds=3,
                **{
                    stat + "_" + field: function([r[field] for r in peers])
                    for field in values
                    for stat, function in (
                        ("mean", lambda xs: math.fsum(xs) / 3),
                        ("min", min),
                        ("max", max),
                    )
                },
            )
        )
    return result


def figure(points: list[dict[str, Any]], config: dict[str, Any], folder: Path) -> None:
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), layout="constrained")
    for ri, representation in enumerate(config["representations"]):
        for ci, readout in enumerate(config["readouts"]):
            lookup = {
                (r["seed"], r["role"]): r
                for r in points
                if r["game"] == "dev_medium_oop"
                and r["representation"] == representation
                and r["readout"] == readout
                and r["work_label"] == config["work_labels"][-1]
            }
            coordinates = list(itertools.product(config["seeds"], config["roles"]))
            within = [lookup[k]["within_partition_gain_pct_pot"] for k in coordinates]
            extra = [lookup[k]["extra_information_gap_pct_pot"] for k in coordinates]
            axis = axes[ri, ci]
            axis.bar(range(9), within, label="Within information groups")
            axis.bar(
                range(9), extra, bottom=within, label="Extra exact-information value"
            )
            axis.set_xticks(
                range(9),
                [
                    str(s)[-2:] + "/" + r.replace("stratified", "new")
                    for s, r in coordinates
                ],
                rotation=55,
            )
            axis.set_title(representation + " / " + readout)
            axis.set_ylabel("Exploitability (% initial pot)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2)
    fig.suptitle(
        "Saved medium game, signed/B4, final10m; all seeds20261301/02/03\n"
        "Each stack equals total exploitability; panels have different scales. "
        "River switch is separate. No causal/default claim."
    )
    fig.savefig(folder / "components.png", dpi=140)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/private-prefix/diagnosis")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / args.output
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing complete/partial diagnosis")
    started = time.perf_counter()
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective diagnostic panel changed")
    config = json.loads((root / CONFIG).read_text())
    own_path = root / config["own"]
    native_path = root / config["native"]
    if digest(own_path) != config["own_sha256"]:
        raise ArithmeticError("published own diagnostic input changed")
    print(
        "Replaying bound own/native evidence with constructors blocked; no training...",
        flush=True,
    )

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("diagnosis constructed a learner/reference")

    with ExitStack() as stack:
        for name in (
            "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
            "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            "poker_ai.solver_validation.reference.Reference.__init__",
        ):
            stack.enter_context(patch(name, forbidden))
        own, _ = read(root, own_path, Deadline(900))
        native = json.loads(native_path.read_text())
        check_source(root, native["source"])
        native_journal(native_path, native)
        measured(root, native_path, "real_native")
        validate(native, own, own_path)
        if own["source_sha256"] != config["model_source_sha256"]:
            raise ArithmeticError("frozen model source changed")
        source = source_provenance(
            root, root / CONFIG, entrypoints=("scripts/diagnose_private_prefix.py",)
        )
        pots = {
            g: json.loads(
                (root / "configs/learning-spots" / (g + ".json")).read_text()
            )["pot"]
            for g in config["games"]
        }
        points, paired = panel(config, own, pots)
        method_groups = groups(points, "role", config)
        paired_groups = groups(paired, "baseline_kind", config)
    if (
        len(method_groups) != config["expected_profile_groups"]
        or len(paired_groups) != config["expected_paired_groups"]
    ):
        raise ArithmeticError("complete108/72 diagnostic groups required")
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in (
        ("method-points", points),
        ("paired-points", paired),
        ("method-groups", method_groups),
        ("paired-groups", paired_groups),
    ):
        with (output / (name + ".csv")).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, sorted(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    if not args.no_plots:
        figure(points, config, output)
    persist(
        output / "manifest.json",
        dict(
            status="complete_posthoc_saved_policy_diagnosis",
            source=source,
            source_sha256=sha(source["sha256"]),
            model_source_sha256=config["model_source_sha256"],
            config_sha256=CONFIG_SHA,
            own_sha256=digest(own_path),
            native_sha256=digest(native_path),
            environment=runtime_environment(),
            counts=dict(
                method_points=len(points),
                paired_points=len(paired),
                method_groups=len(method_groups),
                paired_groups=len(paired_groups),
            ),
            outputs={p.name: digest(p) for p in sorted(output.iterdir())},
            seconds=time.perf_counter() - started,
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            new_agent_default=False,
            fresh_global_admission=False,
            scope=config["uncertainty"],
            limitations=config["limits"],
        ),
    )
    print("completed324method/216paired points;108/72groups; no training")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
