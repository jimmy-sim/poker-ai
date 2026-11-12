"""Readable positive-log plot of authenticated sampled results; no new study."""

import argparse
import importlib
import json
from pathlib import Path

from poker_ai.evaluation.compact_sampled_clock import measurement
from poker_ai.evaluation.compact_sampled_gate import checked_path
from poker_ai.evaluation.compact_sampled_report import summaries
from poker_ai.postflop.compact_full_artifacts import atomic, commit_sources
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result", type=Path, default=Path("results/compact-sampled/real/result.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/compact-sampled/real/learning-log.png"),
    )
    args = parser.parse_args()
    result_path, output = ROOT / args.result, ROOT / args.output
    receipt = output.with_suffix(".json")
    if any(p.exists() or p.is_symlink() for p in (output, receipt)):
        raise FileExistsError("retain earlier figures; choose a fresh --output")
    result = json.loads(result_path.read_text())
    measurement(result_path, "report")
    if result["status"] != "completed" or result["failure"] is not None:
        raise ArithmeticError(
            "complete scientific report required, including failed gates"
        )
    # A new display script may coexist with added source. Every named historical
    # dependency must still match its original bytes AND recorded Git blob.
    commit_sources(ROOT, result["source"]["git_commit"], result["source"]["sha256"])
    own_path = checked_path(ROOT, result["inputs"][0])
    native_path = checked_path(ROOT, result["inputs"][1])
    before = [digest(p) for p in (result_path, own_path, native_path)]
    original = json.loads(own_path.read_text())
    config = contract(ROOT)
    summary = summaries(original["rows"], config)
    if summary != result["summary"]:
        raise ArithmeticError("published seed summaries changed")
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    for axis, spot in zip(axes, config["spot_files"], strict=True):
        extrema = [1.0]
        for representation in config["representations"]:
            selected = [
                row
                for row in summary["curves"]
                if row["spot_file"] == spot
                and row["representation"] == representation
                and row["readout"] == "linear"
            ]
            if any(value <= 0 for row in selected for value in row["values"]):
                raise ValueError("positive-log view requires positive raw seed values")
            x = [row["work_checkpoint"] for row in selected]
            axis.plot(
                x,
                [100 * row["median"] for row in selected],
                marker="o",
                label=representation,
            )
            axis.fill_between(
                x,
                [100 * row["minimum"] for row in selected],
                [100 * row["maximum"] for row in selected],
                alpha=0.12,
            )
            extrema.extend(100 * value for row in selected for value in row["values"])
        axis.axhline(1, color="black", linestyle=":", label="median limit (1%)")
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_ylim(min(extrema) / 2, max(extrema) * 2)
        axis.set_title(Path(spot).stem)
        axis.set_xlabel("Total node visits, including exact warm initialization")
        axis.set_ylabel("Exact exploitability (% initial pot)")
        axis.grid(alpha=0.2)
    axes[1].legend(fontsize=7)
    figure.suptitle("Fixed-work B4: LINEAR median and three-seed range; known games")
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=150)
    plt.close(figure)
    if before != [digest(p) for p in (result_path, own_path, native_path)]:
        raise ArithmeticError("display changed scientific input bytes")
    atomic(
        receipt,
        dict(
            scope="data-only display; all scientific results unchanged",
            script_sha256=digest(Path(__file__)),
            scientific_inputs_sha256=before,
            figure_sha256=digest(output),
            scientific_source_fingerprint=result["source"]["fingerprint"],
            all_readouts=324,
            primary_readouts=108,
            new_training=False,
            native_constructed=False,
            matplotlib=matplotlib.__version__,
            intervals="three fixed-seed minimum/maximum, not confidence",
        ),
    )
    print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
