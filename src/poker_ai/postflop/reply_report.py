"""Offline replay, tables and plots for saved-policy response diagnosis."""

import csv
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.reply_diagnosis import IDENTITY, replay
from poker_ai.postflop.river_study import digest


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, _, error = replay(root, path)
    audit = json.loads(audit_path.read_text())
    json.dumps(audit, allow_nan=False)
    expected = {
        tuple(c[k] for k in IDENTITY) + (t,) for c in report["cases"] for t in (0, 1)
    }
    ids = [tuple(r[k] for k in IDENTITY) + (r["target"],) for r in audit["rows"]]
    errors = [
        v for r in audit["rows"] for k, v in r.items() if k.endswith("error_chips")
    ]
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or len(ids) != len(set(ids))
        or set(ids) != expected
        or len(errors) != 4 * len(ids)
        or any(not 0 <= v <= report["config"]["tolerance_chips"] for v in errors)
        or audit["maximum_native_error_chips"] != max(errors)
    ):
        raise ArithmeticError("incomplete/changed reply audit")
    output.mkdir(parents=True, exist_ok=True)
    rows, streets = [], []
    for case in report["cases"]:
        scale = 100 / case["pot"]
        rows.append(
            {
                **{k: case[k] for k in IDENTITY},
                "exact_exploitability_percent_pot": scale
                * case["exact_exploitability_chips"],
                "within_partition_percent_pot": scale
                * case["restricted_exploitability_chips"],
                "extra_information_percent_pot": scale
                * case["extra_information_chips"],
            }
        )
        for response in case["responses"]:
            for street, chips in response["street_losses_chips"].items():
                streets.append(
                    {
                        **{k: case[k] for k in IDENTITY},
                        "responding_seat": response["target"],
                        "street": street,
                        "unilateral_loss_chips": chips,
                        "exploitability_contribution_percent_pot": scale * chips / 2,
                    }
                )
    for filename, records in (("summary.csv", rows), ("street-losses.csv", streets)):
        with (output / filename).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    summary = {
        "status": "verified_diagnosis",
        "cases": rows,
        "native_roots_checked": 2 * len(ids),
        "own_reply_values_checked": 2 * len(ids),
        "maximum_native_error_chips": audit["maximum_native_error_chips"],
        "maximum_own_replay_error_chips": error,
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "scope": (
            "fixed-opponent diagnosis only; no training, feature selection "
            "or global admission"
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    lines = [
        "# Saved-policy best-response diagnosis",
        "",
        "All numbers below are % of the initial pot. Exact = within-partition + "
        "extra-information response value (half-summed over seats).",
        "",
        "| Game | Representation | Exact exploitability | Within partition "
        "| Extra information |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {Path(row['spot_file']).stem} | {row['representation']} | "
            f"{row['exact_exploitability_percent_pot']:.8g} | "
            f"{row['within_partition_percent_pot']:.8g} | "
            f"{row['extra_information_percent_pot']:.8g} |"
        )
    lines += [
        "",
        "These are best responses to fixed saved policies, not a prediction of "
        "retraining gains or competitive Hold’em strength. All exact-info losses "
        "are retained, including zeros; their per-seat sums equal unilateral "
        "gains. Native checks share own exported mechanics and information "
        "partitions. Tiny signed values near zero are floating-point roundoff.",
        "",
        "![Response value decomposition](response-values.png)",
        "",
        "![Candidate decision loss by street](candidate-streets.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plot(rows, streets, output)
    return summary


def plot(
    rows: list[dict[str, Any]], streets: list[dict[str, Any]], output: Path
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    games = list(dict.fromkeys(Path(r["spot_file"]).stem for r in rows))
    fig, axes = plt.subplots(1, len(games), figsize=(12, 4.5), squeeze=False)
    for ax, game in zip(axes[0], games, strict=True):
        selected = [r for r in rows if Path(r["spot_file"]).stem == game]
        x = list(range(len(selected)))
        within = [r["within_partition_percent_pot"] for r in selected]
        extra = [r["extra_information_percent_pot"] for r in selected]
        ax.bar(x, within, label="Gain within saved partition")
        ax.bar(x, extra, bottom=within, label="Extra exact-information value")
        ax.set_xticks(
            x, [r["representation"] for r in selected], rotation=20, ha="right"
        )
        ax.set_title(game)
        ax.set_ylabel("Exploitability contribution (% initial pot)")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "Saved final policies, fixed opponents; each bar sums to exact exploitability"
    )
    fig.tight_layout()
    fig.savefig(output / "response-values.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, len(games), figsize=(12, 4.5), squeeze=False)
    for ax, game in zip(axes[0], games, strict=True):
        selected = [
            r
            for r in streets
            if Path(r["spot_file"]).stem == game
            and r["representation"] == "texture_made_b8"
        ]
        ax.bar(
            range(len(selected)),
            [r["exploitability_contribution_percent_pot"] for r in selected],
        )
        ax.set_xticks(
            range(len(selected)),
            [f"Seat {r['responding_seat']}\n{r['street']}" for r in selected],
        )
        ax.set_title(game)
        ax.set_ylabel("Additive loss / 2 (% initial pot)")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "Category candidate: saved-prefix reach, best-reply continuation; no retraining"
    )
    fig.tight_layout()
    fig.savefig(output / "candidate-streets.png", dpi=150)
    plt.close(fig)
