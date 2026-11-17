"""Independent three-clock tree, forwarding and failure fixtures; no poker runs."""

import copy
import os
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import receipt_cpu_support as support  # noqa: E402


class Clock:
    def __init__(self) -> None:
        self.tick = 0

    def __call__(self) -> dict[str, Any]:
        self.tick += 1
        return dict(
            wall=float(self.tick),
            cpu=2.0 * self.tick,
            reaped_cpu=0.5 * self.tick,
            pid=os.getpid(),
            thread=threading.get_ident(),
        )


def route(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ModuleType, object, list[tuple[str, Any, Any]]]:
    """Miniature module aliases mirror the prospective caller structure."""
    current, study, frozen, reduced, cost, reduction = (
        ModuleType(name)
        for name in ("current", "study", "frozen", "reduced", "cost", "reduction")
    )
    token = object()
    calls: list[tuple[str, Any, Any]] = []

    def prerequisites(value: Any, *, keyword: Any) -> Any:
        calls.append(("prerequisites", value, keyword))
        return token

    def profile(value: Any, *, keyword: Any) -> Any:
        calls.append(("profile", value, keyword))
        return frozen.inputs.prerequisites(value, keyword=keyword)

    def admission(value: Any, *, keyword: Any) -> Any:
        calls.append(("admission", value, keyword))
        for _ in range(3):
            assert reduction.read_profile(value, keyword=keyword) is token
            assert cost.read_profile(value, keyword=keyword) is token
        return token

    def root(value: Any, *, keyword: Any) -> Any:
        calls.append(("root", value, keyword))
        assert study.require_admission(value, keyword=keyword) is token
        return study.inputs.prerequisites(value, keyword=keyword)

    inputs = ModuleType("inputs")
    inputs.prerequisites = prerequisites  # type: ignore[attr-defined]
    reduced.prerequisites = prerequisites  # type: ignore[attr-defined]
    frozen.inputs = inputs  # type: ignore[attr-defined]
    study.inputs = reduced  # type: ignore[attr-defined]
    study.require_admission = admission  # type: ignore[attr-defined]
    current.read_saved = root  # type: ignore[attr-defined]
    reduction.read_profile = profile  # type: ignore[attr-defined]
    cost.read_profile = profile  # type: ignore[attr-defined]
    declared = (
        (support.ROOT, current, "read_saved", root),
        ("admission", study, "require_admission", admission),
        ("profile_receipt", reduction, "read_profile", profile),
        ("profile_receipt", cost, "read_profile", profile),
    )
    modules = (
        ("direct_prerequisites", study, "inputs", reduced, "prerequisites"),
        ("receipt_prerequisites", frozen, "inputs", inputs, "prerequisites"),
    )
    monkeypatch.setattr(support, "targets", lambda: declared)
    monkeypatch.setattr(support, "module_targets", lambda: modules)
    return current, token, calls


def capture(
    monkeypatch: pytest.MonkeyPatch, *, enabled: bool = True
) -> tuple[Any, list[dict[str, Any]]]:
    current, token, calls = route(monkeypatch)
    observer = support.Observer(enabled=enabled, read_clock=Clock())
    with observer.hooks():
        with observer.read(0):
            pass
        for index in (1, 2):
            with observer.read(index):
                assert current.read_saved(token, keyword=token) is token
    assert len(calls) == 30
    assert all(value is token and keyword is token for _, value, keyword in calls)
    results = support.validate_state(
        observer.state(),
        observer.reads,
        enabled=enabled,
        pid=os.getpid(),
        thread=threading.get_ident(),
    )
    return observer, results


def test_real_callsite_defining_identities_and_fixed_inventory() -> None:
    for _, owner, name, original in support.targets():
        assert getattr(owner, name) is original
    for _, owner, name, module, member in support.module_targets():
        assert getattr(owner, name) is module and callable(getattr(module, member))
    assert support.inventory() == (
        ("earlier_archive", None),
        ("admission", 0),
        ("profile_receipt", 1),
        ("receipt_prerequisites", 2),
        ("profile_receipt", 1),
        ("receipt_prerequisites", 4),
        ("profile_receipt", 1),
        ("receipt_prerequisites", 6),
        ("profile_receipt", 1),
        ("receipt_prerequisites", 8),
        ("profile_receipt", 1),
        ("receipt_prerequisites", 10),
        ("profile_receipt", 1),
        ("receipt_prerequisites", 12),
        ("direct_prerequisites", 0),
    )


@pytest.mark.parametrize("enabled", [False, True])
def test_all_calls_forward_and_all_three_vectors_reconcile(
    monkeypatch: pytest.MonkeyPatch, enabled: bool
) -> None:
    observer, results = capture(monkeypatch, enabled=enabled)
    assert results[0]["selected_calls"] == 0
    assert observer.state()["selected_calls"] == (30 if enabled else 0)
    for row in results[1:]:
        assert row["selected_calls"] == (15 if enabled else 0)
        for key, factor in (("wall", 1.0), ("cpu", 2.0), ("reaped_cpu", 0.5)):
            total = row["inclusive_vectors"][key]["earlier_archive"]
            assert total == (29 * factor if enabled else 0)
            assert sum(row["exclusive_vectors"][key].values()) == total
    assert sum(len(r["events"]) for r in observer.reads) == (60 if enabled else 0)


@pytest.mark.parametrize("key", ["cpu", "wall", "reaped_cpu"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0, True])
def test_bad_vector_coordinates_rejected(key: str, bad: Any) -> None:
    value = Clock()()
    value[key] = bad
    with pytest.raises(ArithmeticError):
        support.check_clock(value)


@pytest.mark.parametrize(
    "mutation", ["clock", "parent", "category", "event", "count", "producer"]
)
def test_saved_tree_or_event_changes_rejected(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    observer, _ = capture(monkeypatch)
    row = copy.deepcopy(observer.reads[1])
    item = row["ledger"]["rows"][3]
    if mutation == "clock":
        item["after"]["reaped_cpu"] = item["before"]["reaped_cpu"] - 1
    elif mutation == "parent":
        item["parent"] = 0
    elif mutation == "category":
        item["category"] = "direct_prerequisites"
    elif mutation == "event":
        row["events"] = row["events"][1:]
    elif mutation == "count":
        row["ledger"]["rows"].pop()
    else:
        item["before"]["pid"] += 1
    with pytest.raises(ArithmeticError):
        support.validate_read(row, 1, enabled=True)


def test_callback_failure_keeps_primary_and_restores_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current, token, _ = route(monkeypatch)
    declared = support.targets()
    original = current.read_saved
    error = ValueError("primary fixture failure")

    def failed(*args: Any, **kwargs: Any) -> Any:
        raise error

    vars(current)["read_saved"] = failed
    monkeypatch.setattr(
        support,
        "targets",
        lambda: ((support.ROOT, current, "read_saved", failed), *declared[1:]),
    )
    observer = support.Observer(enabled=True, read_clock=Clock())
    with pytest.raises(ValueError) as caught:
        with observer.hooks(), observer.read(0):
            current.read_saved(token, keyword=token)
    assert caught.value is error
    assert current.read_saved is failed and original is not failed
    assert observer.state()["restored"] is True
    assert observer.reads[0]["status"] == "partial"


def test_unknown_category_and_cap_reject_before_callback() -> None:
    regions = support.Regions(1, read_clock=Clock())
    calls = []

    def callback() -> None:
        calls.append(1)

    with pytest.raises(ArithmeticError):
        regions.wrap("unknown", callback)
    root = regions.wrap(support.ROOT, callback)
    regions.active = True
    root()
    with pytest.raises(ArithmeticError):
        root()
    assert calls == [1]


@pytest.mark.parametrize("maximum", [True, 0, 29, 31])
def test_observer_uses_fixed_boundary_cap(maximum: int) -> None:
    with pytest.raises(ArithmeticError, match="thirty-boundary"):
        support.Observer(enabled=True, maximum=maximum)


def test_unrelated_call_outside_root_passes_without_measurement() -> None:
    regions = support.Regions(30, read_clock=Clock())
    token = object()
    selected = regions.wrap("profile_receipt", lambda value: value)
    regions.active = True
    assert selected(token) is token
    assert regions.total == 0 and regions.rows == []


@pytest.mark.parametrize("mode", ["reentrant", "thread", "wrong_parent"])
def test_nested_call_protection(mode: str) -> None:
    regions = support.Regions(30, read_clock=Clock())
    calls = []
    errors: list[BaseException] = []

    def forbidden() -> None:
        calls.append("unexpected")

    wrong = regions.wrap("receipt_prerequisites", forbidden)

    def root_body() -> None:
        if mode == "reentrant":
            root()
        elif mode == "wrong_parent":
            wrong()
        else:

            def other_thread() -> None:
                try:
                    root()
                except BaseException as error:
                    errors.append(error)

            thread = threading.Thread(target=other_thread)
            thread.start()
            thread.join(timeout=2)
            assert not thread.is_alive()

    root = regions.wrap(support.ROOT, root_body)
    regions.active = True
    if mode == "thread":
        root()
        assert len(errors) == 1 and isinstance(errors[0], ArithmeticError)
    else:
        with pytest.raises(ArithmeticError):
            root()
    assert calls == [] and regions.stack == [] and regions.errors > 0


@pytest.mark.parametrize("with_primary", [False, True])
def test_mutated_hook_is_restored_and_cannot_replace_primary(
    monkeypatch: pytest.MonkeyPatch, with_primary: bool
) -> None:
    current, _, _ = route(monkeypatch)
    original = current.read_saved
    observer = support.Observer(enabled=True, read_clock=Clock())
    primary = ValueError("primary remains primary")
    with pytest.raises(ValueError if with_primary else ArithmeticError) as caught:
        with observer.hooks():
            vars(current)["read_saved"] = lambda: None
            if with_primary:
                raise primary
    if with_primary:
        assert caught.value is primary
    assert current.read_saved is original
    assert "binding_changed" in observer.state()["cleanup_failures"]
    assert observer.state()["restored"] is False


def test_emission_failure_is_retained_and_restores_all_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current, token, _ = route(monkeypatch)
    original = current.read_saved
    failure = OSError("event writer fixture")

    def sink(index: int, row: dict[str, Any]) -> None:
        raise failure

    observer = support.Observer(enabled=True, read_clock=Clock(), event_sink=sink)
    with pytest.raises(OSError) as caught:
        with observer.hooks(), observer.read(0):
            current.read_saved(token, keyword=token)
    assert caught.value is failure and current.read_saved is original
    assert observer.state()["restored"] is True
    assert observer.reads[0]["status"] == "partial"


def test_initial_changed_binding_is_refused_without_replacing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current, _, _ = route(monkeypatch)
    changed = object()
    vars(current)["read_saved"] = changed
    observer = support.Observer(enabled=True, read_clock=Clock())
    with pytest.raises(ArithmeticError, match="unchanged archive callsite"):
        with observer.hooks():
            raise AssertionError("changed hook entered")
    assert current.read_saved is changed and observer.started is False


def test_event_callback_cannot_reenter_measured_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current, token, calls = route(monkeypatch)
    original = current.read_saved

    def sink(index: int, row: dict[str, Any]) -> None:
        current.read_saved(token, keyword=token)

    observer = support.Observer(enabled=True, read_clock=Clock(), event_sink=sink)
    with pytest.raises(ArithmeticError):
        with observer.hooks(), observer.read(0):
            current.read_saved(token, keyword=token)
    assert calls == [] and current.read_saved is original
    assert observer.state()["restored"] is True and observer.state()["errors"] > 0
