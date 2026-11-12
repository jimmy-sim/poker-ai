"""Admission plumbing fixtures; no real Hold'em trajectory or measured proof."""

import copy
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop import compact_full_run as own
from poker_ai.postflop.compact_full_context import Context, contexts, metrics
from poker_ai.postflop.compact_full_native_checks import (
    FIELDS,
    FORMAT,
    REFERENCE,
    comparison,
    validate,
)
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.public_range_definition import contract

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fixtures() -> list[Context]:
    return list(contexts(ROOT, software=True))


def uniform_snapshot(context: Context) -> dict[str, Any]:
    tree = context.scoring.partition
    return artifacts.capture(
        context,
        1,
        tree.normalize(tree.legal),
        tree.legal.copy(),
        np.zeros_like(tree.legal),
    )


def test_software_factory_exercises_all_twelve_bindings(
    fixtures: list[Context],
) -> None:
    assert len(fixtures) == 12
    assert len({(c.spot_file, c.representation) for c in fixtures}) == 12
    a, b = fixtures[:2]
    assert not np.array_equal(
        a.scoring.exact_to_partition, b.scoring.exact_to_partition
    )
    for context in fixtures:
        tree = context.scoring.partition
        policy = tree.normalize(tree.legal)
        np.testing.assert_array_equal(
            context.scoring.expand(policy),
            context.scoring.exact.normalize(context.scoring.exact.legal),
        )
    assert (
        fixtures[0].scoring.exact.terminal_values.tolist()
        == (-fixtures[6].scoring.exact.terminal_values).tolist()
    )


def test_zero_support_is_fallback_not_learned(fixtures: list[Context]) -> None:
    context = fixtures[0]
    tree = context.scoring.partition
    result = metrics(context, tree.normalize(tree.legal), np.zeros_like(tree.legal))
    assert result["coverage"] == 0
    assert result["all_own_reach_coverage"] == result["river_own_reach_coverage"] == 0
    assert result["positive_average_rows"] == 0
    assert result["initialization_work"] == 0


def test_own_snapshot_round_trip_and_no_overwrite(
    tmp_path: Path, fixtures: list[Context]
) -> None:
    context = fixtures[1]
    saved = uniform_snapshot(context)
    path = tmp_path / "0000.json.gz"
    receipt = artifacts.write_snapshot(path, saved)
    assert (
        artifacts.decode(context, artifacts.load_snapshot(tmp_path, receipt)) == saved
    )
    with pytest.raises(FileExistsError):
        artifacts.write_snapshot(path, saved)
    path.write_bytes(path.read_bytes() + b"corruption")
    with pytest.raises(ArithmeticError):
        artifacts.load_snapshot(tmp_path, receipt)


@pytest.mark.parametrize("field", ["file", "bytes", "sha256"])
def test_archive_receipt_rejects_changes(
    tmp_path: Path, fixtures: list[Context], field: str
) -> None:
    receipt = artifacts.write_snapshot(
        tmp_path / "0000.json.gz", uniform_snapshot(fixtures[0])
    )
    receipt[field] = "../elsewhere.json.gz" if field == "file" else 0
    with pytest.raises((ArithmeticError, ValueError)):
        artifacts.load_snapshot(tmp_path, receipt)


@pytest.mark.parametrize(
    "field",
    [
        "format",
        "context_sha256",
        "exact_sha256",
        "partition_sha256",
        "mapping_sha256",
        "actions",
        "total_node_work",
        "iteration",
        "metrics",
    ],
)
def test_snapshot_rejects_scalar_and_binding_corruption(
    fixtures: list[Context], field: str
) -> None:
    saved = uniform_snapshot(fixtures[1])
    saved[field] = True
    with pytest.raises((ArithmeticError, ValueError, TypeError)):
        artifacts.decode(fixtures[1], saved)


@pytest.mark.parametrize("field", ["policy", "strategy_sum", "regrets"])
@pytest.mark.parametrize("value", [True, "0.5", float("nan"), float("inf"), -1.0])
def test_snapshot_rejects_invalid_arrays(
    fixtures: list[Context], field: str, value: Any
) -> None:
    saved = uniform_snapshot(fixtures[0])
    saved[field][0][0] = value
    with pytest.raises((ArithmeticError, ValueError)):
        artifacts.decode(fixtures[0], saved)


def test_snapshot_rejects_valid_but_wrong_average(fixtures: list[Context]) -> None:
    saved = uniform_snapshot(fixtures[0])
    saved["strategy_sum"][0][0] = 100
    with pytest.raises(ArithmeticError, match="normalized"):
        artifacts.decode(fixtures[0], saved)


def scalar_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    config = contract(ROOT)
    rows = [
        dict(
            spot_file=s,
            representation=r,
            iteration=t,
            context_sha256=config["contexts"][s],
            metrics=dict(
                value_player_zero_chips=-0.125,
                best_response_zero_chips=0.25,
                best_response_one_chips=0.5,
                exploitability_chips=0.375,
            ),
        )
        for s in config["spot_files"]
        for r in config["representations"]
        for t in config["full"]["checkpoints"]
    ]
    own_fixture = dict(
        rows=rows, software_only=False, source=dict(fingerprint="fixture")
    )
    audit = dict(
        format=FORMAT,
        status="completed",
        failure=None,
        own_sha256="fixture",
        software_only=False,
        source=dict(fingerprint="fixture"),
        reference=REFERENCE,
        installed_license=dict(
            sha256=REFERENCE["license_sha256"],
            previously_read_record="docs/solver_validation.md",
        ),
        actual_admission=False,
        fresh_global_admission=False,
        comparisons=[comparison(r, {k: r["metrics"][k] for k in FIELDS}) for r in rows],
    )
    return own_fixture, audit


def test_native_self_comparison_zero_gap() -> None:
    own_fixture, audit = scalar_fixture()
    validate(own_fixture, audit, "fixture")
    assert all(r["maximum_error_chips"] == 0 for r in audit["comparisons"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "context",
        "value",
        "offset_roots",
        "error",
        "source",
        "partial",
        "reference",
        "input",
        "scope",
    ],
)
def test_native_schema_and_failure_checks(mutation: str) -> None:
    own_fixture, audit = scalar_fixture()
    row = audit["comparisons"][0]
    if mutation == "missing":
        audit["comparisons"].pop()
    elif mutation == "duplicate":
        audit["comparisons"][-1] = copy.deepcopy(row)
    elif mutation == "context":
        row["context_sha256"] = "different"
    elif mutation == "value":
        row["native"][FIELDS[0]] += 0.1
    elif mutation == "offset_roots":
        # Equal and opposite BR errors cancel in aggregate exploitability.
        row["native"][FIELDS[1]] += 0.1
        row["native"][FIELDS[2]] -= 0.1
    elif mutation == "error":
        row["maximum_error_chips"] = 1
    elif mutation == "source":
        audit["source"] = dict(fingerprint="changed")
    elif mutation == "partial":
        audit["status"] = "incomplete"
    elif mutation == "reference":
        audit["reference"] = dict(REFERENCE, version="changed")
    elif mutation == "input":
        audit["own_sha256"] = "changed"
    else:
        audit["actual_admission"] = True
    with pytest.raises((ArithmeticError, ValueError)):
        validate(own_fixture, audit, "fixture")


@pytest.mark.parametrize("value", [True, "0", float("nan"), float("inf")])
def test_nonfinite_or_nonnumeric_native_scalars(value: Any) -> None:
    own_fixture, audit = scalar_fixture()
    audit["comparisons"][0]["native"][FIELDS[0]] = value
    with pytest.raises(ValueError):
        validate(own_fixture, audit, "fixture")


def test_full_runner_retains_completed_checkpoint_on_failure(
    tmp_path: Path, fixtures: list[Context], monkeypatch: pytest.MonkeyPatch
) -> None:
    class FailingSolver:
        def __init__(self, tree: Any) -> None:
            self.iteration = 0
            self.strategy_sum = tree.legal.copy()
            self.regrets = np.zeros_like(tree.legal)
            self.average_policy = tree.normalize(tree.legal)

        def step(self) -> None:
            if self.iteration == 1:
                raise RuntimeError("unit fixture interrupted after first checkpoint")
            self.iteration += 1

    monkeypatch.setattr(
        artifacts, "source", lambda *a, **k: dict(fingerprint="fixture")
    )
    from poker_ai.postflop import compact_full_gate

    monkeypatch.setattr(compact_full_gate, "checks", lambda *a, **k: {})
    monkeypatch.setattr(artifacts, "check_source", lambda *a, **k: None)
    monkeypatch.setattr(own, "runtime", lambda: {})
    monkeypatch.setattr(own, "check_runtime", lambda *a, **k: None)
    monkeypatch.setattr(own, "contexts", lambda *a, **k: iter(fixtures))
    monkeypatch.setattr(own, "solver", FailingSolver)
    path = tmp_path / "own.json"
    result = own.run(
        ROOT,
        path,
        software=True,
        started=time.perf_counter(),
        check_path=ROOT / "configs/compact-public-range.json",
    )
    assert result["status"] == "incomplete"
    assert result["failure"]["type"] == "RuntimeError"
    assert len(result["rows"]) == 1
    assert list((tmp_path / "snapshots").glob("*.json.gz"))
    assert json.loads(path.read_text()) == result
    with pytest.raises(ArithmeticError):
        artifacts.inventory(result, contract(ROOT))


def test_same_kernel_tiny_fixture_agrees_with_scalar_training(
    fixtures: list[Context],
) -> None:
    pytest.importorskip("numba")
    from dataclasses import fields
    from types import SimpleNamespace
    from typing import cast

    from poker_ai.finite import ArrayTree
    from poker_ai.postflop.jit_cfr import FusedCFRPlus
    from poker_ai.postflop.matrix import MatrixTree
    from poker_ai.postflop.tree import SpotTree
    from poker_ai.solver_validation.arithmetic import ScalarCFRPlus

    # A structural shim supplies the scalar oracle's ragged child list. It is
    # not a poker source and is never used by the real source factory.
    tree = fixtures[1].scoring.partition
    matrix = MatrixTree(
        **{f.name: getattr(tree, f.name) for f in fields(ArrayTree)},
        source=cast(
            SpotTree,
            SimpleNamespace(
                children=[
                    [int(v) for v in row[valid]]
                    for row, valid in zip(tree.children, tree.valid, strict=True)
                ]
            ),
        ),
        exact_to_abstract=np.arange(len(tree.keys), dtype=np.int64),
        encoding="exact",
        node_actions=(),
    )
    fused = FusedCFRPlus(matrix)
    scalar = ScalarCFRPlus(
        matrix, fused_values=True, fused_regrets=False, fused_averages=True
    )
    for _ in range(16):
        fused.step()
        scalar.step()
    np.testing.assert_array_equal(fused.regrets[:, :2], scalar.regrets)
    np.testing.assert_array_equal(fused.strategy_sum[:, :2], scalar.averages)


def test_tiny_native_adapter_checks_both_roots(fixtures: list[Context]) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.solver_validation.controlled_pipeline import license_record
    from poker_ai.solver_validation.matched_array_reference import ScalarReference

    license_record(dict(native_reference=REFERENCE))
    context = fixtures[1]
    raw = uniform_snapshot(context)
    policy = context.scoring.expand(np.asarray(raw["policy"], dtype=np.float64))
    ref = ScalarReference(context.scoring.exact)
    result = comparison(
        raw,
        dict(
            value_player_zero_chips=ref.value(policy),
            best_response_zero_chips=ref.response_value(policy, 0),
            best_response_one_chips=ref.response_value(policy, 1),
        ),
    )
    assert result["maximum_error_chips"] <= 1e-9


def test_fixed_definition_bytes_still_match() -> None:
    config = contract(ROOT)
    assert len(config["representations"]) == 6
    assert (
        sha(config)
        == "794c4938ce7bbe9d1170fcc091e5dc5f02ab7583f58e776eec461a4cb07d5d70"
    )


def test_commit_source_binds_actual_git_blob() -> None:
    import hashlib
    import subprocess

    name = "src/poker_ai/__init__.py"
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    checksum = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    artifacts.commit_sources(ROOT, commit, {name: checksum})
    with pytest.raises(ArithmeticError):
        artifacts.commit_sources(ROOT, commit, {name: "changed"})


def fake_complete_run(
    tmp_path: Path, fixtures: list[Context], monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Exercise all actual checkpoint loops with a marked fake solver, not proof."""
    from poker_ai.postflop import compact_full_gate

    class FakeSolver:
        def __init__(self, tree: Any) -> None:
            self.iteration = 0
            self.strategy_sum = tree.legal.copy()
            self.regrets = np.zeros_like(tree.legal)
            self.average_policy = tree.normalize(tree.legal)

        def step(self) -> None:
            self.iteration += 1
            self.strategy_sum += 1 * (self.average_policy > 0)

    monkeypatch.setattr(
        artifacts, "source", lambda *a, **k: dict(fingerprint="fixture")
    )
    monkeypatch.setattr(artifacts, "check_source", lambda *a, **k: None)
    monkeypatch.setattr(own, "runtime", lambda: {})
    monkeypatch.setattr(own, "check_runtime", lambda *a, **k: None)
    monkeypatch.setattr(own, "contexts", lambda *a, **k: iter(fixtures))
    monkeypatch.setattr(own, "solver", FakeSolver)
    monkeypatch.setattr(compact_full_gate, "checks", lambda *a, **k: {})
    output = tmp_path / "own.json"
    result = own.run(
        ROOT,
        output,
        software=True,
        started=time.perf_counter(),
        check_path=ROOT / "configs/compact-public-range.json",
    )
    assert result["status"] == "completed"
    assert result["replay"]["profiles_checked"] == 72
    return output


def test_full_capture_and_replay_manifest_integration(
    tmp_path: Path, fixtures: list[Context], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = fake_complete_run(tmp_path, fixtures, monkeypatch)
    assert len(list((tmp_path / "snapshots").glob("*.json.gz"))) == 72
    result = json.loads(path.read_text())
    result["rows"][0]["total_node_work"] += 1
    path.write_text(json.dumps(result))
    with pytest.raises(ArithmeticError):
        own.replay(ROOT, path)


def test_native_mid_audit_failure_retains_completed_comparisons(
    tmp_path: Path, fixtures: list[Context], monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.solver_validation import compact_full as native

    path = fake_complete_run(tmp_path, fixtures, monkeypatch)
    monkeypatch.setattr(
        artifacts, "published", lambda *a, **k: "unit publication fixture"
    )
    monkeypatch.setattr(native, "measurement", lambda *a, **k: {})
    monkeypatch.setattr(native, "runtime", lambda: {})
    monkeypatch.setattr(native, "license_record", lambda *a, **k: {})
    monkeypatch.setattr(native, "contexts", lambda *a, **k: iter(fixtures))

    class FailingReference:
        def __init__(self, tree: Any) -> None:
            self.calls = 0

        def value(self, policy: Any) -> float:
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("unit native failure after one completed comparison")
            return 0.0

        def response_value(self, policy: Any, target: int) -> float:
            return 1.0

    monkeypatch.setattr(native, "ScalarReference", FailingReference)
    output = tmp_path / "native.json"
    result = native.run(ROOT, path, output, started=time.perf_counter())
    assert result["status"] == "incomplete"
    assert result["failure"]["type"] == "RuntimeError"
    assert len(result["comparisons"]) == 1
    assert result["actual_admission"] is False
    assert json.loads(output.read_text()) == result
