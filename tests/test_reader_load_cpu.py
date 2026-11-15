"""Software-only nested loader coverage, restoration and new-family routing."""

import copy
import importlib
import json
import os
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
tool = importlib.import_module("profile_reader_loads")
coarse = tool.coarse


def original_globals() -> tuple[Any, Any, Any]:
    return coarse.CATEGORIES, coarse.targets, coarse.modules


def assert_restored(before: tuple[Any, Any, Any]) -> None:
    assert all(a is b for a, b in zip(original_globals(), before, strict=True))


def capture() -> tuple[Any, list[dict[str, Any]]]:
    ticks = iter(range(10000))
    events: list[dict[str, Any]] = []

    def clock() -> dict[str, Any]:
        tick = next(ticks)
        return dict(
            wall=float(tick),
            cpu=float(tick),
            pid=os.getpid(),
            thread=threading.get_ident(),
        )

    regions = coarse.Regions(4096, events.append, clock)
    regions.read_index = 0
    regions.active = True
    return regions, events


def saved(regions: Any) -> dict[str, Any]:
    return dict(
        status="complete",
        rows=copy.deepcopy(regions.rows),
        errors=regions.errors,
        pid=regions.pid,
        thread=regions.thread,
    )


def test_extension_is_bounded_and_old_parser_remains_unchanged() -> None:
    before = original_globals()
    with tool.extension():
        assert coarse.CATEGORIES is tool.CATEGORIES
        assert coarse.targets is tool.targets
        assert coarse.modules is tool.modules
        regions, events = capture()
        result = regions.wrap("comparison_inputs", lambda: object())()
        assert result is not None
        summary = coarse.validate_regions(
            saved(regions), events, regions.pid, regions.thread, 0
        )
        assert set(summary["groups"]) == set(tool.CATEGORIES)
    assert_restored(before)
    with pytest.raises(ArithmeticError):
        coarse.validate_regions(saved(regions), events, regions.pid, regions.thread, 0)
    with pytest.raises(ValueError):
        regions.wrap("comparison_inputs", lambda: None)


def test_nested_extension_rejected_without_corrupting_outer_scope() -> None:
    before = original_globals()
    with tool.extension():
        with pytest.raises(ArithmeticError, match="nested"):
            with tool.extension():
                pytest.fail("nested scope entered")
        assert coarse.CATEGORIES is tool.CATEGORIES
    assert_restored(before)


@pytest.mark.parametrize("name", ["CATEGORIES", "targets", "modules"])
def test_changed_baseline_is_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    before = original_globals()
    value = tuple(list(tool.BASE_CATEGORIES)) if name == "CATEGORIES" else lambda: ()
    with monkeypatch.context() as m:
        m.setattr(coarse, name, value)
        with pytest.raises(ArithmeticError, match="changed"):
            with tool.extension():
                pytest.fail("changed baseline accepted")
    assert_restored(before)


def test_extension_restores_on_primary_exception() -> None:
    before = original_globals()
    error = RuntimeError("fictional primary")
    with pytest.raises(RuntimeError) as found:
        with tool.extension():
            raise error
    assert found.value is error
    assert_restored(before)


def test_six_nested_categories_have_no_double_counted_cpu() -> None:
    before = original_globals()
    order = (
        "comparison_inputs",
        "legacy_inputs",
        "matrix_build",
        "spot_tree_build",
        "sampled_source_replay",
        "checkpoint_replay",
    )
    with tool.extension():
        regions, events = capture()
        sentinel = object()

        def nested(i: int) -> Any:
            return regions.wrap(
                order[i], lambda: nested(i + 1) if i + 1 < len(order) else sentinel
            )()

        assert nested(0) is sentinel
        summary = coarse.validate_regions(
            saved(regions), events, regions.pid, regions.thread, 0
        )
        assert summary["calls"] == 6 and summary["selected_union_cpu"] == 11
        assert (
            sum(g["exclusive_selected_cpu"] for g in summary["groups"].values()) == 11
        )
        assert summary["groups"]["comparison_inputs"]["inclusive_cpu"] == 11
        assert summary["groups"]["comparison_inputs"]["exclusive_selected_cpu"] == 2
        assert summary["groups"]["checkpoint_replay"]["exclusive_selected_cpu"] == 1
    assert_restored(before)


@pytest.mark.parametrize(
    "kind", ["category", "missing", "parent", "read", "cpu", "thread", "failed"]
)
def test_six_category_schema_changes_fail_closed(kind: str) -> None:
    with tool.extension():
        regions, events = capture()
        regions.wrap("comparison_inputs", lambda: None)()
        value = saved(regions)
        if kind == "category":
            events[0]["category"] = "unregistered"
        elif kind == "missing":
            events.pop()
        elif kind == "parent":
            events[0]["parent"] = 0
        elif kind == "read":
            events[0]["read"] = 7
        elif kind == "cpu":
            events[1]["after"]["cpu"] = -1
        elif kind == "thread":
            events[0]["before"]["thread"] += 1
        else:
            events[1]["status"] = "primary_failed"
        with pytest.raises(ArithmeticError):
            coarse.validate_regions(value, events, regions.pid, regions.thread, 0)


def test_new_boundary_rejects_off_thread_capture_before_calling_body() -> None:
    calls: list[Any] = []
    errors: list[BaseException] = []
    with tool.extension():
        regions, _ = capture()
        selected = regions.wrap("legacy_inputs", lambda: calls.append(True))

        def worker() -> None:
            try:
                selected()
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], ArithmeticError)
        assert not calls and not regions.rows and regions.errors == 1


def test_target_factory_is_ordinary_and_checks_actual_private_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from compact_cached import cli

    selected = tool.targets()
    assert tuple(x[0] for x in selected) == tool.CATEGORIES
    monkeypatch.setattr(cli, "load", lambda: None)
    with pytest.raises(ArithmeticError, match="alias"):
        tool.targets()


@pytest.mark.parametrize("kind", ["generator", "coroutine", "async_generator"])
def test_iterator_or_async_factory_is_not_timed_as_an_ordinary_body(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from compact_cached import cli

    import poker_ai.evaluation.compact_opponent_sources as comparison

    def generator() -> Any:
        yield None

    async def coroutine() -> None:
        return None

    async def async_generator() -> Any:
        yield None

    target = dict(
        generator=generator, coroutine=coroutine, async_generator=async_generator
    )[kind]
    monkeypatch.setattr(comparison, "load", target)
    monkeypatch.setattr(cli, "load", target)
    with pytest.raises(ArithmeticError, match="ordinary"):
        tool.targets()


def test_owned_alias_inventory_includes_private_package_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    a, b, ignored = (
        ModuleType("compact_cached.cpu_fixture"),
        ModuleType("poker_ai.cpu_fixture"),
        ModuleType("unowned.cpu_fixture"),
    )
    monkeypatch.setitem(sys.modules, a.__name__, a)
    monkeypatch.setitem(sys.modules, "compact_cached.cpu_same_object", a)
    monkeypatch.setitem(sys.modules, b.__name__, b)
    monkeypatch.setitem(sys.modules, ignored.__name__, ignored)
    result = list(tool.modules())
    assert result.count(a) == 1 and b in result and ignored not in result


@pytest.mark.parametrize("failure", [False, True])
def test_private_and_late_loader_aliases_are_captured_and_restored(
    monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    from compact_cached import cli

    import poker_ai.evaluation.compact_fixed_inputs as sampled
    import poker_ai.evaluation.compact_opponent_sources as comparison
    import poker_ai.evaluation.opponent_learning_sources as legacy

    before = original_globals()
    sentinel, argument = object(), object()
    primary = RuntimeError("fictional loader failure")
    seen: list[Any] = []

    def legacy_load(*args: Any, **kwargs: Any) -> Any:
        seen.append((args, kwargs))
        return sentinel

    def sampled_load(*args: Any, **kwargs: Any) -> Any:
        if failure:
            raise primary
        return sentinel

    def comparison_load(*args: Any, **kwargs: Any) -> Any:
        assert legacy.load(*args, **kwargs) is sentinel
        return sampled.replay_sources(*args, **kwargs)

    monkeypatch.setattr(comparison, "load", comparison_load)
    monkeypatch.setattr(cli, "load", comparison_load)
    monkeypatch.setattr(legacy, "load", legacy_load)
    monkeypatch.setattr(sampled, "replay_sources", sampled_load)
    earlier: Any = ModuleType("compact_cached.cpu_earlier")
    late: Any = ModuleType("compact_cached.cpu_late")
    earlier.load = comparison_load
    monkeypatch.setitem(sys.modules, earlier.__name__, earlier)
    monkeypatch.setitem(sys.modules, late.__name__, late)
    state: dict[str, Any] = {}
    with tool.extension():
        regions, events = capture()
        with coarse.selected_hooks(regions, state):
            late.load = comparison.load
            assert (
                vars(cli)["load"] is comparison.load and earlier.load is comparison.load
            )
            if failure:
                with pytest.raises(RuntimeError) as found:
                    vars(cli)["load"](argument, declared=True)
                assert found.value is primary
            else:
                assert earlier.load(argument, declared=True) is sentinel
            assert seen == [((argument,), dict(declared=True))]
        assert (
            vars(cli)["load"] is comparison_load
            and earlier.load is comparison_load
            and late.load is comparison_load
        )
        assert state["restored"] is True and state["aliases_remaining"] == 0
        if not failure:
            summary = coarse.validate_regions(
                saved(regions), events, regions.pid, regions.thread, 0
            )
            assert summary["calls"] == 3
            assert summary["groups"]["comparison_inputs"]["exclusive_selected_cpu"] == 3
    assert_restored(before)


def test_original_selected_counts_are_checked_against_pinned_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    c = tool.contract(ROOT)
    data = [
        dict(
            summary=dict(
                groups={
                    k: dict(calls=row["counts"].get(k, int(row["read"] > 0)))
                    for k in tool.CATEGORIES
                }
            )
        )
        for row in c["baseline_selected_read_counts"]
    ]

    def phases(*args: Any) -> Any:
        assert coarse.CATEGORIES is tool.CATEGORIES
        return data

    monkeypatch.setattr(coarse, "phase_ledgers", phases)
    before = original_globals()
    assert tool.phase_ledgers(tmp_path, {}, {}, c, root=ROOT) is data
    assert_restored(before)
    data[1]["summary"]["groups"]["checkpoint_replay"]["calls"] -= 1
    with pytest.raises(ArithmeticError, match="lost or gained"):
        tool.phase_ledgers(tmp_path, {}, {}, c, root=ROOT)
    assert_restored(before)


@pytest.mark.parametrize("kind", ["config_baseline", "extra_read"])
def test_changed_baseline_description_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kind: str
) -> None:
    c = tool.contract(ROOT)
    data = [
        dict(
            summary=dict(
                groups={k: dict(calls=row["counts"].get(k, 0)) for k in tool.CATEGORIES}
            )
        )
        for row in c["baseline_selected_read_counts"]
    ]
    monkeypatch.setattr(coarse, "phase_ledgers", lambda *args: data)
    if kind == "config_baseline":
        c["baseline_selected_read_counts"][0]["counts"]["matrix_build"] = 1
    else:
        data.append(copy.deepcopy(data[-1]))
    with pytest.raises((ArithmeticError, ValueError)):
        tool.phase_ledgers(tmp_path, {}, {}, c, root=ROOT)


def test_retained_input_tamper_rejected_without_touching_historical_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = tool.contract(ROOT)
    victim = ROOT / next(iter(c["input_sha256"]))
    original = tool.digest
    monkeypatch.setattr(
        tool, "digest", lambda p: "0" * 64 if p == victim else original(p)
    )
    with pytest.raises(ArithmeticError, match="retained input"):
        tool.contract(ROOT)


@pytest.mark.parametrize(
    "kind",
    [
        "complete",
        "entry",
        "config",
        "extra",
        "prior",
        "dirty",
        "wrong_checkout",
        "wrong_entry",
    ],
)
def test_new_family_source_binding_is_complete_and_preserves_prior(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    import poker_ai.postflop.compact_full_artifacts as files
    import poker_ai.validation.five_card as provenance

    c = tool.contract(ROOT)
    anchor = json.loads((ROOT / c["preserved_source_anchor"]).read_text())["source"][
        "sha256"
    ]
    prior = dict(sha256=copy.deepcopy(anchor))
    if kind == "prior":
        prior["sha256"][next(iter(anchor))] = "changed"
    own = {
        tool.ENTRY: tool.digest(ROOT / tool.ENTRY),
        tool.CONFIG: tool.digest(ROOT / tool.CONFIG),
    }
    if kind in ("entry", "config"):
        own.pop(tool.ENTRY if kind == "entry" else tool.CONFIG)
    elif kind == "extra":
        own["scripts/unexpected.py"] = "unexpected"
    monkeypatch.setattr(coarse, "binding", lambda root, **kwargs: ({}, prior))
    monkeypatch.setattr(
        provenance,
        "source_provenance",
        lambda *args, **kwargs: dict(
            sha256=own, dirty=kind == "dirty", git_commit="a" * 40
        ),
    )
    checked: list[Any] = []
    monkeypatch.setattr(files, "commit_sources", lambda *args: checked.append(args))
    if kind == "wrong_checkout":
        monkeypatch.setattr(coarse, "__file__", "/fictional/collector.py")
    elif kind == "wrong_entry":
        monkeypatch.setattr(tool, "__file__", "/fictional/newentry.py")
    if kind == "complete":
        _, source = tool.binding(ROOT)
        assert len(source["sha256"]) == 406 and len(checked) == 1
        assert all(source["sha256"][k] == v for k, v in anchor.items())
    else:
        with pytest.raises(ArithmeticError):
            tool.binding(ROOT)
        assert not checked
    assert (
        anchor
        == json.loads((ROOT / c["preserved_source_anchor"]).read_text())["source"][
            "sha256"
        ]
    )


def original_fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    c = tool.contract(ROOT)
    row = json.loads((ROOT / c["historical_original"]).read_text())
    (tmp_path / "old").mkdir()
    for p in (ROOT / "results/card-audit-clock-trace/pair/uncached").rglob("*"):
        if p.is_file():
            target = (
                tmp_path
                / "old"
                / p.relative_to(ROOT / "results/card-audit-clock-trace/pair/uncached")
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    return c, row


# Same failure contracts are exercised through the new family routing.
def test_original_result_checks_existing_data(tmp_path: Path) -> None:
    c, row = original_fixture(tmp_path)
    assert tool.original_result(ROOT, tmp_path, c) == row


@pytest.mark.parametrize(
    "kind",
    [
        "mode",
        "status",
        "base_admission_rejected",
        "identity",
        "card_cache",
        "source",
        "raw",
        "worker",
    ],
)
def test_original_result_rejects_changes(tmp_path: Path, kind: str) -> None:
    c, row = original_fixture(tmp_path)
    if kind in ("mode", "status"):
        row[kind] = "changed"
    elif kind == "base_admission_rejected":
        row[kind] = False
    elif kind == "identity":
        row[kind]["profiles"].pop()
    elif kind == "card_cache":
        row[kind]["rank"]["hits"] += 1
    elif kind == "source":
        row[kind]["sha256"].popitem()
    elif kind == "raw":
        (tmp_path / "old/read-phases.json").write_text("{}")
    else:
        (tmp_path / "old/worker-telemetry/worker-0.json").write_text("{}")
    (tmp_path / "old/child.json").write_text(json.dumps(row))
    with pytest.raises((ArithmeticError, KeyError)):
        tool.original_result(ROOT, tmp_path, c)


def test_config_and_inputs_guarded(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    (tmp_path / tool.CONFIG).write_text("{}")
    with pytest.raises(ArithmeticError, match="contract"):
        tool.contract(tmp_path)


@pytest.mark.parametrize("kind", ["missing_extras", "missing_checks", "wrong_mode"])
def test_child_preflight_stops_before_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    c = tool.contract(ROOT)
    calls = []
    monkeypatch.setattr(tool, "binding", lambda root, **k: (c, {}))

    def no_checks(*a: Any) -> None:
        raise ArithmeticError("fixture missing checks")

    def no_extras(*a: Any) -> None:
        raise ArithmeticError("fixture missing extras")

    monkeypatch.setattr(
        tool, "checked", no_checks if kind == "missing_checks" else lambda *a: None
    )
    monkeypatch.setattr(tool.helpers, "runtime_requirements", no_extras)
    monkeypatch.setattr(tool.original, "child", lambda *a: calls.append(a))
    assert (
        tool.child(
            ROOT,
            "wrong" if kind == "wrong_mode" else "control",
            tmp_path,
            tool.time.perf_counter(),
        )
        == 1
    )
    assert not calls
    assert (
        json.loads((tmp_path / "child.json").read_text())["status"] == "failed_retained"
    )


@pytest.mark.parametrize("code", [1, 124])
def test_pair_stops_and_retains_first_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    root = tmp_path
    output = root / "results/runs/failure"
    c = tool.contract(ROOT)
    calls = []
    monkeypatch.setattr(tool, "contract", lambda r: c)
    monkeypatch.setattr(tool.original, "control", lambda c: {})

    def supervise(command: list[str], folder: Path, cap: float) -> dict[str, Any]:
        calls.append(cap)
        folder.mkdir()
        (folder / "command.log").write_text("fixture")
        return dict(
            returncode=code,
            interrupted="TimeoutExpired" if code == 124 else None,
            seconds=1,
        )

    monkeypatch.setattr(tool, "supervise", supervise)
    assert tool.pair(root, output) == 1
    saved = json.loads((output / "pair.json").read_text())
    assert len(calls) == 1 and calls[0] <= 900 and saved["status"] == "failed_retained"
    assert saved["measurements"][0]["returncode"] == code
    with pytest.raises(ValueError):
        tool.pair(root, output)


def test_existing_output_never_overwritten(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tool.pair(tmp_path, tmp_path)


def test_control_keeps_original_child_and_observer_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_cached import cli

    c = tool.contract(ROOT)
    import numpy

    import poker_ai.reproducibility as reproducibility

    monkeypatch.setattr(tool.sys, "version", "3.11.17 fictional fixture")
    monkeypatch.setattr(numpy, "__version__", "2.4.6")
    monkeypatch.setattr(reproducibility, "runtime_environment", lambda: c["runtime"])
    previous = cli.read
    calls = []
    monkeypatch.setattr(tool, "binding", lambda *a, **k: (c, dict(sha256={})))
    monkeypatch.setattr(tool, "checked", lambda *a: None)
    monkeypatch.setattr(tool.helpers, "runtime_requirements", lambda c: {})
    monkeypatch.setattr(tool.original, "control", lambda c: {})
    # Qualification hashing is stubbed, not a real source-admitted collection.
    monkeypatch.setattr(tool, "digest", lambda p: "fixture")

    def fake(root: Path, mode: str, out: Path, origin: float) -> int:
        assert cli.read is previous and mode == "uncached"
        calls.append(mode)
        (out / "child.json").write_text("retained original child")
        return 0

    monkeypatch.setattr(tool.original, "child", fake)
    monkeypatch.setattr(
        tool, "original_result", lambda *a: dict(identity={"fictional": True})
    )
    assert tool.child(ROOT, "control", tmp_path, tool.time.perf_counter()) == 0
    saved = json.loads((tmp_path / "child.json").read_text())
    assert calls == ["uncached"] and "old/child.json" in saved["raw_sha256"]
    assert not (tmp_path / "inner-reads.json").exists()


def test_primary_error_survives_observer_failure_and_restores_registry() -> None:
    before = original_globals()
    primary = RuntimeError("fictional original error")

    def emit(row: dict[str, Any]) -> None:
        if row["status"] != "running":
            raise OSError("fictional failed capture write")

    def body() -> None:
        raise primary

    with pytest.raises(RuntimeError) as found:
        with tool.extension():
            regions, _ = capture()
            regions.emit = emit
            regions.wrap("sampled_source_replay", body)()
    assert found.value is primary and regions.errors == 1
    assert regions.rows[0]["status"] == "primary_with_observer_failure"
    assert_restored(before)


@pytest.mark.parametrize("kind", ["python", "numpy"])
def test_wrong_actual_runtime_stops_new_family_before_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    import numpy

    c = tool.contract(ROOT)
    monkeypatch.setattr(tool, "binding", lambda *args, **kwargs: (c, {}))
    monkeypatch.setattr(tool, "checked", lambda *args: None)
    monkeypatch.setattr(tool.helpers, "runtime_requirements", lambda *args: {})
    monkeypatch.setattr(
        sys, "version", "0.0.0 fixture" if kind == "python" else "3.11.17 fixture"
    )
    monkeypatch.setattr(numpy, "__version__", "0.0.0" if kind == "numpy" else "2.4.6")
    calls: list[Any] = []
    monkeypatch.setattr(tool.original, "child", lambda *args: calls.append(args))
    assert tool.child(ROOT, "control", tmp_path, tool.time.perf_counter()) == 1
    assert not calls
    assert (
        json.loads((tmp_path / "child.json").read_text())["status"] == "failed_retained"
    )


def test_qualification_routes_to_new_family_without_old_permit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import poker_ai.evaluation.diagnostic_receipts as receipts

    calls: list[Any] = []
    source = dict(fingerprint="fictional406")

    def check(root: Path, path: Path, current: dict[str, Any]) -> None:
        calls.append((root, path, current))
        raise ArithmeticError("fictional missing new qualification")

    def old_permit(*args: Any) -> None:
        pytest.fail("new family used prior collector qualification")

    monkeypatch.setattr(receipts, "checks", check)
    monkeypatch.setattr(coarse, "checked", old_permit)
    with pytest.raises(ArithmeticError, match="new qualification"):
        tool.checked(tmp_path, source)
    assert calls == [(tmp_path, tmp_path / tool.FOLDER / "checks.json", source)]


def test_extension_does_not_change_real_prior_source_binding() -> None:
    before = original_globals()
    _, plain = coarse.binding(ROOT, clean=False)
    assert len(plain["sha256"]) == 404
    with tool.extension():
        _, extended = coarse.binding(ROOT, clean=False)
        assert extended["sha256"] == plain["sha256"]
        assert extended["fingerprint"] == plain["fingerprint"]
    assert_restored(before)
