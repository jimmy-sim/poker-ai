"""Follow seven fixed archive-reader frames in an authenticated saved graph."""

import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import earlier_source_profile_support as original
from inspect_earlier_source_profile import contract as original_contract

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/archive-reader-edges.json"
CONFIG_SHA = "37c76231f408c323fac4f5341904fa1ec7b0ab1751ca4bb45adeedb515c8a8e2"


def contract(root: Path) -> dict[str, Any]:
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ArithmeticError("fixed archive-reader selection changed")
    config: dict[str, Any] = json.loads(raw)
    return config


def coordinates(
    root: Path, stats: dict[str, Any], selected: tuple[tuple[str, str], ...]
) -> None:
    """Bind defining-function aliases to original source, not importing labels."""
    base = original_contract(root)
    child = json.loads((root / base["pair"] / "profile/child.json").read_text())
    source = child["source"]["sha256"]
    for filename, name in selected:
        path = root / filename
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or filename not in source
            or hashlib.sha256(path.read_bytes()).hexdigest() != source[filename]
        ):
            raise ArithmeticError("selected producer source bytes changed")
        nodes = [
            n
            for n in ast.parse(path.read_bytes()).body
            if isinstance(n, ast.FunctionDef) and n.name == name
        ]
        frames = [
            f for f in stats["functions"] if (f["file"], f["name"]) == (filename, name)
        ]
        if len(nodes) != 1 or nodes[0].decorator_list or len(frames) != 1:
            raise ArithmeticError("unique undecorated defining coordinate required")
        node, frame = nodes[0], frames[0]
        args = [
            a.arg
            for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
        ]
        args += [a.arg for a in (node.args.vararg, node.args.kwarg) if a is not None]
        if (frame["line"], frame["qualname"], frame["arguments"]) != (
            node.lineno,
            name,
            args,
        ):
            raise ArithmeticError("saved defining coordinate differs from producer")


def analyze(root: Path) -> tuple[dict[str, Any], str]:
    config = contract(root)
    selected = tuple(tuple(pair) for pair in config["selected"])
    # This unchanged reader checks the original pair, hashes, source and units.
    stats, transcript = original.saved_graph(root, original_contract(root))
    coordinates(root, stats, selected)
    saved = original.direct_calls(stats, selected)
    saved["selection_contract_sha256"] = CONFIG_SHA
    saved["prospective_issue"] = config["prospective_issue"]
    return saved, transcript


def write_report(root: Path, output: Path) -> dict[str, Any]:
    base = original_contract(root)
    folder = root / base["pair"]
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous archive-reader reports")
    if output.resolve().is_relative_to(folder.resolve()):
        raise ValueError("cannot export into original producer inputs")

    def inputs() -> dict[str, str]:
        paths = {root / name for name in base["input_sha256"]}
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ArithmeticError("historical raw symlink refused")
            if path.is_file():
                paths.add(path)
        return {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)
        }

    before = inputs()
    saved, transcript = analyze(root)
    output.mkdir(parents=True)
    tables = {
        "all-functions.csv": saved["functions"],
        "all-callers.csv": saved["callers"],
        "selected-edges.csv": original.edge_rows(saved),
        "selected-functions.csv": [
            dict(
                **p["frame"],
                incoming_edges=len(p["incoming"]),
                outgoing_edges=len(p["outgoing"]),
                accounted_seconds=p["accounted_seconds"],
                residual_seconds=p["residual_seconds"],
                units=original.UNITS,
            )
            for p in saved["selected"]
        ],
    }
    for name, rows in tables.items():
        if not rows:
            raise ArithmeticError("complete nonempty table required")
        with (output / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {k: v for k, v in saved.items() if k not in ("functions", "callers")}
    summary.update(
        input_sha256=base["input_sha256"],
        producer_source_fingerprint=base["producer_source_fingerprint"],
        reference_constructed=False,
        poker_training_performed=False,
        admission_evidence=False,
        limitations=(
            "Dependent historical elapsed-stack aggregates include waits and profiler "
            "overhead. Nested pages overlap; shared grandchildren cannot be assigned "
            "to a caller. No current CPU, causal savings, optimization or strength "
            "admission. No new profiler, solver or trajectory."
        ),
    )
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    (output / "authentication.log").write_text(transcript)
    if inputs() != before:
        raise ArithmeticError("saved inputs changed during extraction")
    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--function", type=int, choices=range(1, 8))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None:
        saved = write_report(ROOT, ROOT / args.output)
    else:
        saved, _ = analyze(ROOT)
    print("Historical elapsed-stack seconds including waits; nested totals overlap.")
    for index, page in enumerate(saved["selected"], 1):
        row = page["frame"]
        print(
            f"{index}: {row['file']}:{row['line']} {row['qualname']}; "
            f"{row['total_calls']} calls; self {row['self_seconds']:.6f}s; "
            f"inclusive {row['cumulative_seconds']:.6f}s"
        )
    if args.function is not None:
        by_id = {r["id"]: r for r in saved["functions"]}
        page = saved["selected"][args.function - 1]
        for direction in ("incoming", "outgoing"):
            print(direction + " (all direct edges):")
            for edge in sorted(
                page[direction],
                key=lambda r: (-r["cumulative_seconds"], r["caller"], r["callee"]),
            ):
                peer = by_id[
                    edge["caller"] if direction == "incoming" else edge["callee"]
                ]
                print(
                    f"  {edge['cumulative_seconds']:.6f}s; "
                    f"{edge['total_calls']} calls; entry {peer['entry_index']}; "
                    f"{peer['file']}:{peer['line']} {peer['qualname']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
