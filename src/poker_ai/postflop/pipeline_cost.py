"""Cost calibration of saved OWN policies; never perform a training update."""

import gzip
import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import default_rng

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import FloatArray
from poker_ai.postflop import parallel_profile
from poker_ai.postflop.cell_process import THREAD_ENV, Send, partition, run_batch
from poker_ai.postflop.controlled_checkpoints import (
    diagnostics,
    pack_policy,
    read_snapshot,
    write_snapshot,
)
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_protocol import (
    CANDIDATE,
    build_representation_control,
    range_context,
)
from poker_ai.postflop.range_reply import load_inputs as load_saved
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.row_profile import fingerprint
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/controlled-pipeline-check.json"
ENTRIES = (
    "scripts/profile_controlled_pipeline.py",
    "scripts/audit_controlled_pipeline.py",
    "scripts/report_controlled_pipeline.py",
)
FORMAT = "poker-ai-saved-own-pipeline-cost-v1"
DETAIL_FORMAT = "poker-ai-saved-own-pipeline-profiles-v1"
CASE = ("spot_file", "representation", "training", "seed", "range_context_sha256")
METRICS = (
    "exact_exploitability_chips",
    "within_partition_gain_chips",
    "extra_information_gap_chips",
    "river_only_gain_exact_prefix_chips",
    "value_player_zero_chips",
)


def identity(case: dict[str, Any]) -> str:
    return json.dumps({k: case[k] for k in CASE}, sort_keys=True)


def inputs(
    root: Path, config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    fixed = dict(
        schema_version=1,
        status="saved_own_policy_pipeline_calibration_no_new_learning",
        worker_count=3,
        repetitions=3,
        own_calibration_maximum_seconds=1200,
        native_calibration_maximum_seconds=1200,
        forecast_own_cap_seconds=7200,
        forecast_native_cap_seconds=3600,
        forecast_guard_multiplier=2.0,
        future_policy_count=840,
        future_checkpoints_per_cell=6,
        tolerance_chips=1e-9,
        parallel_profile="results/parallel-cell-profile/profile.json",
        saved_policy_config="configs/range-mass-reply-diagnosis.json",
    )
    if (
        any(not parallel_profile.same(config[k], v) for k, v in fixed.items())
        or len(config["input_sha256"]) != 10
        or any(digest(root / p) != sha for p, sha in config["input_sha256"].items())
        or not parallel_profile.same(config, json.loads((root / CONFIG).read_text()))
    ):
        raise ArithmeticError("pipeline calibration config/prerequisite changed")
    _, forecast = parallel_profile.report(root, root / config["parallel_profile"])
    protocol = json.loads((root / "configs/training-isolation.json").read_text())
    comparison = protocol["future_comparison"]
    saved_config = json.loads((root / config["saved_policy_config"]).read_text())
    _, all_profiles = load_saved(root, saved_config)
    old = json.loads((root / "results/range-mass-replies/diagnosis.json").read_text())
    cases = []
    for record in all_profiles:
        if record["representation"] not in comparison["representations"]:
            continue
        peer = next(r for r in old["cases"] if all(r[k] == record[k] for k in CASE))
        cases.append(
            {
                **record,
                "source_metrics": dict(
                    exact_exploitability_chips=peer["exact_exploitability_chips"],
                    within_partition_gain_chips=peer["restricted_exploitability_chips"],
                    extra_information_gap_chips=peer["extra_information_chips"],
                    value_player_zero_chips=peer["saved_value_player_zero_chips"],
                ),
            }
        )
    cases.sort(
        key=lambda r: (
            r["spot_file"],
            r["representation"],
            r["training"],
            r["seed"] or 0,
        )
    )
    expected = {
        (game, name, training, seed)
        for game in comparison["spot_files"]
        for name in comparison["representations"]
        for training, seeds in (("full", [None]), ("sampled", comparison["seeds"]))
        for seed in seeds
    }
    found = [
        (r["spot_file"], r["representation"], r["training"], r["seed"]) for r in cases
    ]
    if len(cases) != 16 or len(set(found)) != 16 or set(found) != expected:
        raise ArithmeticError("saved-own-policy selection changed")
    return cases, protocol, forecast


def contexts(
    root: Path, comparison: dict[str, Any]
) -> dict[tuple[str, str], ScoringContext]:
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    result = {}
    for game in comparison["spot_files"]:
        raw = SpotTree.build(load_spot(root / game))
        exact = MatrixTree.build(raw)
        masks = (river_mask(exact, 0), river_mask(exact, 1))
        for name in comparison["representations"]:
            limited = (
                exact
                if name == "exact"
                else build_representation_control(raw, name, model)
            )
            result[game, name] = ScoringContext(
                exact, limited, limited.exact_to_abstract, masks
            )
    return result


def source_policy(context: ScoringContext, case: dict[str, Any]) -> FloatArray:
    if not isinstance(context.exact, MatrixTree):
        raise ValueError("saved poker profile requires its matrix source")
    expected = (
        range_context(context.exact.source.spot).identifier
        if case["representation"] == CANDIDATE
        else None
    )
    if case["range_context_sha256"] != expected:
        raise ArithmeticError("saved range context changed")
    exact = context.exact.dense_exact(tuple(tuple(v) for v in case["policy"]))
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    limited = exact[first].copy()
    if context.expand(limited).tobytes() != exact.tobytes():
        raise ArithmeticError("saved own profile violates its partition")
    return limited


def observation_cost_fixture(context: ScoringContext, policy: FloatArray) -> None:
    """Time observer array reads using explicit NONTRAINED diagnostic fixtures.

    Old final policy files do not contain controlled-trainer regret arrays. Same-
    shape copies of the old policy stand in for regret/average storage; half the
    keys stand in for visited-key lookups. No resulting norm/coverage is a learning
    metric. No initialization/update or random draw occurs. This also includes two
    state fingerprints and a read-only policy copy as in the real observer.
    """
    dummy = ControlledTrainer(context.partition, default_rng(0))
    dummy.regrets = policy.copy()
    dummy.strategy_sum = policy.copy()
    dummy.sampled_keys = set(dummy.tree.keys[::2])
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    river = (context.river_masks[0] | context.river_masks[1])[first]
    fingerprint(dummy)
    exported = dummy.average_policy.copy()
    exported.flags.writeable = False
    diagnostics(dummy, river)
    fingerprint(dummy)


def own_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root = Path(payload["root"])
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    matrices = contexts(root, payload["comparison"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    for index in indices:
        deadline.check()
        case = payload["cases"][index]
        context = matrices[case["spot_file"], case["representation"]]
        policy = source_policy(context, case)
        started, cpu = time.perf_counter(), time.process_time()
        observation_cost_fixture(context, policy)
        score = context.score(policy, tolerance=payload["config"]["tolerance_chips"])
        if (
            max(
                abs(score.metrics[k] - value)
                for k, value in case["source_metrics"].items()
            )
            > payload["config"]["tolerance_chips"]
        ):
            raise ArithmeticError("published own saved-policy metrics changed")
        metadata = dict(
            case={k: case[k] for k in CASE},
            metrics=score.metrics,
            responses=score.responses,
            replies=[
                {k: pack_policy(context.exact, v) for k, v in row.items()}
                for row in score.replies
            ],
            maximum_accounting_error=score.maximum_accounting_error,
        )
        path = (
            Path(payload["scratch"])
            / f"repeat-{payload['repeat']}"
            / f"case-{index}.json.gz"
        )
        receipt = write_snapshot(path, context.partition, policy, metadata)
        replay = read_snapshot(path, context.partition, receipt, metadata)
        if replay.tobytes() != policy.tobytes():
            raise ArithmeticError("saved own policy did not round trip exactly")
        elapsed, consumed = time.perf_counter() - started, time.process_time() - cpu
        row = dict(
            index=index,
            case={k: case[k] for k in CASE},
            metrics=score.metrics,
            responses=score.responses,
            accounting_error=score.maximum_accounting_error,
            receipt=receipt,
            metadata_sha256=hashlib.sha256(
                json.dumps(
                    metadata, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest(),
            seconds=elapsed,
            cpu_seconds=consumed,
        )
        event = dict(kind="cell", index=index, row=row)
        if payload["repeat"] == 0:
            event["detail"] = {
                **metadata,
                "policy": pack_policy(context.partition, policy),
                "index": index,
            }
        send(event)
    return dict(cells=len(indices))


def cell_events(saved: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        e
        for b in saved["batches"]
        for w in b["workers"]
        for e in w["messages"]
        if e["kind"] == "cell"
    ]


def validate_batches(saved: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    """Complete 3x16 old-policy gate, including exact repeat artifact digests."""
    batches = saved["batches"]
    if len(batches) != 3 or not parallel_profile.same(
        [b["repeat"] for b in batches], [0, 1, 2]
    ):
        raise ArithmeticError("incomplete own pipeline repeat grid")
    expected = partition(16, 3)
    hashes: dict[int, tuple[str, str, str]] = {}
    count = 0
    for batch in batches:
        if (
            batch["status"] != "completed"
            or batch["failure"] is not None
            or not parallel_profile.same(batch["worker_count"], 3)
            or not parallel_profile.same(batch["assignments"], expected)
            or len(batch["workers"]) != 3
            or not all(
                parallel_profile.finite(batch[k], positive=(k == "seconds"))
                for k in (
                    "seconds",
                    "parent_cpu_seconds",
                    "reaped_children_cpu_seconds",
                )
            )
        ):
            raise ArithmeticError("partial/changed own pipeline batch")
        pids = []
        for slot, worker in enumerate(batch["workers"]):
            events = worker["messages"]
            if (
                not parallel_profile.same(worker["slot"], slot)
                or type(worker["pid"]) is not int
                or worker["pid"] <= 0
                or not parallel_profile.same(worker["exitcode"], 0)
                or [e["kind"] for e in events]
                != ["started", "prepared"] + ["cell"] * len(expected[slot]) + ["done"]
                or not parallel_profile.same(events[0]["pid"], worker["pid"])
                or events[0]["thread_environment"] != THREAD_ENV
                or not parallel_profile.finite(events[1]["seconds"])
                or not parallel_profile.finite(events[-1]["seconds"], positive=True)
                or not parallel_profile.finite(events[-1]["cpu_seconds"])
                or events[-1]["seconds"] > batch["seconds"] + 1e-6
                or not parallel_profile.same(
                    events[-1]["summary"], dict(cells=len(expected[slot]))
                )
            ):
                raise ArithmeticError("own worker setup/identity/events changed")
            pids.append(worker["pid"])
            measured = events[1]["seconds"]
            for index, event in zip(expected[slot], events[2:-1], strict=True):
                row, case = event["row"], cases[index]
                if (
                    not parallel_profile.same(event["index"], index)
                    or not parallel_profile.same(row["index"], index)
                    or not parallel_profile.same(
                        row["case"], {k: case[k] for k in CASE}
                    )
                    or set(row["metrics"]) != set(METRICS)
                    or not all(
                        type(v) in (int, float) and math.isfinite(v)
                        for v in row["metrics"].values()
                    )
                    or max(
                        abs(row["metrics"][k] - v)
                        for k, v in case["source_metrics"].items()
                    )
                    > saved["config"]["tolerance_chips"]
                    or not parallel_profile.finite(row["seconds"], positive=True)
                    or not parallel_profile.finite(row["cpu_seconds"])
                    or not parallel_profile.finite(row["accounting_error"])
                    or row["accounting_error"] > saved["config"]["tolerance_chips"]
                    or type(row["receipt"]["bytes"]) is not int
                    or row["receipt"]["bytes"] <= 0
                    or any(
                        type(row[k]) is not str or len(row[k]) != 64
                        for k in ("metadata_sha256",)
                    )
                ):
                    raise ArithmeticError(
                        "saved-policy metric/roundtrip/timer mismatch"
                    )
                signature = (
                    row["receipt"]["sha256"],
                    row["receipt"]["policy_sha256"],
                    row["metadata_sha256"],
                )
                if (
                    any(not isinstance(s, str) or len(s) != 64 for s in signature)
                    or hashes.setdefault(index, signature) != signature
                ):
                    raise ArithmeticError(
                        "own policy or metric bits changed between repeats"
                    )
                measured += row["seconds"]
                count += 1
            if measured > events[-1]["seconds"] + 1e-6:
                raise ArithmeticError("own worker timer omits measured cells")
        if len(set(pids)) != 3:
            raise ArithmeticError("own workers do not have distinct PIDs")
    if count != 48:
        raise ArithmeticError("incomplete 48 own calibration cases")


def load_bundle(path: Path, saved: dict[str, Any]) -> list[dict[str, Any]]:
    bundle = path.parent / saved["details_file"]
    if digest(bundle) != saved["details_sha256"]:
        raise ArithmeticError("own pipeline profiles changed")
    data = json.loads(gzip.decompress(bundle.read_bytes()))
    if data["format"] != DETAIL_FORMAT or len(data["profiles"]) != 16:
        raise ArithmeticError("own pipeline profile bundle incomplete")
    return cast(list[dict[str, Any]], data["profiles"])


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain own pipeline calibration")
    started, parent_cpu, child_times = (
        time.perf_counter(),
        time.process_time(),
        os.times(),
    )
    config = json.loads((root / CONFIG).read_text())
    cases, protocol, _ = inputs(root, config)
    source = source_provenance(root, root / CONFIG, entrypoints=ENTRIES)
    if source["dirty"] is not False:
        raise ValueError("publish checked pipeline code before calibration")
    deadline = Deadline(config["own_calibration_maximum_seconds"])
    deadline.started = started
    scratch = root / "results/runs/controlled-pipeline-check" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        environment=runtime_environment(),
        batches=[],
        fixtures=[],
        scratch=str(scratch),
        seconds=0.0,
        training_performed=False,
        strength_comparison_performed=False,
        details_file=None,
        details_sha256=None,
        diagnostic_timing_fixture=(
            "same-shape old-policy arrays and half-key lookup set; "
            "no trained diagnostic values claimed"
        ),
    )

    def persist() -> None:
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - parent_cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - child_times.children_user
            - child_times.children_system
        )
        tmp = output.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(saved, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        tmp.replace(output)

    try:
        for repeat in range(3):
            batch: dict[str, Any] = {}
            saved["batches"].append(batch)
            payload = dict(
                root=str(root),
                cases=cases,
                comparison=protocol["future_comparison"],
                config=config,
                remaining_seconds=config["own_calibration_maximum_seconds"]
                - (time.perf_counter() - started),
                scratch=str(scratch),
                repeat=repeat,
            )
            try:
                run_batch(16, 3, own_job, payload, deadline, batch)
            finally:
                batch["repeat"] = repeat
            persist()
            print(f"old-own scoring/roundtrip repeat {repeat + 1}/3", flush=True)
        validate_batches(saved, cases)
        details = sorted(
            [e["detail"] for e in cell_events(saved) if "detail" in e],
            key=lambda d: d["index"],
        )
        bundle = output.with_name(output.stem + "-profiles.json.gz")
        if bundle.exists():
            raise FileExistsError("retain own pipeline profiles")
        bundle.write_bytes(
            gzip.compress(
                json.dumps(
                    dict(format=DETAIL_FORMAT, profiles=details),
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode(),
                mtime=0,
            )
        )
        saved.update(details_file=bundle.name, details_sha256=digest(bundle))
        # Only the unique 16 owned profiles belong in the bundle. Timing events
        # retain hashes and scalar metrics, without three duplicate large arrays.
        for event in cell_events(saved):
            event.pop("detail", None)
        from poker_ai.postflop.pipeline_render import fixture

        for repeat in range(3):
            deadline.check()
            saved["fixtures"].append(
                fixture(root, protocol, details, scratch / f"io-fixture-{repeat}")
            )
            deadline.check()
            persist()
        inputs(root, config)
        if any(
            digest(root / p) != sha
            for p, sha in cast(dict[str, str], source["sha256"]).items()
        ):
            raise ArithmeticError("pipeline source changed")
        deadline.check()
        saved["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        saved["status"] = "incomplete"
        saved["failure"] = dict(type=type(error).__name__, reason=str(error))
    finally:
        persist()
    return saved
