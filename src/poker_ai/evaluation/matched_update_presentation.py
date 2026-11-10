"""Deterministic two-axis contrasts from previously audited saved scalar values."""

import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any

from poker_ai.evaluation.matched_update_data import READOUTS, SEEDS, Data
from poker_ai.postflop.river_study import digest

METRICS = (
    "exact_exploitability",
    "within_partition_gain",
    "extra_information_gap",
    "river_only_gain_exact_prefix",
    "value_player_zero",
)
GROUP = ("spot_file", "representation", "regret_rule", "readout", "batch", "axis")
CASE = ("spot_file", "representation", "regret_rule", "seed")
AXES = ("same_work_label", "same_updates")


def number(value: Any) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ArithmeticError("finite non-boolean numeric value required")
    return float(value)


def contrast(
    left: dict[str, Any], right: dict[str, Any], pot: float
) -> dict[str, float]:
    denominator = number(pot)
    if denominator <= 0:
        raise ArithmeticError("initial pot must be positive")
    result = {}
    for metric in METRICS:
        a, b = (number(r["metrics"][metric + "_chips"]) for r in (left, right))
        result[metric + "_delta_chips"] = number(a - b)
        result[metric + "_delta_pct_pot"] = number(100 * (a - b) / denominator)
    for side, row in (("left", left), ("right", right)):
        result[side + "_exact_pct_pot"] = (
            100 * number(row["metrics"]["exact_exploitability_chips"]) / denominator
        )
    return result


def views(data: Data) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prefixes = {r["id"]: r for r in data.own["rows"]}
    new_fixed = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in data.own["fixed_matches"]
    }
    old_fixed = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in data.sources.fixed
    }
    points, fixed = [], []
    for pair in data.own["self_pairs"]:
        prefix = prefixes[pair["planned_prefix_id"]]
        batch = data.right[pair["reused_profile_id"]]
        full = data.final_b1[prefix["path_index"], pair["readout"]]
        pot = data.pots[prefix["case"]["spot_file"]]
        for axis, left in ((AXES[0], full), (AXES[1], prefix)):
            if any(left["case"][k] != batch["case"][k] for k in CASE):
                raise ArithmeticError("paired context/seed changed")
            if (
                axis == "same_updates"
                and not left["iteration"]
                == batch["iteration"]
                == pair["target_iteration"]
            ):
                raise ArithmeticError("matched iteration coordinates changed")
            if axis == "same_work_label" and left["work_label"] != batch["work_label"]:
                raise ArithmeticError("original work labels changed")
            common = dict(
                target_id=pair["target_id"],
                readout=pair["readout"],
                axis=axis,
                batch=batch["batch_size"],
                **{k: left["case"][k] for k in CASE},
                left_id=left["id"],
                right_id=batch["id"],
            )
            points.append(
                dict(
                    **common,
                    left_iteration=left["iteration"],
                    right_iteration=batch["iteration"],
                    left_work=left["total_work"],
                    right_work=batch["total_work"],
                    node_work_ratio=number(left["total_work"])
                    / number(batch["total_work"]),
                    **contrast(left, batch, pot),
                )
            )
            opponents = sorted(
                (op, seat) for own, op, seat in old_fixed if own == batch["id"]
            )
            if len(opponents) != 8 or len({op for op, _ in opponents}) != 4:
                raise ArithmeticError("four fixed opponents and both seats required")
            for opponent, seat in opponents:
                a = (new_fixed if axis == "same_updates" else old_fixed)[
                    left["id"], opponent, seat
                ]
                b = old_fixed[batch["id"], opponent, seat]
                if any(
                    a[k] != b[k] for k in ("opponent_policy_sha256", "reply_sha256")
                ) or any(
                    abs(number(a[k]) - number(b[k])) > 1e-9
                    for k in (
                        "restricted_reply_value_chips",
                        "achieved_reply_value_chips",
                    )
                ):
                    raise ArithmeticError("fixed opponent/reply root changed")
                ev = number(a["baseline_value_chips"]) - number(
                    b["baseline_value_chips"]
                )
                gain = number(a["gain_chips"]) - number(b["gain_chips"])
                if abs(ev + gain) > 1e-9:
                    raise ArithmeticError("target EV/gain signs changed")
                fixed.append(
                    dict(
                        **common,
                        opponent_profile_id=opponent,
                        target=seat,
                        ev_delta_chips=ev,
                        gain_delta_chips=gain,
                        ev_delta_pct_pot=100 * ev / pot,
                        gain_delta_pct_pot=100 * gain / pot,
                    )
                )
    expected = len(data.own["self_pairs"]) * 2
    if len(points) != expected or len(fixed) != expected * 8:
        raise ArithmeticError("complete two-axis output inventory required")
    for rows, extra in ((points, ()), (fixed, ("opponent_profile_id", "target"))):
        keys = ("target_id", "readout", "axis", *extra)
        if len({tuple(r[k] for k in keys) for r in rows}) != len(rows):
            raise ArithmeticError("duplicate two-axis pair")
        rows.sort(key=lambda r: tuple(r[k] for k in (*GROUP, "seed", *extra)))
    return points, fixed


def means(
    rows: list[dict[str, Any]], by: tuple[str, ...], values: tuple[str, ...]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[k] for k in by), []).append(row)
    result = []
    for key, group in sorted(grouped.items()):
        if (
            len(group) != 3
            or any(type(r["seed"]) is not int for r in group)
            or {r["seed"] for r in group} != set(SEEDS)
        ):
            raise ArithmeticError("exactly all three unique declared seeds required")
        record = dict(zip(by, key, strict=True), seeds=3)
        for value in values:
            numbers = [number(r[value]) for r in sorted(group, key=lambda r: r["seed"])]
            record["mean_" + value] = math.fsum(numbers) / 3
            record["min_" + value] = min(numbers)
            record["max_" + value] = max(numbers)
        result.append(record)
    return result


def csv_file(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ArithmeticError("cannot silently export an empty table")
    # Explicit canonical order, independent of dict insertion/JSON round trips.
    fields = sorted(rows[0])
    if any(set(r) != set(fields) for r in rows):
        raise ArithmeticError("table columns changed")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plots(groups: list[dict[str, Any]], folder: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list(
        "B1_to_batch", ["#2166ac", "#ffffff", "#d66000"]
    )
    contexts = sorted({tuple(r[k] for k in GROUP[:3]) for r in groups})
    columns = list(itertools.product(AXES, (4, 16)))
    for readout in READOUTS:
        lookup = {
            (tuple(r[k] for k in GROUP[:3]), r["axis"], r["batch"]): r
            for r in groups
            if r["readout"] == readout
        }
        matrix = np.array(
            [
                [
                    lookup[c, a, b]["mean_exact_exploitability_delta_pct_pot"]
                    for a, b in columns
                ]
                for c in contexts
            ]
        )
        extent = max(float(np.abs(matrix).max()), 1e-9)
        figure, ax = plt.subplots(figsize=(10, 7), layout="constrained")
        picture = ax.imshow(matrix, cmap=cmap, vmin=-extent, vmax=extent, aspect="auto")
        ax.set_xticks(
            range(4),
            [
                f"{'Same work label' if a == AXES[0] else 'Same updates'}\nB{b}"
                for a, b in columns
            ],
        )
        ax.set_yticks(
            range(len(contexts)),
            [
                f"{Path(g).stem} / {'q8' if rep != 'exact' else 'exact'} / {rule}"
                for g, rep, rule in contexts
            ],
        )
        for i, j in itertools.product(range(len(contexts)), range(4)):
            ax.text(j, i, f"{matrix[i, j]:.5f}", ha="center", va="center", fontsize=9)
        ax.set_title(
            f"{readout}: all contexts; means of three fixed seeds\n"
            "Blue: B1 lower; orange: batch lower. Scales differ across readouts."
        )
        figure.colorbar(
            picture,
            ax=ax,
            label="B1 minus batch exploitability (percentage points of initial pot)",
        )
        figure.savefig(folder / (readout + ".png"), dpi=160)
        plt.close(figure)


def write(data: Data, folder: Path, *, no_plots: bool) -> dict[str, str]:
    points, fixed = views(data)
    if len(points) != 288 or len(fixed) != 2304:
        raise ArithmeticError("all144 pairs on both axes required")
    values = (
        "left_exact_pct_pot",
        "right_exact_pct_pot",
        "node_work_ratio",
        *(m + "_delta_pct_pot" for m in METRICS),
    )
    grouped = means(points, GROUP, values)
    fixed_groups = means(
        fixed,
        (*GROUP, "opponent_profile_id", "target"),
        ("ev_delta_pct_pot", "gain_delta_pct_pot"),
    )
    if len(grouped) != 96 or len(fixed_groups) != 768:
        raise ArithmeticError("complete group inventory required")
    folder.mkdir(parents=True, exist_ok=False)
    for name, rows in (
        ("self-points", points),
        ("self-groups", grouped),
        ("fixed-points", fixed),
        ("fixed-groups", fixed_groups),
    ):
        csv_file(folder / (name + ".csv"), rows)
    text = [
        "# Complete two-axis comparisons",
        "",
        "All three fixed seeds per row; descriptive means, not confidence bounds.",
        (
            "Delta is B1 minus batch in percentage points of initial pot; "
            "lower self exploitability is better."
        ),
        (
            "Same-work B1 final endpoints are reused for both batch targets. "
            "Readouts share trajectories."
        ),
        "",
        (
            "| Game/encoding/rule/readout | Batch | Axis | B1 mean | Batch mean | "
            "Delta | Seed delta min–max | B1/batch work ratio |"
        ),
        "|---|---:|---|---:|---:|---:|---|---:|",
    ]
    for row in grouped:
        label = " / ".join(
            (
                Path(row["spot_file"]).stem,
                row["representation"],
                row["regret_rule"],
                row["readout"],
            )
        )
        metric = "exact_exploitability_delta_pct_pot"
        cells = [label, str(row["batch"]), row["axis"]]
        cells += [
            f"{row[k]:.6f}"
            for k in (
                "mean_left_exact_pct_pot",
                "mean_right_exact_pct_pot",
                "mean_" + metric,
            )
        ]
        cells += [
            f"{row['min_' + metric]:.6f} to {row['max_' + metric]:.6f}",
            f"{row['mean_node_work_ratio']:.6f}",
        ]
        text.append("|" + "|".join(cells) + "|")
    text += [
        "",
        (
            "All individual seed/target conditions remain in the CSVs. "
            "Fixed EV uses the responding seat’s sign; gain has the opposite sign. "
            "Better fixed EV need not mean lower self exploitability. "
            "Known tiny ranges, three seeds and dependent readouts do not establish "
            "general strength, convergence or default/fresh/global admission."
        ),
    ]
    (folder / "tables.md").write_text("\n".join(text) + "\n")
    summary = dict(
        status="read_only_two_axis_report",
        self_points=288,
        self_groups=96,
        fixed_points=2304,
        fixed_groups=768,
        full_B1_readout_identities=72,
        prefix_readout_identities=144,
        declared_seeds_per_group=3,
        training_performed=False,
        reference_constructed=False,
        new_agent_default=False,
        fresh_global_admission=False,
        source_own_sha256=digest(data.root / "results/matched-update-study/own.json"),
        source_native_sha256=digest(
            data.root / "results/matched-update-study/native.json"
        ),
        uncertainty=(
            "three fixed seeds; shared games/readouts/trajectories; "
            "no population intervals"
        ),
    )
    (folder / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    if not no_plots:
        plots(grouped, folder)
    return {p.name: digest(p) for p in sorted(folder.iterdir())}
