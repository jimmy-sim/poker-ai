"""Render complete saved river-refinement records; never train a strategy."""

import argparse
import copy
import csv
import gzip
import importlib
import importlib.util
import json
import math
import warnings
from pathlib import Path
from typing import Any, cast

from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

ROLES = ("B1", "IID", "stratified")
SUFFIXES = ("exact", "restricted")
PROBES = ("q8", "exact_mass", "ordered_relations", "exact_info")
SEEDS = (20261301, 20261302, 20261303)
VALUE = "local_sharing_cost_chips_per_cf_decision"
REPLAY_ROUNDOFF = 1e-12


def replay_summary(actual: dict[str, Any], saved: dict[str, Any]) -> float:
    """Exact structure/support; bounded roundoff ONLY for local float costs.

    Archived file hashes remain exact. This is not a performance/root/support
    tolerance, and does not rewrite any saved score. BLAS reductions can round
    differently across platforms even on identical retained binary64 inputs.
    """
    left, right = copy.deepcopy(actual), copy.deepcopy(saved)
    maximum = 0.0
    if len(left["probes"]) != len(right["probes"]):
        raise ArithmeticError("complete replay probe inventory required")
    for a, b in zip(left["probes"], right["probes"], strict=True):
        for suffix in SUFFIXES:
            x, y = (p["panels"][suffix].pop(VALUE) for p in (a, b))
            if any(
                type(v) not in (int, float) or not math.isfinite(v) or v < 0
                for v in (x, y)
            ):
                raise ArithmeticError("finite nonnegative replay costs required")
            error = abs(x - y)
            if error > REPLAY_ROUNDOFF or (
                a["probe"] == "exact_info" and (x != 0 or y != 0)
            ):
                raise ArithmeticError(
                    f"local sharing cost replay error {error:.17g} "
                    "exceeds fixed roundoff/zero control"
                )
            maximum = max(maximum, error)
    if canonical(left) != canonical(right):
        fields = [k for k in left if canonical(left[k]) != canonical(right.get(k))]
        raise ArithmeticError(
            f"complete row replay structure/support differs at {fields}"
        )
    return maximum


def checked(root: Path, folder: Path) -> list[dict[str, Any]]:
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest["status"] != "complete_saved_river_refinement_diagnostic"
        or (folder / "failure.json").exists()
        or manifest["constructors_blocked"] is not True
        or any(
            manifest[k] is not False
            for k in (
                "training_performed",
                "reference_constructed",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
        or not 0 < manifest["seconds"] < 900
    ):
        raise ArithmeticError("complete constructor-blocked diagnostic required")
    check_source(root, manifest["source"])
    config_path = root / "configs/river-refinement-diagnosis.json"
    cfg = json.loads(config_path.read_text())
    expected_outputs = {"summary.json", "rows.json.gz", "partial.json"} | {
        f"partial-{seed}-{role}.json.gz" for seed in SEEDS for role in ROLES
    }
    if (
        manifest["source_sha256"] != sha(manifest["source"]["sha256"])
        or manifest["config_sha256"] != digest(config_path)
        or set(manifest["outputs"]) != expected_outputs
        or set(manifest["input_sha256"])
        != {cfg[k] for k in ("own", "native", "panel_config")}
    ):
        raise ArithmeticError("complete source/input/output receipt required")
    if (
        digest(root / cfg["own"]) != cfg["own_sha256"]
        or digest(root / cfg["panel_config"]) != cfg["panel_config_sha256"]
    ):
        raise ArithmeticError("prospectively pinned own/panel input changed")
    if any(digest(folder / p) != h for p, h in manifest["outputs"].items()):
        raise ArithmeticError("saved refinement output changed")
    if any(digest(root / p) != h for p, h in manifest["input_sha256"].items()):
        raise ArithmeticError("bound refinement input changed")
    profiles = json.loads((folder / "summary.json").read_text())["profiles"]
    detail = json.loads(gzip.decompress((folder / "rows.json.gz").read_bytes()))[
        "profiles"
    ]
    expected = [(seed, role) for seed in SEEDS for role in ROLES]
    if [(p["seed"], p["role"]) for p in profiles] != expected or [
        (p["seed"], p["role"]) for p in detail
    ] != expected:
        raise ArithmeticError("complete ordered nine-profile panel required")
    spec = importlib.util.spec_from_file_location(
        "refinement_numeric_check", root / "scripts/diagnose_river_refinement.py"
    )
    assert spec is not None and spec.loader is not None
    numeric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(numeric)
    if manifest["config_sha256"] != numeric.CONFIG_SHA:
        raise ArithmeticError("prospective numeric protocol changed")
    maximum_replay_error = 0.0
    for p, d in zip(profiles, detail, strict=True):
        if (
            any(p[k] != d[k] for k in ("source_id", "policy_sha256"))
            or [r["target"] for r in p["responses"]] != [0, 1]
            or [r["target"] for r in d["responses"]] != [0, 1]
        ):
            raise ArithmeticError("saved refinement identity/seat changed")
        for summary, inventory in zip(p["responses"], d["responses"], strict=True):
            recalculated = numeric.summarize(inventory["rows"], inventory["target"])
            maximum_replay_error = max(
                maximum_replay_error,
                replay_summary(recalculated, {k: summary[k] for k in recalculated}),
            )
    if maximum_replay_error > 0:
        warnings.warn(
            f"Local cost replay roundoff {maximum_replay_error:.17g} "
            "(limit 1e-12); archived bytes unchanged.",
            RuntimeWarning,
            stacklevel=2,
        )
    return cast(list[dict[str, Any]], profiles)


def flat(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for p in profiles:
        for response in p["responses"]:
            for probe in response["probes"]:
                for suffix in SUFFIXES:
                    rows.append(
                        dict(
                            seed=p["seed"],
                            role=p["role"],
                            target=response["target"],
                            suffix=suffix,
                            probe=probe["probe"],
                            groups=probe["groups"],
                            river_infos=response["river_infos"],
                            supported_infos=response["supported_infos"],
                            unsupported_infos=response["unsupported_infos"],
                            **probe["panels"][suffix],
                        )
                    )
    expected = {
        (seed, role, target, suffix, probe)
        for seed in SEEDS
        for role in ROLES
        for target in (0, 1)
        for suffix in SUFFIXES
        for probe in PROBES
    }
    identities = [
        (r["seed"], r["role"], r["target"], r["suffix"], r["probe"]) for r in rows
    ]
    if len(identities) != len(expected) or set(identities) != expected:
        raise ArithmeticError("complete 144-condition table required")
    if any(
        type(r[VALUE]) not in (int, float)
        or not math.isfinite(r[VALUE])
        or r[VALUE] < 0
        for r in rows
    ):
        raise ArithmeticError("finite nonnegative local costs required")
    return rows


def report(root: Path, folder: Path, output: Path, *, plots: bool) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous refinement report")
    profiles = checked(root, folder)
    rows = flat(profiles)
    output.mkdir(parents=True)
    with (output / "conditions.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    aggregate = []
    for suffix in SUFFIXES:
        for role in ROLES:
            for probe in PROBES:
                cells = [
                    r
                    for r in rows
                    if (r["suffix"], r["role"], r["probe"]) == (suffix, role, probe)
                ]
                if len(cells) != 6:
                    raise ArithmeticError(
                        "all six dependent seed/seat conditions required"
                    )
                values = [r[VALUE] for r in cells]
                aggregate.append(
                    dict(
                        suffix=suffix,
                        role=role,
                        probe=probe,
                        mean=math.fsum(values) / 6,
                        minimum=min(values),
                        maximum=max(values),
                    )
                )
    persist(output / "summary.json", dict(aggregates=aggregate, conditions=len(rows)))
    if plots:
        draw(aggregate, output / "static-probes.png")
    provenance = source_provenance(
        root,
        root / "configs/river-refinement-diagnosis.json",
        entrypoints=("scripts/report_river_refinement.py",),
    )
    persist(
        output / "manifest.json",
        dict(
            source=provenance,
            input_manifest_sha256=digest(folder / "manifest.json"),
            outputs={p.name: digest(p) for p in sorted(output.iterdir())},
            limits=(
                "Local fixed-Q counterfactual-weighted sharing, not root EV/"
                "exploitability or training improvement. Means/ranges of 2 seats "
                "x 3 dependent fixed seeds, not confidence intervals."
            ),
        ),
    )


def draw(aggregate: list[dict[str, Any]], path: Path) -> None:
    import numpy as np

    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
    for ax, suffix in zip(axes, SUFFIXES, strict=True):
        for index, role in enumerate(ROLES):
            data = [
                next(
                    r
                    for r in aggregate
                    if (r["suffix"], r["role"], r["probe"]) == (suffix, role, probe)
                )
                for probe in PROBES
            ]
            y = np.array([r["mean"] for r in data])
            low = y - np.array([r["minimum"] for r in data])
            high = np.array([r["maximum"] for r in data]) - y
            ax.bar(
                np.arange(4) + (index - 1) * 0.25,
                y,
                width=0.25,
                label=role,
                yerr=np.array([low, high]),
                capsize=3,
            )
        ax.set_xticks(
            range(4),
            ["q8", "exact mass", "combo outcomes", "exact infos\n(singleton control)"],
            rotation=12,
        )
        ax.set_title(
            "Exact reply suffix" if suffix == "exact" else "Grouped reply suffix"
        )
        ax.set_ylabel("Local sharing cost (chips / CF-weighted river decision)")
        ax.grid(axis="y", alpha=0.25)
        ax.legend()
    fig.suptitle(
        "Fixed saved replies: means and ranges over 2 seats × 3 fixed seeds\n"
        "Local diagnostic; not exploitability, hand EV loss or retraining gain"
    )
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("results/river-refinement"))
    parser.add_argument(
        "--output", type=Path, default=Path("results/river-refinement/report")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report(root, root / args.report, root / args.output, plots=not args.no_plots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
