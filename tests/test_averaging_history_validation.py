"""EXPLICIT fictional ledgers test schema completeness, not research outcomes."""

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs, inputs
from poker_ai.evaluation.averaging_history_validation import gather, grid
from poker_ai.evaluation.controlled_reply_inputs import Inputs, SourcePolicy, expected
from poker_ai.postflop.cell_process import THREAD_ENV, partition

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fictional_ledger() -> tuple[Any, ...]:
    """Invented counters/hashes/zeros for validation only; no policies are trained."""
    config = inputs(ROOT)
    cases = [
        dict(json.loads(k), bridge="common", regret_weight="linear")
        for k in sorted(expected(config))
    ]
    sources, prefixes, rows, masses = [], {}, [], []
    for index, case in enumerate(cases):
        original = dict(
            id=f"FICTIONAL-source-{index}",
            index=index,
            initialization_visits=100,
            total_work=10000003,
            iteration=1000,
            receipt=dict(policy_sha256="e" * 64),
        )
        source = SourcePolicy(case, original, np.ones((1, 1)))
        sources.append(source)

        def common(
            label: int,
            index: int = index,
            case: dict[str, Any] = case,
            source: SourcePolicy = source,
            original: dict[str, Any] = original,
        ) -> dict[str, Any]:
            return dict(
                index=index,
                case=case,
                source_profile_id=source.identifier,
                source_snapshot_id=original["id"],
                original_index=index,
                original_policy_sha256="e" * 64,
                source_sha256="f" * 64,
                initialization_visits=100,
                work_label=label,
                iteration=1000 if label == 10000000 else 1,
                previous_work=label - 1,
                total_work=label + 3,
                last_iteration_visits=4,
                state_sha256="a" * 64,
                learning_path_sha256="b" * 64,
                receipt=dict(policy_sha256="c" * 64),
            )

        for label in config["original_average_replay_labels"]:
            prefixes[source.identifier, label] = dict(
                id=f"FICTIONAL-prefix-{index}-{label}",
                state_sha256="a" * 64,
                iteration=1000 if label == 10000000 else 1,
                total_work=label + 3,
            )
        for order, label in enumerate(config["cumulative_mass_work_labels"]):
            identifier = f"case-{index:03d}-mass-{label}"
            masses.append(
                dict(
                    **common(label),
                    id=identifier,
                    kind="cumulative_mass",
                    order=order,
                    file=f"masses/{identifier}.json.gz",
                )
            )
        variants = [f"current-{v}" for v in config["current_work_labels"]] + [
            "whole_average",
            "suffix_5m_10m",
            "suffix_9m_10m",
        ]
        for order, variant in enumerate(variants):
            label = config["current_work_labels"][order] if order < 5 else 10000000
            identifier = f"case-{index:03d}-{variant}"
            rows.append(
                dict(
                    **common(label),
                    id=identifier,
                    order=order,
                    kind="current"
                    if order < 5
                    else "whole_average"
                    if order == 5
                    else "suffix",
                    variant=variant,
                    file=f"snapshots/{identifier}.json.gz",
                    coverage=None if order < 5 else {"FICTIONAL_SCHEMA_ONLY": True},
                    current_movement={} if 0 < order < 5 else None,
                    window={"FICTIONAL_SCHEMA_ONLY": True} if order > 5 else None,
                    metrics=dict(
                        exact_exploitability_chips=0.0,
                        within_partition_gain_chips=0.0,
                        extra_information_gap_chips=0.0,
                        river_only_gain_exact_prefix_chips=0.0,
                        value_player_zero_chips=0.0,
                    ),
                    responses=[dict(target=0), dict(target=1)],
                    reply_sha256=[{}, {}],
                    maximum_accounting_error=0.0,
                )
            )
    data = HistoryInputs(config, Inputs({}, {}, {}, tuple(sources)), prefixes, {})
    workers = []
    for slot, assigned in enumerate(partition(64, 3)):
        events: list[dict[str, Any]] = [
            dict(kind="started", thread_environment=THREAD_ENV)
        ]
        for index in assigned:
            source = sources[index]
            for label in config["original_average_replay_labels"]:
                peer = prefixes[source.identifier, label]
                events.append(
                    dict(
                        kind="cell",
                        phase="prefix",
                        index=index,
                        work_label=label,
                        source_snapshot_id=peer["id"],
                        **{
                            k: peer[k]
                            for k in ("state_sha256", "iteration", "total_work")
                        },
                    )
                )
            for row in rows[index * 8 : index * 8 + 8]:
                events.append(dict(kind="cell", phase="profile", index=index, row=row))
            for row in masses[index * 3 : index * 3 + 3]:
                events.append(dict(kind="cell", phase="mass", index=index, row=row))
            events.append(
                dict(
                    kind="cell",
                    phase="trained",
                    index=index,
                    prefixes=3,
                    profiles=8,
                    masses=3,
                    work=10000003,
                    iteration=1000,
                )
            )
        events.append(
            dict(
                kind="done",
                summary=dict(
                    cells=len(assigned),
                    profiles=8 * len(assigned),
                    masses=3 * len(assigned),
                    prefixes=3 * len(assigned),
                ),
            )
        )
        workers.append(dict(slot=slot, exitcode=0, messages=events))
    batch = dict(
        status="completed", failure=None, assignments=partition(64, 3), workers=workers
    )
    return data, rows, masses, batch


def test_complete_fictional_grid_and_worker_ledger_contract(
    fictional_ledger: tuple[Any, ...],
) -> None:
    data, rows, masses, batch = fictional_ledger
    grid(rows, masses, data, "f" * 64)
    actual = gather(batch, data, "f" * 64)
    assert actual == (rows, masses)


@pytest.mark.parametrize(
    "mode",
    [
        "missing_profile",
        "missing_mass",
        "duplicate",
        "order",
        "index",
        "binding",
        "crossing",
        "kind",
        "label",
        "target",
        "nan",
        "pair",
        "path",
        "movement",
        "window",
    ],
)
def test_partial_altered_or_mismatched_current_grid_fails(
    fictional_ledger: tuple[Any, ...], mode: str
) -> None:
    data, original, boundary, _ = fictional_ledger
    rows, masses = copy.deepcopy(original), copy.deepcopy(boundary)
    if mode == "missing_profile":
        rows.pop()
    elif mode == "missing_mass":
        masses.pop()
    elif mode == "duplicate":
        rows[-1] = rows[-2]
    elif mode == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif mode == "index":
        rows[0]["index"] = False
    elif mode == "binding":
        rows[0]["source_sha256"] = "0" * 64
    elif mode == "crossing":
        rows[0]["previous_work"] = rows[0]["work_label"]
    elif mode == "kind":
        rows[0]["kind"] = "whole_average"
    elif mode == "label":
        rows[0]["work_label"] += 1
    elif mode == "target":
        rows[0]["responses"][0]["target"] = False
    elif mode == "nan":
        rows[0]["metrics"]["within_partition_gain_chips"] = float("nan")
    elif mode == "pair":
        rows[0]["learning_path_sha256"] = "0" * 64
    elif mode == "path":
        rows[0]["file"] = "../outside.json.gz"
    elif mode == "movement":
        rows[1]["current_movement"] = None
    elif mode == "window":
        rows[6]["window"] = None
    with pytest.raises(ArithmeticError):
        grid(rows, masses, data, "f" * 64)


@pytest.mark.parametrize(
    "mode",
    [
        "partial",
        "assignment",
        "exit",
        "thread",
        "done",
        "prefix",
        "duplicate_prefix",
        "missing_prefix",
        "trained",
        "wrong_worker",
    ],
)
def test_partial_worker_or_prefix_ledger_fails(
    fictional_ledger: tuple[Any, ...], mode: str
) -> None:
    data, _, _, original = fictional_ledger
    batch = copy.deepcopy(original)
    worker = batch["workers"][0]
    if mode == "partial":
        batch["status"] = "running"
    elif mode == "assignment":
        batch["assignments"][0].pop()
    elif mode == "exit":
        worker["exitcode"] = 1
    elif mode == "thread":
        worker["messages"][0]["thread_environment"] = {}
    elif mode == "done":
        worker["messages"].pop()
    elif mode == "prefix":
        worker["messages"][1]["state_sha256"] = "0" * 64
    elif mode == "duplicate_prefix":
        worker["messages"].insert(1, copy.deepcopy(worker["messages"][1]))
    elif mode == "missing_prefix":
        worker["messages"].pop(1)
    elif mode == "trained":
        next(e for e in worker["messages"] if e.get("phase") == "trained")["work"] += 1
    elif mode == "wrong_worker":
        worker["messages"][1]["index"] = 1
    with pytest.raises(ArithmeticError):
        gather(batch, data, "f" * 64)
