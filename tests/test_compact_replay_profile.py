"""Full replay identity, lossless profiling, caps and retained failures."""

import copy
import gzip
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "compact_replay_profiler", ROOT / "scripts/profile_compact_replay.py"
    )
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def original() -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(
        (ROOT / "results/compact-own-opponent-learning/cost/0/own.json").read_text()
    )
    return saved


def test_prospective_config_and_whole_original_identity(tool: Any) -> None:
    c = tool.contract(ROOT)
    saved = original()
    assert (
        tool.identity(saved, c, saved["own_replay"])["own_replay"]["unique_profiles"]
        == 432
    )
    assert saved["source_sha256"] == c["original_source_sha256"]
    assert saved["source"]["sha256"] == c["original_named_source"]
    assert all(
        tool.digest(ROOT / p) == h for p, h in c["published_input_sha256"].items()
    )


def test_changed_prospective_config_is_refused(tool: Any, tmp_path: Path) -> None:
    path = tmp_path / tool.CONFIG
    path.parent.mkdir()
    path.write_text("{}")
    with pytest.raises(ArithmeticError, match="contract changed"):
        tool.contract(tmp_path)


@pytest.mark.parametrize("damage", ["source_hash", "named_source", "own", "archive"])
def test_preflight_refuses_changed_original_inputs(
    tool: Any, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    from poker_ai.evaluation import compact_opponent_source

    saved = original()["source"]
    config = tool.contract(ROOT)
    if damage == "source_hash":
        saved["fingerprint"] = "changed"
    elif damage == "named_source":
        saved["sha256"] = {"missing": "source"}
    elif damage == "own":
        config["own_sha256"] = "changed"
    else:
        first = next(iter(config["published_input_sha256"]))
        config["published_input_sha256"][first] = "changed"
    monkeypatch.setattr(compact_opponent_source, "source", lambda *a, **k: saved)
    monkeypatch.setattr(tool, "contract", lambda *a: config)
    with pytest.raises(ArithmeticError, match="corpus or original source"):
        tool.preflight(ROOT)


@pytest.mark.parametrize(
    "field,value",
    [
        ("scope", "learned"),
        ("poker_training_performed", True),
        ("reference_constructed", True),
        ("actual_poker_training_work", 1),
    ],
)
def test_cost_only_identity_cannot_claim_learning(
    tool: Any, field: str, value: Any
) -> None:
    saved = original()
    saved[field] = value
    with pytest.raises(ArithmeticError, match="cost-only"):
        tool.identity(saved, tool.contract(ROOT), saved["own_replay"])


@pytest.mark.parametrize(
    "field",
    [
        "raw_profiles",
        "raw_ledgers",
        "fixed_conditions",
        "unique_profiles",
        "policy_and_ledger_bits_exact",
    ],
)
def test_incomplete_replay_counts_are_refused(tool: Any, field: str) -> None:
    saved = original()
    saved["own_replay"][field] = False if field == "policy_and_ledger_bits_exact" else 1
    with pytest.raises(ArithmeticError, match="cost-only"):
        tool.identity(saved, tool.contract(ROOT), saved["own_replay"])


def children(tool: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    plain = dict(
        status="complete_read_only_replay",
        mode="plain",
        identity=tool.identity(
            original(), tool.contract(ROOT), original()["own_replay"]
        ),
        source=dict(sha256={"source": "hash"}),
        config_sha256=tool.CONFIG_SHA,
    )
    profile = copy.deepcopy(plain)
    profile["mode"] = "profile"
    return plain, profile


def test_plain_profile_identity_is_exact(tool: Any) -> None:
    plain, profile = children(tool)
    assert tool.pair_identity(plain, profile)["status"] == "same_complete_cost_replay"
    profile["identity"]["own_replay"]["maximum_error"] = 1e-16
    with pytest.raises(ArithmeticError, match="identity changed"):
        tool.pair_identity(plain, profile)


@pytest.mark.parametrize("damage", ["status", "mode", "source", "config", "hash"])
def test_pair_source_order_and_full_hash_are_required(tool: Any, damage: str) -> None:
    plain, profile = children(tool)
    if damage in ("status", "mode"):
        profile[damage] = "wrong"
    elif damage == "source":
        profile["source"]["sha256"]["source"] = "different"
    elif damage == "config":
        profile["config_sha256"] = "different"
    else:
        profile["identity"]["complete_own_sha256"] = "different"
    with pytest.raises(ArithmeticError, match="identity changed"):
        tool.pair_identity(plain, profile)


@pytest.mark.parametrize("calls", [0, 1, 2])
def test_recording_requires_exactly_one_real_computed_summary(
    tool: Any,
    monkeypatch: pytest.MonkeyPatch,
    calls: int,
) -> None:
    from poker_ai.evaluation import compact_opponent_cli as frozen

    stored = original()
    actual = copy.deepcopy(stored["own_replay"])
    actual["maximum_error"] = 1e-16
    monkeypatch.setattr(frozen, "replay", lambda *args, **kwargs: actual)

    def read(*args: Any) -> Any:
        for _ in range(calls):
            vars(frozen)["replay"]()
        return stored

    monkeypatch.setattr(frozen, "read", read)
    if calls != 1:
        with pytest.raises(ArithmeticError, match="one complete computed"):
            tool.read_with_actual(ROOT, Path("fixture"), None)
    else:
        result = tool.read_with_actual(ROOT, Path("fixture"), None)
        assert result["computed_replay"]["maximum_error"] == 1e-16
        assert result["own"]["own_replay"]["maximum_error"] == 0
        plain, profile = children(tool)
        profile["identity"] = tool.identity(stored, tool.contract(ROOT), actual)
        with pytest.raises(ArithmeticError, match="identity changed"):
            tool.pair_identity(plain, profile)


@pytest.mark.parametrize("exitcode", [0, 7])
def test_supervisor_retains_complete_or_failed_child(
    tool: Any, tmp_path: Path, exitcode: int
) -> None:
    destination = tmp_path / "child"
    code = (
        "from pathlib import Path; import sys; "
        "Path(sys.argv[1]).write_text('{}'); print('retained'); "
        "sys.exit(int(sys.argv[2]))"
    )
    command = [
        sys.executable,
        "-c",
        code,
        str(destination / "child.json"),
        str(exitcode),
    ]
    result = tool.supervise(command, destination, 10)
    assert result["returncode"] == exitcode
    assert result["reaped_child_user_seconds"] >= 0
    assert result["reaped_child_system_seconds"] >= 0
    assert result["child_sha256"] == tool.digest(destination / "child.json")
    assert json.loads((destination / "measurement.json").read_text()) == result
    assert "retained" in (destination / "command.log").read_text()
    with pytest.raises(FileExistsError):
        tool.supervise(command, destination, 10)


def test_hard_timeout_retains_partial_child(tool: Any, tmp_path: Path) -> None:
    destination = tmp_path / "timeout"
    code = (
        "from pathlib import Path; import sys,time; "
        'Path(sys.argv[1]).write_text(\'{"status":"partial"}\'); '
        "print('partial',flush=True); time.sleep(60)"
    )
    result = tool.supervise(
        [sys.executable, "-c", code, str(destination / "child.json")], destination, 0.3
    )
    assert result["returncode"] == 124
    assert result["interrupted"] == "TimeoutExpired"
    assert json.loads((destination / "child.json").read_text())["status"] == "partial"
    assert result["seconds"] < 5


def test_profile_read_keeps_raw_frames_on_failure(
    tool: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.evaluation import compact_opponent_cli
    from poker_ai.evaluation.batch_cost_stats import validate

    def fail(*args: Any) -> Any:
        raise ValueError("retained fixture failure")

    monkeypatch.setattr(compact_opponent_cli, "read", fail)
    with pytest.raises(ValueError, match="fixture failure"):
        tool.profile_read(ROOT, tmp_path / "missing", None, tmp_path)
    assert (tmp_path / "replay.prof").is_file()
    with gzip.open(tmp_path / "functions-callers.json.gz", "rt") as stream:
        saved = json.load(stream)
    validate(saved)
    assert any(r["name"] == "fail" for r in saved["functions"])


def test_child_preflight_failure_is_retained(
    tool: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: Any) -> Any:
        raise ArithmeticError("changed fixed input")

    monkeypatch.setattr(tool, "preflight", fail)
    with pytest.raises(ArithmeticError, match="changed fixed input"):
        tool.child(ROOT, "plain", tmp_path, time.perf_counter())
    saved = json.loads((tmp_path / "child.json").read_text())
    assert saved["status"] == "failed_retained"
    assert saved["training_performed"] is False
    assert saved["reference_constructed"] is False


@pytest.mark.parametrize("damage", [None, "child", "profile", "pair", "measurement"])
def test_viewer_authenticates_full_children_and_raw_profile(
    tool: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    damage: str | None,
) -> None:

    plain, profiled = children(tool)
    monkeypatch.setattr(tool, "authenticate_source", lambda *args: None)
    folders = [tmp_path / mode for mode in ("plain", "profile")]
    for folder in folders:
        folder.mkdir()
    monkeypatch.setattr(
        tool,
        "read_with_actual",
        lambda *args: dict(own=original(), computed_replay=original()["own_replay"]),
    )
    tool.profile_read(ROOT, tmp_path / "own", None, folders[1])
    profiled["profile_files"] = {
        name: tool.digest(folders[1] / name)
        for name in ("replay.prof", "functions-callers.json.gz")
    }
    measurements = []
    for folder, data in zip(folders, (plain, profiled), strict=True):
        tool.atomic(folder / "child.json", data)
        measured = dict(
            returncode=0,
            interrupted=None,
            seconds=1.0,
            child_sha256=tool.digest(folder / "child.json"),
        )
        measurements.append(measured)
        tool.atomic(folder / "measurement.json", measured)
    saved = dict(
        order=["plain", "profile"],
        measurements=measurements,
        **tool.pair_identity(plain, profiled),
    )
    tool.atomic(tmp_path / "pair.json", saved)
    if damage == "child":
        (folders[0] / "child.json").write_text("{}")
    elif damage == "profile":
        (folders[1] / "functions-callers.json.gz").write_bytes(b"changed")
    elif damage == "pair":
        saved["complete_own_sha256"] = "changed"
        tool.atomic(tmp_path / "pair.json", saved)
    elif damage == "measurement":
        (folders[0] / "measurement.json").write_text("{}")
    if damage:
        with pytest.raises(ArithmeticError):
            tool.show(tmp_path)
    else:
        tool.show(tmp_path)
        output = capsys.readouterr().out
        assert "identical plain/profile" in output
        assert "caller edges" in output


def test_viewer_checks_named_historical_source_not_a_new_aggregate(tool: Any) -> None:
    source = original()["source"]
    tool.authenticate_source(ROOT, source)
    source["fingerprint"] = "changed"
    with pytest.raises(ArithmeticError, match="named scientific source changed"):
        tool.authenticate_source(ROOT, source)


def test_shallow_history_refuses_evidence_until_full_history_is_fetched(
    tool: Any,
    tmp_path: Path,
) -> None:
    from poker_ai.postflop.learning_artifacts import sha

    origin, shallow = tmp_path / "origin", tmp_path / "shallow"
    origin.mkdir()

    def git(root: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True
        ).strip()

    git(origin, "init", "--quiet")
    (origin / "sample.py").write_text("value = 1\n")
    git(origin, "add", "sample.py")
    settings = ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid")
    git(origin, *settings, "commit", "--quiet", "-m", "fixture source")
    ancestor = git(origin, "rev-parse", "HEAD")
    hashes = {"sample.py": tool.digest(origin / "sample.py")}
    (origin / "later.txt").write_text("later fixture\n")
    git(origin, "add", "later.txt")
    git(origin, *settings, "commit", "--quiet", "-m", "fixture later")
    subprocess.run(
        ["git", "clone", "--quiet", "--depth", "1", origin.as_uri(), str(shallow)],
        check=True,
    )
    saved = dict(git_commit=ancestor, sha256=hashes, fingerprint=sha(hashes))
    assert git(shallow, "rev-parse", "--is-shallow-repository") == "true"
    with pytest.raises(subprocess.CalledProcessError):
        tool.authenticate_source(shallow, saved)
    git(shallow, "fetch", "--quiet", "--unshallow", "origin")
    assert git(shallow, "rev-parse", "--is-shallow-repository") == "false"
    tool.authenticate_source(shallow, saved)


def test_full_tiny_read_profile_matches_plain_in_fresh_process(tmp_path: Path) -> None:
    """Actual complete reader/guard/432 scores, not a mocked replay loop."""
    code = """import importlib.util,json,sys
from pathlib import Path
from poker_ai.evaluation.compact_opponent_cli import read
from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.postflop.river_study import Deadline
root,out=map(Path,sys.argv[1:])
spec=importlib.util.spec_from_file_location('profile_tool',root/'scripts/profile_compact_replay.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
own=root/'results/compact-own-opponent-learning/software/own.json'
plain=module.read_with_actual(root,own,Deadline(120))
profile=module.profile_read(root,own,Deadline(120),out)
assert module.canonical(plain)==module.canonical(profile)
assert plain['computed_replay']['unique_profiles']==432
with isolated(worker=False):
 from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
 try: ReducedDispatchBatchTrainer(None,None,None)
 except AssertionError as error: assert 'read-only compact parent' in str(error)
 else: raise AssertionError('constructor unblocked')
print('complete432_identity_no_constructors')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(ROOT), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "complete432_identity_no_constructors" in result.stdout
