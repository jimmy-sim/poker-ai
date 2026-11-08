"""Spawn isolated fixed cell partitions and retain partial events on failure."""

import multiprocessing as mp
import os
import time
from collections.abc import Callable
from multiprocessing.connection import Connection, wait
from typing import Any, cast

from poker_ai.postflop.river_study import Deadline

Send = Callable[[dict[str, Any]], None]
Job = Callable[[int, list[int], dict[str, Any], Send], dict[str, Any]]
THREAD_ENV = dict.fromkeys(
    (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ),
    "1",
)


def partition(size: int, workers: int) -> list[list[int]]:
    if type(size) is not int or type(workers) is not int or not 1 <= workers <= size:
        raise ValueError("need nonempty fixed worker partitions")
    return [list(range(slot, size, workers)) for slot in range(workers)]


def _entry(
    job: Job, slot: int, indices: list[int], payload: dict[str, Any], pipe: Connection
) -> None:
    started, cpu = time.perf_counter(), time.process_time()
    try:
        pipe.send(
            dict(
                kind="started",
                pid=os.getpid(),
                thread_environment={k: os.environ.get(k) for k in THREAD_ENV},
            )
        )
        summary = job(slot, indices, payload, pipe.send)
        pipe.send(
            dict(
                kind="done",
                seconds=time.perf_counter() - started,
                cpu_seconds=time.process_time() - cpu,
                summary=summary,
            )
        )
    except BaseException as error:
        pipe.send(dict(kind="error", type=type(error).__name__, reason=str(error)))
        raise
    finally:
        pipe.close()


def run_batch(
    size: int,
    workers: int,
    job: Job,
    payload: dict[str, Any],
    deadline: Deadline,
    record: dict[str, Any],
) -> None:
    """Drain child pipes while running; terminate/reap all children on failure.

    Spawn/import/start/collection/join belong to batch wall time. POSIX os.times
    reaped-child CPU deltas include imports, unlike timers inside _entry. The
    parent does not run other child commands during this interval. Thread settings
    are requests inherited by children, not measurements of OS thread counts.
    """
    assignments = partition(size, workers)
    if record:
        raise ValueError("batch record must be fresh")
    started, cpu, times = time.perf_counter(), time.process_time(), os.times()
    record.update(
        worker_count=workers,
        assignments=assignments,
        workers=[
            dict(slot=s, pid=None, messages=[], exitcode=None) for s in range(workers)
        ],
        status="running",
        failure=None,
    )
    context = mp.get_context("spawn")
    processes = []
    receivers: dict[Connection, int] = {}
    old = {key: os.environ.get(key) for key in THREAD_ENV}
    try:
        os.environ.update(THREAD_ENV)
        try:
            for slot, indices in enumerate(assignments):
                deadline.check()
                receiver, sender = context.Pipe(duplex=False)
                process = context.Process(
                    target=_entry, args=(job, slot, indices, payload, sender)
                )
                receivers[receiver] = slot
                try:
                    process.start()
                finally:
                    sender.close()
                processes.append(process)
                record["workers"][slot]["pid"] = process.pid
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        active = list(receivers)
        while active:
            deadline.check()
            for ready in wait(active, timeout=0.05):
                receiver = cast(Connection, ready)
                slot = receivers[receiver]
                try:
                    event = receiver.recv()
                except EOFError:
                    active.remove(receiver)
                    receiver.close()
                    continue
                if not isinstance(event, dict) or event.get("kind") not in {
                    "started",
                    "prepared",
                    "cell",
                    "done",
                    "error",
                }:
                    raise ChildProcessError("invalid child event")
                record["workers"][slot]["messages"].append(event)
                if event["kind"] == "error":
                    raise ChildProcessError(
                        f"worker {slot}: {event['type']}: {event['reason']}"
                    )
        for process, worker in zip(processes, record["workers"], strict=True):
            process.join(timeout=1.0)
            if process.is_alive() or process.exitcode != 0:
                raise ChildProcessError(f"worker {worker['slot']} did not exit cleanly")
            if sum(e["kind"] == "done" for e in worker["messages"]) != 1:
                raise ChildProcessError("worker exited without completion")
        deadline.check()
        record["status"] = "completed"
    except BaseException as error:
        record["status"] = "incomplete"
        record["failure"] = dict(type=type(error).__name__, reason=str(error))
        raise
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
        for process, worker in zip(processes, record["workers"], strict=False):
            process.join(timeout=1.0)
            if process.is_alive():
                process.kill()
                process.join(timeout=1.0)
            worker["exitcode"] = process.exitcode
        for receiver in receivers:
            receiver.close()
        now = os.times()
        record.update(
            seconds=time.perf_counter() - started,
            parent_cpu_seconds=time.process_time() - cpu,
            reaped_children_cpu_seconds=(
                now.children_user
                + now.children_system
                - times.children_user
                - times.children_system
            ),
        )
