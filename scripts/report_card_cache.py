"""Report a complete saved parent card-cache pair, including adverse outcomes."""

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from check_card_cache import CONFIG, CONFIG_SHA, contract, show
from profile_compact_replay import digest
from report_cached_native import elapsed_parts, write_csv

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/report_card_cache.py"
SOURCE = "b55a86b3042043ae4c4d74b87a3fa02fd95727252fb50ca53beb6bbb580fd751"


def measured(child: dict[str, Any]) -> None:
    if (
        child.get("config_sha256") != CONFIG_SHA
        or child.get("source", {}).get("fingerprint") != SOURCE
        or child.get("status") != "complete_card_cache_audit"
        or child.get("admission_evidence") is not False
        or child.get("base_admission_rejected") is not True
    ):
        raise ArithmeticError(
            "complete registered diagnostic source and scope required"
        )


def render(folder: Path, output: Path) -> dict[str, Any]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.reproducibility import runtime_environment
    from poker_ai.validation.five_card import source_provenance

    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous card-cache report")
    children = [
        json.loads((folder / name / "child.json").read_text())
        for name in ("uncached", "cached")
    ]
    for child in children:
        measured(child)
    show(ROOT, folder)
    pair = json.loads((folder / "pair.json").read_text())
    rows = []
    counters: list[dict[str, Any]] = []
    for mode, measurement, child in zip(
        pair["order"], pair["measurements"], children, strict=True
    ):
        native = json.loads((folder / mode / "native.json").read_text())
        reads = json.loads((folder / mode / "read-phases.json").read_text())["phases"]
        rows.append(
            dict(
                mode=mode,
                whole_wall_seconds=measurement["seconds"],
                parent_body_cpu_seconds=child["parent_body_cpu_seconds"],
                elapsed_parts=elapsed_parts(
                    measurement["seconds"], reads, native["native_batch"]["seconds"]
                ),
            )
        )
        counters.extend(
            dict(mode=mode, function=name, **row)
            for name, row in child["card_cache"].items()
        )
    source: dict[str, Any] = dict(
        source_provenance(
            ROOT, ROOT / CONFIG, entrypoints=(ENTRY, "scripts/report_cached_native.py")
        )
    )
    source["sha256"].update(children[0]["source"]["sha256"])
    source["fingerprint"] = sha(source["sha256"])
    commit_sources(ROOT, source["git_commit"], source["sha256"])
    summary = dict(
        scope="ONE_ORDERED_COMPLETE_SAVED_PARENT_CARD_CACHE_PAIR_NOT_ADMISSION",
        source=source,
        environment=runtime_environment(),
        admission_evidence=False,
        poker_training_performed=False,
        production_integrated=False,
        modes=rows,
        card_cache=counters,
        wall_reduction_percent=100
        * (1 - rows[1]["whole_wall_seconds"] / rows[0]["whole_wall_seconds"]),
        narrow_wall_time_pass=pair["narrow_wall_time_pass"],
        limitations=(
            "One ordered saved case; no population runtime/peak-memory/training "
            "strength or changed old forecast/permit. Reference workers unchanged; "
            "no reference strategies used in training."
        ),
    )
    output.mkdir(parents=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(output / "card-cache.csv", counters)
    write_csv(
        output / "elapsed-parts.csv",
        [
            dict(mode=r["mode"], part=k, wall_seconds=v)
            for r in rows
            for k, v in r["elapsed_parts"].items()
        ],
    )
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    figure, axes = plt.subplots(1, 2, figsize=(14, 5.5), layout="constrained")
    left = [0.0, 0.0]
    labels = {
        "tiny_proof_read": "Tiny proof read",
        "initial_own_read": "Initial own read",
        "reference_worker_batch": "Reference workers",
        "final_own_read": "Final own read",
        "other_elapsed": "Other elapsed",
    }
    for part, label in labels.items():
        values = [r["elapsed_parts"][part] for r in rows]
        axes[0].bar(["Uncached", "Cached"], values, bottom=left, label=label)
        left = [a + b for a, b in zip(left, values, strict=True)]
    axes[0].set(
        ylabel="Whole-command elapsed seconds",
        title="Every mandatory audit stage retained",
    )
    axes[0].legend(fontsize=8)
    for offset, mode in ((-0.18, "uncached"), (0.18, "cached")):
        values = [
            next(
                r["original_calls"]
                for r in counters
                if r["mode"] == mode and r["function"] == name
            )
            for name in ("canonical", "rank")
        ]
        axes[1].bar([offset, 1 + offset], values, width=0.36, label=mode.capitalize())
    axes[1].set(
        xticks=[0, 1],
        xticklabels=["Card normalization", "Hand ranking"],
        ylabel="Original function calls (log scale)",
        title="Reuse original immutable card-only results",
        yscale="log",
    )
    axes[1].legend()
    figure.suptitle(
        "One complete saved audit pair; parent only; no new learning or admission"
    )
    figure.savefig(output / "card-cache.png", dpi=160)
    plt.close(figure)
    files = {
        str(p.relative_to(folder)): digest(p) for p in folder.rglob("*") if p.is_file()
    }
    (output / "manifest.json").write_text(
        json.dumps(
            dict(
                input_sha256=files,
                output_sha256={
                    p.name: digest(p) for p in output.iterdir() if p.is_file()
                },
                original_inputs_retained=True,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pair", type=Path, default=Path("results/card-computation-cache/pair")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/card-computation-cache/report"),
    )
    args = parser.parse_args()
    contract(ROOT)
    saved = render(ROOT / args.pair, ROOT / args.output)
    print(
        json.dumps(
            dict(
                narrow_wall_time_pass=saved["narrow_wall_time_pass"],
                wall_reduction_percent=saved["wall_reduction_percent"],
                scope=saved["scope"],
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
