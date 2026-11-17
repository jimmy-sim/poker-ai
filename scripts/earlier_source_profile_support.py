"""Read direct call edges from a retained elapsed-stack profile, without replay."""

import math
from pathlib import Path
from typing import Any

from poker_ai.evaluation.batch_cost_stats import validate

SELECTED = (
    ("src/poker_ai/evaluation/opponent_learning_sources.py", "load"),
    ("src/poker_ai/evaluation/opponent_learning_sources.py", "build_game"),
    ("src/poker_ai/evaluation/opponent_learning_sources.py", "frozen_opponent"),
    ("src/poker_ai/evaluation/opponent_learning_sources.py", "boundaries"),
    ("src/poker_ai/evaluation/batch_current_inputs.py", "load"),
)
UNITS = "elapsed_stack_seconds_including_blocked_waits"
TOLERANCE_SECONDS = 1e-7


def direct_calls(
    stats: dict[str, Any],
    selected: tuple[tuple[str, str], ...] = SELECTED,
) -> dict[str, Any]:
    """Keep exact entry identities and caller-specific first-level costs.

    Cumulative function values include all callers. An outgoing edge instead
    describes direct calls from its selected caller. Pages at different depths
    overlap and must not be summed. Nonrecursive selected frames are required;
    self time plus outgoing cumulative edge time must recover that frame's
    cumulative time within the fixed absolute roundoff tolerance.
    """
    validate(stats)
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("distinct selected function coordinates required")
    functions = stats["functions"]
    by_id = {row["id"]: row for row in functions}
    pages = []
    for filename, name in selected:
        matches = [r for r in functions if (r["file"], r["name"]) == (filename, name)]
        if len(matches) != 1:
            raise ArithmeticError(
                "selected frame missing or ambiguous; no label merging"
            )
        frame = matches[0]
        if frame["primitive_calls"] != frame["total_calls"]:
            raise ArithmeticError("recursive selected frame cannot be partitioned")
        outgoing = [r for r in stats["callers"] if r["caller"] == frame["id"]]
        incoming = [r for r in stats["callers"] if r["callee"] == frame["id"]]
        if any(edge["callee"] == frame["id"] for edge in outgoing):
            raise ArithmeticError("selected self-recursive edge unsupported")
        accounted = frame["self_seconds"] + math.fsum(
            row["cumulative_seconds"] for row in outgoing
        )
        residual = frame["cumulative_seconds"] - accounted
        if abs(residual) > TOLERANCE_SECONDS:
            raise ArithmeticError(
                "direct child/self times do not recover selected frame"
            )
        for direction, rows in (("incoming", incoming), ("outgoing", outgoing)):
            for edge in rows:
                peer = by_id[
                    edge["caller"] if direction == "incoming" else edge["callee"]
                ]
                callee = frame if direction == "incoming" else peer
                if edge["total_calls"] > callee["total_calls"]:
                    raise ArithmeticError("edge call count exceeds its aggregate frame")
        pages.append(
            dict(
                frame=dict(frame),
                incoming=[dict(edge) for edge in incoming],
                outgoing=[dict(edge) for edge in outgoing],
                accounted_seconds=accounted,
                residual_seconds=residual,
            )
        )
    return dict(
        units=UNITS,
        tolerance_seconds=TOLERANCE_SECONDS,
        frame_count=stats["frame_count"],
        edge_count=stats["edge_count"],
        selected=pages,
        # Preserve complete original entries/edges, including duplicate labels.
        functions=[dict(row) for row in functions],
        callers=[dict(row) for row in stats["callers"]],
        scope=(
            "Historical profiled elapsed values; no current CPU estimate, "
            "optimizer admission or training"
        ),
    )


def source_coordinates(
    stats: dict[str, Any], root: Path, source_map: dict[str, str]
) -> None:
    """Check selected top-level source coordinates against retained producer bytes.

    The recorded bytecode digest is retained, not recompiled under a different
    Python minor. Exact producer source hashes and top-level AST coordinates bind
    these rows across supported data-reader runtimes.
    """
    import ast
    import hashlib

    for filename, name in SELECTED:
        path = root / filename
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or filename not in source_map
        ):
            raise ArithmeticError("selected source must be a pinned regular file")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source_map[filename]:
            raise ArithmeticError("selected producer source bytes changed")
        definitions = [
            node
            for node in ast.parse(raw).body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        if len(definitions) != 1 or definitions[0].decorator_list:
            raise ArithmeticError("unique undecorated top-level function required")
        node = definitions[0]
        frames = [
            row
            for row in stats["functions"]
            if (row["file"], row["name"]) == (filename, name)
        ]
        arguments = [
            arg.arg
            for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        ]
        if node.args.vararg:
            arguments.append(node.args.vararg.arg)
        if node.args.kwarg:
            arguments.append(node.args.kwarg.arg)
        if (
            len(frames) != 1
            or frames[0]["line"] != node.lineno
            or frames[0]["qualname"] != name
            or frames[0]["arguments"] != arguments
        ):
            raise ArithmeticError(
                "selected saved code coordinate differs from producer source"
            )


def edge_rows(saved: dict[str, Any]) -> list[dict[str, Any]]:
    """Every selected incoming/outgoing edge, with both unmerged identities."""
    by_id = {row["id"]: row for row in saved["functions"]}
    rows = []
    for page in saved["selected"]:
        frame = page["frame"]
        for direction in ("incoming", "outgoing"):
            for edge in page[direction]:
                caller, callee = by_id[edge["caller"]], by_id[edge["callee"]]
                rows.append(
                    dict(
                        selected_id=frame["id"],
                        selected_file=frame["file"],
                        selected_name=frame["qualname"],
                        direction=direction,
                        **edge,
                        caller_file=caller["file"],
                        caller_name=caller["qualname"],
                        caller_entry=caller["entry_index"],
                        callee_file=callee["file"],
                        callee_name=callee["qualname"],
                        callee_entry=callee["entry_index"],
                        units=UNITS,
                    )
                )
    return rows


def saved_graph(root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Authenticate the original completed producer; never call its launcher."""
    import contextlib
    import hashlib
    import io
    import json

    from report_cached_native import ROOT as historical_root
    from report_cached_native import gather

    if historical_root.resolve() != root.resolve():
        raise ArithmeticError("historical reader must authenticate this repository")

    if (
        config["units"] != UNITS
        or tuple(tuple(pair) for pair in config["selected"]) != SELECTED
        or config["absolute_accounting_tolerance_seconds"] != TOLERANCE_SECONDS
        or any(
            config[key] is not False
            for key in (
                "reference_constructed",
                "poker_training_performed",
                "admission_evidence",
            )
        )
    ):
        raise ArithmeticError(
            "fixed saved-data selection, units and no-construction scope required"
        )
    for filename, expected in config["input_sha256"].items():
        path = root / filename
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ArithmeticError("pinned input must stay within repository")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ArithmeticError("saved profile input bytes changed")
    folder = root / config["pair"]
    if not folder.resolve().is_relative_to(root.resolve()):
        raise ArithmeticError("producer folder must stay within repository")
    child = json.loads((folder / "profile/child.json").read_text())
    if child["source"]["fingerprint"] != config["producer_source_fingerprint"]:
        raise ArithmeticError("historical producer source identity changed")
    # gather authenticates the fixed pair, every raw producer hash, source
    # commit tree, exact scalar/replay identity, elapsed units and full schema.
    # It never calls the producer's child/main or constructs an own/native game.
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        _, stats = gather(folder)
    source_coordinates(stats, root, child["source"]["sha256"])
    return stats, output.getvalue()


def write_report(
    root: Path, destination: Path, config: dict[str, Any]
) -> dict[str, Any]:
    """Export every saved entry/edge and selected pages; reject prior output."""
    import csv
    import hashlib
    import json

    if destination.exists() or destination.is_symlink():
        raise FileExistsError("retain previous data-only reports")
    folder = root / config["pair"]
    if not folder.resolve().is_relative_to(root.resolve()):
        raise ArithmeticError("producer folder must stay within repository")
    if destination.resolve().is_relative_to(folder.resolve()):
        raise ValueError("reports must not be written into historical producer inputs")

    def all_input_hashes() -> dict[str, str]:
        paths = {root / name for name in config["input_sha256"]}
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ArithmeticError("historical raw inventory contains a symlink")
            if path.is_file():
                paths.add(path)
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)
        }

    before = all_input_hashes()
    stats, transcript = saved_graph(root, config)
    saved = direct_calls(stats, SELECTED)
    destination.mkdir(parents=True)

    def write_csv(name: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            raise ArithmeticError("complete nonempty table required")
        with (destination / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv("all-functions.csv", saved["functions"])
    write_csv("all-callers.csv", saved["callers"])
    write_csv("selected-edges.csv", edge_rows(saved))
    write_csv(
        "selected-functions.csv",
        [
            dict(
                **page["frame"],
                incoming_edges=len(page["incoming"]),
                outgoing_edges=len(page["outgoing"]),
                accounted_seconds=page["accounted_seconds"],
                residual_seconds=page["residual_seconds"],
                units=UNITS,
            )
            for page in saved["selected"]
        ],
    )
    summary = dict(
        scope=config["scope"],
        units=UNITS,
        input_sha256=config["input_sha256"],
        producer_source_fingerprint=config["producer_source_fingerprint"],
        frame_count=saved["frame_count"],
        edge_count=saved["edge_count"],
        selected=saved["selected"],
        absolute_accounting_tolerance_seconds=TOLERANCE_SECONDS,
        reference_constructed=False,
        poker_training_performed=False,
        admission_evidence=False,
        limitations=(
            "Historical instrumented elapsed-stack aggregates include blocked waits "
            "and profiler overhead. Function totals combine all callers; direct "
            "edges retain their caller scope. Incoming/outgoing tables and selected "
            "pages overlap and must not be added across levels. No current CPU "
            "estimate, counterfactual saving, optimizer admission, new measurement "
            "or strength claim."
        ),
    )
    (destination / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    (destination / "authentication.log").write_text(transcript)
    after = all_input_hashes()
    if before != after:
        raise ArithmeticError("saved report inputs changed during analysis")
    return summary
