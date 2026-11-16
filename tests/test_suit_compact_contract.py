"""New effective source, process roles, publication and unchanged math tests."""

import ast
import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from compact_suit import admission, cache, contract
from compact_suit.normalization import Normalization
from compact_suit.source import MODULES, source

ROOT = Path(__file__).resolve().parents[1]


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


def state(*, parent: bool) -> dict[str, Any]:
    n = Normalization(contract.variant(ROOT)["normalization"], parent=parent)
    with n.installed():
        pass
    return n.summary()


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "missing_parent",
        "live_parent",
        "wrong_parent",
        "missing_worker",
        "optimized_worker",
        "worker_pid",
        "worker_bool",
        "bad_config_type",
        "extra_card_cache",
        "recall_disabled",
        "worker_source",
    ],
)
def test_all_processes_need_correct_effective_execution(damage: str | None) -> None:
    parent = state(parent=True)
    workers = []
    for i in range(3):
        worker = state(parent=False)
        workers.append(
            dict(
                pid=worker["pid"],
                slot=i,
                messages=[
                    dict(
                        kind="done",
                        summary=dict(
                            implementation_sha256=contract.CONFIG_SHA,
                            normalization=worker,
                            validation_cache=counts(),
                        ),
                    )
                ],
            )
        )
    row = dict(
        implementation_config=contract.variant(ROOT),
        validation_cache=counts(),
        normalization=parent,
        native_batch=dict(workers=workers),
    )
    target = workers[0]["messages"][0]["summary"]
    if damage == "missing_parent":
        del row["normalization"]
    elif damage == "live_parent":
        parent.update(active=True, restored=False, status="running")
    elif damage == "wrong_parent":
        parent.update(role="worker", enabled=False)
    elif damage == "missing_worker":
        del target["normalization"]
    elif damage == "optimized_worker":
        target["normalization"] = copy.deepcopy(parent)
    elif damage == "worker_pid":
        workers[0]["pid"] += 1
    elif damage == "worker_bool":
        target["normalization"]["requests"] = False
    elif damage == "bad_config_type":
        row["implementation_config"]["normalization"]["adaptive_full_hand_cache"] = 0
    elif damage == "extra_card_cache":
        parent["full_hand_cache_hits"] = 1
    elif damage == "recall_disabled":
        row["validation_cache"]["enabled"] = False
    elif damage == "worker_source":
        target["implementation_sha256"] = "0" * 64
    if damage is None:
        cache.check_execution(ROOT, row)
    else:
        with pytest.raises(ArithmeticError):
            cache.check_execution(ROOT, row)


def test_complete_source_and_unchanged_scientific_inputs() -> None:
    saved = source(ROOT)
    assert len(saved["sha256"]) == 433
    assert len(MODULES) == 13
    old = json.loads(
        (ROOT / "results/suit-candidates/software/child/child.json").read_text()
    )["source"]["sha256"]
    assert len(old) == 418 and all(saved["sha256"][k] == v for k, v in old.items())
    c = contract.variant(ROOT)
    assert c["caps"] == dict(
        cost_native=900,
        cost_own=900,
        forecast=900,
        software_shared=180,
        study_native=900,
        study_own=7200,
    )
    assert contract.contract(ROOT)["seeds"] == [20261301, 20261302, 20261303]
    if saved["dirty"]:
        with pytest.raises(ValueError):
            source(ROOT, clean=True)
    else:
        assert source(ROOT, clean=True)["fingerprint"] == saved["fingerprint"]


def test_source_and_cache_worker_imports_are_reference_free() -> None:
    code = """from pathlib import Path
from compact_suit.source import source
from compact_suit.cache import cached
from poker_ai.evaluation.compact_opponent_guard import isolated
with isolated(worker=True),cached(Path.cwd(),parent=False):
    assert len(source(Path.cwd())["sha256"])==433
print("reference-free complete source and inactive worker normalization")
"""
    env = dict(
        os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts")
    )
    subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, check=True
    )


@pytest.mark.parametrize("name", ["training_forecast", "forecast", "kernel_geometry"])
def test_forecast_math_is_the_original_function(name: str) -> None:
    old = ast.parse((ROOT / "scripts/compact_cached/admission.py").read_text())
    new = ast.parse((ROOT / "scripts/compact_suit/admission.py").read_text())

    def pick(tree: ast.Module) -> ast.FunctionDef:
        return next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
        )

    assert ast.dump(pick(old), include_attributes=False) == ast.dump(
        pick(new), include_attributes=False
    )


def test_old_failed_forecast_cannot_become_a_new_admission() -> None:
    old = json.loads(
        (ROOT / "results/compact-cached-learning/forecast.json").read_text()
    )
    assert old["forecast"]["strict_native_pass"] is False
    assert old["forecast"]["guarded_native_seconds"] > 900
    with pytest.raises((ArithmeticError, FileNotFoundError, KeyError)):
        admission.permit(ROOT, old)


def test_real_runtime_guard_is_explicit() -> None:
    import numpy as np

    expected = contract.contract(ROOT)["prefix_runtime"]
    if (
        sys.version.split()[0] == expected["python"]
        and np.__version__ == expected["numpy"]
    ):
        contract.require_prefix_runtime(ROOT)
    else:
        with pytest.raises(ArithmeticError, match="original Python/NumPy"):
            contract.require_prefix_runtime(ROOT)


@pytest.mark.parametrize("positive", [False, True])
def test_cost_parent_requires_actual_reduced_coverage(positive: bool) -> None:
    from poker_ai.evaluation.opponent_learning_design import COST

    n = Normalization(contract.variant(ROOT)["normalization"], parent=True)
    with n.installed():
        if positive:
            n.call((0, 4), ())
    row = dict(
        implementation_config=contract.variant(ROOT),
        validation_cache=counts(),
        normalization=n.summary(),
        scope=COST,
        operation="cost-own",
    )
    if positive:
        cache.check_execution(ROOT, row)
    else:
        with pytest.raises(ArithmeticError, match="positive actual parent"):
            cache.check_execution(ROOT, row)
