"""Mutation/failure boundaries and complete tiny replay, not a skipped guard."""

import copy
import importlib.util
import os
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.finite import ArrayTree
from poker_ai.postflop.reply_trace import require_recall, response_profile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0" * 64  # Synthetic version salt; real runner checks the pinned source.


@pytest.fixture
def tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "recall_cache_fixture", ROOT / "scripts/recall_cache_support.py"
    )
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tree() -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[:3] = [[1, 2], [3, 4], [5, 6]]
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[:3] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, 0, 0, -2, -2, -2, -2], dtype=np.int64),
        np.array([0, 1, 2, -1, -1, -1, -1], dtype=np.int64),
        ("root", "left", "right"),
        ((0, 1),) * 3,
        np.zeros(3, dtype=np.int64),
        np.ones((3, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        np.array([0.0, 0.0, 0.0, 1.0, -1.0, 2.0, -2.0]),
        (np.array([0], dtype=np.int64), np.array([1, 2], dtype=np.int64)),
    )


def test_successful_proof_is_reused_without_retaining_strategy(tool: Any) -> None:
    t = tree()
    cache = tool.RecallProofs(require_recall, VERSION, enabled=True)
    for _ in range(5):
        cache(t)
    assert cache.summary() == dict(
        requests=5,
        original_traversals=1,
        hits=4,
        rejections=0,
        fallbacks=0,
        successful_proofs=1,
        enabled=True,
    )
    assert all(isinstance(x, str) and len(x) == 64 for x in cache.proven)


@pytest.mark.parametrize(
    "field", ["children", "valid", "player", "information", "levels"]
)
def test_every_structural_mutation_revalidates(tool: Any, field: str) -> None:
    t = tree()
    cache = tool.RecallProofs(require_recall, VERSION, enabled=True)
    cache(t)
    if field == "children":
        t.children[0, 0] = 2
    elif field == "valid":
        t.valid[0, 0] = False
    elif field == "player":
        t.player[1] = 1
    elif field == "information":
        t.information[2] = 1  # Forgets which own root action was taken.
    else:
        t.levels[1][:] = [2, 1]
    try:
        require_recall(t)
    except Exception as expected:
        with pytest.raises(type(expected)):
            cache(t)
    else:
        cache(t)
    assert cache.traversals == 2 and cache.hits == 0


def test_rejected_check_is_never_a_cached_success_and_restored_tree_reuses(
    tool: Any,
) -> None:
    t = tree()
    cache = tool.RecallProofs(require_recall, VERSION, enabled=True)
    cache(t)
    t.information[2] = 1
    for _ in range(2):
        with pytest.raises(ValueError, match="perfect recall"):
            cache(t)
    assert cache.rejections == 2 and len(cache.proven) == 1
    t.information[2] = 2
    cache(t)
    assert cache.hits == 1 and cache.traversals == 3


def test_equal_depth_failure_is_preserved(tool: Any) -> None:
    t = tree()
    children = np.zeros((8, 2), dtype=np.int64)
    children[[0, 1, 5]] = [[1, 2], [3, 4], [6, 7]]
    children[2, 0] = 5
    valid = np.zeros((8, 2), dtype=np.bool_)
    valid[[0, 1, 5]] = True
    valid[2, 0] = True
    t = replace(
        t,
        children=children,
        valid=valid,
        player=np.array([-1, 0, -1, -2, -2, 0, -2, -2], dtype=np.int64),
        information=np.array([-1, 0, -1, -1, -1, 0, -1, -1], dtype=np.int64),
        levels=tuple(np.array(a, dtype=np.int64) for a in ([0], [1, 2], [5])),
    )
    with pytest.raises(ValueError, match="equal-depth"):
        require_recall(t)
    cache = tool.RecallProofs(require_recall, VERSION, enabled=True)
    with pytest.raises(ValueError, match="equal-depth"):
        cache(t)
    assert not cache.proven


@pytest.mark.parametrize("kind", ["object", "float", "subclass", "levels_list"])
def test_unsupported_inputs_use_original_checker_each_time(
    tool: Any, kind: str
) -> None:
    t = tree()
    if kind in ("object", "float"):
        t = replace(
            t, information=t.information.astype(object if kind == "object" else float)
        )
    elif kind == "subclass":

        class Special(np.ndarray[Any, Any]):
            pass

        t = replace(t, information=t.information.view(Special))
    else:
        t = replace(t, levels=cast(Any, list(t.levels)))
    cache = tool.RecallProofs(require_recall, VERSION, enabled=True)
    cache(t)
    cache(t)
    assert cache.traversals == 2 and cache.fallbacks == 2 and not cache.proven


def test_shape_dtype_version_and_levels_are_in_key(tool: Any) -> None:
    t = tree()
    key = tool.geometry(t, VERSION)
    assert key != tool.geometry(t, "1" * 64)
    assert key != tool.geometry(
        replace(t, children=t.children.astype(np.int32)), VERSION
    )
    assert key != tool.geometry(
        replace(t, levels=t.levels + (np.array([], dtype=np.int64),)), VERSION
    )
    assert key == tool.geometry(
        replace(t, children=np.asfortranarray(t.children)), VERSION
    )


def test_mutation_during_original_validation_is_not_certified(tool: Any) -> None:
    t = tree()

    def mutating(value: ArrayTree) -> None:
        require_recall(value)
        value.information[2] = 1

    cache = tool.RecallProofs(mutating, VERSION, enabled=True)
    with pytest.raises(ValueError, match="changed during"):
        cache(t)
    assert not cache.proven and cache.rejections == 1


def test_policy_payoffs_and_chance_data_are_not_cached(tool: Any) -> None:
    from poker_ai.postflop import reply_trace

    t = tree()
    policy = np.full((3, 2), 0.5)
    expected = response_profile(t, policy, 0)
    cache = tool.RecallProofs(require_recall, VERSION, enabled=True)
    with patch.object(reply_trace, "require_recall", cache):
        assert np.array_equal(response_profile(t, policy, 0), expected)
        t.terminal_values[5], t.terminal_values[6] = -10.0, 20.0
        new = response_profile(t, policy, 0)
        t.chance_reach[:] = 0.5
        cache(t)
    assert not np.array_equal(new, expected)
    assert cache.traversals == 1 and cache.hits == 2


@pytest.mark.parametrize("version", ["", "0" * 63, "g" * 64])
def test_validator_version_is_required(tool: Any, version: str) -> None:
    with pytest.raises(ValueError, match="SHA256"):
        tool.RecallProofs(require_recall, version, enabled=True)


def test_uncached_control_forwards_every_request(tool: Any) -> None:
    c = tool.RecallProofs(require_recall, VERSION, enabled=False)
    c(tree())
    c(tree())
    assert c.requests == c.traversals == 2 and not c.proven and c.hits == 0


def test_hook_aliases_restore_even_on_failure(tool: Any) -> None:
    import importlib

    c = tool.contract(ROOT)
    modules = [importlib.import_module(x.rsplit(".", 1)[0]) for x in c["hooks"]]
    originals = [vars(m)["require_recall"] for m in modules]
    with pytest.raises(RuntimeError, match="fixture stop"):
        with tool.hooks(c, enabled=True) as cache:
            assert all(vars(m)["require_recall"] is cache for m in modules)
            raise RuntimeError("fixture stop")
    assert all(
        vars(m)["require_recall"] is old
        for m, old in zip(modules, originals, strict=True)
    )


def test_changed_prospective_contract_is_rejected(tool: Any, tmp_path: Path) -> None:
    p = tmp_path / tool.CONFIG
    p.parent.mkdir()
    p.write_text("{}")
    # The dependency helper is loaded from the actual unchanged checkout.
    with patch.object(tool, "profile_tool", return_value=tool.profile_tool(ROOT)):
        with pytest.raises(ArithmeticError, match="contract changed"):
            tool.contract(tmp_path)


def pair() -> tuple[dict[str, Any], dict[str, Any]]:
    a: dict[str, Any] = dict(
        status="complete_saved_replay",
        mode="uncached",
        identity={"computed": 0.0},
        source=dict(sha256={"code": "hash"}),
        config_sha256="config",
        cache=dict(
            requests=2832,
            original_traversals=2832,
            hits=0,
            rejections=0,
            fallbacks=0,
            successful_proofs=0,
            enabled=False,
        ),
    )
    b = copy.deepcopy(a)
    b["mode"] = "cached"
    b["cache"].update(
        original_traversals=32, hits=2800, successful_proofs=32, enabled=True
    )
    return a, b


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "computed",
        "source",
        "config",
        "requests",
        "hits",
        "traversals",
        "rejection",
    ],
)
def test_pair_identity_and_full_request_counters(tool: Any, damage: str | None) -> None:
    a, b = pair()
    if damage == "computed":
        b["identity"]["computed"] = 1e-16
    elif damage == "source":
        b["source"]["sha256"] = {"code": "changed"}
    elif damage == "config":
        b["config_sha256"] = "changed"
    elif damage == "requests":
        b["cache"]["requests"] = 2
    elif damage == "hits":
        b["cache"]["hits"] = 0
    elif damage == "traversals":
        b["cache"]["original_traversals"] = 2832
    elif damage == "rejection":
        b["cache"]["rejections"] = 1
    if damage:
        with pytest.raises(ArithmeticError):
            tool.pair_identity(a, b)
    else:
        assert (
            tool.pair_identity(a, b)["status"]
            == "same_complete_replay_with_reused_proofs"
        )


def test_pair_refuses_late_start_before_creating_output(
    tool: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cutoff = datetime.now(UTC) + timedelta(seconds=3890)
    destination = tmp_path / "not-created"
    monkeypatch.setattr(
        sys,
        "argv",
        ["compare", "--stop-at", cutoff.isoformat(), "--output", str(destination)],
    )
    with pytest.raises(TimeoutError, match="reserves"):
        tool.main(ROOT)
    assert not destination.exists()


def test_full_tiny_replay_cache_matches_all_computed_results_fresh(
    tmp_path: Path,
) -> None:
    code = """import sys,json
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'scripts'))
import recall_cache_support as tool
from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.postflop.river_study import Deadline
p=tool.profile_tool(root);c=tool.contract(root);own=root/'results/compact-own-opponent-learning/software/own.json'
with isolated(worker=False),tool.hooks(c,enabled=False) as a:
 first=p.read_with_actual(root,own,Deadline(120))
with isolated(worker=False),tool.hooks(c,enabled=True) as b:
 second=p.read_with_actual(root,own,Deadline(120))
assert p.canonical(first)==p.canonical(second)
assert first['computed_replay']['unique_profiles']==432
assert a.requests==b.requests and b.hits>0 and b.traversals<a.traversals
print(json.dumps(dict(status='all432_tiny_replay_identity',uncached=a.summary(),cached=b.summary())))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(ROOT)],
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all432_tiny_replay_identity" in result.stdout
