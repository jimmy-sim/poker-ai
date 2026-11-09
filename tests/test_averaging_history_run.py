"""Own-run admission/failure boundaries; fictional headers are schema-only."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from poker_ai.evaluation import averaging_history_protocol as protocol
from poker_ai.evaluation import averaging_history_run as own
from poker_ai.evaluation.averaging_history_inputs import inputs
from poker_ai.postflop.learning_artifacts import sha

ROOT = Path(__file__).resolve().parents[1]


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("gate failed to block downstream work")


@pytest.fixture
def own_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    config = inputs(ROOT)
    source = dict(dirty=False, sha256={"EXPLICIT_SCHEMA_SOURCE": "f" * 64})
    admission = dict(source_sha256=sha(source["sha256"]))
    data = SimpleNamespace(base=SimpleNamespace(policies=[]))
    monkeypatch.setattr(own, "inputs", lambda root: config)
    monkeypatch.setattr(own, "runtime_environment", lambda: config["prefix_runtime"])
    monkeypatch.setattr(protocol, "source", lambda root: source)
    monkeypatch.setattr(protocol, "require_admission", lambda *a, **kw: admission)
    monkeypatch.setattr(own, "load", lambda root: data)
    parent = tmp_path / "configs"
    parent.mkdir()
    (parent / "training-isolation.json").write_text('{"future_comparison":{}}')
    return tmp_path, config, source, admission, data


@pytest.mark.parametrize("gate", ["runtime", "admission"])
def test_no_poker_input_or_worker_before_admission(
    own_fixture: tuple[Any, ...],
    monkeypatch: pytest.MonkeyPatch,
    gate: str,
) -> None:
    root, _, _, _, _ = own_fixture

    def fail(*args: Any, **kwargs: Any) -> None:
        raise ArithmeticError("explicit preflight denial fixture")

    monkeypatch.setattr(
        protocol,
        "require_prefix_runtime" if gate == "runtime" else "require_admission",
        fail,
    )
    monkeypatch.setattr(own, "load", forbidden)
    monkeypatch.setattr(own, "run_batch", forbidden)
    output = root / "own.json"
    with pytest.raises(ArithmeticError, match="preflight denial"):
        own.run(root, output)
    assert not output.exists()
    assert not (root / "results/runs").exists()


def test_worker_failure_retains_partial_receipt_and_original_attempt(
    own_fixture: tuple[Any, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _, _, _ = own_fixture

    def fail(*args: Any, **kwargs: Any) -> None:
        batch = args[-1]
        batch.update(status="incomplete", failure="EXPLICIT_TIMEOUT_FIXTURE")
        raise TimeoutError("explicit worker timeout fixture")

    monkeypatch.setattr(own, "run_batch", fail)
    output = root / "own.json"
    with pytest.raises(TimeoutError):
        own.run(root, output)
    before = output.read_bytes()
    saved = json.loads(before)
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["batch"]["status"] == "incomplete"
    assert saved["rows"] == saved["masses"] == saved["fixed_matches"] == []
    assert saved["own_replay"] is None
    assert Path(saved["scratch"]).exists()
    with pytest.raises(FileExistsError):
        own.run(root, output)
    assert output.read_bytes() == before


@pytest.fixture
def fictional_saved(
    own_fixture: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch
) -> tuple[Any, ...]:
    root, config, source, admission, _ = own_fixture
    monkeypatch.setattr(own, "check_source", lambda *a: None)
    monkeypatch.setattr(protocol, "validate_replay", lambda *a: None)
    monkeypatch.setattr(own, "gather", lambda *a: (["EXPLICIT_SCHEMA_ROW"], []))
    saved = dict(
        format=protocol.FORMAT,
        status="completed_own_native_pending",
        failure=None,
        config=config,
        training_performed=True,
        new_learning_rule=False,
        reference_output_used_in_training=False,
        seconds=1.0,
        source=source,
        source_sha256=admission["source_sha256"],
        admission=admission,
        own_replay=dict(seconds=0.5),
        environment=config["prefix_runtime"],
        batch={},
        rows=["EXPLICIT_SCHEMA_ROW"],
        masses=[],
        fixed_matches=[{}] * 2048,
    )
    path = root / "EXPLICIT_SCHEMA_NOT_RESEARCH.json"
    return root, path, saved


def test_read_saved_passes_header_only_fixture(
    fictional_saved: tuple[Any, ...],
) -> None:
    root, path, saved = fictional_saved
    path.write_text(json.dumps(saved))
    assert own.read_saved(root, path)[0] == saved


@pytest.mark.parametrize(
    "mode",
    [
        "incomplete",
        "failure",
        "training_bool",
        "new_rule",
        "reference",
        "cap",
        "nan",
        "runtime",
        "admission",
        "source",
        "replay_time",
        "row",
        "mass",
        "fixed_missing",
    ],
)
def test_read_saved_rejects_changed_headers_and_ledger_bindings(
    fictional_saved: tuple[Any, ...],
    mode: str,
) -> None:
    root, path, original = fictional_saved
    saved = copy.deepcopy(original)
    if mode == "incomplete":
        saved["status"] = "incomplete"
    elif mode == "failure":
        saved["failure"] = dict(reason="EXPLICIT_FIXTURE")
    elif mode == "training_bool":
        saved["training_performed"] = 1
    elif mode == "new_rule":
        saved["new_learning_rule"] = True
    elif mode == "reference":
        saved["reference_output_used_in_training"] = True
    elif mode == "cap":
        saved["seconds"] = 7200.0
    elif mode == "nan":
        saved["seconds"] = float("nan")
    elif mode == "runtime":
        saved["environment"]["python"] = "3.12.15"
    elif mode == "admission":
        saved["admission"]["source_sha256"] = "0" * 64
    elif mode == "source":
        saved["source_sha256"] = "0" * 64
    elif mode == "replay_time":
        saved["own_replay"]["seconds"] = 2.0
    elif mode == "row":
        saved["rows"] = []
    elif mode == "mass":
        saved["masses"] = [{}]
    else:
        saved["fixed_matches"].pop()
    path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        own.read_saved(root, path)
