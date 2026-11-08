"""Comparison-only native costs/roots for committed OLD own policy profiles."""

import hashlib
import json
import math
import os
import time
from importlib.metadata import distribution, version
from pathlib import Path
from typing import Any, cast

import numpy as np

from poker_ai.postflop import pipeline_cost as own
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.pipeline_native_checks import validate_native
from poker_ai.postflop.pipeline_report import replay_own
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.solver_validation.reply_diagnosis import partition_source
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-saved-own-pipeline-native-cost-v1"


def license_record(config: dict[str, Any]) -> dict[str, Any]:
    """Reuse the already-read pinned Apache license; verify installed bytes again."""
    reference = config["native_reference"]
    if (
        version("open_spiel") != reference["version"]
        or reference["name"] != "OpenSpiel"
        or reference["license"] != "Apache-2.0"
        or reference["version"] != "2.0.2"
        or reference["license_sha256"]
        != "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
    ):
        raise ArithmeticError("pinned native reference/license changed")
    dist = distribution("open_spiel")
    files = [
        f
        for f in dist.files or []
        if ".dist-info/" in str(f) and str(f).upper().endswith("/LICENSE")
    ]
    if not files:
        raise ArithmeticError("installed OpenSpiel license missing")
    if any(
        hashlib.sha256(Path(str(dist.locate_file(f))).read_bytes()).hexdigest()
        != reference["license_sha256"]
        for f in files
    ):
        raise ArithmeticError("installed native license bytes changed")
    return dict(
        installed_license_files=[str(f) for f in files],
        sha256=reference["license_sha256"],
        previously_read_record="docs/solver_validation.md",
    )


def references(
    contexts: dict[tuple[str, str], ScoringContext],
) -> dict[tuple[str, str], tuple[Reference, Reference]]:
    exact = {}
    result = {}
    for (game, name), context in contexts.items():
        if not isinstance(context.exact, MatrixTree) or not isinstance(
            context.partition, MatrixTree
        ):
            raise ValueError("native policy audit requires bounded poker sources")
        if game not in exact:
            exact[game] = Reference(context.exact.source)
        limited = (
            exact[game]
            if name == "exact"
            else Reference(partition_source(context.partition))
        )
        result[game, name] = exact[game], limited
    return result


def compare_one(
    context: ScoringContext, refs: tuple[Reference, Reference], detail: dict[str, Any]
) -> dict[str, Any]:
    """Native actions/solver policies are never requested, returned or persisted."""
    if not isinstance(context.exact, MatrixTree) or not isinstance(
        context.partition, MatrixTree
    ):
        raise ValueError("native comparison requires poker matrix sources")
    exact, limited = refs
    average = unpack_policy(context.partition, detail["policy"])
    saved = context.expand(average)
    baseline = exact.value(context.exact.exact_policy(saved))
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    responses = []
    for target in (0, 1):
        sign = 1 if target == 0 else -1
        native_exact = exact.native_policy(context.exact.exact_policy(saved))
        native_limited = limited.native_policy(
            tuple(
                tuple(float(x) for x in average[i, : len(menu)])
                for i, menu in enumerate(context.partition.actions)
            )
        )
        b = float(
            exact.pyspiel.TabularBestResponse(exact.game, target, native_exact).value(
                ""
            )
        )
        c = float(
            limited.pyspiel.TabularBestResponse(
                limited.game, target, native_limited
            ).value("")
        )
        achieved = {}
        for name in ("exact", "restricted", "river_before"):
            dense = unpack_policy(context.exact, detail["replies"][target][name])
            context.exact.validate_policy(dense)
            if name == "restricted":
                context.partition.validate_policy(dense[first])
            achieved[name] = sign * exact.value(context.exact.exact_policy(dense))
        responses.append(
            dict(
                target=target,
                exact_root_chips=b,
                restricted_root_chips=c,
                achieved_exact_chips=achieved["exact"],
                achieved_restricted_chips=achieved["restricted"],
                achieved_river_before_chips=achieved["river_before"],
            )
        )
    metrics = dict(
        exact_exploitability_chips=math.fsum(r["exact_root_chips"] for r in responses)
        / 2,
        within_partition_gain_chips=math.fsum(
            r["restricted_root_chips"] for r in responses
        )
        / 2,
        extra_information_gap_chips=math.fsum(
            r["exact_root_chips"] - r["restricted_root_chips"] for r in responses
        )
        / 2,
        river_only_gain_exact_prefix_chips=math.fsum(
            r["exact_root_chips"] - r["achieved_river_before_chips"] for r in responses
        )
        / 2,
        value_player_zero_chips=baseline,
    )
    errors = [abs(metrics[k] - detail["metrics"][k]) for k in own.METRICS]
    for target, row in enumerate(responses):
        own_reply = detail["responses"][target]
        for native_name, own_name in {
            "exact_root_chips": "exact_reply_value_chips",
            "restricted_root_chips": "restricted_reply_value_chips",
            "achieved_exact_chips": "exact_reply_value_chips",
            "achieved_restricted_chips": "restricted_reply_value_chips",
            "achieved_river_before_chips": "river_before_value_chips",
        }.items():
            errors.append(abs(row[native_name] - own_reply[own_name]))
    if any(not math.isfinite(e) for e in errors):
        raise ArithmeticError("nonfinite native own-profile comparison")
    return dict(
        native_metrics=metrics, responses=responses, maximum_error_chips=max(errors)
    )


def native_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    license_record(payload["config"])
    matrices = own.contexts(Path(payload["root"]), payload["comparison"])
    refs = references(matrices)
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    for index in indices:
        deadline.check()
        detail = payload["profiles"][index]
        group = detail["case"]["spot_file"], detail["case"]["representation"]
        started, cpu = time.perf_counter(), time.process_time()
        comparison = compare_one(matrices[group], refs[group], detail)
        if comparison["maximum_error_chips"] > payload["config"]["tolerance_chips"]:
            raise ArithmeticError("native pipeline value/root/own reply disagreement")
        send(
            dict(
                kind="cell",
                index=index,
                row=dict(
                    index=index,
                    case=detail["case"],
                    **comparison,
                    seconds=time.perf_counter() - started,
                    cpu_seconds=time.process_time() - cpu,
                ),
            )
        )
    return dict(cells=len(indices))


def audit(root: Path, own_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain native pipeline calibration")
    started, cpu, child = time.perf_counter(), time.process_time(), os.times()
    source = source_provenance(root, root / own.CONFIG, entrypoints=own.ENTRIES)
    if source["dirty"] is not False:
        raise ValueError("commit own calibration before native comparison")
    saved, profiles, cases, protocol, _ = replay_own(root, own_path)
    license_info = license_record(saved["config"])
    deadline = Deadline(saved["config"]["native_calibration_maximum_seconds"])
    deadline.started = started
    result: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        input_sha256=digest(own_path),
        details_sha256=saved["details_sha256"],
        reference=saved["config"]["native_reference"],
        source=source,
        license=license_info,
        environment=runtime_environment(),
        batches=[],
        seconds=0.0,
        training_performed=False,
        reference_actions_exported=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    def persist() -> None:
        result["seconds"] = time.perf_counter() - started
        result["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        result["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - child.children_user
            - child.children_system
        )
        tmp = output.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        tmp.replace(output)

    try:
        for repeat in range(3):
            batch: dict[str, Any] = {}
            result["batches"].append(batch)
            payload = dict(
                root=str(root),
                profiles=profiles,
                config=saved["config"],
                comparison=protocol["future_comparison"],
                remaining_seconds=saved["config"]["native_calibration_maximum_seconds"]
                - (time.perf_counter() - started),
            )
            try:
                run_batch(16, 3, native_job, payload, deadline, batch)
            finally:
                batch["repeat"] = repeat
            persist()
            print(f"old-own native value/root/reply repeat {repeat + 1}/3", flush=True)
        validate_native(result, saved, profiles, cases)
        if any(
            digest(root / p) != sha
            for p, sha in cast(dict[str, str], source["sha256"]).items()
        ):
            raise ArithmeticError("native pipeline source changed")
        if digest(own_path) != result["input_sha256"]:
            raise ArithmeticError("own calibration changed during native comparison")
        deadline.check()
        result["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        result["status"] = "incomplete"
        result["failure"] = dict(type=type(error).__name__, reason=str(error))
    finally:
        persist()
    return result
