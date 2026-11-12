"""No-training IO/score stand-ins from pinned OWN full-control policies only."""

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.evaluation.compact_sampled_prior import verify
from poker_ai.finite import FloatArray
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_full_run import check_runtime, runtime
from poker_ai.postflop.compact_sampled_state import table, unpack
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.toy.analysis import evaluate

FORMAT = "compact-sampled-own-cost-v1"
STATE = "compact-sampled-cost-standin-v1"


def scalar(context: Context, policy: FloatArray) -> dict[str, float]:
    result = evaluate(context.scoring.exact, context.scoring.expand(policy))
    return dict(
        value_player_zero_chips=result.value_player_zero,
        best_response_zero_chips=result.best_response_zero,
        best_response_one_chips=result.best_response_one,
        exploitability_chips=result.exploitability,
        exploitability_pot=result.exploitability / context.pot,
    )


def full_profiles(root: Path) -> dict[tuple[Any, ...], dict[str, Any]]:
    path = root / "results/compact-full-control/own.json"
    saved = json.loads(path.read_text())
    return {tuple(r[k] for k in files.IDENTITY): r for r in saved["rows"]}


def standin(
    root: Path,
    context: Context,
    case: dict[str, Any],
    label: int,
    index: int,
    fingerprint: str,
    full: dict[tuple[Any, ...], dict[str, Any]],
) -> dict[str, Any]:
    position = inputs.labels(root, "cost").index(label)
    iteration = inputs.protocol(root)["full_cost_source_iterations"][position]
    original = full[case["spot_file"], case["representation"], iteration]
    raw = files.load_snapshot(
        root / "results/compact-full-control/snapshots", original["snapshot"]
    )
    files.decode(context, raw)
    tree = context.scoring.partition
    policy = table(tree, np.asarray(raw["policy"], dtype=np.float64), signed=False)
    regrets = table(tree, np.asarray(raw["regrets"], dtype=np.float64), signed=True)
    average = table(
        tree, np.asarray(raw["strategy_sum"], dtype=np.float64), signed=False
    )
    return dict(
        format=STATE,
        scope="cost",
        source_fingerprint=fingerprint,
        **case,
        path_index=index,
        work_checkpoint=label,
        binding=context.binding,
        full_source_identity={k: original[k] for k in files.IDENTITY},
        full_source_receipt=original["snapshot"],
        policies={name: policy for name in inputs.READOUTS},
        regrets=regrets,
        uniform_sum=average,
        linear_sum=average,
        cost_extra_mass=average,
        sampled_training_performed=False,
        scope_note=(
            "Old OWN full policy copied into three IO slots; NOT sampled books/readouts"
        ),
    )


def run(
    root: Path, output: Path, repetition: int, checks: Path, started: float
) -> dict[str, Any]:
    if type(repetition) is not int or repetition not in (0, 1, 2):
        raise ValueError("fixed cost repetitions0,1,2 required")
    directory = output.parent / (output.stem + "-states")
    if output.exists() or directory.exists():
        raise FileExistsError("retain prior cost outputs")
    saved: dict[str, Any] = dict(
        format=FORMAT,
        scope="cost",
        status="running",
        failure=None,
        source=inputs.source(root),
        runtime=runtime(),
        repetition=repetition,
        protocol_sha256=inputs.SPEC_SHA,
        actual_admission=False,
        fresh_global_admission=False,
        sampled_training_performed=False,
        learner_constructed=False,
        state_directory=directory.name,
        points=[],
        rows=[],
    )

    def clock() -> None:
        if time.perf_counter() - started >= 900:
            raise TimeoutError("complete nontraining cost cap")

    def persist() -> None:
        saved.update(
            seconds=time.perf_counter() - started,
            peak_process_rss_bytes=peak_rss_bytes(),
        )
        files.atomic(output, saved)

    try:
        persist()
        from poker_ai.evaluation.compact_sampled_gate import require_checks

        saved["checks"] = require_checks(root, checks)
        check_runtime(saved["runtime"], real=True)
        saved["prior_full"] = verify(root)
        lookup = inputs.game_contexts(root, "cost")
        full = full_profiles(root)
        for index, case in enumerate(inputs.cases(root, "cost")):
            context = lookup[case["spot_file"], case["representation"]]
            for label in inputs.labels(root, "cost"):
                clock()
                raw = standin(
                    root,
                    context,
                    case,
                    label,
                    index,
                    saved["source"]["fingerprint"],
                    full,
                )
                receipt = files.write_snapshot(
                    directory / f"{index:02d}-{label}.json.gz", raw
                )
                restored = files.load_snapshot(directory, receipt)
                if canonical(restored) != canonical(raw):
                    raise ArithmeticError("stand-in archive changed")
                point = dict(
                    **case,
                    path_index=index,
                    work_checkpoint=label,
                    context_sha256=context.context_sha256,
                    state_receipt=receipt,
                )
                saved["points"].append(point)
                for name in inputs.READOUTS:
                    policy = unpack(
                        context.scoring.partition, raw["policies"][name], signed=False
                    )
                    saved["rows"].append(
                        dict(**point, readout=name, **scalar(context, policy))
                    )
                persist()
        clock()
        inputs.check_source(root, saved["source"])
        saved["status"] = "completed"
        persist()
        saved["replay"] = replay(root, output)
        clock()
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        persist()
    return saved


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    if (
        saved["format"] != FORMAT
        or saved["scope"] != "cost"
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["sampled_training_performed"] is not False
        or saved["learner_constructed"] is not False
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
        or saved["protocol_sha256"] != inputs.SPEC_SHA
        or saved["state_directory"] != path.stem + "-states"
    ):
        raise ArithmeticError("complete nontraining cost scope required")
    inputs.check_source(root, saved["source"])
    check_runtime(saved["runtime"], real=True)
    if canonical(saved["prior_full"]) != canonical(verify(root)):
        raise ArithmeticError("cost prior full proof changed")
    lookup = inputs.game_contexts(root, "cost")
    full = full_profiles(root)
    rows = []
    points = saved["points"]
    expected_points = inputs.expected(root, "cost", readouts=False)
    ids = [inputs.identity(p, inputs.POINT) for p in points]
    if len(ids) != 108 or len(set(ids)) != 108 or set(ids) != expected_points:
        raise ArithmeticError("cost108-slot inventory incomplete")
    for point in points:
        index = point["path_index"]
        case = inputs.cases(root, "cost")[index]
        if any(point[k] != case[k] for k in inputs.PATH):
            raise ArithmeticError("cost path identity changed")
        context = lookup[case["spot_file"], case["representation"]]
        raw = files.load_snapshot(
            path.parent / saved["state_directory"], point["state_receipt"]
        )
        expected = standin(
            root,
            context,
            case,
            point["work_checkpoint"],
            index,
            saved["source"]["fingerprint"],
            full,
        )
        if canonical(raw) != canonical(expected):
            raise ArithmeticError("cost source full policy changed")
        for name in inputs.READOUTS:
            policy = unpack(
                context.scoring.partition, raw["policies"][name], signed=False
            )
            rows.append(dict(**point, readout=name, **scalar(context, policy)))
    if canonical(rows) != canonical(saved["rows"]):
        raise ArithmeticError("cost IO/metric replay changed")
    return dict(
        raw_states_checked=108,
        readouts_checked=324,
        sampled_training_performed=False,
        learner_constructed=False,
        actual_admission=False,
    )


def policy_rows(
    root: Path, path: Path, saved: dict[str, Any]
) -> Iterator[tuple[Context, dict[str, Any], FloatArray]]:
    lookup = inputs.game_contexts(root, "cost")
    rows = {inputs.identity(r, inputs.IDENTITY): r for r in saved["rows"]}
    for point in saved["points"]:
        context = lookup[point["spot_file"], point["representation"]]
        raw = files.load_snapshot(
            path.parent / saved["state_directory"], point["state_receipt"]
        )
        for name in inputs.READOUTS:
            key = inputs.identity(dict(point, readout=name), inputs.IDENTITY)
            policy = unpack(
                context.scoring.partition, raw["policies"][name], signed=False
            )
            yield context, rows[key], context.scoring.expand(policy)
