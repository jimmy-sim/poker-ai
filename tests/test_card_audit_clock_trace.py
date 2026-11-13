"""Raw resource units/accounting and source-bound complete diagnostic failures."""

import copy
import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
resources = importlib.import_module("card_clock_support")
tool = importlib.import_module("trace_card_audit")


def observation() -> dict[str, Any]:
    before = resources.snapshot()
    after = copy.deepcopy(before)
    for field in resources.CLOCKS:
        after[field] += 1
    for kind in ("self_usage", "reaped_child_usage"):
        for field in (*resources.CPU, *resources.COUNTERS):
            after[kind][field] += 1
    result: dict[str, Any] = resources.record(before, after)
    return result


def test_real_own_process_snapshots_and_peak_units() -> None:
    row = resources.record(resources.snapshot(), resources.snapshot())
    resources.check_record(row)
    raw = row["before"]
    expected = (
        "bytes"
        if sys.platform == "darwin"
        else "KiB"
        if sys.platform.startswith("linux")
        else "platform_native_uninterpreted"
    )
    assert raw["rss_unit"] == expected
    assert (
        row["interval"]["resources"]["self_usage"][
            "peak_is_cumulative_not_interval_allocation"
        ]
        is True
    )
    assert "ru_maxrss" not in row["interval"]["resources"]["self_usage"]["delta"]


@pytest.mark.parametrize(
    "damage",
    [
        "pid",
        "platform",
        "units",
        "nan",
        "bool",
        "negative",
        "missing",
        "counter_decrease",
        "derived",
    ],
)
def test_invalid_or_mismatched_resource_record(damage: str) -> None:
    row = observation()
    if damage == "pid":
        row["after"]["pid"] += 1
    elif damage == "platform":
        row["after"]["platform"] = "other"
    elif damage == "units":
        row["after"]["rss_unit"] = "unspecified"
    elif damage == "nan":
        row["after"]["process_cpu_seconds"] = float("nan")
    elif damage == "bool":
        row["after"]["self_usage"]["ru_minflt"] = True
    elif damage == "negative":
        row["after"]["perf_seconds"] = -1
    elif damage == "missing":
        row["after"]["self_usage"].pop("ru_majflt")
    elif damage == "counter_decrease":
        row["after"]["self_usage"]["ru_nvcsw"] = (
            row["before"]["self_usage"]["ru_nvcsw"] - 1
        )
    else:
        row["interval"]["clocks"]["perf_seconds"] += 1
    with pytest.raises(ArithmeticError):
        resources.check_record(row)


def test_utc_can_adjust_and_process_cpu_is_not_wall_interval() -> None:
    row = observation()
    a, b = row["before"], row["after"]
    b["utc_seconds"] = a["utc_seconds"] - 1
    b["process_cpu_seconds"] = a["process_cpu_seconds"] + 4
    actual = resources.interval(a, b)
    assert actual["clocks"]["utc_seconds"] == -1
    assert actual["clocks"]["process_cpu_seconds"] > actual["clocks"]["perf_seconds"]


def test_original_timing_failure_and_all_kernel_limits_preserved() -> None:
    c = tool.contract(ROOT)
    old = tool.historical.contract(ROOT)
    failure = json.loads((ROOT / c["failure_pair"]).read_text())
    assert tool.digest(ROOT / c["failure_pair"]) == c["failure_pair_sha256"]
    assert failure["narrow_wall_time_pass"] is False
    assert [
        c[x]
        for x in (
            "maximum_child_seconds",
            "maximum_pair_seconds",
            "canonical_maxsize",
            "rank_maxsize",
        )
    ] == [
        old[x]
        for x in (
            "maximum_child_seconds",
            "maximum_pair_seconds",
            "canonical_maxsize",
            "rank_maxsize",
        )
    ]
    assert (
        c["admission_evidence"]
        is c["production_integrated"]
        is c["poker_training_performed"]
        is False
    )


@pytest.mark.parametrize("damage", ["historical", "failure"])
def test_changed_historical_source_or_failure_rejected(
    damage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = tool.contract(ROOT)
    if damage == "failure":
        c["failure_pair_sha256"] = "changed"
    monkeypatch.setattr(tool, "contract", lambda *a: c)
    monkeypatch.setattr(
        tool.historical,
        "preflight",
        lambda *a, **k: (
            c,
            dict(
                fingerprint="changed"
                if damage == "historical"
                else c["historical_source"]
            ),
        ),
    )
    with pytest.raises(ArithmeticError):
        tool.preflight(ROOT)


def test_control_records_request_not_unobserved_system_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "control"
    binary.write_bytes(b"fixture")
    c = dict(
        idle_control=dict(
            path=str(binary), arguments=["-i"], sha256=tool.digest(binary)
        )
    )
    monkeypatch.setattr(tool.sys, "platform", "darwin")
    result = tool.control(c)
    assert (
        result["requested"] is True
        and result["assertion_state_independently_audited"] is False
    )
    binary.write_bytes(b"changed")
    with pytest.raises(ArithmeticError, match="binary"):
        tool.control(c)


def test_missing_roles_and_fresh_partial_child_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / tool.FOLDER / "checks.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(checks=[], source_fingerprint="fixture")))
    with pytest.raises(ArithmeticError, match="six exact-source"):
        tool.checked(tmp_path, dict(fingerprint="fixture"))
    monkeypatch.setattr(
        tool,
        "preflight",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("fixture before body")),
    )
    with pytest.raises(ValueError, match="before body"):
        tool.child(ROOT, "cached", tmp_path, time.perf_counter())
    saved = json.loads((tmp_path / "child.json").read_text())
    resources.valid(saved["child_before"])
    assert saved["status"] == "failed_retained" and saved["admission_evidence"] is False


def fixture_identity() -> dict[str, Any]:
    return dict(
        computed_replays=[dict(scope=x) for x in ("tiny", "cost", "cost")],
        worker_summaries=[dict(slot=i) for i in range(3)],
    )


def write_resources(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    identity = fixture_identity()
    source = dict(sha256={"fixture": "hash"})
    (tmp_path / "parent-resource-reads.json").write_text(
        json.dumps(
            dict(
                reads=[
                    dict(
                        scope=r["scope"],
                        status="complete",
                        before=(probe := observation())["before"],
                        observation=probe,
                    )
                    for r in identity["computed_replays"]
                ]
            )
        )
    )
    (tmp_path / "native.json").write_text(
        json.dumps(
            dict(native_batch=dict(workers=[dict(pid=1000 + i) for i in range(3)]))
        )
    )
    folder = tmp_path / "worker-telemetry"
    folder.mkdir()
    for slot in range(3):
        probe = observation()
        probe["before"]["pid"] = probe["after"]["pid"] = 1000 + slot
        (folder / f"worker-{slot}.json").write_text(
            json.dumps(
                dict(
                    status="complete_worker_resource_trace",
                    slot=slot,
                    indices=list(range(slot, 6, 3)),
                    config_sha256=tool.CONFIG_SHA,
                    source=source,
                    numeric_summary=identity["worker_summaries"][slot],
                    runtime=dict(
                        tool.contract(ROOT)["runtime"],
                        module_is_under_checked_source_root=True,
                    ),
                    observation=probe,
                    before=probe["before"],
                )
            )
        )
    return source, identity


@pytest.mark.parametrize(
    "damage",
    [
        "none",
        "missing_read",
        "counter",
        "worker_partial",
        "worker_summary",
        "source",
        "config",
        "partition",
    ],
)
def test_every_raw_read_worker_and_source_required(
    damage: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = importlib.import_module("profile_compact_replay")
    monkeypatch.setattr(parent, "authenticate_source", lambda *a: None)
    source, identity = write_resources(tmp_path)
    if damage in ("missing_read", "counter"):
        p = tmp_path / "parent-resource-reads.json"
        saved = json.loads(p.read_text())
        if damage == "missing_read":
            saved["reads"].pop()
        else:
            saved["reads"][0]["observation"]["interval"]["clocks"]["perf_seconds"] += 1
        p.write_text(json.dumps(saved))
    elif damage != "none":
        p = tmp_path / "worker-telemetry/worker-1.json"
        saved = json.loads(p.read_text())
        if damage == "worker_partial":
            saved["status"] = "running"
        elif damage == "worker_summary":
            saved["numeric_summary"] = {}
        elif damage == "source":
            saved["source"] = {"sha256": {}}
        elif damage == "config":
            saved["config_sha256"] = "changed"
        elif damage == "partition":
            saved["indices"] = [1]
        p.write_text(json.dumps(saved))
    if damage == "none":
        assert tool.validate_resources(ROOT, tmp_path, source, identity) == dict(
            reads=3, workers=3, source_bound=True
        )
    else:
        with pytest.raises(ArithmeticError):
            tool.validate_resources(ROOT, tmp_path, source, identity)


def test_resource_observer_restores_aliases_and_environment_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_cached import cli

    original, job = cli.read, vars(cli)["independent"]
    monkeypatch.setenv("POKER_CARD_CLOCK_DIR", "prior")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("fixture execution")

    monkeypatch.setattr(tool.base, "execute_child", fail)
    with pytest.raises(ValueError, match="fixture execution"):
        tool.execute_child(ROOT, tmp_path, tool.contract(ROOT))
    assert cli.read is original and vars(cli)["independent"] is job
    import os

    assert os.environ["POKER_CARD_CLOCK_DIR"] == "prior"


def test_worker_failure_retains_raw_start_and_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "results/runs/workers"
    folder.mkdir(parents=True)
    monkeypatch.setenv("POKER_CARD_CLOCK_DIR", str(folder))
    monkeypatch.setattr(
        tool,
        "preflight",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("worker source failure")),
    )
    with pytest.raises(ValueError, match="worker source"):
        resources.worker(0, [0, 3], dict(root=str(tmp_path)), lambda x: None)
    saved = json.loads((folder / "worker-0.json").read_text())
    assert saved["status"] == "failed_retained" and saved["slot"] == 0
    resources.valid(saved["before"])
    resources.valid(saved["after_failure"])
    with pytest.raises(FileExistsError):
        resources.worker(0, [0, 3], dict(root=str(tmp_path)), lambda x: None)


def test_complete_pair_requires_telemetry_and_keeps_old_failure() -> None:
    children = [
        json.loads(
            (
                ROOT / "results/card-computation-cache/pair" / m / "child.json"
            ).read_text()
        )
        for m in ("uncached", "cached")
    ]
    for row in children:
        row.update(
            status="complete_card_clock_trace",
            config_sha256=tool.CONFIG_SHA,
            resource_validation=dict(reads=3, workers=3, source_bound=True),
            idle_control=dict(
                tool.contract(ROOT)["idle_control"],
                requested=True,
                assertion_state_independently_audited=False,
            ),
        )
    assert (
        tool.pair_identity(children[0], children[1], tool.contract(ROOT))["status"]
        == "same_complete_audit_with_resource_trace"
    )
    children[1]["resource_validation"]["workers"] = 2
    with pytest.raises(ArithmeticError, match="resource"):
        tool.pair_identity(children[0], children[1], tool.contract(ROOT))


def test_parent_read_failure_keeps_started_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_cached import cli

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("read failed after start")

    def invoke(*args: Any, **kwargs: Any) -> Any:
        return cli.read(ROOT, tmp_path / "fixture", None)  # type: ignore[arg-type]

    monkeypatch.setattr(cli, "read", fail)
    monkeypatch.setattr(tool.base, "execute_child", invoke)
    with pytest.raises(ValueError, match="read failed"):
        tool.execute_child(ROOT, tmp_path, tool.contract(ROOT))
    saved = json.loads((tmp_path / "parent-resource-reads.json").read_text())["reads"]
    assert len(saved) == 1 and saved[0]["status"] == "failed_retained"
    resources.valid(saved[0]["before"])
    resources.valid(saved[0]["after_failure"])


@pytest.mark.parametrize(
    "damage", ["none", "no_control", "display", "wrong_mode", "extra"]
)
def test_supervised_control_command_is_authenticated(damage: str) -> None:
    c = tool.contract(ROOT)
    command = [
        c["idle_control"]["path"],
        "-i",
        "python",
        "scripts/trace_card_audit.py",
        "--output",
        "run/uncached",
        "--_mode",
        "uncached",
    ]
    if damage == "no_control":
        command = command[2:]
    elif damage == "display":
        command[1] = "-d"
    elif damage == "wrong_mode":
        command[-1] = "cached"
    elif damage == "extra":
        command.append("unexpected")
    if damage == "none":
        tool.controlled_command(command, "uncached", c)
    else:
        with pytest.raises(ArithmeticError, match="idle-control command"):
            tool.controlled_command(command, "uncached", c)


def test_worker_observation_preserves_unmodified_numeric_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    native = importlib.import_module("compact_cached.native")
    folder = tmp_path / "results/runs/workers"
    folder.mkdir(parents=True)
    monkeypatch.setenv("POKER_CARD_CLOCK_DIR", str(folder))
    source = dict(sha256={"fixture": "hash"})
    monkeypatch.setattr(tool, "preflight", lambda *a, **k: ({}, source))
    numeric = dict(profiles=144, fixed_conditions=384, maximum_error_chips=1e-13)
    monkeypatch.setattr(native, "independent", lambda *a, **k: numeric)
    actual = resources.worker(2, [2, 5], dict(root=str(tmp_path)), lambda x: None)
    saved = json.loads((folder / "worker-2.json").read_text())
    assert (
        actual is numeric
        and saved["numeric_summary"] == numeric
        and saved["source"] == source
        and saved["status"] == "complete_worker_resource_trace"
    )
    resources.check_record(saved["observation"])
