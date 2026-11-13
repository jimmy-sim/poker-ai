"""Complete native instrumentation identity, provenance and retained failures."""

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture
def tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "native_profiler", ROOT / "scripts/profile_cached_native.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def saved() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        (ROOT / "results/compact-cached-learning/cost/0/native.json").read_text()
    )
    return result


def reads() -> list[dict[str, Any]]:
    paths = [
        "results/compact-cached-learning/software/own.json",
        *["results/compact-cached-learning/cost/0/own.json"] * 2,
    ]
    result = []
    for path in paths:
        own = json.loads((ROOT / path).read_text())
        result.append(dict(scope=own["scope"], computed=own["own_replay"]))
    return result


def children(tool: Any, saved: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    plain = dict(
        status="complete_native_parent_profile",
        mode="plain",
        base_admission_rejected=True,
        identity=tool.identity(saved, reads()),
        source=dict(sha256={"base": "hash"}),
        config_sha256=tool.CONFIG_SHA,
    )
    profiled = copy.deepcopy(plain)
    profiled["mode"] = "profile"
    return plain, profiled


def test_contract_and_full_original_cost_inventory(
    tool: Any, saved: dict[str, Any]
) -> None:
    c = tool.contract(ROOT)
    assert all(tool.digest(ROOT / p) == h for p, h in c["input_sha256"].items())
    assert saved["source_sha256"] == c["base_source_sha256"]
    result = tool.identity(saved, reads())
    assert len(result["profiles"]) == 432
    assert len(result["fixed_conditions"]) == 1152
    assert len(result["computed_replays"]) == 3


def test_changed_config_rejected(tool: Any, tmp_path: Path) -> None:
    path = tmp_path / tool.CONFIG
    path.parent.mkdir()
    path.write_text("{}")
    with pytest.raises(ArithmeticError, match="contract changed"):
        tool.contract(tmp_path)


@pytest.mark.parametrize("damage", ["source", "input"])
def test_source_or_input_tampering_rejected(
    tool: Any, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    from compact_cached import source

    c = tool.contract(ROOT)
    if damage == "input":
        c["input_sha256"][next(iter(c["input_sha256"]))] = "changed"
    monkeypatch.setattr(tool, "contract", lambda *a: c)
    monkeypatch.setattr(
        source,
        "source",
        lambda *a, **k: dict(
            fingerprint="changed" if damage == "source" else c["base_source_sha256"]
        ),
    )
    with pytest.raises(ArithmeticError, match="source or inputs"):
        tool.preflight(ROOT)


@pytest.mark.parametrize(
    "key,value",
    [
        ("poker_training_performed", True),
        ("reference_constructed", False),
        ("reference_output_used_in_training", True),
        ("long_run_admitted", True),
        ("new_agent_default", True),
        ("fresh_global_admission", True),
        ("repetition", True),
        ("status", "partial"),
        ("scope", "real"),
    ],
)
def test_scope_and_admission_identity_rejected(
    tool: Any, saved: dict[str, Any], key: str, value: Any
) -> None:
    saved[key] = value
    with pytest.raises(ArithmeticError, match="inventory"):
        tool.identity(saved, reads())


@pytest.mark.parametrize(
    "damage",
    [
        "profiles",
        "fixed",
        "final_read",
        "computed",
        "bits",
        "worker",
        "worker_implementation",
        "cache",
    ],
)
def test_every_scalar_replay_and_worker_required(
    tool: Any, saved: dict[str, Any], damage: str
) -> None:
    replays = reads()
    if damage == "profiles":
        saved["profiles"].pop()
    elif damage == "fixed":
        saved["fixed_conditions"].pop()
    elif damage == "final_read":
        replays.pop()
    elif damage == "computed":
        replays[-1]["computed"]["maximum_error_chips"] = 123
    elif damage == "bits":
        replays[0]["computed"]["policy_and_ledger_bits_exact"] = False
    elif damage == "worker":
        saved["native_batch"]["workers"].pop()
    elif damage == "worker_implementation":
        next(
            m
            for m in saved["native_batch"]["workers"][0]["messages"]
            if m.get("kind") == "done"
        )["summary"]["implementation_sha256"] = "changed"
    else:
        saved["validation_cache"]["enabled"] = False
    with pytest.raises(ArithmeticError):
        tool.identity(saved, replays)


def test_pair_exactness_and_scope(tool: Any, saved: dict[str, Any]) -> None:
    plain, profiled = children(tool, saved)
    assert (
        tool.pair_identity(plain, profiled)["status"]
        == "same_complete_native_scalar_and_replay_results"
    )
    profiled["identity"]["verification"]["maximum_error_chips"] += 1e-16
    with pytest.raises(ArithmeticError, match="identity changed"):
        tool.pair_identity(plain, profiled)


@pytest.mark.parametrize(
    "damage", ["mode", "source", "config", "admission", "final_replay"]
)
def test_pair_cannot_hide_effective_changes(
    tool: Any, saved: dict[str, Any], damage: str
) -> None:
    plain, profiled = children(tool, saved)
    if damage == "mode":
        profiled["mode"] = "plain"
    elif damage == "source":
        profiled["source"]["sha256"] = {}
    elif damage == "config":
        profiled["config_sha256"] = "changed"
    elif damage == "admission":
        profiled["base_admission_rejected"] = False
    else:
        profiled["identity"]["computed_replays"].pop()
    with pytest.raises(ArithmeticError, match="identity changed"):
        tool.pair_identity(plain, profiled)


def test_instrumentation_receipt_rejected_by_base(
    tool: Any, saved: dict[str, Any]
) -> None:
    from compact_cached.cache import check_execution

    check_execution(ROOT, saved)
    saved["implementation_config"] = dict(
        instrumentation_config=tool.CONFIG,
        instrumentation_sha256=tool.CONFIG_SHA,
        admission_evidence=False,
    )
    with pytest.raises(ArithmeticError, match="implementation contract"):
        check_execution(ROOT, saved)


def test_missing_source_roles_rejected(tool: Any, tmp_path: Path) -> None:
    path = tmp_path / tool.FOLDER / "checks.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(checks=[], source_fingerprint="fixture")))
    with pytest.raises(ArithmeticError, match="six exact-source"):
        tool.checked(tmp_path, dict(fingerprint="fixture"))


def test_fresh_failure_is_retained(
    tool: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        tool,
        "preflight",
        lambda *a, **k: (_ for _ in ()).throw(ArithmeticError("fixture failure")),
    )
    with pytest.raises(ArithmeticError, match="fixture failure"):
        tool.child(ROOT, "plain", tmp_path, tool.time.perf_counter())
    saved = json.loads((tmp_path / "child.json").read_text())
    assert saved["status"] == "failed_retained" and saved["admission_evidence"] is False


def test_cpu_profile_keeps_all_raw_functions(tool: Any) -> None:
    from poker_ai.evaluation.batch_cost_stats import extract, validate

    profiler = tool.cProfile.Profile(timer=tool.time.process_time_ns, timeunit=1e-9)
    assert profiler.runcall(sum, range(10)) == 45
    saved = extract(profiler, ROOT)
    validate(saved)
    assert saved["frame_count"] >= 1 and saved["total_self_seconds"] >= 0


def test_observation_keeps_all_reads_and_restores_hook(
    tool: Any, saved: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_cached import cli

    inventory = reads()
    index = 0

    def fake_read(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal index
        row = inventory[index]
        index += 1
        kwargs["observed"].append(row["computed"])
        return dict(scope=row["scope"])

    def fake_child(root: Path, argv: list[str]) -> int:
        for _ in range(3):
            cli.read(root, tmp_path / "fixture", None)  # type: ignore[arg-type]
        (tmp_path / "native.json").write_text(json.dumps(saved))
        return 0

    monkeypatch.setattr(cli, "read", fake_read)
    monkeypatch.setattr(cli, "child_main", fake_child)
    result = tool.execute_child(ROOT, tmp_path, tool.contract(ROOT))
    assert cli.read is fake_read and index == 3
    assert result["computed_replays"] == inventory
    marked = json.loads((tmp_path / "native.json").read_text())
    assert marked["implementation_config"]["admission_evidence"] is False
    assert marked["base_implementation_config"] == saved["implementation_config"]


def test_observation_hook_restored_on_native_failure(
    tool: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_cached import cli

    original = cli.read

    def fail(*args: Any, **kwargs: Any) -> int:
        raise ArithmeticError("native fixture failure")

    monkeypatch.setattr(cli, "child_main", fail)
    with pytest.raises(ArithmeticError, match="fixture failure"):
        tool.execute_child(ROOT, tmp_path, tool.contract(ROOT))
    assert cli.read is original


def test_complete_supervisor_timeout_retains_partial_bytes(
    tool: Any, tmp_path: Path
) -> None:
    target = tmp_path / "timeout"
    result = tool.supervise(
        [
            sys.executable,
            "-c",
            "import time; print('partial',flush=True); time.sleep(3)",
        ],
        target,
        0.15,
    )
    assert result["returncode"] == 124 and result["interrupted"] == "TimeoutExpired"
    assert "partial" in (target / "command.log").read_text()
    assert json.loads((target / "measurement.json").read_text()) == result
    with pytest.raises(FileExistsError):
        tool.supervise([sys.executable, "-c", "pass"], target, 1)


def test_profile_child_keeps_raw_stats_and_blocks_base_admission(
    tool: Any,
    tmp_path: Path,
    saved: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import numpy

    c = tool.contract(ROOT)
    c["runtime"] = dict(python=sys.version.split()[0], numpy=numpy.__version__)
    current = dict(sha256={"fixture": "source"})
    monkeypatch.setattr(tool, "preflight", lambda *a, **k: (c, current))
    monkeypatch.setattr(tool, "checked", lambda *a: None)

    def fake(*args: Any) -> dict[str, Any]:
        native = copy.deepcopy(saved)
        native["implementation_config"] = dict(admission_evidence=False)
        (tmp_path / "native.json").write_text(json.dumps(native))
        return dict(tool.identity(saved, reads()))

    monkeypatch.setattr(tool, "execute_child", fake)
    assert tool.child(ROOT, "profile", tmp_path, tool.time.perf_counter()) == 0
    result = json.loads((tmp_path / "child.json").read_text())
    assert result["base_admission_rejected"] is True
    assert result["status"] == "complete_native_parent_profile"
    assert set(result["profile_files"]) == {
        "native-parent.prof",
        "functions-callers.json.gz",
    }
    for name, checksum in result["profile_files"].items():
        assert tool.digest(tmp_path / name) == checksum
