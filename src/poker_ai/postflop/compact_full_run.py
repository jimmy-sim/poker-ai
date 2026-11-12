"""Own full-control capture/replay, with complete and partial evidence retained."""

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, Protocol, cast

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop.compact_full_context import Context, contexts
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.public_range_definition import check_inputs, contract
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.reproducibility import runtime_environment

Factory = Callable[[Path, bool], list[Context]]


class Solver(Protocol):
    iteration: int
    strategy_sum: FloatArray
    regrets: FloatArray

    @property
    def average_policy(self) -> FloatArray: ...

    def step(self) -> None: ...


def solver(tree: ArrayTree) -> Solver:
    # The unchanged JIT kernel consumes only ArrayTree fields. Keep the legacy
    # MatrixTree annotation/source untouched; the fixture exercises this adapter.
    import importlib

    module = importlib.import_module("poker_ai.postflop.jit_cfr")
    return cast(Solver, module.FusedCFRPlus(tree))


def runtime() -> dict[str, Any]:
    return dict(**runtime_environment(), numba=version("numba"))


def check_runtime(saved: dict[str, Any], *, real: bool) -> None:
    import platform

    if (
        saved["numpy"] != version("numpy")
        or saved["numba"] != version("numba")
        or saved["python"] != runtime_environment()["python"]
    ):
        raise ArithmeticError("own/native/replay runtime changed")
    if real and (platform.python_version() != "3.11.17" or version("numpy") != "2.4.6"):
        raise ArithmeticError(
            "real compact trajectories require Python3.11.17/NumPy2.4.6"
        )


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = contract(root)
    artifacts.inventory(saved, config)
    artifacts.check_source(root, saved["source"])
    check_runtime(saved["runtime"], real=not saved["software_only"])
    rows = saved["rows"]
    partitions = {(r["spot_file"], r["representation"]): r for r in saved["partitions"]}
    checked = 0
    for context in contexts(root, software=saved["software_only"]):
        partition = partitions[context.spot_file, context.representation]
        if canonical(partition) != canonical(
            dict(**context.binding, **context.diagnostics)
        ):
            raise ArithmeticError("replayed layout diagnostics changed")
        for row in rows:
            if (row["spot_file"], row["representation"]) != (
                context.spot_file,
                context.representation,
            ):
                continue
            raw = artifacts.load_snapshot(path.parent / "snapshots", row["snapshot"])
            actual = artifacts.decode(context, raw)
            expected = {k: v for k, v in row.items() if k != "snapshot"}
            scalar = {
                k: v
                for k, v in actual.items()
                if k not in {"policy", "strategy_sum", "regrets", "actions", "format"}
            }
            if canonical(expected) != canonical(scalar):
                raise ArithmeticError("manifest and raw checkpoint disagree")
            checked += 1
    if checked != config["full"]["expected_profiles"]:
        raise ArithmeticError("replay omitted a planned profile")
    artifacts.check_source(root, saved["source"])
    return dict(
        profiles_checked=checked,
        maximum_metric_error_chips=0.0,
        poker_training_performed=False,
        actual_admission=False,
    )


def run(
    root: Path,
    output: Path,
    *,
    software: bool,
    started: float,
    admission: Path | None = None,
    check_path: Path | None = None,
) -> dict[str, Any]:
    if output.exists() or output.parent.joinpath("snapshots").exists():
        raise FileExistsError("retain previous full-control destination")
    config = contract(root)
    cap = 180 if software else config["full"]["maximum_seconds"]

    def clock() -> None:
        if time.perf_counter() - started >= cap:
            raise TimeoutError("complete own full-control cap reached")

    saved: dict[str, Any] = dict(
        format=artifacts.FORMAT,
        status="running",
        failure=None,
        software_only=software,
        source=artifacts.source(root, clean=True),
        runtime=runtime(),
        started_at_utc=datetime.now(UTC).isoformat(),
        rows=[],
        partitions=[],
        actual_admission=False,
        fresh_global_admission=False,
        sampled_learning="not_run",
        backend=config["full"]["backend"],
        averaging="linear, alternating CFR+, no separate warm stage",
        new_agent_default=False,
        rss_convention="process lifetime high-water, not isolated per-layout RAM",
    )

    def persist() -> None:
        saved.update(
            seconds=time.perf_counter() - started,
            peak_process_rss_bytes=peak_rss_bytes(),
        )
        artifacts.atomic(output, saved)

    try:
        persist()
        clock()
        from poker_ai.postflop.compact_full_gate import bound, checks

        if check_path is None:
            raise ValueError("source-bound execution checks required")
        checks(root, check_path)
        saved["checks"] = bound(root, check_path)
        if not software:
            from poker_ai.postflop.compact_full_gate import require_admission

            if admission is None:
                raise ValueError(
                    "checked published admission required before any real trajectory"
                )
            saved["admission"] = require_admission(root, admission)
        check_runtime(saved["runtime"], real=not software)
        check_inputs(root, config)
        for context in contexts(root, software=software):
            clock()
            saved["partitions"].append(dict(**context.binding, **context.diagnostics))
            trainer = solver(context.scoring.partition)
            for checkpoint in config["full"]["checkpoints"]:
                while trainer.iteration < checkpoint:
                    clock()
                    trainer.step()
                clock()
                snapshot = artifacts.capture(
                    context,
                    checkpoint,
                    trainer.average_policy,
                    trainer.strategy_sum,
                    trainer.regrets,
                )
                index = len(saved["rows"])
                receipt = artifacts.write_snapshot(
                    output.parent / "snapshots" / f"{index:04d}.json.gz", snapshot
                )
                saved["rows"].append(
                    dict(
                        **{
                            k: v
                            for k, v in snapshot.items()
                            if k
                            not in {
                                "policy",
                                "strategy_sum",
                                "regrets",
                                "actions",
                                "format",
                            }
                        },
                        snapshot=receipt,
                    )
                )
                persist()
        clock()
        artifacts.check_source(root, saved["source"])
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
