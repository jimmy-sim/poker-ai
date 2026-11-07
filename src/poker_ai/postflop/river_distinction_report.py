"""Replay river distinction receipts and plot frozen-policy comparisons only."""

import csv
import importlib
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.river_distinctions import PANELS, PROBES, replay
from poker_ai.postflop.river_study import digest


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, _, error = replay(root, path)
    audit = json.loads(audit_path.read_text())
    json.dumps(audit, allow_nan=False)
    own = {
        (c["spot_file"], c["representation"], r["target"], p["prefix"]): p
        for c in report["cases"]
        for r in c["responses"]
        for p in r["panels"]
    }
    ids = [
        (r["spot_file"], r["representation"], r["target"], r["prefix"])
        for r in audit["rows"]
    ]
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or len(ids) != len(set(ids))
        or set(ids) != set(own)
        or audit["native_profiles_checked"] != 2 * len(ids)
    ):
        raise ArithmeticError("incomplete/mismatched river native audit")
    errors = []
    stored_errors: list[float] = []
    for key, row in zip(ids, audit["rows"], strict=True):
        p = own[key]
        stored_errors.extend(
            row[k]
            for k in ("before_error_chips", "after_error_chips", "gain_error_chips")
        )
        errors.extend(
            [
                abs(row["before_native_chips"] - p["before_value_chips"]),
                abs(row["after_native_chips"] - p["after_value_chips"]),
                abs(
                    row["after_native_chips"]
                    - row["before_native_chips"]
                    - p["river_gain_chips"]
                ),
            ]
        )
    if audit["maximum_native_error_chips"] != max(stored_errors) or any(
        not 0 <= e <= report["config"]["tolerance_chips"]
        for e in errors + stored_errors
    ):
        raise ArithmeticError("river native root agreement changed")
    rows, probes = [], []
    for case in report["cases"]:
        scale = 100 / (2 * case["pot"])
        rows.append(
            {
                "spot_file": case["spot_file"],
                "representation": case["representation"],
                "information_value_percent_pot": scale
                * sum(r["exact_information_value_chips"] for r in case["responses"]),
                "river_upgrade_restricted_prefix_percent_pot": scale
                * sum(
                    r["river_gain_restricted_prefix_chips"] for r in case["responses"]
                ),
                "earlier_readjustment_percent_pot": scale
                * sum(r["prefix_readjustment_chips"] for r in case["responses"]),
                "river_upgrade_exact_prefix_percent_pot": scale
                * sum(
                    p["river_gain_chips"]
                    for r in case["responses"]
                    for p in r["panels"]
                    if p["prefix"] == "exact_prefix"
                ),
            }
        )
        for response in case["responses"]:
            for panel in response["panels"]:
                probes.append(
                    {
                        "spot_file": case["spot_file"],
                        "representation": case["representation"],
                        "target": response["target"],
                        "prefix": panel["prefix"],
                        "positive_reach_infos": panel["positive_reach_infos"],
                        "strict_missed_infos": panel["strict_missed_infos"],
                        "tie_only_difference_infos": panel["tie_only_difference_infos"],
                        "conflicting_rows": panel["conflicting_rows"],
                        **panel["unresolved_after_probe"],
                    }
                )
    output.mkdir(parents=True, exist_ok=True)
    for name, records in (("gains.csv", rows), ("conflicts.csv", probes)):
        with (output / name).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    summary = {
        "status": "verified_diagnosis",
        "cases": rows,
        "native_profiles_checked": audit["native_profiles_checked"],
        "maximum_native_error_chips": max(errors + stored_errors),
        "maximum_own_replay_error_chips": error,
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "scope": (
            "fixed own river-only switches and static probe counts; no feature"
            " training/global admission"
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    lines = [
        "# Missing river distinctions",
        "",
        (
            "All gains below are half-summed across responding seats, as % "
            "initial pot. The first two switch components sum to the previous "
            "exact-information premium. The exact-prefix river upgrade is a "
            "separate panel, not an additional component."
        ),
        "",
        (
            "| Game | Representation | Information premium | River upgrade, "
            "restricted prefix | Earlier readjustment | River upgrade, exact "
            "prefix |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {Path(r['spot_file']).stem} | {r['representation']} | "
            f"{r['information_value_percent_pot']:.8g} | "
            f"{r['river_upgrade_restricted_prefix_percent_pot']:.8g} | "
            f"{r['earlier_readjustment_percent_pot']:.8g} | "
            f"{r['river_upgrade_exact_prefix_percent_pot']:.8g} |"
        )
    lines += [
        "",
        (
            "Probe counts refer to original merged rows still containing a "
            "strict reachable conflict after partitioning by one static "
            "signature. These are structural counts on known tiny ranges, not "
            "EV gains or trained-feature acceptance. Both prefix panels and "
            "all per-info records are retained. Native checks share own "
            "exported mechanics."
        ),
        "",
        "![Frozen river switches](river-gains.png)",
        "",
        "![Remaining candidate conflicts](probe-conflicts.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plots(rows, probes, output)
    return summary


def plots(
    rows: list[dict[str, Any]], probes: list[dict[str, Any]], output: Path
) -> None:
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    games = list(dict.fromkeys(Path(r["spot_file"]).stem for r in rows))
    fig, axes = plt.subplots(1, len(games), figsize=(12, 4.5), squeeze=False)
    for ax, game in zip(axes[0], games, strict=True):
        selected = [r for r in rows if Path(r["spot_file"]).stem == game]
        first = [r["river_upgrade_restricted_prefix_percent_pot"] for r in selected]
        second = [r["earlier_readjustment_percent_pot"] for r in selected]
        x = list(range(len(selected)))
        ax.bar(x, first, label="River upgrade after restricted prefix")
        ax.bar(x, second, bottom=first, label="Earlier choices with exact river play")
        ax.set_xticks(
            x, [r["representation"] for r in selected], rotation=20, ha="right"
        )
        ax.set_title(game)
        ax.set_ylabel("Information premium (% initial pot)")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "Frozen own policies: only river rows switch first; no feature training"
    )
    fig.tight_layout()
    fig.savefig(output / "river-gains.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, len(games), figsize=(12, 4.5), squeeze=False)
    for ax, game in zip(axes[0], games, strict=True):
        fields = ["conflicting_rows", *PROBES]
        for j, prefix in enumerate(PANELS):
            selected = [
                r
                for r in probes
                if Path(r["spot_file"]).stem == game
                and r["representation"] == "texture_made_b8"
                and r["prefix"] == prefix
            ]
            ax.bar(
                [i - 0.2 + 0.4 * j for i in range(4)],
                [sum(r[k] for r in selected) for k in fields],
                width=0.4,
                label=prefix,
            )
        ax.set_xticks(
            range(4),
            ["Before probe", "Own rank", "Range compatible", "Range relations"],
            rotation=15,
            ha="right",
        )
        ax.set_title(game)
        ax.set_ylabel("Original rows with unresolved strict conflicts")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "Category candidate, both responders; static diagnostic probes, "
        "not trained features"
    )
    fig.tight_layout()
    fig.savefig(output / "probe-conflicts.png", dpi=150)
    plt.close(fig)
