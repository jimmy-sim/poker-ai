"""Checkpoint observer safety fixtures; no poker trajectory or reference run."""

import copy
import math
import os
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import checkpoint_cpu_support as tool
import profile_coarse_reader as coarse


def empty_read() -> dict[str, Any]:
    observer = tool.Observer(enabled=False)
    with observer.hooks(), observer.read(0):
        pass
    return copy.deepcopy(observer.reads[0])


def test_plain_reads_cannot_nest() -> None:
    observer = tool.Observer(enabled=False)
    with observer.hooks(), observer.read(0), pytest.raises(ArithmeticError):
        with observer.read(1):
            pass


def test_cleanup_clock_failure_preserves_original_exception() -> None:
    primary = RuntimeError("own replay failed")
    calls = 0

    def clock() -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("final clock unavailable")
        return dict(wall=10.0, cpu=1.0, pid=os.getpid(), thread=threading.get_ident())

    observer = tool.Observer(enabled=False, read_clock=clock)
    with pytest.raises(RuntimeError) as caught:
        with observer.hooks(), observer.read(0):
            raise primary
    assert caught.value is primary
    assert observer.restored is True
    assert observer.reads[0]["status"] != "complete"


@pytest.mark.parametrize(
    "damage", ["nan", "infinity", "negative_wall", "ledger_pid", "extra_clock"]
)
def test_bad_complete_read_rejected(damage: str) -> None:
    row = empty_read()
    if damage == "nan":
        row["before"]["cpu"] = math.nan
    elif damage == "infinity":
        row["after"]["cpu"] = math.inf
    elif damage == "negative_wall":
        row["before"]["wall"] = row["after"]["wall"] = -1.0
    elif damage == "ledger_pid":
        row["ledger"]["pid"] = True
    else:
        row["before"]["unaccounted"] = 1
    with pytest.raises(ArithmeticError):
        tool.validate_read(row, 0)


def test_empty_plain_read_is_valid_and_registry_restored() -> None:
    result = tool.validate_read(empty_read(), 0)
    assert result["calls"] == 0 and result["selected_union_cpu"] == 0
    assert coarse.CATEGORIES is tool.ORIGINAL_CATEGORIES


@pytest.fixture
def fake_checkpoint(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Lifecycle-only fixture. Actual mathematical replay has separate tests."""
    from poker_ai.evaluation import opponent_learning_own as own
    from poker_ai.postflop import learning_artifacts as artifacts
    from poker_ai.postflop import learning_training as training
    from poker_ai.postflop.controlled_scoring import ScoringContext

    calls: list[Any] = []
    sentinel = object()
    context: Any = object.__new__(ScoringContext)
    training_api: Any = training

    def decode(*args: Any, **kwargs: Any) -> Any:
        calls.append(("decode", args, kwargs))
        return sentinel

    def score(*args: Any, **kwargs: Any) -> Any:
        calls.append(("score", args, kwargs))
        return sentinel

    def root(*args: Any, **kwargs: Any) -> Any:
        calls.append(("root", args, kwargs))
        assert training_api.decode(*args, **kwargs) is sentinel
        assert context.score(*args, **kwargs) is sentinel
        return sentinel

    monkeypatch.setattr(artifacts, "decode", decode)
    monkeypatch.setattr(training, "decode", decode)
    monkeypatch.setattr(ScoringContext, "score", score)
    monkeypatch.setattr(training, "replay_snapshot", root)
    monkeypatch.setattr(own, "replay_snapshot", root)
    return own, training, artifacts, ScoringContext, context, calls, sentinel


def complete_fake_reads(fake: Any, *, enabled: bool = True) -> tool.Observer:
    own, _, _, _, _, _, sentinel = fake
    observer = tool.Observer(enabled=enabled)
    with observer.hooks():
        for index in range(3):
            with observer.read(index):
                assert own.replay_snapshot("positional", named=sentinel) is sentinel
    return observer


@pytest.mark.parametrize("enabled", [False, True])
def test_forwarding_complete_state_and_named_root_only(
    fake_checkpoint: Any, enabled: bool
) -> None:
    own, training, artifacts, context_type, context, calls, sentinel = fake_checkpoint
    originals = (
        own.replay_snapshot,
        training.replay_snapshot,
        artifacts.decode,
        context_type.score,
    )
    observer = tool.Observer(enabled=enabled)
    with observer.hooks():
        assert training.replay_snapshot is originals[1]
        for index in range(3):
            with observer.read(index):
                # These reusable and unrelated calls must never start a root.
                assert training.replay_snapshot("legacy") is sentinel
                assert artifacts.decode("outside") is sentinel
                assert context.score("outside") is sentinel
                argument = object()
                assert own.replay_snapshot(argument, named=sentinel) is sentinel
                selected = calls[-3:]
                assert selected[0][1] == (argument,)
                assert selected[0][2]["named"] is sentinel
        assert observer.state()["active"] is True
    assert (
        own.replay_snapshot,
        training.replay_snapshot,
        artifacts.decode,
        context_type.score,
    ) == originals
    results = tool.validate_state(
        observer.state(),
        observer.reads,
        enabled=enabled,
        pid=os.getpid(),
        thread=threading.get_ident(),
        expected=1,
    )
    assert [r["calls"] for r in results] == [3 if enabled else 0] * 3
    with pytest.raises(ArithmeticError, match="reused"):
        with observer.hooks():
            pass


@pytest.mark.parametrize("failure_point", ["root", "decode", "score"])
def test_primary_exception_identity_and_partial_retention(
    fake_checkpoint: Any, monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    own, training, artifacts, context_type, _, _, _ = fake_checkpoint
    primary = ValueError("fixture fails")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise primary

    if failure_point == "root":
        monkeypatch.setattr(training, "replay_snapshot", fail)
        monkeypatch.setattr(own, "replay_snapshot", fail)
    elif failure_point == "decode":
        monkeypatch.setattr(artifacts, "decode", fail)
        monkeypatch.setattr(training, "decode", fail)
    else:
        monkeypatch.setattr(context_type, "score", fail)
    observer = tool.Observer(enabled=True)
    with pytest.raises(ValueError) as caught:
        with observer.hooks(), observer.read(0):
            own.replay_snapshot(object())
    assert caught.value is primary
    assert observer.restored and observer.reads[0]["status"] == "partial"
    assert observer.reads[0]["ledger"]["rows"][0]["failure_kind"] == "ValueError"
    with pytest.raises(ArithmeticError):
        tool.validate_read(observer.reads[0], 1)


def test_initial_and_late_function_and_bound_aliases_restored(
    fake_checkpoint: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import ModuleType

    own, _, artifacts, context_type, context, _, _ = fake_checkpoint
    initial: Any = ModuleType("poker_ai.observer_initial_fixture")
    initial.decode = artifacts.decode
    bound = context.score
    initial.bound = bound
    monkeypatch.setitem(sys.modules, initial.__name__, initial)
    previous = (own.replay_snapshot, artifacts.decode, context_type.score)
    late: Any = ModuleType("poker_ai.observer_late_fixture")
    observer = tool.Observer(enabled=True)
    with observer.hooks(), observer.read(0):
        assert initial.decode is artifacts.decode
        assert initial.bound.__func__ is context_type.score
        late.root = own.replay_snapshot
        late.decode = artifacts.decode
        late.bound = context.score
        monkeypatch.setitem(sys.modules, late.__name__, late)
        late.root("fixture")
    assert initial.decode is previous[1] and initial.bound is bound
    assert late.root is previous[0] and late.decode is previous[1]
    assert late.bound.__func__ is previous[2] and late.bound.__self__ is context
    assert observer.restored and observer.remaining == 0
    tool.validate_read(observer.reads[0], 1)


@pytest.mark.parametrize("bad_index", [-1, 1, True, 0.0, "0"])
def test_ordered_typed_read_inventory(fake_checkpoint: Any, bad_index: Any) -> None:
    observer = tool.Observer(enabled=True)
    with observer.hooks(), pytest.raises(ArithmeticError):
        with observer.read(bad_index):
            pass


@pytest.mark.parametrize("bad_maximum", [0, -1, True, 1.0])
def test_typed_positive_call_cap(bad_maximum: Any) -> None:
    with pytest.raises(ValueError):
        tool.Observer(enabled=True, maximum=bad_maximum)


def test_cap_failure_is_retained_and_restored(fake_checkpoint: Any) -> None:
    own = fake_checkpoint[0]
    observer = tool.Observer(enabled=True, maximum=2)
    with pytest.raises(ArithmeticError, match="cap"):
        with observer.hooks(), observer.read(0):
            own.replay_snapshot("fixture")
    assert observer.regions.total == 2 and observer.regions.errors > 0
    assert observer.restored and observer.reads[0]["status"] == "partial"


def test_wrong_parent_thread_rejected(fake_checkpoint: Any) -> None:
    observer = tool.Observer(enabled=True)
    errors = []

    def foreign() -> None:
        try:
            fake_checkpoint[0].replay_snapshot("foreign")
        except BaseException as error:
            errors.append(error)

    with observer.hooks(), observer.read(0):
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert len(errors) == 1 and isinstance(errors[0], ArithmeticError)
    assert observer.restored and observer.reads[0]["status"] == "partial"


@pytest.mark.parametrize(
    "field",
    [
        "enabled",
        "pid",
        "thread",
        "active",
        "restored",
        "aliases_remaining",
        "original_root_unchanged",
        "errors",
        "cleanup_failures",
        "selected_calls",
        "maximum",
        "read_count",
        "categories",
    ],
)
def test_saved_state_tampering_rejected(fake_checkpoint: Any, field: str) -> None:
    observer = complete_fake_reads(fake_checkpoint)
    state = observer.state()
    value = state[field]
    state[field] = int(value) if type(value) is bool else "changed"
    with pytest.raises(ArithmeticError):
        tool.validate_state(
            state,
            observer.reads,
            enabled=True,
            pid=os.getpid(),
            thread=threading.get_ident(),
            expected=1,
        )


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "bool_index",
        "bool_parent",
        "bool_pid",
        "bool_errors",
        "partial",
        "event_missing",
        "event_extra",
        "parent",
        "reorder",
        "outside",
        "negative_cpu",
        "overlap",
        "unbound_read",
        "late_category",
        "wrong_producer",
    ],
)
def test_selected_ledger_tampering_rejected(fake_checkpoint: Any, damage: str) -> None:
    observer = complete_fake_reads(fake_checkpoint)
    row = copy.deepcopy(observer.reads[0])
    selected = row["ledger"]["rows"]
    if damage == "missing":
        del row["after"]
    elif damage == "extra":
        row["invented"] = 1
    elif damage == "bool_index":
        selected[0]["index"] = False
    elif damage == "bool_parent":
        selected[1]["parent"] = False
    elif damage == "bool_pid":
        selected[0]["before"]["pid"] = True
    elif damage == "bool_errors":
        row["ledger"]["errors"] = False
    elif damage == "partial":
        row["status"] = "partial"
    elif damage == "event_missing":
        row["events"].pop()
    elif damage == "event_extra":
        row["events"].append(copy.deepcopy(row["events"][-1]))
    elif damage == "parent":
        selected[1]["parent"] = None
    elif damage == "reorder":
        selected[1], selected[2] = selected[2], selected[1]
    elif damage == "outside":
        row["before"]["cpu"] = selected[0]["before"]["cpu"] + 1
    elif damage == "negative_cpu":
        row["after"]["cpu"] = -1
    elif damage == "overlap":
        selected[1]["after"]["cpu"] = selected[2]["after"]["cpu"] + 1
    elif damage == "unbound_read":
        selected[0]["read"] = 1
    elif damage == "late_category":
        selected[1]["category"] = "matrix_build"
    else:
        row["ledger"]["thread"] += 1
    with pytest.raises(ArithmeticError):
        tool.validate_read(row, 1)


def independent_value(tree: Any, policy: Any) -> float:
    """Terminal recursion, without ArrayTree.values/edges or a reply calculator."""

    def visit(node: int) -> float:
        owner = int(tree.player[node])
        if owner == -2:
            return float(tree.terminal_values[node])
        weights = (
            tree.chance_edges[node]
            if owner == -1
            else policy[int(tree.information[node])]
        )
        return math.fsum(
            float(weights[a]) * visit(int(tree.children[node, a]))
            for a in range(len(tree.valid[node]))
            if tree.valid[node, a]
        )

    return visit(0)


def independent_reply(context: Any, policy: Any, target: int, *, exact: bool) -> float:
    """Enumerate every legal pure own decision, summing hidden histories first."""
    import itertools

    import numpy as np

    tree = context.exact if exact else context.partition
    base = policy[context.exact_to_partition] if exact else policy
    owned = [i for i, owner in enumerate(tree.owners) if owner == target]
    values = []
    for choices in itertools.product(*(range(len(tree.actions[i])) for i in owned)):
        candidate = base.copy()
        for i, action in zip(owned, choices, strict=True):
            candidate[i] = np.eye(candidate.shape[1])[action]
        values.append((1 if target == 0 else -1) * independent_value(tree, candidate))
    return max(values)


@pytest.mark.parametrize("game", [0, 1])
@pytest.mark.parametrize("kind", ["coarse", "fine", "mixed0", "mixed1"])
def test_actual_checkpoint_replay_matches_independent_terminal_and_pure_math(
    tmp_path: Path, game: int, kind: str
) -> None:
    import numpy as np

    from poker_ai.evaluation import opponent_learning_own as own_module
    from poker_ai.evaluation.opponent_learning_contexts import software_context
    from poker_ai.postflop import learning_artifacts as artifacts
    from poker_ai.postflop import learning_training as training
    from poker_ai.postflop.controlled_checkpoints import write_snapshot
    from poker_ai.postflop.controlled_scoring import ScoringContext

    own: Any = own_module
    context = software_context(game).scoring[kind]
    weights = np.arange(1, context.partition.legal.size + 1, dtype=np.float64).reshape(
        context.partition.legal.shape
    )
    policy = context.partition.normalize(weights)
    policy_bits = policy.tobytes()
    score = context.score(policy)
    value = independent_value(context.exact, policy[context.exact_to_partition])
    assert score.metrics["value_player_zero_chips"] == pytest.approx(value, abs=1e-14)
    for target in (0, 1):
        reply = independent_reply(context, policy, target, exact=True)
        restricted = independent_reply(context, policy, target, exact=False)
        assert score.responses[target]["exact_reply_value_chips"] == pytest.approx(
            reply, abs=1e-14
        )
        assert score.responses[target]["restricted_reply_value_chips"] == pytest.approx(
            restricted, abs=1e-14
        )
        assert score.responses[target]["baseline_value_chips"] == pytest.approx(
            (1 if target == 0 else -1) * value, abs=1e-14
        )
    metadata = dict(id="fictional-unit-fixture", **training.score_data(context, score))
    path = tmp_path / "own.json.gz"
    receipt = write_snapshot(path, context.partition, policy, metadata)
    row = dict(**metadata, receipt=receipt, metadata_sha256=artifacts.sha(metadata))
    blob = path.read_bytes()
    expected = training.replay_snapshot(context, row, blob, 1e-9)
    originals = (
        own.replay_snapshot,
        training.replay_snapshot,
        artifacts.decode,
        ScoringContext.score,
    )
    observer = tool.Observer(enabled=True)
    with observer.hooks():
        for index in range(3):
            with observer.read(index):
                assert own.replay_snapshot(context, row, blob, 1e-9) == expected
    assert policy.tobytes() == policy_bits and path.read_bytes() == blob
    assert (
        own.replay_snapshot,
        training.replay_snapshot,
        artifacts.decode,
        ScoringContext.score,
    ) == originals
    assert observer.restored
    results = tool.validate_state(
        observer.state(),
        observer.reads,
        enabled=True,
        pid=os.getpid(),
        thread=threading.get_ident(),
        expected=1,
    )
    assert all(r["calls"] == 3 for r in results)


def test_exact_nested_cpu_accounting_and_residual(fake_checkpoint: Any) -> None:
    # Eight ordered stamps: read start, root start, decode start/end,
    # score start/end, root end, read end. Units are invented CPU seconds.
    ticks = iter([0.0, 1.0, 2.0, 4.0, 5.0, 8.0, 10.0, 12.0])

    def clock() -> dict[str, Any]:
        value = next(ticks)
        return dict(
            wall=value, cpu=value, pid=os.getpid(), thread=threading.get_ident()
        )

    observer = tool.Observer(enabled=True, read_clock=clock)
    with observer.hooks(), observer.read(0):
        fake_checkpoint[0].replay_snapshot("fixture")
    result = tool.validate_read(observer.reads[0], 1)
    assert result["read_cpu_seconds"] == 12
    assert result["selected_union_cpu"] == 9
    assert result["outside_checkpoint_cpu_seconds"] == 3
    assert result["groups"]["checkpoint_decode"]["inclusive_cpu"] == 2
    assert result["groups"]["checkpoint_score"]["inclusive_cpu"] == 3
    assert result["groups"]["own_checkpoint"]["exclusive_selected_cpu"] == 4


def test_late_bound_root_alias_is_restored(
    fake_checkpoint: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import MethodType, ModuleType

    own = fake_checkpoint[0]
    original = own.replay_snapshot
    late: Any = ModuleType("compact_suit.observer_late_fixture")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    observer = tool.Observer(enabled=True)
    with observer.hooks():
        late.bound = MethodType(own.replay_snapshot, object())
    assert late.bound.__func__ is original
    assert observer.restored


@pytest.mark.parametrize("primary_failure", [False, True])
def test_cleanup_failure_attempts_other_restorations_and_preserves_primary(
    fake_checkpoint: Any, monkeypatch: pytest.MonkeyPatch, primary_failure: bool
) -> None:
    from types import ModuleType

    own, _, artifacts, context_type, _, _, _ = fake_checkpoint
    original = (own.replay_snapshot, artifacts.decode, context_type.score)

    class Difficult(ModuleType):
        refusing = False

        def __setattr__(self, name: str, value: Any) -> None:
            if name == "root" and self.refusing:
                raise OSError("late alias refused restoration")
            super().__setattr__(name, value)

    late = Difficult("poker_ai.observer_difficult_fixture")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    sentinel = RuntimeError("original replay error")
    observer = tool.Observer(enabled=True)
    with pytest.raises(RuntimeError if primary_failure else ArithmeticError) as caught:
        with observer.hooks():
            late.root = own.replay_snapshot
            late.refusing = True
            if primary_failure:
                raise sentinel
    if primary_failure:
        assert caught.value is sentinel
    assert (own.replay_snapshot, artifacts.decode, context_type.score) == original
    assert observer.remaining == 1 and not observer.restored
    assert observer.cleanup_failures == ["OSError"]


def test_recursive_root_rejected_and_restored(
    fake_checkpoint: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    own, training = fake_checkpoint[:2]

    def recursive() -> None:
        own.replay_snapshot()

    monkeypatch.setattr(own, "replay_snapshot", recursive)
    monkeypatch.setattr(training, "replay_snapshot", recursive)
    observer = tool.Observer(enabled=True)
    with pytest.raises(ArithmeticError, match="recursion"):
        with observer.hooks(), observer.read(0):
            own.replay_snapshot()
    assert observer.restored and observer.regions.total == 1


def test_wrong_process_rejected(
    fake_checkpoint: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    observer = tool.Observer(enabled=True)
    with observer.hooks(), observer.read(0):
        with monkeypatch.context() as changed:
            changed.setattr(os, "getpid", lambda: observer.regions.pid + 1)
            with pytest.raises(ArithmeticError, match="serial parent"):
                fake_checkpoint[0].replay_snapshot("foreign")
    assert observer.restored and observer.reads[0]["status"] == "partial"


@pytest.mark.parametrize("primary_failure", [False, True])
def test_boundary_retention_failure_preserves_primary_and_restores(
    fake_checkpoint: Any, primary_failure: bool
) -> None:
    primary = RuntimeError("fixture error")
    rows = []

    def save(row: dict[str, Any]) -> None:
        rows.append(row)
        if len(rows) == 2:
            raise OSError("save failed")

    observer = tool.Observer(enabled=True, read_sink=save)
    with pytest.raises(RuntimeError if primary_failure else OSError) as caught:
        with observer.hooks(), observer.read(0):
            fake_checkpoint[0].replay_snapshot("fixture")
            if primary_failure:
                raise primary
    if primary_failure:
        assert caught.value is primary
    assert observer.restored and len(rows) == 2
    assert observer.reads[0]["status"] == "partial"


def test_classmethod_descriptor_subclass_and_bound_alias_restoration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import ModuleType

    class Base:
        @classmethod
        def score(cls, item: Any, *, named: Any) -> Any:
            assert named is item
            return cls, item

    class Child(Base):
        pass

    initial: Any = ModuleType("poker_ai.classmethod_fixture")
    initial.bound = Child.score
    monkeypatch.setitem(sys.modules, initial.__name__, initial)
    descriptor, bound = vars(Base)["score"], initial.bound
    observer = tool.Observer(enabled=True)
    failures: list[str] = []
    bindings = tool.Bindings(failures)
    with tool.categories():
        wrapper = observer.regions.wrap("checkpoint_score", descriptor.__func__)
        try:
            bindings.install(Base, "score", wrapper, aliases=True)
            item = object()
            assert Child.score(item, named=item) == (Child, item)
            assert initial.bound(item, named=item) == (Child, item)
        finally:
            bindings.restore()
    assert vars(Base)["score"] is descriptor and "score" not in vars(Child)
    assert initial.bound is bound and bindings.restored and not failures


@pytest.mark.parametrize("primary_failure", [False, True])
def test_changed_defining_attribute_rejected_but_restored(
    fake_checkpoint: Any, primary_failure: bool
) -> None:
    own, _, _, context_type = fake_checkpoint[:4]
    original = context_type.score
    primary = ValueError("original checkpoint failure")
    observer = tool.Observer(enabled=True)
    with pytest.raises(ValueError if primary_failure else ArithmeticError) as caught:
        with observer.hooks():
            context_type.score = lambda *args, **kwargs: None
            if primary_failure:
                raise primary
    if primary_failure:
        assert caught.value is primary
    assert (
        context_type.score is original
        and own.replay_snapshot is fake_checkpoint[1].replay_snapshot
    )
    assert not observer.restored and observer.cleanup_failures == ["binding_changed"]


def test_selected_emitter_reentrancy_rejected(fake_checkpoint: Any) -> None:
    observer = tool.Observer(enabled=True)

    def emit(index: int, row: dict[str, Any]) -> None:
        fake_checkpoint[0].replay_snapshot("recursive emission")

    observer.event_sink = emit
    with pytest.raises(ArithmeticError, match="reentrancy"):
        with observer.hooks(), observer.read(0):
            fake_checkpoint[0].replay_snapshot("fixture")
    assert observer.regions.total == 1 and observer.regions.errors > 0
    assert observer.restored and observer.reads[0]["status"] == "partial"
