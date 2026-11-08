"""Replay old-own scoring and forecast the remaining controlled-study costs."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop import pipeline_cost as own
from poker_ai.postflop.controlled_checkpoints import pack_policy, unpack_policy
from poker_ai.postflop.controlled_profile import cells
from poker_ai.postflop.parallel_profile import finite, same
from poker_ai.postflop.pipeline_render import SCOPE
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import digest


def check_source(root: Path, source: dict[str, Any]) -> None:
    if source["dirty"] is not False or any(
        digest(root / p) != sha for p, sha in source["sha256"].items()
    ):
        raise ArithmeticError("pipeline originally-clean source changed")


def replay_own(
    root: Path, path: Path
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    cases, protocol, training = own.inputs(root, saved["config"])
    if (
        saved["format"] != own.FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["training_performed"] is not False
        or saved["strength_comparison_performed"] is not False
        or not {
            *own.ENTRIES,
            own.CONFIG,
            "src/poker_ai/postflop/controlled_scoring.py",
            "src/poker_ai/postflop/controlled_checkpoints.py",
            "src/poker_ai/postflop/pipeline_cost.py",
            "src/poker_ai/postflop/pipeline_render.py",
            "src/poker_ai/postflop/pipeline_report.py",
            "src/poker_ai/solver_validation/controlled_pipeline.py",
        }.issubset(saved["source"]["sha256"])
    ):
        raise ArithmeticError("partial/changed own pipeline header")
    check_source(root, saved["source"])
    own.validate_batches(saved, cases)
    profiles = own.load_bundle(path, saved)
    matrices = own.contexts(root, protocol["future_comparison"])
    if not same([d["index"] for d in profiles], list(range(16))):
        raise ArithmeticError("own profile order/inventory changed")
    maximum = 0.0
    for index, (case, detail) in enumerate(zip(cases, profiles, strict=True)):
        context = matrices[case["spot_file"], case["representation"]]
        policy = own.source_policy(context, case)
        stored = unpack_policy(context.partition, detail["policy"])
        if stored.tobytes() != policy.tobytes():
            raise ArithmeticError("own calibration policy differs from old source")
        score = context.score(policy, tolerance=saved["config"]["tolerance_chips"])
        actual = dict(
            case={k: case[k] for k in own.CASE},
            metrics=score.metrics,
            responses=score.responses,
            replies=[
                {k: pack_policy(context.exact, v) for k, v in r.items()}
                for r in score.replies
            ],
            maximum_accounting_error=score.maximum_accounting_error,
            policy=pack_policy(context.partition, policy),
            index=index,
        )
        maximum = max(maximum, compare(actual, detail))
        metadata = {
            k: detail[k]
            for k in (
                "case",
                "metrics",
                "responses",
                "replies",
                "maximum_accounting_error",
            )
        }

        sha = hashlib.sha256(
            json.dumps(
                metadata, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        policy_sha = hashlib.sha256(
            np.asarray(policy, dtype="<f8").tobytes()
        ).hexdigest()
        for event in own.cell_events(saved):
            row = event["row"]
            if row["index"] == index:
                maximum = max(
                    maximum,
                    compare(row["metrics"], score.metrics),
                    compare(row["responses"], score.responses),
                    abs(row["accounting_error"] - score.maximum_accounting_error),
                )
                if (
                    row["metadata_sha256"] != sha
                    or row["receipt"]["policy_sha256"] != policy_sha
                ):
                    raise ArithmeticError(
                        "own calibration metadata/policy binding changed"
                    )
    if maximum > saved["config"]["tolerance_chips"]:
        raise ArithmeticError("own pipeline metrics/replies changed")
    if len(saved["fixtures"]) != 3:
        raise ArithmeticError("missing full-size IO fixture repeats")
    for fixture in saved["fixtures"]:
        if (
            fixture["scope"] != SCOPE
            or not same(fixture["rows"], 840)
            or not same(fixture["unique_source_profiles"], 16)
            or not same(fixture["figures"], 8)
            or not finite(fixture["seconds"], positive=True)
            or not finite(fixture["cpu_seconds"])
            or len(fixture["artifacts"]) != 11
            or any(
                type(a["bytes"]) is not int
                or a["bytes"] <= 0
                or not isinstance(a["sha256"], str)
                or len(a["sha256"]) != 64
                for a in fixture["artifacts"].values()
            )
        ):
            raise ArithmeticError("synthetic IO fixture coverage/cost changed")
    observed = math.fsum(b["seconds"] for b in saved["batches"]) + math.fsum(
        f["seconds"] for f in saved["fixtures"]
    )
    if (
        not finite(saved["seconds"], positive=True)
        or observed > saved["seconds"] + 1e-6
        or saved["seconds"] > saved["config"]["own_calibration_maximum_seconds"]
        or not finite(saved["parent_cpu_seconds"])
        or not finite(saved["reaped_children_cpu_seconds"])
        or saved["reaped_children_cpu_seconds"] + 0.05
        < math.fsum(b["reaped_children_cpu_seconds"] for b in saved["batches"])
        or saved["parent_cpu_seconds"] + 1e-6
        < math.fsum(b["parent_cpu_seconds"] for b in saved["batches"])
        + math.fsum(f["cpu_seconds"] for f in saved["fixtures"])
    ):
        raise ArithmeticError("own calibration elapsed/CPU accounting changed")
    return saved, profiles, cases, protocol, training


def residuals(batches: list[dict[str, Any]]) -> tuple[float, float]:
    worker = max(
        w["messages"][-1]["seconds"]
        - math.fsum(e["row"]["seconds"] for e in w["messages"] if e["kind"] == "cell")
        for b in batches
        for w in b["workers"]
    )
    launch = max(
        b["seconds"] - max(w["messages"][-1]["seconds"] for w in b["workers"])
        for b in batches
    )
    if worker < -1e-6 or launch < -1e-6:
        raise ArithmeticError("negative pipeline overhead residual")
    return worker, launch


def group_costs(saved: dict[str, Any]) -> dict[tuple[str, str], float]:
    """Worst observed case/repeat, retaining all old full/sampled source profiles."""
    result: dict[tuple[str, str], float] = {}
    for event in own.cell_events(saved):
        row = event["row"]
        group = row["case"]["spot_file"], row["case"]["representation"]
        result[group] = max(result.get(group, 0.0), row["seconds"])
    return result


def own_forecast(
    saved: dict[str, Any], protocol: dict[str, Any], training: dict[str, Any]
) -> dict[str, Any]:
    config = saved["config"]
    workload = cells(protocol["future_comparison"])
    cost = group_costs(saved)
    train = training["forecasts"]["3"]
    sums = [
        train["worker_training_seconds"][slot]
        + math.fsum(
            2
            * config["future_checkpoints_per_cell"]
            * cost[cell["spot_file"], cell["representation"]]
            for index, cell in enumerate(workload)
            if index % 3 == slot
        )
        for slot in range(3)
    ]
    worker, launch = residuals(saved["batches"])
    parent = (
        saved["seconds"]
        - math.fsum(b["seconds"] for b in saved["batches"])
        - math.fsum(f["seconds"] for f in saved["fixtures"])
    )
    fixture = max(f["seconds"] for f in saved["fixtures"])
    training_extra = (
        train["maximum_worker_nontraining_seconds"]
        + train["maximum_launch_collection_seconds"]
    )
    known = max(sums) + training_extra + worker + launch + parent + fixture
    guarded = config["forecast_guard_multiplier"] * known
    return dict(
        worker_training_scoring_replay_seconds=sums,
        training_overhead_seconds=training_extra,
        scoring_worker_preparation_seconds=worker,
        scoring_launch_collection_seconds=launch,
        parent_input_bundle_validation_seconds=parent,
        full_size_fixture_maximum_seconds=fixture,
        unguarded_seconds=known,
        guarded_seconds=guarded,
        cap_seconds=config["forecast_own_cap_seconds"],
        group_maximum_seconds=[
            dict(spot_file=k[0], representation=k[1], seconds=v)
            for k, v in sorted(cost.items())
        ],
        decision="own_pipeline_forecast_exceeds_cap"
        if guarded > config["forecast_own_cap_seconds"]
        else "forecast_fits_requires_separate_checked_learning_runner",
        training_admitted=False,
        strength_comparison_performed=False,
    )


def native_forecast(
    saved: dict[str, Any], native: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    workload = cells(protocol["future_comparison"])
    cost, replay = group_costs(native), group_costs(saved)
    sums = [
        math.fsum(
            saved["config"]["future_checkpoints_per_cell"]
            * (cost[cell["spot_file"], cell["representation"]])
            for i, cell in enumerate(workload)
            if i % 3 == slot
        )
        for slot in range(3)
    ]
    worker, launch = residuals(native["batches"])
    parent = native["seconds"] - math.fsum(b["seconds"] for b in native["batches"])
    serial_replay = math.fsum(
        saved["config"]["future_checkpoints_per_cell"]
        * replay[cell["spot_file"], cell["representation"]]
        for cell in workload
    )
    known = max(sums) + serial_replay + worker + launch + parent
    guarded = saved["config"]["forecast_guard_multiplier"] * known
    return dict(
        worker_native_seconds=sums,
        serial_own_input_replay_seconds=serial_replay,
        native_worker_preparation_seconds=worker,
        native_launch_collection_seconds=launch,
        native_parent_validation_seconds=parent,
        unguarded_seconds=known,
        guarded_seconds=guarded,
        cap_seconds=saved["config"]["forecast_native_cap_seconds"],
        decision="native_pipeline_forecast_exceeds_cap"
        if guarded > saved["config"]["forecast_native_cap_seconds"]
        else "forecast_fits_comparison_only",
        training_admitted=False,
        strength_comparison_performed=False,
    )


def summary(root: Path, own_path: Path, native_path: Path) -> dict[str, Any]:
    saved, profiles, cases, protocol, training = replay_own(root, own_path)
    native: dict[str, Any] = json.loads(native_path.read_text())
    json.dumps(native, allow_nan=False)
    if (
        native["format"] != "poker-ai-saved-own-pipeline-native-cost-v1"
        or native["status"] != "completed"
        or native["failure"] is not None
        or native["input_sha256"] != digest(own_path)
        or native["details_sha256"] != saved["details_sha256"]
        or not same(native["reference"], saved["config"]["native_reference"])
        or native["training_performed"] is not False
        or native["reference_actions_exported"] is not False
        or not {
            *own.ENTRIES,
            own.CONFIG,
            "src/poker_ai/solver_validation/controlled_pipeline.py",
        }.issubset(native["source"]["sha256"])
    ):
        raise ArithmeticError("changed/partial native pipeline header")
    check_source(root, native["source"])
    # The native stage intentionally uses the same complete timing/event schema;
    # its specialized scalar checks do not import native code into this reporter.
    from poker_ai.postflop.pipeline_native_checks import validate_native

    validate_native(native, saved, profiles, cases)
    own_f, native_f = (
        own_forecast(saved, protocol, training),
        native_forecast(saved, native, protocol),
    )
    return dict(
        own_sha256=digest(own_path),
        native_sha256=digest(native_path),
        own_cases=48,
        native_cases=48,
        unique_old_profiles=16,
        own_seconds=saved["seconds"],
        native_seconds=native["seconds"],
        own_aggregate_cpu_seconds=saved["parent_cpu_seconds"]
        + saved["reaped_children_cpu_seconds"],
        native_aggregate_cpu_seconds=native["parent_cpu_seconds"]
        + native["reaped_children_cpu_seconds"],
        own_forecast=own_f,
        native_forecast=native_f,
        maximum_native_error_chips=max(
            e["row"]["maximum_error_chips"] for e in own.cell_events(native)
        ),
        maximum_fixture_seconds=max(f["seconds"] for f in saved["fixtures"]),
        synthetic_fixture_scope=SCOPE,
        training_admitted=False,
        training_performed=False,
        decision="forecasts_fit_requires_separate_checked_learning_runner"
        if own_f["guarded_seconds"] <= own_f["cap_seconds"]
        and native_f["guarded_seconds"] <= native_f["cap_seconds"]
        else "pipeline_forecast_exceeds_declared_cap",
    )


def tables(report: dict[str, Any]) -> str:
    lines = [
        "# Saved-own-policy pipeline calibration",
        "",
        "Old own policies only: 16 unique profiles, "
        "48 own cases and 48 native comparisons.",
        "No new learning or strength result. "
        "The 840-row IO fixture is explicitly synthetic.",
        "",
        "| Stage | Actual calibration wall (s) | Aggregate CPU (s) | "
        "Guarded future forecast (s) | Cap (s) |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("own", "native"):
        f = report[name + "_forecast"]
        lines.append(
            f"| {name} | {report[name + '_seconds']:.3f} | "
            f"{report[name + '_aggregate_cpu_seconds']:.3f} | "
            f"{f['guarded_seconds']:.3f} | {f['cap_seconds']} |"
        )
    lines += [
        "",
        "Maximum native scalar error: "
        f"{report['maximum_native_error_chips']:.3g} chips.",
        f"Decision: {report['decision']}.",
        "No automatic learning admission, default, river-cause or global claim.",
    ]
    return "\n".join(lines) + "\n"
