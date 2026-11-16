"""Read complete published suit-pipeline costs; never build a game or train."""

import argparse
import csv
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "results/compact-suit-learning"
SOURCE = "7381900fbd120938875a51bbd32ddb0afa340527eba5db1e1c50824a859e3f78"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gather(root: Path) -> dict[str, Any]:
    """Authenticate saved proof, complete clocks and forecast without replay."""
    from compact_suit.admission import forecast, training_forecast
    from compact_suit.cache import check_execution
    from compact_suit.clock import measurement
    from compact_suit.publication import committed
    from compact_suit.source import check_source, source

    from poker_ai.postflop.parallel_profile import same

    current = source(root)
    if current["fingerprint"] != SOURCE or len(current["sha256"]) != 433:
        raise ArithmeticError("complete checked suit-pipeline source required")
    path = root / FOLDER / "forecast.json"
    saved = json.loads(path.read_text())
    committed(root, path)
    if (
        saved["status"] != "complete_fixed_cost_forecast"
        or saved["failure"] is not None
    ):
        raise ArithmeticError("complete published forecast required")
    check_source(root, saved["source"])
    check_execution(root, saved)
    measurement(path, "forecast")
    hashes = dict(saved["verified_input_sha256"])
    hashes[str(path.relative_to(root))] = digest(path)
    for name, expected in hashes.items():
        member = root / name
        if (
            member.is_symlink()
            or not member.resolve().is_relative_to(root.resolve())
            or digest(member) != expected
        ):
            raise ArithmeticError("saved forecast input changed or escaped repository")
        committed(root, member)
    own: list[dict[str, Any]] = []
    native: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for repetition in (0, 1, 2):
        for mode, target in (("own", own), ("native", native)):
            member = root / FOLDER / f"cost/{repetition}/{mode}.json"
            receipt = json.loads(member.read_text())
            if hashes.get(str(member.relative_to(root))) != digest(member):
                raise ArithmeticError("all six complete cost members must be sealed")
            check_source(root, receipt["source"])
            check_execution(root, receipt)
            m = measurement(member, "cost-own" if mode == "own" else "cost-audit")
            if (
                type(receipt["repetition"]) is not int
                or receipt["repetition"] != repetition
            ):
                raise ArithmeticError("fixed cost repetition changed")
            if (
                receipt["poker_training_performed"] is not False
                or receipt["reference_output_used_in_training"] is not False
            ):
                raise ArithmeticError("cost and comparison-only scope required")
            target.append(receipt)
            rows.append(
                dict(
                    mode=mode,
                    repetition=repetition,
                    complete_seconds=m["seconds"],
                    reduced_requests=receipt["normalization"]["reduced_evaluations"],
                    errors=receipt["normalization"]["errors"],
                    fallbacks=receipt["normalization"]["fallbacks"],
                )
            )
    original = json.loads((root / "results/reduced-batch-study/own.json").read_text())
    training = training_forecast(original)
    recorded = saved["forecast"]["training"]
    if not same(
        training, {k: v for k, v in recorded.items() if k != "kernel_geometry"}
    ):
        raise ArithmeticError("all 24 original timing paths must match")
    # Geometry was built and checked by the complete forecast. A saved-data
    # report authenticates that record; it does not repeat a constructor here.
    training["kernel_geometry"] = recorded["kernel_geometry"]
    recomputed = forecast(training, own, native)
    if not same(recomputed, saved["forecast"]):
        raise ArithmeticError("maximum-based forecast arithmetic changed")
    return dict(
        scope="SAVED_COMPLETE_SUIT_PIPELINE_COSTS_NOT_PLAYING_STRENGTH",
        source_sha256=SOURCE,
        measured_costs=rows,
        forecast=recomputed,
        input_sha256=hashes,
        new_training_performed=False,
        compute_forecast_pass=recomputed["strict_own_pass"]
        and recomputed["strict_native_pass"],
        study_admission_claimed=False,
        default_changed=False,
        limitations=[
            "Three fixed sequential cost stand-ins; no new training "
            "or independent strength trials.",
            "The maximum retains runtime variation; no confidence interval "
            "or causal speedup claimed.",
            "Known restricted games; competitive full-game Hold'em strength "
            "remains unestablished.",
        ],
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def show(summary: dict[str, Any]) -> None:
    f = summary["forecast"]
    print("Complete validation costs; old-own stand-ins, zero new training")
    for mode in ("own", "native"):
        values = [
            r["complete_seconds"]
            for r in summary["measured_costs"]
            if r["mode"] == mode
        ]
        print(f"{mode}: " + ", ".join(f"{x:.3f}s" for x in values))
    for mode, cap in (("own", 7200), ("native", 900)):
        result = "PASS" if f[f"strict_{mode}_pass"] else "FAIL"
        print(
            f"{mode} conservative forecast: "
            f"{f[f'guarded_{mode}_seconds']:.3f}s / {cap}s: {result}"
        )
    print(
        "Cost evidence only. No stronger strategy, default change "
        "or study admission claimed."
    )


def render(root: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain earlier reports; choose a fresh output folder")
    summary = gather(root)
    output.mkdir(parents=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(output / "costs.csv", summary["measured_costs"])
    f = summary["forecast"]
    forecast_rows = [
        dict(
            mode=mode,
            guarded_seconds=f[f"guarded_{mode}_seconds"],
            cap_seconds=cap,
            strict_pass=f[f"strict_{mode}_pass"],
        )
        for mode, cap in (("own", 7200), ("native", 900))
    ]
    write_csv(output / "forecast.csv", forecast_rows)
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    for axis, mode in zip(axes, ("own", "native"), strict=True):
        rows = [r for r in summary["measured_costs"] if r["mode"] == mode]
        axis.bar(
            [str(r["repetition"]) for r in rows], [r["complete_seconds"] for r in rows]
        )
        axis.set_title(f"Complete {mode} costs")
        axis.set_xlabel("Fixed repetition")
        axis.set_ylabel("Complete command seconds")
        axis.set_ylim(bottom=0)
        if mode == "native":
            axis.axhline(
                390,
                color="firebrick",
                linestyle="--",
                label="Strict forecast needs N < 390s",
            )
            axis.legend(fontsize=8)
    figure.suptitle("All work retained; cost stand-ins, not new learning")
    figure.savefig(output / "complete-costs.png", dpi=140)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(8, 4.8), layout="constrained")
    axis.bar(
        [r["mode"] for r in forecast_rows],
        [100 * r["guarded_seconds"] / r["cap_seconds"] for r in forecast_rows],
        color=["#4477aa" if r["strict_pass"] else "#cc6677" for r in forecast_rows],
    )
    axis.axhline(100, color="firebrick", linestyle="--", label="Strict limit")
    axis.set_ylim(bottom=0)
    axis.set_ylabel("Conservative forecast as % of command cap")
    axis.set_title("Original maximum-based budget rules")
    axis.legend()
    figure.savefig(output / "forecast.png", dpi=140)
    plt.close(figure)
    from compact_suit.source import source

    from poker_ai.reproducibility import runtime_environment

    manifest = dict(
        scope="Saved-data rendering, not new scientific collection",
        renderer_sha256=digest(Path(__file__)),
        scientific_source=source(root),
        environment=runtime_environment(),
        output_sha256={
            p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()
        },
    )
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = gather(ROOT) if args.output is None else render(ROOT, args.output)
    show(summary)


if __name__ == "__main__":
    main()
