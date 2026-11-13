"""Effective code/counters/namespace and gate negatives; not study admission."""

import copy
import importlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def modules(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return {
        name: importlib.import_module("compact_cached." + name)
        for name in ("cache", "source", "contract", "clock", "admission", "workers")
    }


def counts() -> dict[str, Any]:
    return dict(
        enabled=True,
        requests=10,
        original_traversals=2,
        hits=8,
        rejections=0,
        fallbacks=0,
        successful_proofs=2,
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "disabled",
        "bool",
        "negative",
        "missing",
        "extra",
        "sum",
        "proofs",
        "rejection",
        "fallback",
    ],
)
def test_cache_counter_schema(modules: dict[str, Any], damage: str | None) -> None:
    row = counts()
    if damage == "disabled":
        row["enabled"] = False
    elif damage == "bool":
        row["hits"] = True
    elif damage == "negative":
        row["hits"] = -1
    elif damage == "missing":
        del row["enabled"]
    elif damage == "extra":
        row["reference_strategy"] = []
    elif damage == "sum":
        row["requests"] += 1
    elif damage == "proofs":
        row["successful_proofs"] += 1
    elif damage == "rejection":
        row["rejections"] = 1
    elif damage == "fallback":
        row["fallbacks"] = 5
    if damage:
        with pytest.raises(ArithmeticError):
            modules["cache"].check_counters(row)
    else:
        modules["cache"].check_counters(row)


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "implementation",
        "missing_parent",
        "worker_missing",
        "worker_source",
        "worker_disabled",
        "worker_count",
        "done_count",
    ],
)
def test_every_process_needs_effective_execution(
    modules: dict[str, Any], monkeypatch: pytest.MonkeyPatch, damage: str | None
) -> None:
    tool = modules["cache"]
    monkeypatch.setattr(tool, "variant", lambda r: {"SYNTHETIC_UNIT": True})
    worker = dict(
        messages=[
            dict(
                kind="done",
                summary=dict(
                    validation_cache=counts(),
                    implementation_sha256=modules["contract"].CONFIG_SHA,
                ),
            )
        ]
    )
    row = dict(
        implementation_config={"SYNTHETIC_UNIT": True},
        validation_cache=counts(),
        training_batch=dict(workers=[copy.deepcopy(worker) for _ in range(3)]),
    )
    if damage == "implementation":
        row["implementation_config"] = {}
    elif damage == "missing_parent":
        del row["validation_cache"]
    elif damage == "worker_missing":
        del row["training_batch"]["workers"][0]["messages"][0]["summary"][
            "validation_cache"
        ]
    elif damage == "worker_source":
        row["training_batch"]["workers"][0]["messages"][0]["summary"][
            "implementation_sha256"
        ] = "OLD_SOURCE"
    elif damage == "worker_disabled":
        row["training_batch"]["workers"][0]["messages"][0]["summary"][
            "validation_cache"
        ]["enabled"] = False
    elif damage == "worker_count":
        row["training_batch"]["workers"].pop()
    elif damage == "done_count":
        row["training_batch"]["workers"][0]["messages"] *= 2
    if damage:
        with pytest.raises(ArithmeticError):
            tool.check_execution(ROOT, row)
    else:
        tool.check_execution(ROOT, row)
        row["native_batch"] = row.pop("training_batch")
        tool.check_execution(ROOT, row)


def test_full_source_binds_all_actual_adapter_files(modules: dict[str, Any]) -> None:
    tool = modules["source"]
    saved = tool.source(ROOT)
    assert (
        saved["fingerprint"]
        != "2ace916f0812efd1d93d0f16f533a9ecab15deceda482e94553df9a158d6a989"
    )
    assert len(saved["sha256"]) == 380
    for name in tool.MODULES:
        assert f"{tool.PACKAGE}/{name}.py" in saved["sha256"]
    assert tool.ENTRY in saved["sha256"]
    name = tool.PACKAGE + "/cache.py"
    del saved["sha256"][name]
    from poker_ai.postflop.learning_artifacts import sha

    saved["fingerprint"] = sha(saved["sha256"])
    with pytest.raises(ArithmeticError, match="implementation source changed"):
        tool.check_source(ROOT, saved)


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink"])
def test_module_inventory_is_not_implicit(
    modules: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    tool = modules["source"]
    # The path guard is tested on the actual source; simulate a transplanted
    # module identity for these inventory-only fixtures, never a real receipt.
    folder = tmp_path / tool.PACKAGE
    folder.mkdir(parents=True)
    for name in tool.MODULES:
        (folder / (name + ".py")).write_text("# UNIT\n")
    monkeypatch.setattr(tool, "__file__", str(folder / "source.py"))
    monkeypatch.setattr(tool, "variant", lambda root: {})
    if kind == "extra":
        (folder / "unbound.py").write_text("# UNIT")
    elif kind == "missing":
        (folder / "cache.py").unlink()
    else:
        (folder / "cache.py").unlink()
        (folder / "cache.py").symlink_to(folder / "cli.py")
    with pytest.raises(ArithmeticError, match="module inventory"):
        tool.source(tmp_path)


def test_same_scientific_contract_and_fixed_formulas(modules: dict[str, Any]) -> None:
    from poker_ai.evaluation import compact_opponent_admission as old
    from poker_ai.evaluation.compact_opponent_contract import contract
    from poker_ai.evaluation.opponent_learning_design import COST

    assert modules["contract"].contract(ROOT) == contract(ROOT)
    training = {"T": 610.943356249918}
    for native in (300.0, 390.0, 545.10507225):
        a = [
            dict(scope=COST, repetition=i, complete_command=dict(seconds=309.0))
            for i in range(3)
        ]
        b = [
            dict(scope=COST, repetition=i, complete_command=dict(seconds=native))
            for i in range(3)
        ]
        assert modules["admission"].forecast(training, a, b) == old.forecast(
            training, a, b
        )


@pytest.mark.parametrize(
    "payload", [{}, {"saved_policy": []}, {"reference_strategy": []}]
)
def test_worker_payload_is_structural_only(
    modules: dict[str, Any], payload: dict[str, Any]
) -> None:
    with pytest.raises(ValueError, match="only structural"):
        modules["workers"].training(0, list(range(0, 30, 3)), payload, lambda e: None)


def test_output_namespace_and_late_start(modules: dict[str, Any]) -> None:
    c = modules["clock"]
    for operation in (
        "software-own",
        "software-audit",
        "forecast",
        "admit",
        "study",
        "audit",
    ):
        assert "results/compact-cached-learning/" in str(
            c.output_path(ROOT, c.arguments([operation]))
        )
    now = datetime.now(UTC)
    with pytest.raises(TimeoutError):
        c.schedule("study", (now + timedelta(seconds=11099)).isoformat(), now)
    c.schedule("study", (now + timedelta(seconds=11100)).isoformat(), now)
    assert c.CAPS["study"] == 7200 and c.CAPS["audit"] == 900


def test_fresh_worker_cache_imports_stay_reference_free() -> None:
    code = """from pathlib import Path
from compact_cached.cache import cached
from poker_ai.evaluation.compact_opponent_guard import isolated,runtime
with isolated(worker=True),cached(Path.cwd()):
 names=('pyspiel','open_spiel.python.policy',
        'poker_ai.solver_validation.reference')
 for name in names:
  try: __import__(name)
  except AssertionError: pass
  else: raise AssertionError('reference import allowed')
runtime(worker=True)
print('all3 reference imports rejected with actual cache hooks')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=dict(
            os.environ,
            PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(ROOT / "scripts"))),
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all3 reference imports rejected" in result.stdout


@pytest.mark.parametrize(
    "damage", [None, "implementation", "disabled", "parent_missing"]
)
def test_worker_rejects_a_cross_family_permit_before_publication(
    modules: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str | None,
) -> None:
    import numpy as np

    tool = modules["workers"]
    unit = {"UNIT_EXECUTION_NOT_A_REAL_PERMIT": True}
    monkeypatch.setattr(modules["cache"], "variant", lambda r: unit)
    monkeypatch.setattr(
        tool,
        "contract",
        lambda r: dict(
            prefix_runtime=dict(python=sys.version.split()[0], numpy=np.__version__)
        ),
    )
    path = tmp_path / tool.ADMISSION
    path.parent.mkdir(parents=True)
    saved: dict[str, Any] = dict(
        implementation_config=unit,
        validation_cache=counts(),
        source_sha256="a" * 64,
        status="compact_own_opponent_learning_admitted",
        long_run_admitted=True,
        new_agent_default=False,
        fresh_global_admission=False,
        maximum_own_seconds=7200,
        maximum_native_seconds=900,
    )
    if damage == "implementation":
        saved["implementation_config"] = {}
    elif damage == "disabled":
        saved["validation_cache"]["enabled"] = False
    elif damage == "parent_missing":
        del saved["validation_cache"]
    path.write_text(json.dumps(saved))
    publications = []
    monkeypatch.setattr(tool, "published", lambda *a: publications.append(path))
    from poker_ai.postflop.river_study import digest

    if damage:
        with pytest.raises(ArithmeticError):
            tool.worker_admission(tmp_path, "a" * 64, digest(path))
        assert not publications
    else:
        tool.worker_admission(tmp_path, "a" * 64, digest(path))
        assert publications == [path]


@pytest.mark.parametrize(
    "parity",
    [None, {}, {"status": "all324policies216books30warms_exact_with_original_own_toy"}],
)
def test_formal_toy_publication_requires_parity_record(
    modules: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    parity: dict[str, Any] | None,
) -> None:
    from poker_ai.evaluation.opponent_learning_design import TOY

    tool = modules["cache"]
    monkeypatch.setattr(tool, "variant", lambda root: {"UNIT_ONLY": True})
    own = dict(
        implementation_config={"UNIT_ONLY": True},
        validation_cache=counts(),
        status="completed_own_native_pending",
        scope=TOY,
        software_vector_parity=parity,
    )
    if parity:
        tool.check_execution(ROOT, own)
    else:
        with pytest.raises(ArithmeticError, match="parity evidence"):
            tool.check_execution(ROOT, own)
