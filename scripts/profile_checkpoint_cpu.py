"""Observe current checkpoint CPU without changing any scientific implementation.

The stdlib supervisor charges startup, every prerequisite, all original reads,
three reference workers, extraction and final writes. Own software evidence is
published first. Report mode reads saved data only and cannot train or solve.
"""

import argparse
import hashlib
import importlib
import json
import math
import os
import re
import resource
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from itertools import product
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/checkpoint-replay-cpu.json"
CONFIG_SHA = "8ff9c7352b33973097ef9bb1b0b5d357e166792af0668378df2c5be2761f8da7"
ENTRY = "scripts/profile_checkpoint_cpu.py"
SUPPORT = "scripts/checkpoint_cpu_support.py"
FOLDER = "results/checkpoint-replay-cpu"


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def contract(root: Path) -> dict[str, Any]:
    from poker_ai.evaluation.diagnostic_receipts import config

    return config(root, CONFIG, CONFIG_SHA)


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from compact_suit.source import source

    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    old = source(root, clean=clean)
    if (
        old["fingerprint"] != c["base_source_sha256"]
        or len(old["sha256"]) != c["base_source_files"]
    ):
        raise ArithmeticError("preserve all433 scientific source bytes")
    saved: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    saved["sha256"].update(old["sha256"])
    saved["fingerprint"] = sha(saved["sha256"])
    if (
        len(saved["sha256"]) != c["source_files"]
        or clean
        and saved["dirty"] is not False
    ):
        raise ArithmeticError("publish clean complete436-file observer source")
    if clean:
        commit_sources(root, saved["git_commit"], saved["sha256"])
    return c, saved


def checked(root: Path, source: dict[str, Any]) -> None:
    import trace_card_audit as original
    from compact_suit.admission import published

    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    checks(root, path, source)
    published(root, path)
    for row in json.loads(path.read_text())["checks"]:
        p = root / row["log"]["file"]
        published(root, p)
        text = p.read_text(encoding="utf-8-sig")
        py, np = ("3.11.17", "2.4.6") if row["minor"] == "311" else ("3.12.15", "2.5.4")
        if row["numpy"] != np:
            raise ArithmeticError("actual qualified NumPy required")
        if row["role"] == "hosted":
            original.actual_host_runtime(text, py, np)
        elif set(re.findall(r"ACTUAL_PYTHON=([0-9.]+)", text)) != {py} or set(
            re.findall(r"ACTUAL_NUMPY=([0-9.]+)", text)
        ) != {np}:
            raise ArithmeticError("actual qualified local runtime required")


def runtime(c: dict[str, Any]) -> None:
    import numpy as np

    if (
        sys.version.split()[0] != c["runtime"]["python"]
        or np.__version__ != c["runtime"]["numpy"]
    ):
        raise ArithmeticError("original Python3.11.17/NumPy2.4.6 required")


def terminal_value(tree: Any, policy: Any) -> float:
    """Independent terminal recursion, without ArrayTree value/edge operations."""

    def visit(node: int) -> float:
        owner = int(tree.player[node])
        if owner == -2:
            return float(tree.terminal_values[node])
        weights = (
            tree.chance_edges[node]
            if owner == -1
            else policy[int(tree.information[node])]
        )
        return math.fsum(
            float(weights[a]) * visit(int(tree.children[node, a]))
            for a, valid in enumerate(tree.valid[node])
            if valid
        )

    return visit(0)


def pure_reply(context: Any, policy: Any, target: int, *, exact: bool) -> float:
    """Enumerate pure choices by information group, then sum hidden histories."""
    import numpy as np

    tree = context.exact if exact else context.partition
    base = policy[context.exact_to_partition] if exact else policy
    owned = [i for i, owner in enumerate(tree.owners) if owner == target]
    values = []
    for choices in product(*(range(len(tree.actions[i])) for i in owned)):
        candidate = base.copy()
        for index, action in zip(owned, choices, strict=True):
            candidate[index] = np.eye(candidate.shape[1])[action]
        values.append((1 if target == 0 else -1) * terminal_value(tree, candidate))
    return max(values)


def own_math(output: Path) -> dict[str, Any]:
    """Fresh own tiny checkpoints; no learner or independent reference exists."""
    import checkpoint_cpu_support as observer_support
    import numpy as np

    from poker_ai.evaluation import opponent_learning_own as own
    from poker_ai.evaluation.opponent_learning_contexts import software_context
    from poker_ai.postflop import learning_artifacts as artifacts
    from poker_ai.postflop import learning_training as training
    from poker_ai.postflop.controlled_checkpoints import write_snapshot
    from poker_ai.postflop.controlled_scoring import ScoringContext

    name = "replay_snapshot"
    original = getattr(own, name)
    original_decode, original_score = artifacts.decode, ScoringContext.score
    cases = []
    maximum_error = 0.0
    for game in (0, 1):
        for kind, context in software_context(game).scoring.items():
            weights = np.arange(
                1, context.partition.legal.size + 1, dtype=np.float64
            ).reshape(context.partition.legal.shape)
            policy = context.partition.normalize(weights)
            score = context.score(policy)
            value = terminal_value(context.exact, policy[context.exact_to_partition])
            errors = [abs(value - score.metrics["value_player_zero_chips"])]
            for target in (0, 1):
                errors.extend(
                    [
                        abs(
                            pure_reply(context, policy, target, exact=True)
                            - score.responses[target]["exact_reply_value_chips"]
                        ),
                        abs(
                            pure_reply(context, policy, target, exact=False)
                            - score.responses[target]["restricted_reply_value_chips"]
                        ),
                    ]
                )
            maximum_error = max(maximum_error, *errors)
            metadata = dict(
                id=f"fictional-{game}-{kind}", **training.score_data(context, score)
            )
            path = output / "snapshots" / (metadata["id"] + ".json.gz")
            receipt = write_snapshot(path, context.partition, policy, metadata)
            row = dict(
                **metadata, receipt=receipt, metadata_sha256=artifacts.sha(metadata)
            )
            blob = path.read_bytes()
            cases.append((context, row, blob, original(context, row, blob, 1e-9)))
    observer = observer_support.Observer(enabled=True)
    actual = []
    with observer.hooks():
        for index in range(3):
            with observer.read(index):
                actual.append(
                    [
                        getattr(own, name)(ctx, row, blob, 1e-9)
                        for ctx, row, blob, _ in cases
                    ]
                )
    summaries = observer_support.validate_state(
        observer.state(),
        observer.reads,
        enabled=True,
        pid=os.getpid(),
        thread=threading.get_ident(),
        expected=8,
    )
    expected = [result for _, _, _, result in cases]
    if (
        actual != [expected] * 3
        or maximum_error > 1e-14
        or getattr(own, name) is not original
        or training.replay_snapshot is not original
        or artifacts.decode is not original_decode
        or ScoringContext.score is not original_score
    ):
        raise ArithmeticError("fresh own observer mathematical proof failed")
    return dict(
        status="eight_actual_own_checkpoints_independent_math_and_exact_replay",
        cases=8,
        maximum_independent_error=maximum_error,
        units="fictional signal-game payoff units; not Holdem chips",
        original_results=expected,
        instrumented_results=actual,
        observer_state=observer.state(),
        reads=observer.reads,
        summaries=summaries,
        reference_constructed=False,
        poker_training_performed=False,
    )


def proof(root: Path, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="running",
        admission_evidence=False,
        reference_constructed=False,
        poker_training_performed=False,
        pid=os.getpid(),
        thread=threading.get_ident(),
    )
    atomic(output / "child.json", saved)
    try:
        c, source = binding(root)
        checked(root, source)
        runtime(c)
        from poker_ai.evaluation.compact_opponent_guard import isolated

        with isolated(worker=False):
            own_proof = own_math(output)
        saved.update(source=source, config_sha256=CONFIG_SHA, proof=own_proof)
        after_c, after = binding(root, clean=False)
        if c != after_c or source["sha256"] != after["sha256"]:
            raise ArithmeticError("proof source changed")
        saved["raw_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in sorted((output / "snapshots").rglob("*"))
            if p.is_file()
        }
        saved.update(
            status="complete_own_only_observer_proof",
            seconds=time.perf_counter() - origin,
        )
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(status="failed_retained", failure_kind=type(error).__name__)
        atomic(output / "child.json", saved)
        raise


def own_published(root: Path, source: dict[str, Any]) -> dict[str, Any]:
    import checkpoint_cpu_support as support
    from compact_suit.admission import published
    from profile_compact_replay import authenticate_source

    folder = root / FOLDER / "software"
    saved = json.loads((folder / "child.json").read_text())
    measurement = json.loads((folder / "measurement.json").read_text())
    actual = saved["proof"]
    expected_snapshots = {
        f"snapshots/fictional-{game}-{kind}.json.gz"
        for game in (0, 1)
        for kind in ("coarse", "fine", "mixed0", "mixed1")
    }
    if set(saved["raw_sha256"]) != expected_snapshots or any(
        p.is_symlink() for p in folder.rglob("*")
    ):
        raise ArithmeticError("complete fresh eight-checkpoint inventory required")
    if {
        str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()
    } != expected_snapshots | {"child.json", "measurement.json", "command.log"}:
        raise ArithmeticError("unexpected own-proof raw member")
    if (
        actual["status"]
        != "eight_actual_own_checkpoints_independent_math_and_exact_replay"
        or type(actual["cases"]) is not int
        or actual["cases"] != 8
        or type(actual["maximum_independent_error"]) not in (int, float)
        or not math.isfinite(actual["maximum_independent_error"])
        or not 0 <= actual["maximum_independent_error"] <= 1e-14
        or actual["reference_constructed"] is not False
        or actual["poker_training_performed"] is not False
        or type(actual["original_results"]) is not list
        or len(actual["original_results"]) != 8
        or any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1e-9
            for v in actual["original_results"]
        )
    ):
        raise ArithmeticError("typed independent own mathematical proof required")
    if (
        saved["status"] != "complete_own_only_observer_proof"
        or saved["config_sha256"] != CONFIG_SHA
        or saved["source"]["sha256"] != source["sha256"]
        or saved["reference_constructed"] is not False
        or saved["poker_training_performed"] is not False
        or actual["cases"] != 8
        or actual["maximum_independent_error"] > 1e-14
        or actual["instrumented_results"] != [actual["original_results"]] * 3
        or type(measurement["returncode"]) is not int
        or measurement["returncode"] != 0
        or type(measurement["seconds"]) not in (int, float)
        or measurement["interrupted"] is not None
        or not 0 < measurement["seconds"] < 180
        or measurement["child_sha256"] != digest(folder / "child.json")
        or type(measurement["child_pid"]) is not int
        or measurement["child_pid"] != saved["pid"]
        or actual["observer_state"]["pid"] != saved["pid"]
        or actual["observer_state"]["thread"] != saved["thread"]
    ):
        raise ArithmeticError("publish complete fresh own-only observer proof first")
    for name, checksum in saved["raw_sha256"].items():
        path = folder / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(folder.resolve())
            or digest(path) != checksum
        ):
            raise ArithmeticError("fresh own snapshot bytes changed")
    authenticate_source(root, saved["source"])
    summaries = support.validate_state(
        actual["observer_state"],
        actual["reads"],
        enabled=True,
        pid=actual["observer_state"]["pid"],
        thread=actual["observer_state"]["thread"],
        expected=8,
    )
    if summaries != actual["summaries"]:
        raise ArithmeticError("own proof summaries changed")
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            published(root, path)
    return dict(
        file=str((folder / "child.json").relative_to(root)),
        sha256=digest(folder / "child.json"),
    )


def numerical_identity(
    saved: dict[str, Any], replays: list[dict[str, Any]]
) -> dict[str, Any]:
    """Every scalar/replay and semantic counter; OS identities are separate."""
    from compact_suit.contract import CONFIG_SHA as base_config

    from poker_ai.evaluation.opponent_learning_design import COST, TOY

    if (
        saved["status"] != "completed_scalar_comparison"
        or saved["failure"] is not None
        or saved["scope"] != COST
        or type(saved["repetition"]) is not int
        or saved["repetition"] != 0
        or len(saved["profiles"]) != 432
        or len(saved["fixed_conditions"]) != 1152
        or [r["scope"] for r in replays] != [TOY, COST, COST]
        or replays[1] != replays[2]
        or any(
            r["computed"]["unique_profiles"] != 432
            or r["computed"]["fixed_conditions"] != 1152
            or r["computed"]["policy_and_ledger_bits_exact"] is not True
            for r in replays
        )
        or any(
            saved[k] is not False
            for k in (
                "poker_training_performed",
                "reference_output_used_in_training",
                "long_run_admitted",
                "new_agent_default",
                "fresh_global_admission",
                "reference_actions_exported",
            )
        )
        or saved["reference_constructed"] is not True
    ):
        raise ArithmeticError("complete fixed scalar/replay inventory required")
    summaries = []
    batch = saved["native_batch"]
    if batch["status"] != "completed" or len(batch["workers"]) != 3:
        raise ArithmeticError("all three original native workers required")
    for slot, worker in enumerate(batch["workers"]):
        done = [m for m in worker["messages"] if m.get("kind") == "done"]
        if (
            worker["slot"] != slot
            or worker["exitcode"] != 0
            or len(done) != 1
            or done[0]["summary"]["implementation_sha256"] != base_config
        ):
            raise ArithmeticError("complete original worker identity required")
        summary = dict(done[0]["summary"])
        summary["normalization"] = {
            k: v
            for k, v in summary["normalization"].items()
            if k not in ("pid", "thread")
        }
        summaries.append(summary)
    return dict(
        own_sha256=saved["own_sha256"],
        base_source_sha256=saved["source_sha256"],
        implementation_config=saved["implementation_config"],
        profiles=saved["profiles"],
        fixed_conditions=saved["fixed_conditions"],
        verification=saved["verification"],
        normalization={
            k: v
            for k, v in saved["normalization"].items()
            if k not in ("pid", "thread")
        },
        validation_cache=saved["validation_cache"],
        worker_summaries=summaries,
        computed_replays=replays,
        license=saved["license"],
        reference_actions_exported=False,
        training_performed=False,
    )


@contextmanager
def observe_reader(output: Path, *, enabled: bool) -> Iterator[dict[str, Any]]:
    import checkpoint_cpu_support as support
    from compact_suit import cli

    underlying = cli.read
    replays: list[dict[str, Any]] = []
    receipt: dict[str, Any] = dict(replays=replays)
    with ExitStack() as stack:
        streams = [
            stack.enter_context((output / f"read-{i}-events.jsonl").open("xb"))
            for i in range(3)
        ]

        def emit(index: int, event: dict[str, Any]) -> None:
            streams[index].write(canonical(event) + b"\n")
            streams[index].flush()

        def save_read(row: dict[str, Any]) -> None:
            atomic(output / f"read-{row['index']}.json", row)

        observer = support.Observer(
            enabled=enabled, event_sink=emit, read_sink=save_read
        )

        def read(*args: Any, **kwargs: Any) -> dict[str, Any]:
            if len(args) != 3 or kwargs:
                raise ArithmeticError(
                    "unchanged complete current read call shape required"
                )
            computed: list[dict[str, Any]] = []
            with observer.read(len(replays)):
                saved = underlying(*args, observed=computed)
                if len(computed) != 1:
                    raise ArithmeticError(
                        "one actual whole mathematical replay required"
                    )
                replays.append(dict(scope=saved["scope"], computed=computed[0]))
            return saved

        primary = False
        try:
            with observer.hooks(), patch.object(cli, "read", read):
                yield receipt
        except BaseException:
            primary = True
            raise
        finally:
            receipt.update(state=observer.state(), reads=observer.reads)
            try:
                atomic(output / "observer.json", receipt)
            except BaseException:
                if not primary:
                    raise


def execute_child(
    root: Path, output: Path, c: dict[str, Any], *, enabled: bool
) -> dict[str, Any]:
    from compact_suit import cli
    from compact_suit.cache import check_execution

    raw = output / "native.json"
    primary = False
    native: dict[str, Any] | None = None
    try:
        with observe_reader(output, enabled=enabled) as observed:
            code = cli.child_main(
                root,
                [
                    "cost-audit",
                    "--repetition",
                    "0",
                    "--own",
                    c["base_own"],
                    "--output",
                    str(raw),
                ],
            )
        if code != 0:
            raise ArithmeticError("complete original cost-audit child failed")
        native = json.loads(raw.read_text())
        check_execution(root, native)
        identity = numerical_identity(native, observed["replays"])
    except BaseException:
        primary = True
        raise
    finally:
        # Also mark partial/failed outputs; restoration cannot turn a diagnostic
        # into production evidence. A secondary write error never masks replay.
        if raw.is_file():
            try:
                retained = json.loads(raw.read_text())
                retained["base_implementation_config"] = retained[
                    "implementation_config"
                ]
                retained["implementation_config"] = dict(
                    instrumentation_config=CONFIG,
                    instrumentation_sha256=CONFIG_SHA,
                    admission_evidence=False,
                )
                retained["instrumentation_scope"] = c["scope"]
                atomic(raw, retained)
            except BaseException as error:
                if not primary:
                    raise
                try:
                    atomic(
                        output / "invalidation-failure.json",
                        dict(failure_kind=type(error).__name__),
                    )
                except BaseException:
                    pass  # The primary child failure remains authoritative.
    assert native is not None
    try:
        check_execution(root, json.loads(raw.read_text()))
    except ArithmeticError:
        return dict(
            identity=identity,
            base_admission_rejected=True,
            observer=observed,
            worker_body_clocks=[
                dict(
                    slot=w["slot"],
                    wall_seconds=m["seconds"],
                    cpu_seconds=m["cpu_seconds"],
                )
                for w in native["native_batch"]["workers"]
                for m in w["messages"]
                if m.get("kind") == "done"
            ],
        )
    raise ArithmeticError("instrumented receipt must fail base admission")


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    import checkpoint_cpu_support as support

    saved: dict[str, Any] = dict(
        status="running",
        mode=mode,
        pid=os.getpid(),
        thread=threading.get_ident(),
        admission_evidence=False,
        poker_training_performed=False,
        reference_output_used_in_training=False,
        executable=sys.executable,
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
    )
    atomic(output / "child.json", saved)
    try:
        if mode not in ("plain", "profiled"):
            raise ArithmeticError("fixed observer pair mode required")
        c, source = binding(root)
        runtime(c)
        checked(root, source)
        saved.update(
            source=source,
            config_sha256=CONFIG_SHA,
            own_proof=own_published(root, source),
        )
        atomic(output / "child.json", saved)
        # Both arms import identical target modules before original parent hooks.
        from compact_suit import cli  # noqa: F401

        from poker_ai.reproducibility import runtime_environment

        saved["environment"] = runtime_environment()
        os.environ["POKER_COMPACT_OPPONENT_STARTED"] = repr(origin)
        from profile_coarse_reader import clock

        saved["body_before"] = clock()
        result = execute_child(root, output, c, enabled=mode == "profiled")
        saved["body_after"] = clock()
        saved["complete_body_parent_cpu_seconds"] = (
            saved["body_after"]["cpu"] - saved["body_before"]["cpu"]
        )
        observed = result.pop("observer")
        summaries = support.validate_state(
            observed["state"],
            observed["reads"],
            enabled=mode == "profiled",
            pid=saved["pid"],
            thread=saved["thread"],
            expected=432,
        )
        if [r["scope"] for r in observed["replays"]] != c["expected"]["read_scopes"]:
            raise ArithmeticError("fixed complete read scope inventory changed")
        after_c, after = binding(root, clean=False)
        if after_c != c or after["sha256"] != source["sha256"]:
            raise ArithmeticError("observer source or sealed inputs changed")
        saved.update(
            result,
            status="complete_checkpoint_cpu_diagnostic",
            summaries=summaries,
            reference_constructed=True,
            seconds=time.perf_counter() - origin,
        )
        saved["raw_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
            and p.name not in ("child.json", "command.log", "measurement.json")
        }
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
            seconds=time.perf_counter() - origin,
        )
        atomic(output / "child.json", saved)
        raise


def pair_identity(children: list[dict[str, Any]]) -> dict[str, Any]:
    if (
        len(children) != 2
        or [r["mode"] for r in children] != ["plain", "profiled"]
        or any(
            r["status"] != "complete_checkpoint_cpu_diagnostic"
            or r["base_admission_rejected"] is not True
            or r["config_sha256"] != CONFIG_SHA
            for r in children
        )
        or children[0]["pid"] == children[1]["pid"]
        or children[0]["source"]["sha256"] != children[1]["source"]["sha256"]
        or canonical(children[0]["identity"]) != canonical(children[1]["identity"])
    ):
        raise ArithmeticError("complete separate plain/profiled identity required")
    return dict(
        status="exact_complete_scalar_and_computed_replay_identity",
        identity_sha256=hashlib.sha256(canonical(children[0]["identity"])).hexdigest(),
    )


def supervise(command: list[str], output: Path, cap: float) -> dict[str, Any]:
    """Bound a fresh child, retain its real PID and reap interrupted descendants."""
    if type(cap) not in (int, float) or not math.isfinite(cap) or cap <= 0:
        raise ValueError("positive finite complete child cap required")
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing complete/partial observer output")
    output.mkdir(parents=True)
    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    environment = dict(os.environ, POKER_COMPACT_REPLAY_PROFILE_STARTED=repr(started))
    with (output / "command.log").open("xb") as log:
        process = subprocess.Popen(
            command,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        interrupted = None
        try:
            code = process.wait(timeout=max(0.001, started + cap - time.perf_counter()))
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            interrupted = type(error).__name__
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124 if isinstance(error, subprocess.TimeoutExpired) else 130
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = dict(
        command=command,
        child_pid=process.pid,
        started_perf_counter=started,
        cap_seconds=cap,
        returncode=code,
        interrupted=interrupted,
        seconds=time.perf_counter() - started,
        reaped_child_user_seconds=after.ru_utime - before.ru_utime,
        reaped_child_system_seconds=after.ru_stime - before.ru_stime,
        child_sha256=digest(output / "child.json")
        if (output / "child.json").is_file()
        else None,
        scope=(
            "complete child startup/imports/prerequisites/original work/capture/"
            "final writes; excludes supervisor receipt; "
            "OS CPU may be partial on failure"
        ),
    )
    atomic(output / "measurement.json", result)
    return result


def pair(root: Path, output: Path) -> int:

    started = time.perf_counter()
    if (
        output.exists()
        or output.is_symlink()
        or not output.resolve().is_relative_to(root.resolve() / "results/runs")
    ):
        raise FileExistsError(
            "fresh ignored pair destination required; retain every attempt"
        )
    output.mkdir(parents=True)
    saved: dict[str, Any] = dict(
        status="running",
        order=["plain", "profiled"],
        measurements=[],
        admission_evidence=False,
    )
    atomic(output / "pair.json", saved)
    try:
        c, source = binding(root)
        checked(root, source)
        own_published(root, source)
        for mode in c["order"]:
            remaining = c["caps"]["shared_seconds"] - (time.perf_counter() - started)
            if remaining <= 0:
                raise TimeoutError("shared1800-second pair cap exhausted")
            measurement = supervise(
                [
                    sys.executable,
                    str(root / ENTRY),
                    "--child",
                    mode,
                    "--output",
                    str(output / mode),
                ],
                output / mode,
                min(c["caps"]["child_seconds"], remaining),
            )
            saved["measurements"].append(measurement)
            atomic(output / "pair.json", saved)
            if measurement["returncode"] != 0:
                raise ArithmeticError("retained failed child; no favorable retry")
        saved.update(
            pair_identity(
                [
                    json.loads((output / mode / "child.json").read_text())
                    for mode in c["order"]
                ]
            )
        )
        saved["seconds"] = time.perf_counter() - started
        if saved["seconds"] >= c["caps"]["shared_seconds"]:
            raise TimeoutError("complete pair exceeded shared1800seconds")
        atomic(output / "pair.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        atomic(output / "pair.json", saved)
        raise


def saved_pair(root: Path, output: Path) -> dict[str, Any]:
    """Authenticate complete saved evidence without a replay or reference call."""
    import checkpoint_cpu_support as support
    from compact_suit.cache import check_execution
    from profile_compact_replay import authenticate_source

    from poker_ai.evaluation.opponent_learning_workers import gather_independent
    from poker_ai.evaluation.private_prefix_journal import validate as validate_journal
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.solver_validation.opponent_learning import validate_rows

    c = contract(root)
    pair_data = json.loads((output / "pair.json").read_text())
    if (
        pair_data["order"] != c["order"]
        or len(pair_data["measurements"]) != 2
        or pair_data["status"] != "exact_complete_scalar_and_computed_replay_identity"
    ):
        raise ArithmeticError("complete fixed ordered pair required")
    children, ledgers = [], []
    for mode, measurement in zip(c["order"], pair_data["measurements"], strict=True):
        folder = output / mode
        child_data = json.loads((folder / "child.json").read_text())
        if (
            measurement != json.loads((folder / "measurement.json").read_text())
            or measurement["returncode"] != 0
            or type(measurement["returncode"]) is not int
            or measurement["interrupted"] is not None
            or not 0 < measurement["seconds"] < min(900, measurement["cap_seconds"])
            or measurement["child_sha256"] != digest(folder / "child.json")
            or type(measurement["child_pid"]) is not int
            or measurement["child_pid"] != child_data["pid"]
            or child_data["mode"] != mode
            or child_data["source"]["fingerprint"]
            != sha(child_data["source"]["sha256"])
        ):
            raise ArithmeticError("saved complete producer measurement changed")
        for stamp in (child_data["body_before"], child_data["body_after"]):
            support.check_clock(stamp)
            if (
                stamp["pid"] != measurement["child_pid"]
                or stamp["thread"] != child_data["thread"]
            ):
                raise ArithmeticError("complete body producer changed")
        start, end = child_data["body_before"], child_data["body_after"]
        if (
            not measurement["started_perf_counter"]
            <= start["wall"]
            <= end["wall"]
            <= measurement["started_perf_counter"] + measurement["seconds"]
            or child_data["complete_body_parent_cpu_seconds"]
            != end["cpu"] - start["cpu"]
            or end["cpu"] < start["cpu"]
        ):
            raise ArithmeticError("complete body and supervisor clocks changed")
        expected_command = [
            child_data["executable"],
            str(Path(child_data["execution_root"]) / ENTRY),
            "--child",
            mode,
            "--output",
            child_data["execution_output"],
        ]
        if measurement["command"] != expected_command or not Path(
            child_data["execution_output"]
        ).is_relative_to(Path(child_data["execution_root"]) / "results/runs"):
            raise ArithmeticError("actual complete child command/output changed")
        authenticate_source(root, child_data["source"])
        expected_raw = {"observer.json", "native.json", "native-events.jsonl"} | {
            f"read-{i}{suffix}"
            for i in range(3)
            for suffix in (".json", "-events.jsonl")
        }
        if set(child_data["raw_sha256"]) != expected_raw or any(
            p.is_symlink() for p in folder.rglob("*")
        ):
            raise ArithmeticError(
                "complete explicit raw observation inventory required"
            )
        actual_raw = {
            str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()
        }
        if actual_raw != expected_raw | {
            "child.json",
            "command.log",
            "measurement.json",
        }:
            raise ArithmeticError("unexpected or missing raw diagnostic member")
        for name, checksum in child_data["raw_sha256"].items():
            path = folder / name
            if (
                path.is_symlink()
                or not path.resolve().is_relative_to(folder.resolve())
                or digest(path) != checksum
            ):
                raise ArithmeticError("saved raw observation changed")
        observed = json.loads((folder / "observer.json").read_text())
        results = support.validate_state(
            observed["state"],
            observed["reads"],
            enabled=mode == "profiled",
            pid=measurement["child_pid"],
            thread=child_data["thread"],
            expected=432,
        )
        if (
            results != child_data["summaries"]
            or observed["replays"] != child_data["identity"]["computed_replays"]
        ):
            raise ArithmeticError("saved computed summary changed")
        for row in observed["reads"]:
            if any(
                not start[k] <= row["before"][k] <= row["after"][k] <= end[k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("complete read outside actual parent body")
        for index, row in enumerate(observed["reads"]):
            stream = folder / f"read-{index}-events.jsonl"
            if [json.loads(line) for line in stream.read_bytes().splitlines()] != row[
                "events"
            ] or json.loads((folder / f"read-{index}.json").read_text()) != row:
                raise ArithmeticError(
                    "independently retained boundary/event stream changed"
                )
        native = json.loads((folder / "native.json").read_text())
        if native["implementation_config"] != dict(
            instrumentation_config=CONFIG,
            instrumentation_sha256=CONFIG_SHA,
            admission_evidence=False,
        ):
            raise ArithmeticError("saved instrumentation must reject base admission")
        native["implementation_config"] = native["base_implementation_config"]
        check_execution(root, native)
        if (
            native["normalization"]["pid"] != measurement["child_pid"]
            or native["normalization"]["thread"] != child_data["thread"]
        ):
            raise ArithmeticError("base parent and observer producer differ")
        own = json.loads((root / c["base_own"]).read_text())
        if validate_rows(native, own) != native["verification"]:
            raise ArithmeticError("saved scalar comparison verification changed")
        gathered = gather_independent(native["native_batch"], own)
        if any(native[k] != v for k, v in gathered.items()):
            raise ArithmeticError("complete native workers and scalar rows differ")
        validate_journal(
            folder / native["journal"]["file"],
            native["journal"],
            native["source_sha256"],
            {
                3: native["events"],
                **{w["slot"]: w["messages"] for w in native["native_batch"]["workers"]},
            },
        )
        clocks = [
            dict(
                slot=w["slot"], wall_seconds=m["seconds"], cpu_seconds=m["cpu_seconds"]
            )
            for w in native["native_batch"]["workers"]
            for m in w["messages"]
            if m.get("kind") == "done"
        ]
        if clocks != child_data["worker_body_clocks"] or any(
            type(x[k]) not in (int, float) or not math.isfinite(x[k]) or x[k] < 0
            for x in clocks
            for k in ("wall_seconds", "cpu_seconds")
        ):
            raise ArithmeticError("saved separate worker clocks changed")
        if numerical_identity(native, observed["replays"]) != child_data["identity"]:
            raise ArithmeticError("complete raw numerical identity changed")
        children.append(child_data)
        ledgers.append(results)
    identity = pair_identity(children)
    if (
        any(pair_data[k] != v for k, v in identity.items())
        or not 0 < pair_data["seconds"] < 1800
    ):
        raise ArithmeticError("saved pair identity/shared clock changed")
    if (
        pair_data["measurements"][0]["started_perf_counter"]
        + pair_data["measurements"][0]["seconds"]
        > pair_data["measurements"][1]["started_perf_counter"]
    ):
        raise ArithmeticError("pair child clocks overlap")
    return dict(pair=pair_data, children=children, ledgers=ledgers)


def exports(saved: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Disjoint selected CPU, whole wall and separate worker-body clocks."""
    reads, commands = [], []
    for mode, child_data, measurement, ledgers in zip(
        ("plain", "profiled"),
        saved["children"],
        saved["pair"]["measurements"],
        saved["ledgers"],
        strict=True,
    ):
        for index, result in enumerate(ledgers):
            groups = result["groups"]
            reads.append(
                dict(
                    mode=mode,
                    read=index,
                    read_cpu_seconds=result["read_cpu_seconds"],
                    decode_cpu_seconds=groups["checkpoint_decode"]["inclusive_cpu"],
                    score_cpu_seconds=groups["checkpoint_score"]["inclusive_cpu"],
                    checkpoint_residual_cpu_seconds=groups["own_checkpoint"][
                        "exclusive_selected_cpu"
                    ],
                    outside_checkpoint_cpu_seconds=result[
                        "outside_checkpoint_cpu_seconds"
                    ],
                    selected_union_cpu_seconds=result["selected_union_cpu"],
                    selected_calls=result["calls"],
                )
            )
        commands.append(
            dict(
                mode=mode,
                complete_wall_seconds=measurement["seconds"],
                parent_body_cpu_seconds=child_data["complete_body_parent_cpu_seconds"],
                total_worker_body_cpu_seconds=math.fsum(
                    x["cpu_seconds"] for x in child_data["worker_body_clocks"]
                ),
                maximum_worker_body_wall_seconds=max(
                    x["wall_seconds"] for x in child_data["worker_body_clocks"]
                ),
            )
        )
    return reads, commands


def report(root: Path, output: Path, destination: Path | None = None) -> None:
    """Saved-data report; a separate raw publication must precede this analysis."""
    import csv

    from compact_suit.admission import published

    saved = saved_pair(root, output)
    for path in sorted(output.rglob("*")):
        if path.is_file() and "report" not in path.relative_to(output).parts:
            published(root, path)
    reads, commands = exports(saved)
    folder = destination if destination is not None else output / "report"
    if folder.exists() or folder.is_symlink():
        raise FileExistsError("retain existing checkpoint report")
    folder.mkdir()
    for name, rows in (("reads.csv", reads), ("commands.csv", commands)):
        with (folder / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    atomic(
        folder / "summary.json",
        dict(
            reads=reads,
            commands=commands,
            identity_sha256=saved["pair"]["identity_sha256"],
            admission_evidence=False,
            limitations=(
                "One ordered pair; timer/capture overhead and order are "
                "confounded. Process CPU excludes native-worker CPU. "
                "Residual includes all unselected checkpoint work, "
                "not serializer self CPU. No training, strength or "
                "production-cost admission."
            ),
        ),
    )
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")

    profiled = [r for r in reads if r["mode"] == "profiled"]
    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = [0.0] * 3
    for key, label in (
        ("decode_cpu_seconds", "Decode / validate"),
        ("score_cpu_seconds", "Recompute score"),
        ("checkpoint_residual_cpu_seconds", "Other checkpoint work"),
        ("outside_checkpoint_cpu_seconds", "Outside selected checkpoint"),
    ):
        values = [r[key] for r in profiled]
        ax.bar(range(3), values, bottom=bottom, label=label)
        bottom = [a + b for a, b in zip(bottom, values, strict=True)]
    ax.set(
        xticks=range(3),
        xticklabels=[
            "Tiny proof read",
            "Cost read before native",
            "Cost read after native",
        ],
        ylabel="Parent process CPU seconds",
        title="Complete reads: disjoint observed CPU regions",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "checkpoint-cpu.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(
        [r["mode"] for r in commands], [r["complete_wall_seconds"] for r in commands]
    )
    axes[0].set(ylabel="Elapsed seconds", title="Whole command wall clock")
    for index, row in enumerate(commands):
        axes[1].bar(
            index - 0.2,
            row["parent_body_cpu_seconds"],
            width=0.4,
            color="tab:blue",
            label="Parent body CPU" if index == 0 else None,
        )
        axes[1].bar(
            index + 0.2,
            row["total_worker_body_cpu_seconds"],
            width=0.4,
            color="tab:orange",
            label="Sum of worker body CPU" if index == 0 else None,
        )
    axes[1].set(
        xticks=[0, 1],
        xticklabels=["plain", "profiled"],
        ylabel="CPU seconds",
        title="Separate process clocks",
    )
    axes[1].legend()
    fig.suptitle("One ordered pair; no stable overhead or speedup estimate")
    fig.tight_layout()
    fig.savefig(folder / "complete-clocks.png", dpi=150)
    plt.close(fig)
    print(json.dumps(dict(reads=reads, commands=commands), indent=2))


def main() -> int:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=("proof", "pair", "report"))
    parser.add_argument("--child", choices=("proof", "plain", "profiled"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--report-output",
        type=Path,
        help="Fresh report directory; saved inputs stay unchanged",
    )
    args = parser.parse_args()
    output = ROOT / args.output
    if args.report_output is not None and args.operation != "report":
        parser.error("--report-output is only for saved-data reports")
    if args.child and args.operation:
        parser.error("child mode and parent operation are separate")
    if args.child:
        origin = float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"])
        return (
            proof(ROOT, output, origin)
            if args.child == "proof"
            else child(ROOT, args.child, output, origin)
        )
    if args.operation == "report":
        report(
            ROOT,
            output,
            ROOT / args.report_output if args.report_output is not None else None,
        )
        return 0
    if args.operation == "pair":
        return pair(ROOT, output)
    if args.operation != "proof" or args.child is not None:
        parser.error("choose proof or pair")

    if not output.resolve().is_relative_to(ROOT / "results/runs"):
        raise ValueError("fresh ignored own-proof destination required")
    m = supervise(
        [
            sys.executable,
            str(ROOT / ENTRY),
            "--child",
            "proof",
            "--output",
            str(output),
        ],
        output,
        max(0.001, 180 - (time.perf_counter() - started)),
    )
    return 0 if m["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
