"""Observed toy training, exact files and rejection of incomplete study grids."""

import copy
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.postflop import node_profile
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import (
    decode,
    read_archive,
    write_archive,
)
from poker_ai.postflop.learning_correctness import evidence
from poker_ai.postflop.learning_training import (
    replay_snapshot,
    train_one,
    validate_grid,
)
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.training_isolation import sentinel_tree


def toy_context() -> ScoringContext:
    tree = sentinel_tree()
    empty = np.zeros(len(tree.keys), dtype=np.bool_)
    return ScoringContext(tree, tree, np.arange(len(tree.keys)), (empty, empty))


@pytest.fixture
def toy_run(tmp_path: Path) -> tuple[Any, ...]:
    context = toy_context()
    labels = dict(work=[150, 500], iteration=[2, 4, 8])
    cells: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for index, (traversal, bridge) in enumerate(
        [
            ("full", "common"),
            ("external", "common"),
            ("full", "cold_target_history_mass"),
        ]
    ):
        cell = dict(
            spot_file="toy",
            representation="exact",
            traversal=traversal,
            seed=20261301 if traversal == "external" else None,
            bridge=bridge,
            regret_rule="clipped",
            regret_weight="uniform",
            average_weight="linear",
        )
        cells.append(cell)
        control = node_profile.trainer(
            context.partition, cell, "nodes" if traversal == "external" else "parent"
        )
        if bridge != "cold_target_history_mass":
            control.initialize_exact()
        while control.iteration < 4:
            control.step()
        from poker_ai.postflop.row_profile import fingerprint

        prefix = dict(
            iterations=4,
            state_sha256=fingerprint(control),
            total_visits=control.nodes_visited,
            initialization_visits=control.initialization_visits,
        )
        train_one(
            context,
            cell,
            index,
            labels,
            tmp_path,
            "a" * 64,
            Deadline(10),
            events.append,
            prefix,
        )
    rows = [e["row"] for e in events if e["phase"] == "snapshot"]
    done = dict(
        kind="done",
        summary=dict(
            cells=3,
            snapshots=len(rows),
            own_replayed=len(rows),
            maximum_error_chips=0.0,
        ),
    )
    batch = dict(
        status="completed",
        failure=None,
        assignments=[[0, 1, 2]],
        workers=[dict(exitcode=0, messages=[*events, done])],
    )
    return context, cells, labels, rows, batch, tmp_path


def test_toy_observer_storage_replay_and_all_labels(toy_run: tuple[Any, ...]) -> None:
    context, cells, labels, rows, batch, scratch = toy_run
    checked = validate_grid(batch, cells, labels)
    assert len(checked) == len(rows)
    assert sum(len(r["labels"]) for r in rows) == 15
    assert {r["case"]["bridge"] for r in rows} == {"common", "cold_target_history_mass"}
    for row in checked:
        assert (
            replay_snapshot(context, row, (scratch / row["file"]).read_bytes(), 1e-9)
            == 0
        )
        assert row["diagnostics"]["river_visit_coverage"] is None


@pytest.mark.parametrize(
    "mode",
    [
        "missing_label",
        "duplicate_snapshot",
        "wrong_cell",
        "wrong_worker",
        "false_crossing",
        "wrong_overshoot",
        "incomplete",
        "no_done",
        "unreplayed",
        "missing_prefix",
        "nonmonotone",
        "bad_last_work",
    ],
)
def test_reject_incomplete_or_false_grid(toy_run: tuple[Any, ...], mode: str) -> None:
    _, cells, labels, _, batch, _ = toy_run
    batch = copy.deepcopy(batch)
    worker = batch["workers"][0]
    events = worker["messages"]
    packet = next(e for e in events if e.get("phase") == "snapshot")
    row = packet["row"]
    if mode == "missing_label":
        row["labels"].pop()
    elif mode == "duplicate_snapshot":
        events.insert(0, copy.deepcopy(packet))
    elif mode == "wrong_cell":
        row["case"]["seed"] = 9
    elif mode == "wrong_worker":
        packet["index"] = 99
    elif mode == "false_crossing":
        row["labels"] = [["work", 1]]
    elif mode == "wrong_overshoot":
        row["overshoots"] = {}
    elif mode == "incomplete":
        batch["status"] = "incomplete"
    elif mode == "no_done":
        events.pop()
    elif mode == "unreplayed":
        events[-1]["summary"]["own_replayed"] -= 1
    elif mode == "missing_prefix":
        events.remove(next(e for e in events if e.get("phase") == "prefix"))
    elif mode == "nonmonotone":
        row["iteration"] = 0
    else:
        row["last_iteration_visits"] += 1
    with pytest.raises(ArithmeticError):
        validate_grid(batch, cells, labels)


def test_archive_is_streamed_in_order_and_hash_bound(toy_run: tuple[Any, ...]) -> None:
    context, _, _, rows, _, scratch = toy_run
    path = scratch / "archive.jsonl.gz"
    digest = write_archive(path, scratch, rows)
    stream = read_archive(path, digest, rows)
    for row, blob in stream:
        assert decode(blob, context, row)["id"] == row["id"]
    assert list(stream) == []
    with pytest.raises(FileExistsError):
        write_archive(path, scratch, rows)
    with pytest.raises(ArithmeticError, match="hash"):
        list(read_archive(path, "0" * 64, rows))
    with pytest.raises(ArithmeticError, match="order"):
        list(read_archive(path, digest, list(reversed(rows))))


@pytest.mark.parametrize(
    "mode", ["blob", "metadata", "policy", "menu", "format", "shape"]
)
def test_own_artifact_tampering_fails(toy_run: tuple[Any, ...], mode: str) -> None:
    context, _, _, rows, _, scratch = toy_run
    row = copy.deepcopy(rows[0])
    blob = (scratch / row["file"]).read_bytes()
    if mode == "blob":
        blob += b"x"
    else:
        saved = json.loads(gzip.decompress(blob))
        if mode == "metadata":
            saved["metadata"]["source_sha256"] = "b" * 64
        elif mode == "policy":
            saved["policy"][0] = list(reversed(saved["policy"][0]))
            row["receipt"]["policy_sha256"] = "0" * 64
        elif mode == "menu":
            saved["actions"][0].reverse()
        elif mode == "format":
            saved["format"] = "reference-strategy"
        else:
            saved["shape"][0] = True
        blob = gzip.compress(json.dumps(saved).encode(), mtime=0)
        row["receipt"].update(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob))
    with pytest.raises(ArithmeticError):
        decode(blob, context, row)


def test_source_bound_toy_evidence_covers_all_rules_and_warm_cold(
    tmp_path: Path,
) -> None:
    result = evidence(tmp_path)
    assert result["trajectory_count"] == 32
    assert result["postflop_training_performed"] is False
    assert result["own_snapshot_roundtrips"] >= 32 * 3
    assert len(result["synthetic_contrasts"]["factorial"]) == 15


def test_wrong_serial_prefix_stops_before_completed_cell(tmp_path: Path) -> None:
    context = toy_context()
    cell = dict(
        traversal="external",
        bridge="common",
        seed=1,
        regret_rule="signed",
        regret_weight="uniform",
        average_weight="uniform",
    )
    events: list[dict[str, Any]] = []
    with pytest.raises(ArithmeticError, match="prefix"):
        train_one(
            context,
            cell,
            0,
            dict(work=[500], iteration=[8]),
            tmp_path,
            "a" * 64,
            Deadline(10),
            events.append,
            dict(
                iterations=2,
                state_sha256="0" * 64,
                total_visits=0,
                initialization_visits=0,
            ),
        )
    assert not any(e.get("phase") == "trained" for e in events)


@pytest.mark.parametrize(
    "mode",
    [
        "nan_metric",
        "bool_count",
        "path",
        "coverage",
        "norm",
        "initial_work",
        "reply_hash",
        "negative_gain",
        "infinite_time",
        "bool_label",
        "full_work",
    ],
)
def test_reject_nonfinite_typed_or_misaccounted_rows(
    toy_run: tuple[Any, ...], mode: str
) -> None:
    from poker_ai.postflop.learning_validation import validate_row

    _, _, _, rows, _, _ = toy_run
    row = copy.deepcopy(rows[0])
    if mode == "nan_metric":
        row["metrics"]["value_player_zero_chips"] = float("nan")
    elif mode == "bool_count":
        row["index"] = False
    elif mode == "path":
        row["file"] = "../foreign-policy.json.gz"
    elif mode == "coverage":
        row["diagnostics"]["river_visit_coverage"] = 0.0
    elif mode == "norm":
        row["diagnostics"]["regret_norm"] = float("inf")
    elif mode == "initial_work":
        row["initialization_visits"] = 0
    elif mode == "reply_hash":
        row["reply_sha256"][0]["exact"] = "foreign"
    elif mode == "negative_gain":
        row["metrics"]["within_partition_gain_chips"] = -1.0
    elif mode == "infinite_time":
        row["seconds"] = float("inf")
    elif mode == "bool_label":
        row["labels"][0][1] = True
    else:
        row["total_work"] += 1
    with pytest.raises(ArithmeticError):
        validate_row(row)
