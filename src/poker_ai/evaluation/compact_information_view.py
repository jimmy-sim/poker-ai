"""All-case trace tables and fast hash-checked saved-decision browsing."""

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_information_inputs as inputs
from poker_ai.evaluation import diagnostic_receipts as receipts
from poker_ai.evaluation.compact_information_run import FORMAT, replay, summary
from poker_ai.evaluation.diagnostic_clock import measurement
from poker_ai.postflop import compact_full_artifacts as files


def cached(root: Path, path: Path) -> dict[str, Any]:
    """Hash/source/cache inventory checks, not a substitute for mathematical replay."""
    inputs.config(root)
    saved: dict[str, Any] = json.loads(path.read_text())
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["scope"] not in ("software", "real")
    ):
        raise ArithmeticError("complete trace cache required")
    receipts.historical(root, saved["source"], saved["source"]["fingerprint"])
    measurement(path, "software-own" if saved["scope"] == "software" else "own")
    files.published(root, path)
    files.published(root, path.with_name(path.stem + "-child.json"))
    if any(
        saved[k] is not False
        for k in (
            "new_training",
            "native_constructed",
            "independent_new_row_value_audit",
            "actual_admission",
            "fresh_global_admission",
        )
    ):
        raise ArithmeticError("cache cannot assert training/reference/admission")
    rows = saved["panels"]
    keys = [inputs.key(r) for r in rows]
    if (
        len(keys) != 144
        or len(set(keys)) != 144
        or set(keys) != inputs.expected(root, saved["scope"] == "software")
    ):
        raise ArithmeticError("complete 144-panel cache required")
    expected = [
        dict(file=n, sha256=v) for n, v in inputs.config(root)["input_sha256"].items()
    ]
    if saved["parent_inputs"] != expected:
        raise ArithmeticError("cached parent evidence changed")
    for row in rows:
        raw = files.load_snapshot(path.parent / "details", row["receipt"])
        if summary(raw, row["receipt"]) != row:
            raise ArithmeticError("cached detail/manifest changed")
    return saved


def report(root: Path, own_path: Path, out: Path, started: float) -> dict[str, Any]:
    if out.exists():
        raise FileExistsError("retain existing complete/partial report")
    saved: dict[str, Any] = dict(
        format="compact-information-report-v1",
        status="running",
        failure=None,
        source=receipts.source(root, inputs.CONFIG, inputs.ENTRY),
        new_training=False,
        native_constructed=False,
        actual_admission=False,
        fresh_global_admission=False,
        independent_new_row_value_audit=False,
    )
    try:
        saved["replay"] = replay(root, own_path)
        own = cached(root, own_path)
        if own["scope"] != "real":
            raise ValueError("tiny aliases are not poker outcomes")
        for p in (
            own_path,
            own_path.with_name(own_path.stem + "-child.json"),
            *[
                own_path.parent / "details" / r["receipt"]["file"]
                for r in own["panels"]
            ],
        ):
            files.published(root, p)
        out.parent.mkdir(parents=True, exist_ok=True)
        panels = []
        groups: list[dict[str, Any]] = []
        for row in own["panels"]:
            packet = files.load_snapshot(own_path.parent / "details", row["receipt"])
            identity = {k: row[k] for k in inputs.FIELDS}
            panels.append(
                dict(
                    **identity,
                    information_gain_chips=packet["information_gain_chips"],
                    information_gain_percent_pot=100
                    * packet["information_gain_chips"]
                    / packet["initial_pot_chips"],
                    owned_rows=len(packet["rows"]),
                    groups=len(packet["groups"]),
                    strict_conflicting_groups=sum(
                        g["strict_conflict"] for g in packet["groups"]
                    ),
                    maximum_error_chips=packet["maximum_error_chips"],
                )
            )
            groups.extend(dict(**identity, **g) for g in packet["groups"])
        artifacts = []
        for name, rows in (("panels.csv", panels), ("groups.csv", groups)):
            p = out.parent / name
            with p.open("x", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            artifacts.append(p)
        table = out.parent / "tables.md"
        lines = [
            "# Restricted-reply-prefix information trace",
            "",
            "Every one of the 144 panels and 288 source aliases is retained.",
            "Target benefits are not divided by two; "
            "they are not aggregate exploitability.",
            "Prefix reach is the restricted own best reply, "
            "not original sampled reach.",
            "Conditional values are own calculations; "
            "parent B/R roots have the earlier scalar audit.",
            "Street attribution is not causal localization. "
            "No new training or admission.",
            "",
            "| Game | Description | Seed | Target | Fixed opponent | "
            "I (chips) | I (% pot) | Strict groups |",
            "|---|---|---:|---:|---|---:|---:|---:|",
        ]
        for row in panels:
            lines.append(
                "| "
                + " | ".join(
                    [
                        Path(row["spot_file"]).stem,
                        row["representation"],
                        str(row["seed"]),
                        str(row["target"]),
                        row["opponent_source"],
                        f"{row['information_gain_chips']:.10g}",
                        f"{row['information_gain_percent_pot']:.10g}",
                        str(row["strict_conflicting_groups"]),
                    ]
                )
                + " |"
            )
        with table.open("x") as stream:
            stream.write("\n".join(lines) + "\n")
        artifacts.append(table)
        if time.perf_counter() - started >= 900:
            raise TimeoutError("complete report cap")
        receipts.check_source(root, saved["source"], inputs.CONFIG, inputs.ENTRY)
        saved.update(
            status="completed",
            inputs=[receipts.bound(root, own_path)],
            panels=144,
            response_aliases=288,
            artifacts=[receipts.bound(root, p) for p in artifacts],
        )
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        saved["seconds"] = time.perf_counter() - started
        files.atomic(out, saved)
    return saved


def show(packet: dict[str, Any], rank: int, examples: int = 4) -> None:
    if not 1 <= rank <= len(packet["groups"]):
        raise ValueError("choose an available positive group rank")
    group = packet["groups"][rank - 1]
    print(
        f"\n{Path(packet['spot_file']).stem}/{packet['representation']}; "
        f"seed {packet['seed']}; target {packet['target']}; "
        f"fixed {packet['opponent_source']} opponent"
    )
    print("Hash-checked saved trace; full mathematical replay is a separate command.")
    print(
        "Restricted-best-reply prefix; finer legal reply suffix. "
        "Not original sampled reach or universal advice."
    )
    print(
        f"Total information benefit: {packet['information_gain_chips']:.9g} chips; "
        f"group {group['abstract_info']} contributes "
        f"{group['loss_contribution_chips']:.9g}"
    )
    print(
        f"Strict conflict: {group['strict_conflict']}; supported members "
        f"{group['supported_members']}/{group['exact_members']}"
    )
    rows = [
        r
        for r in packet["rows"]
        if r["abstract_info"] == group["abstract_info"]
        and r["restricted_prefix_reach_mass"] > 0
        and r["counterfactual_mass"] > 0
    ]
    rows.sort(key=lambda r: (-r["loss_contribution_chips"], r["exact_info"]))
    chosen = []
    seen: set[tuple[int, ...]] = set()
    for row in rows:
        signature = tuple(row["near_optimal_columns"])
        if signature not in seen:
            chosen.append(row)
            seen.add(signature)
    chosen.extend(r for r in rows if r not in chosen)
    for row in chosen[:examples]:
        print(
            f"\nExact row {row['exact_info']}; {row['street']}; "
            f"own {' '.join(row.get('hole', []))}; "
            f"board {' '.join(row.get('board', []))}"
        )
        print(
            f"Restricted-prefix reach {row['restricted_prefix_reach_mass']:.9g}; "
            f"additive loss {row['loss_contribution_chips']:.9g} chips"
        )
        print(
            "Near-best actions: "
            + ", ".join(row["actions"][i] for i in row["near_optimal_columns"])
        )
        for a, p, v in zip(
            row["actions"],
            row["restricted_probabilities"],
            row["reply_continuation_values_chips"],
            strict=True,
        ):
            print(
                f"  {a}: restricted probability {p:.6g}; "
                f"finer-reply suffix value {v:.9g} chips"
            )


def main(root: Path) -> None:
    parser = argparse.ArgumentParser(
        description="Browse saved information-loss traces; no training/reference."
    )
    parser.add_argument(
        "--own", type=Path, default=Path(inputs.FOLDER) / "real/own.json"
    )
    parser.add_argument("--spot", choices=("low", "medium"), default="medium")
    parser.add_argument("--representation", default="texture_range_q8_own_q8_b8")
    parser.add_argument("--seed", type=int, default=20261301)
    parser.add_argument("--target", type=int, choices=(0, 1), default=1)
    parser.add_argument("--opponent", choices=("S", "F"), default="S")
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    path = root / args.own
    saved = cached(root, path)
    rows = saved["panels"]
    selected = [
        i
        for i, r in enumerate(rows)
        if args.spot in Path(r["spot_file"]).stem
        and r["representation"] == args.representation
        and r["seed"] == args.seed
        and r["target"] == args.target
        and r["opponent_source"] == args.opponent
    ]
    if len(selected) != 1:
        raise ValueError("choose a declared spot/description/seed/target/opponent")
    index = selected[0]
    rank = args.rank
    while True:
        raw = files.load_snapshot(path.parent / "details", rows[index]["receipt"])
        show(raw, rank)
        if not args.interactive:
            break
        try:
            answer = input("\nn/p group, j/k panel, q quit > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if answer == "q":
            break
        if answer == "n":
            rank = rank % len(raw["groups"]) + 1
        elif answer == "p":
            rank = (rank - 2) % len(raw["groups"]) + 1
        elif answer in ("j", "k"):
            index = (index + (1 if answer == "j" else -1)) % len(rows)
            rank = 1
