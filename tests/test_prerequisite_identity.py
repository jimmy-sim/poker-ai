"""Synthetic prerequisite graph checks; no archived reader or native solver."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import audit_receipt_prerequisites as audit
import numpy as np
import pytest
from prerequisite_identity_support import disjoint, observe

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.controlled_reply_inputs import Inputs, SourcePolicy
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.postflop.controlled_scoring import ScoringContext


def synthetic() -> HistoryInputs:
    policies = []
    for index in range(64):
        case = {
            "spot_file": "fictional",
            "representation": "synthetic",
            "traversal": "external",
            "seed": index,
            "regret_rule": "signed",
            "average_weight": "uniform",
        }
        policies.append(SourcePolicy(case, {"index": index}, np.array([float(index)])))
    base = Inputs(
        {},
        {},
        {(str(i), "synthetic"): cast(ScoringContext, f"context-{i}") for i in range(4)},
        tuple(policies),
    )
    labels = [100, 1000, 10000]
    prefixes = {
        (policy.identifier, label): {"index": index, "label": label}
        for index, policy in enumerate(policies)
        for label in labels
    }
    replies = {
        (policy.identifier, target): Reply(target, float(index), (0,))
        for index, policy in enumerate(policies)
        for target in (0, 1)
    }
    return HistoryInputs(
        {"original_average_replay_labels": labels, "input_sha256": {}},
        base,
        prefixes,
        replies,
    )


def test_fresh_synthetic_graphs_match_and_are_disjoint() -> None:
    left, right = synthetic(), synthetic()
    a, first = observe(left)
    b, second = observe(right)
    assert first == second
    assert first.array_count == 64
    disjoint(a, b)
    left.config["extra"] = left.base.policies[0].policy
    assert observe(left)[1].witness != second.witness
    assert observe(right)[1] == second


def test_internal_alias_changes_complete_witness() -> None:
    data = synthetic()
    shared = np.array([1.0, 2.0])
    data.config["aliases"] = [shared, shared]
    first = observe(data)[1].witness
    data.config["aliases"] = [shared, shared.copy()]
    assert observe(data)[1].witness != first


def test_cross_graph_shared_storage_rejects() -> None:
    left, right = synthetic(), synthetic()
    right.base.policies[0].policy[:] = left.base.policies[0].policy
    # Explicitly share a mutable object across otherwise fresh graphs.
    right.config["shared"] = left.config
    with pytest.raises(ArithmeticError, match="share mutable"):
        disjoint(observe(left)[0], observe(right)[0])


def test_overlapping_views_and_unknown_type_reject() -> None:
    data = synthetic()
    backing = np.arange(4.0)
    data.config["views"] = [backing[:3], backing[1:]]
    with pytest.raises(ArithmeticError, match="overlapping"):
        observe(data)
    data.config["views"] = object()
    with pytest.raises(ArithmeticError, match="unsupported"):
        observe(data)


def test_incomplete_semantic_inventory_rejects() -> None:
    data = synthetic()
    data.prefixes.pop(next(iter(data.prefixes)))
    with pytest.raises(ArithmeticError, match="inventory"):
        observe(data)


def test_outer_timeout_retains_partial_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def expire(*args: Any, **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(args[0], audit.LIMIT)

    monkeypatch.setattr("audit_receipt_prerequisites.subprocess.run", expire)
    output = tmp_path / "partial"
    monkeypatch.setattr(sys, "argv", ["audit_receipt_prerequisites.py", str(output)])
    with pytest.raises(SystemExit) as exc:
        audit.main()
    assert exc.value.code == 1
    saved = json.loads((output / "outer.json").read_text())
    assert saved["status"] == "timed_out"
    assert saved["outer_cap_seconds"] == 180
    assert (output / "child.log").is_file()


def test_seven_fresh_loads_complete_with_exact_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "uv.lock").write_text("synthetic lock")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "revision", lambda: ("synthetic-head", False))
    monkeypatch.setattr(audit, "pinned_bytes", lambda root: {"input": "fixed"})
    monkeypatch.setattr(audit, "prerequisites", lambda root: synthetic())
    audit.child(tmp_path)
    saved = json.loads((tmp_path / "child.json").read_text())
    assert saved["status"] == "seven_identical_fresh_disjoint_prerequisites"
    assert [row["index"] for row in saved["observations"]] == list(range(7))
    assert len({row["witness"] for row in saved["observations"]}) == 1
    assert saved["seed"] is None


def test_failed_later_load_retains_earlier_observations(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "uv.lock").write_text("synthetic lock")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "revision", lambda: ("synthetic-head", False))
    monkeypatch.setattr(audit, "pinned_bytes", lambda root: {"input": "fixed"})
    calls = 0

    def load(root: Path) -> HistoryInputs:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise ArithmeticError("synthetic load failure")
        return synthetic()

    monkeypatch.setattr(audit, "prerequisites", load)
    with pytest.raises(ArithmeticError, match="synthetic load failure"):
        audit.child(tmp_path)
    saved = json.loads((tmp_path / "child.json").read_text())
    assert saved["status"] == "running"
    assert len(saved["observations"]) == 3
