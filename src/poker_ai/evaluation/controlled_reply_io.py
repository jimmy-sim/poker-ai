"""Atomic receipts and streamed all-row replay for frozen controlled policies."""

import gzip
import json
import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from poker_ai.evaluation import controlled_reply_compute as calculation
from poker_ai.evaluation.controlled_reply_inputs import (
    CONFIG,
    ENTRIES,
    FORMAT,
    TRACE_FORMAT,
    Inputs,
    config_inputs,
    load,
)
from poker_ai.evaluation.controlled_reply_traces import (
    COLUMNS,
    compare_record,
    public_streets,
    validate_record,
)
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain controlled reply attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = config_inputs(root)
    deadline = Deadline(config["maximum_own_seconds"])
    deadline.started = started
    provenance = source(root)
    if provenance["dirty"] is not False:
        raise ValueError("publish checked source before controlled reply measurement")
    data = load(root)
    deadline.check()
    output.parent.mkdir(parents=True, exist_ok=True)
    archive = output.with_name(output.stem + "-traces.jsonl.gz")
    temporary = archive.with_suffix(".tmp")
    if archive.exists() or temporary.exists():
        raise FileExistsError("retain complete/partial controlled reply traces")
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=provenance,
        environment=runtime_environment(),
        source_report_sha256=digest(root / config["source_report"]),
        self_profiles=[],
        crosses=[],
        details_file=None,
        details_sha256=None,
        seconds=0.0,
        training_performed=False,
        reference_output_used_in_training=False,
        report=None,
    )

    def progress() -> None:
        saved["seconds"] = time.perf_counter() - started
        persist(output, saved)
        deadline.check()

    try:
        with (
            temporary.open("wb") as raw,
            gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as stream,
        ):
            stream.write(
                canonical(dict(format=TRACE_FORMAT, records=128, columns=list(COLUMNS)))
                + b"\n"
            )
            count = 0

            def emit(record: dict[str, Any]) -> None:
                nonlocal count
                stream.write(canonical(record) + b"\n")
                count += 1

            calculation.compute(data, deadline, emit, saved, progress)
            if count != 128:
                raise ArithmeticError("within trace count incomplete")
        temporary.replace(archive)
        saved.update(details_file=archive.name, details_sha256=digest(archive))
        calculation.validate(saved, data)
        # Read the serialized rows too, not only the in-memory generation objects.
        if sum(1 for _ in trace_records(output, saved, data)) != 128:
            raise ArithmeticError("serialized trace inventory incomplete")
        deadline.check()
        from poker_ai.evaluation.controlled_reply_report import write_report

        saved["report"] = write_report(data, saved, output.parent / "report")
        if (
            saved["report"]["source_profiles"] != 64
            or saved["report"]["target_traces"] != 128
            or saved["report"]["crossed_target_conditions"] != 512
            or len(saved["report"]["figures"]) != 4
        ):
            raise ArithmeticError("controlled reply report inventory incomplete")
        deadline.check()
        saved["status"] = "completed_own_native_pending"
    except BaseException as error:
        saved["status"] = "incomplete"
        saved["failure"] = dict(type=type(error).__name__, reason=str(error))
        raise
    finally:
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - children.children_user
            - children.children_system
        )
        persist(output, saved)
    return saved


def trace_records(
    path: Path, saved: dict[str, Any], data: Inputs
) -> Iterator[dict[str, Any]]:
    name = saved["details_file"]
    if not isinstance(name, str) or Path(name).name != name:
        raise ArithmeticError("trace archive path changed")
    archive = path.with_name(name)
    if digest(archive) != saved["details_sha256"]:
        raise ArithmeticError("trace archive hash changed")
    with gzip.open(archive, "rt") as stream:
        header = json.loads(next(stream))
        if not same(
            header, dict(format=TRACE_FORMAT, records=128, columns=list(COLUMNS))
        ):
            raise ArithmeticError("trace archive schema/inventory changed")
        summaries = {item["id"]: item["responses"] for item in saved["self_profiles"]}
        for profile in data.policies:
            context = data.context(profile.case)
            streets = public_streets(context)
            for target in (0, 1):
                line = stream.readline()
                if not line:
                    raise ArithmeticError("trace archive truncated")
                record = json.loads(line)
                if record["summary"]["profile_id"] != profile.identifier or not same(
                    record["summary"]["target"], target
                ):
                    raise ArithmeticError("trace archive profile/target order changed")
                if not same(record["summary"], summaries[profile.identifier][target]):
                    raise ArithmeticError("trace summary differs from own receipt")
                validate_record(
                    record, profile, context, streets, data.config["tolerance_chips"]
                )
                yield record
        if stream.read():
            raise ArithmeticError("trace archive contains extra records")


def read_saved(root: Path, path: Path) -> tuple[dict[str, Any], Inputs]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = config_inputs(root)
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or saved["training_performed"] is not False
        or saved["reference_output_used_in_training"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= config["maximum_own_seconds"]
        or saved["source_report_sha256"] != digest(root / config["source_report"])
    ):
        raise ArithmeticError("incomplete/changed controlled reply receipt")
    check_source(root, saved["source"])
    data = load(root)
    calculation.validate(saved, data)
    return saved, data


def replay(
    root: Path, path: Path, deadline: Deadline | None = None
) -> tuple[dict[str, Any], Inputs, dict[str, Any]]:
    started = time.perf_counter()
    deadline = deadline or Deadline(900)
    saved, data = read_saved(root, path)
    stream = trace_records(path, saved, data)
    maximum, count = 0.0, 0

    def emit(actual: dict[str, Any]) -> None:
        nonlocal maximum, count
        deadline.check()
        try:
            recorded = next(stream)
        except StopIteration as error:
            raise ArithmeticError("replay trace stream ended early") from error
        maximum = max(
            maximum,
            compare_record(
                actual,
                recorded,
                data.config["tolerance_chips"],
                data.config["tolerance_unitless"],
            ),
        )
        count += 1

    actual: dict[str, Any] = dict(self_profiles=[], crosses=[])
    calculation.compute(data, deadline, emit, actual, lambda: None)
    if next(stream, None) is not None:
        raise ArithmeticError("replay has unused trace records")
    maximum = max(maximum, compare(actual, {k: saved[k] for k in actual}))
    if maximum > data.config["tolerance_chips"] or count != 128:
        raise ArithmeticError("controlled reply replay changed")
    deadline.check()
    return (
        saved,
        data,
        dict(
            status="all_controlled_reply_rows_replayed",
            target_traces=count,
            maximum_error_chips=maximum,
            seconds=time.perf_counter() - started,
        ),
    )
