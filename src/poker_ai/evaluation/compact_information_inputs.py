"""Replay the unchanged sealed parent archive under separately bound new code."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_fixed_inputs as parent
from poker_ai.evaluation import diagnostic_receipts as receipts
from poker_ai.evaluation.compact_fixed_clock import measurement
from poker_ai.evaluation.compact_fixed_run import FORMAT, validate_native
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_fixed import fixed_identities, mix, replay_detail
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_full_run import check_runtime
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.river_study import digest

CONFIG = "configs/compact-information-trace.json"
CONFIG_SHA = "78c8f2c5229c1dcf3b1cb6eb2f8a6dceded73ae19fc48d6f52ec92db5af8931b"
ENTRY = "scripts/trace_compact_information.py"
FOLDER = "results/compact-information-trace"
FIELDS = ("spot_file", "representation", "seed", "target", "opponent_source")


def config(root: Path) -> dict[str, Any]:
    value = receipts.config(root, CONFIG, CONFIG_SHA)
    parent.config(root)
    return value


@dataclass(frozen=True)
class Input:
    context: Context
    row: dict[str, Any]
    packet: dict[str, Any]
    native: dict[str, Any]


def load(root: Path, software: bool) -> tuple[dict[str, Any], list[Input]]:
    """Verify original named code and ALL raw parent mixtures; never bypass a guard."""
    c = config(root)
    folder = root / parent.FOLDER / ("software" if software else "real")
    op, np = folder / "own.json", folder / "native.json"
    own, native = json.loads(op.read_text()), json.loads(np.read_text())
    for saved in (own, native):
        parent.historical(root, saved["source"], c["parent_source_fingerprint"])
        check_runtime(saved["runtime"], real=not software)
    if (
        own["format"] != FORMAT
        or own["status"] != "completed"
        or own["failure"] is not None
        or own["scope"] != ("software" if software else "real")
        or any(
            own[k] is not False
            for k in (
                "new_training",
                "native_constructed",
                "actual_admission",
                "fresh_global_admission",
            )
        )
    ):
        raise ArithmeticError("complete original no-training parent archive required")
    measurement(op, "software-own" if software else "own")
    measurement(np, "software-native" if software else "native")
    validate_native(own, native, digest(op), parent.config(root)["native_reference"])
    if canonical(parent.replay_sources(root, software)) != canonical(own["parents"]):
        raise ArithmeticError("original source parents changed")
    rows = own["rows"]
    ids = [parent.identity(r) for r in rows]
    if (
        len(ids) != 144
        or len(set(ids)) != 144
        or set(ids) != parent.expected(root, software)
    ):
        raise ArithmeticError("all 144 sealed parent profiles required")
    lookup = {parent.identity(r): r for r in rows}
    audited = {parent.identity(r): r for r in native["comparisons"]}
    result = []
    for index, pair in enumerate(parent.pairs(root, software)):
        ctx = pair.context
        for mode in parent.config(root)["mixtures"]:
            key = ctx.spot_file, ctx.representation, pair.seed, mode
            row = lookup[key]
            if (
                row["receipt"]["file"] != f"{index:02d}-{mode}.json.gz"
                or canonical(row["origins"]) != canonical(pair.origins)
                or canonical(row["binding"]) != canonical(ctx.binding)
            ):
                raise ArithmeticError("sealed selector/context/receipt changed")
            raw = files.load_snapshot(folder / "details", row["receipt"])
            replay_detail(ctx, mix(ctx, pair.sampled, pair.full, mode), raw)
            expected = dict(
                **{k: row[k] for k in parent.FIELDS},
                binding=ctx.binding,
                origins=pair.origins,
                receipt=row["receipt"],
                metrics=raw["metrics"],
                responses=raw["responses"],
            )
            if canonical(expected) != canonical(row):
                raise ArithmeticError("sealed parent detail/manifest changed")
            result.append(Input(ctx, row, raw, audited[key]))
    if canonical(fixed_identities(rows)) != canonical(own["fixed_opponent_conditions"]):
        raise ArithmeticError("sealed fixed-opponent identities changed")
    if own["replay"]["maximum_identity_error_chips"] != max(
        r["maximum_error_chips"] for r in own["fixed_opponent_conditions"]
    ):
        raise ArithmeticError("sealed parent identity error changed")
    if not software:
        rp = folder / "result.json"
        report = json.loads(rp.read_text())
        parent.historical(root, report["source"], c["parent_source_fingerprint"])
        measurement(rp, "report")
        if (
            report["status"] != "completed"
            or report["failure"] is not None
            or report["actual_admission"] is not False
        ):
            raise ArithmeticError("complete prior diagnostic report required")
        for item in report["inputs"] + report["artifacts"]:
            parent.checked(root, item)
    return own, result


def key(row: dict[str, Any]) -> tuple[Any, ...]:
    if (
        type(row["seed"]) is not int
        or type(row["target"]) is not int
        or row["target"] not in (0, 1)
        or row["opponent_source"] not in ("S", "F")
    ):
        raise ArithmeticError("strict trace coordinate required")
    return tuple(row[k] for k in FIELDS)


def expected(root: Path, software: bool) -> set[tuple[Any, ...]]:
    return {
        (*ident[:3], target, opponent)
        for ident in parent.expected(root, software)
        for target in (0, 1)
        for opponent in ("S", "F")
    }
