"""Actual spawned toy jobs check isolation and failure cleanup, not poker strength."""

import multiprocessing as mp
import os
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import node_profile
from poker_ai.postflop.cell_process import THREAD_ENV, Send, partition, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.training_isolation import sentinel_tree


def toy_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    tree = sentinel_tree()
    for index in indices:
        row, _ = node_profile.measure(
            tree, payload["cells"][index], "nodes", 8, Deadline(10)
        )
        send(dict(kind="cell", index=index, row=row))
    return dict(cells=len(indices))


def failing_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot, indices
    mode = payload["mode"]
    send(dict(kind="cell", example="retained partial event"))
    if mode == "exception":
        raise ValueError("deliberate worker failure")
    if mode == "exit":
        os._exit(0)
    if mode == "invalid":
        send(dict(kind="unrecognized"))
    if mode == "timeout":
        while True:
            time.sleep(0.01)
    return {}


@pytest.mark.parametrize("workers", [1, 2, 3])
def test_fixed_partitions_cover_each_cell_once(workers: int) -> None:
    groups = partition(140, workers)
    assert sorted(i for group in groups for i in group) == list(range(140))
    assert all(
        all(i % workers == slot for i in group) for slot, group in enumerate(groups)
    )


@pytest.mark.parametrize("size,workers", [(0, 1), (2, 3), (True, 1), (3, True), (3, 0)])
def test_reject_invalid_partitions(size: int, workers: int) -> None:
    with pytest.raises(ValueError):
        partition(size, workers)


@pytest.mark.parametrize("workers", [1, 2])
def test_spawned_toy_endpoints_match_serial_and_restore_parent_environment(
    workers: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.postflop.parallel_profile import same

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    monkeypatch.setenv("OMP_NUM_THREADS", "17")
    cells = [
        dict(
            spot_file="software_fixture",
            representation="exact",
            traversal="external",
            regret_rule=clip,
            regret_weight=rw,
            average_weight=aw,
            seed=20261301,
            bridge="common",
        )
        for clip in ("signed", "clipped")
        for rw in ("uniform", "linear")
        for aw in ("uniform", "linear")
    ]
    record: dict[str, Any] = {}
    run_batch(8, workers, toy_job, dict(cells=cells), Deadline(30), record)
    assert record["status"] == "completed"
    assert record["seconds"] > 0
    assert record["parent_cpu_seconds"] >= 0
    assert record["reaped_children_cpu_seconds"] > 0
    assert os.environ["OMP_NUM_THREADS"] == "17"
    assert len({w["pid"] for w in record["workers"]}) == workers
    actual = {}
    for worker in record["workers"]:
        assert worker["exitcode"] == 0
        assert worker["messages"][0]["thread_environment"] == THREAD_ENV
        for event in worker["messages"]:
            if event["kind"] == "cell":
                actual[event["index"]] = event["row"]
    from poker_ai.postflop.controlled_profile import STABLE

    for index, cell in enumerate(cells):
        reference, _ = node_profile.measure(
            sentinel_tree(), cell, "nodes", 8, Deadline(10)
        )
        assert all(same(actual[index][key], reference[key]) for key in STABLE)


@pytest.mark.parametrize("mode", ["exception", "exit", "invalid", "timeout"])
def test_failure_retention_timeout_and_reaped_children(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    monkeypatch.setenv("OMP_NUM_THREADS", "19")
    record: dict[str, Any] = {}
    deadline = Deadline(5 if mode == "timeout" else 30)
    with pytest.raises((ChildProcessError, TimeoutError)):
        run_batch(4, 2, failing_job, dict(mode=mode), deadline, record)
    assert record["status"] == "incomplete"
    assert record["failure"] is not None
    assert os.environ["OMP_NUM_THREADS"] == "19"
    assert all(w["exitcode"] is not None for w in record["workers"])
    assert not {w["pid"] for w in record["workers"]} & {
        p.pid for p in mp.active_children()
    }
    assert any(e["kind"] == "cell" for w in record["workers"] for e in w["messages"])


def test_reject_reusing_a_batch_record() -> None:
    with pytest.raises(ValueError, match="fresh"):
        run_batch(2, 1, toy_job, {}, Deadline(10), dict(previous=True))
