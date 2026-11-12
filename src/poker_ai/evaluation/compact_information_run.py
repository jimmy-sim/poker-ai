"""No-training full information-gain trace, immutable archives and replay."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_information_inputs as inputs
from poker_ai.evaluation import diagnostic_receipts as receipts
from poker_ai.evaluation.compact_fixed_inputs import checked
from poker_ai.evaluation.diagnostic_clock import arguments, measurement
from poker_ai.evaluation.diagnostic_guard import own_only
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_run import check_runtime, runtime
from poker_ai.postflop.compact_information import panel
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.river_study import Deadline

FORMAT = "compact-information-trace-v1"


def selected(
    sources: list[inputs.Input],
) -> list[tuple[inputs.Input, inputs.Input, int]]:
    lookup = {
        (
            r.context.spot_file,
            r.context.representation,
            r.row["seed"],
            r.row["mixture"],
        ): r
        for r in sources
    }
    if len(sources) != 144 or len(lookup) != 144:
        raise ArithmeticError("all 144 source recipes required")
    coords = sorted({k[:3] for k in lookup})
    result = []
    for key in coords:
        for target in (0, 1):
            for opponent in ("S", "F"):
                a = "S" + opponent if target == 0 else opponent + "S"
                b = "F" + opponent if target == 0 else opponent + "F"
                result.append((lookup[*key, a], lookup[*key, b], target))
    if len(result) != 144:
        raise ArithmeticError("all 144 fixed-opponent panels required")
    return result


def verify(
    root: Path,
    path: Path,
    saved: dict[str, Any],
    sources: list[inputs.Input] | None = None,
) -> dict[str, Any]:
    c = inputs.config(root)
    receipts.check_source(root, saved["source"], inputs.CONFIG, inputs.ENTRY)
    software = saved["scope"] == "software"
    if saved["scope"] not in ("software", "real") or any(
        saved[k] is not False
        for k in (
            "new_training",
            "native_constructed",
            "independent_new_row_value_audit",
            "actual_admission",
            "fresh_global_admission",
        )
    ):
        raise ArithmeticError("valid no-training/no-new-reference scope required")
    check_runtime(saved["runtime"], real=not software)
    expected_parents = [dict(file=n, sha256=v) for n, v in c["input_sha256"].items()]
    if saved["parent_inputs"] != expected_parents or saved["parent_inventory"] != dict(
        joint_profiles=144, response_aliases=288
    ):
        raise ArithmeticError("trace parent provenance/inventory changed")
    checked_path = checked(root, saved["checks"])
    if receipts.checks(root, checked_path, saved["source"]) != saved["checks"]:
        raise ArithmeticError("trace checked-source receipt changed")
    if not software and canonical(saved["software_proof"]) != canonical(
        software_proof(root)
    ):
        raise ArithmeticError("published software proof changed")
    if sources is None:
        _, sources = inputs.load(root, software)
    rows = saved["panels"]
    keys = [inputs.key(r) for r in rows]
    if (
        len(keys) != 144
        or len(set(keys)) != 144
        or set(keys) != inputs.expected(root, software)
    ):
        raise ArithmeticError("complete 144 trace panels required")
    lookup = {inputs.key(r): r for r in rows}
    totalrows = 0
    maxerror = 0.0
    for index, (a, b, target) in enumerate(selected(sources)):
        value = panel(a, b, target)
        key = inputs.key(value)
        row = lookup[key]
        if row["receipt"]["file"] != f"{index:03d}.json.gz":
            raise ArithmeticError("trace receipt coordinate changed")
        raw = files.load_snapshot(path.parent / "details", row["receipt"])
        if canonical(raw) != canonical(value) or canonical(row) != canonical(
            summary(value, row["receipt"])
        ):
            raise ArithmeticError("raw trace/alias/accounting replay changed")
        totalrows += len(raw["rows"])
        maxerror = max(maxerror, raw["maximum_error_chips"])
    return dict(
        panels=144,
        response_aliases=288,
        owned_rows=totalrows,
        maximum_error_chips=maxerror,
        new_training=False,
        native_constructed=False,
        actual_admission=False,
        absolute_tolerance_chips=c["absolute_tolerance_chips"],
    )


def summary(value: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k not in ("rows", "groups")} | dict(
        receipt=receipt,
        owned_rows=len(value["rows"]),
        group_count=len(value["groups"]),
        strict_conflicting_groups=sum(g["strict_conflict"] for g in value["groups"]),
    )


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
    ):
        raise ArithmeticError("complete trace archive required")
    measurement(path, "software-own" if saved["scope"] == "software" else "own")
    return verify(root, path, saved)


def software_proof(root: Path) -> dict[str, Any]:
    path = root / inputs.FOLDER / "software/own.json"
    result = replay(root, path)
    saved = json.loads(path.read_text())
    for p in (
        path,
        path.with_name("own-child.json"),
        *[path.parent / "details" / r["receipt"]["file"] for r in saved["panels"]],
    ):
        files.published(root, p)
    return dict(receipt=receipts.bound(root, path), **result)


def run(
    root: Path, out: Path, software: bool, checks: Path, started: float
) -> dict[str, Any]:
    if out.exists() or (out.parent / "details").exists():
        raise FileExistsError("retain complete/partial trace destinations")
    c = inputs.config(root)
    limit = Deadline(
        c["software_maximum_seconds"] if software else c["maximum_own_seconds"]
    )
    limit.started = started
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        scope="software" if software else "real",
        source=receipts.source(root, inputs.CONFIG, inputs.ENTRY),
        runtime=runtime(),
        new_training=False,
        native_constructed=False,
        independent_new_row_value_audit=False,
        actual_admission=False,
        fresh_global_admission=False,
        panels=[],
        partial_progress="Only persisted panels confirmed; later progress unknown",
    )

    def persist() -> None:
        saved["seconds"] = time.perf_counter() - started
        files.atomic(out, saved)

    try:
        with own_only():
            persist()
            saved["checks"] = receipts.checks(root, checks, saved["source"])
            check_runtime(saved["runtime"], real=not software)
            if not software:
                saved["software_proof"] = software_proof(root)
            original, sources = inputs.load(root, software)
            saved["parent_inputs"] = [
                dict(file=n, sha256=v) for n, v in c["input_sha256"].items()
            ]
            saved["parent_inventory"] = dict(
                joint_profiles=len(original["rows"]),
                response_aliases=sum(len(r["responses"]) for r in original["rows"]),
            )
            for index, (a, b, target) in enumerate(selected(sources)):
                limit.check()
                value = panel(a, b, target)
                receipt = files.write_snapshot(
                    out.parent / "details" / f"{index:03d}.json.gz", value
                )
                saved["panels"].append(summary(value, receipt))
                persist()
            saved["replay"] = verify(root, out, saved, sources)
            limit.check()
            receipts.check_source(root, saved["source"], inputs.CONFIG, inputs.ENTRY)
            saved["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        persist()
    return saved


def child(root: Path, argv: list[str]) -> int:
    args = arguments(argv)
    out = root / args.output
    started = float(os.environ.get("POKER_DIAGNOSTIC_STARTED", time.perf_counter()))
    try:
        if args.operation in ("software-own", "own"):
            if args.checks is None:
                raise ValueError("--checks required")
            result = run(
                root, out, args.operation == "software-own", root / args.checks, started
            )
        elif args.operation == "replay":
            if args.own is None:
                raise ValueError("--own required")
            with own_only():
                result = dict(
                    status="completed", failure=None, **replay(root, root / args.own)
                )
            files.atomic(out, result)
        else:
            from poker_ai.evaluation.compact_information_view import report

            if args.own is None:
                raise ValueError("--own required")
            with own_only():
                result = report(root, root / args.own, out, started)
        print(
            json.dumps(
                {
                    k: result.get(k)
                    for k in ("status", "failure", "new_training", "actual_admission")
                },
                sort_keys=True,
            )
        )
        return 0 if result["status"] == "completed" and result["failure"] is None else 1
    except (Exception, KeyboardInterrupt) as error:
        result = dict(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
            new_training=False,
            actual_admission=False,
        )
        if not out.exists():
            files.atomic(out, result)
        print(json.dumps(result, sort_keys=True))
        return 1
