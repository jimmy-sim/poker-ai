"""Render all nine pocket-nines contrasts from the checked saved-data report."""

import argparse
import csv
import gzip
import importlib
import itertools
import json
import math
from pathlib import Path

from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

FOLDER = "results/private-prefix/continuations"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path(FOLDER))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/private-prefix/continuations-figure"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder, output = root / args.report, root / args.output
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing continuation figure")
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["status"] != "complete_saved_continuation_contrast":
        raise ArithmeticError("complete saved continuation report required")
    check_source(root, manifest["source"])
    if any(digest(folder / p) != h for p, h in manifest["outputs"].items()):
        raise ArithmeticError("continuation report bytes changed")
    cfg = json.loads((root / "configs/private-prefix-continuations.json").read_text())
    if (
        digest(root / "configs/private-prefix-continuations.json")
        != manifest["config_sha256"]
    ):
        raise ArithmeticError("continuation figure config changed")
    rows = json.loads(gzip.decompress((folder / "rows.json.gz").read_bytes()))["rows"]
    selected = {
        (r["seed"], r["role"]): r
        for r in rows
        if r["target"] == 1 and r["group"] == 819
    }
    coordinates = list(itertools.product(cfg["seeds"], cfg["roles"]))
    if len(selected) != 9 or set(selected) != set(coordinates):
        raise ArithmeticError("all nine fixed pocket-nines contrasts required")
    table = []
    for seed, role in coordinates:
        r = selected[seed, role]
        if (
            not r["supported"]
            or r["hole"] != ["9c", "9d"]
            or r["board"] != ["Ts", "9s", "4d", "2h"]
            or r["street"] != "TURN"
        ):
            raise ArithmeticError("fixed supported singleton turn example required")
        fold, call = (r["actions"].index(a) for a in ("fold", "call"))
        gaps = {k: v[call] - v[fold] for k, v in r["action_values_chips"].items()}
        if any(not math.isfinite(v) for v in gaps.values()):
            raise ArithmeticError("finite call-minus-fold contrasts required")
        table.append(
            dict(
                seed=seed,
                role=role,
                **{k + "_call_minus_fold_chips": v for k, v in gaps.items()},
            )
        )
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    fig, axis = plt.subplots(figsize=(13, 6))
    fig.subplots_adjust(bottom=0.23, top=0.86, left=0.08, right=0.99)
    x = list(range(9))
    axis.bar(
        [v - 0.18 for v in x],
        [r["exact_call_minus_fold_chips"] for r in table],
        width=0.36,
        label="Exact reply continuation",
    )
    axis.bar(
        [v + 0.18 for v in x],
        [r["river_before_call_minus_fold_chips"] for r in table],
        width=0.36,
        label="Hybrid: constrained own river",
    )
    axis.axhline(0, color="gray", linewidth=1)
    axis.set_xticks(
        x,
        [
            str(s)[-2:]
            + "\n"
            + r.replace("stratified", "new B4").replace("IID", "IID B4")
            for s, r in coordinates
        ],
    )
    axis.set_ylabel("Call value minus fold value (net responding-player chips)")
    axis.set_xlabel("Saved method and fixed seed suffix (01, 02, 03)")
    axis.set_title(
        "Own 9c 9d; board Ts 9s 4d 2h; responding seat 1\n"
        "Only own river continuation changes within each snapshot"
    )
    axis.legend(loc="upper right")
    fig.text(
        0.5,
        0.02,
        "Each pair keeps its snapshot's opponent fixed; all nine snapshots shown.\n"
        "Above zero: calling has higher continuation value than folding. "
        "Complete report: 90 groups / 415 member rows.",
        ha="center",
        fontsize=9,
    )
    output.mkdir(parents=True, exist_ok=False)
    fig.savefig(output / "call-versus-fold.png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    with (output / "call-versus-fold.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, list(table[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(table)
    (output / "manifest.json").write_text(
        json.dumps(
            dict(
                status="complete_posthoc_all_nine_illustration",
                input_manifest_sha256=digest(folder / "manifest.json"),
                input_rows_sha256=digest(folder / "rows.json.gz"),
                renderer_sha256=digest(Path(__file__)),
                outputs={p.name: digest(p) for p in sorted(output.iterdir())},
                unit="net target chips, call minus fold",
                scope="Opponent fixed within each snapshot; "
                "different saved opponents across snapshots. "
                "No training, reference construction or new strength admission.",
            ),
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print("Rendered all nine fixed snapshots; full90/415 report unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
