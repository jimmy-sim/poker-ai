"""Synthetic guarded-skip cases; no archived reader or reference is invoked."""

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_guarded_prerequisite_skip as comparison  # noqa: E402
import guarded_prerequisite_skip_support as subject  # noqa: E402
import profile_receipt_cpu as scientific  # noqa: E402
import receipt_consumer_mutation_support as original_capture  # noqa: E402
from prerequisite_identity_support import Observation  # noqa: E402

from poker_ai.evaluation import batch_cost_inputs as cost
from poker_ai.evaluation import batch_current_inputs as current
from poker_ai.evaluation import batch_reduction_inputs as reduction
from poker_ai.evaluation import frozen_batch_inputs, reduced_study_inputs
from poker_ai.evaluation import frozen_batch_protocol as frozen
from poker_ai.evaluation import reduced_study_run as study
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FakeInputs:
    value: int = 1


def fake_observe(data: HistoryInputs) -> tuple[None, Observation]:
    if cast(FakeInputs, data).value < 0:
        raise ArithmeticError("unsupported graph shape")
    raw = str(cast(FakeInputs, data).value).encode()
    value = hashlib.sha256(raw).hexdigest()
    return None, Observation(value, value, 1, 0)


def install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    mutate: bool = False,
    wrong_argument: bool = False,
    alias_drift: bool = False,
    original_failure: bool = False,
    archive_failure: bool = False,
    unsupported: bool = False,
) -> list[int]:
    calls = [0]

    def loader(root: Path) -> HistoryInputs:
        calls[0] += 1
        if original_failure:
            raise ValueError("synthetic original load failed")
        return cast(HistoryInputs, FakeInputs(-1 if unsupported else 1))

    def profile(root: Path, path: Path) -> dict[str, Any]:
        del path
        data = vars(frozen)["inputs"].prerequisites(root)
        if mutate:
            cast(FakeInputs, data).value += 1
        if alias_drift:
            vars(frozen)["inputs"] = object()
        return {}

    def archive(root: Path, path: Path) -> tuple[dict[str, Any], HistoryInputs]:
        del path
        for index in range(6):
            selected = Path("changed") if wrong_argument and index == 1 else root
            vars(reduction)["read_profile"](selected, Path("timing"))
            if archive_failure:
                raise ValueError("synthetic archive failed")
        data = vars(study)["inputs"].prerequisites(root)
        return {"status": "synthetic"}, data

    monkeypatch.setattr(subject, "observe", fake_observe)
    monkeypatch.setattr(original_capture, "observe", fake_observe)
    monkeypatch.setattr(frozen_batch_inputs, "prerequisites", loader)
    monkeypatch.setattr(reduced_study_inputs, "prerequisites", loader)
    monkeypatch.setattr(reduction, "read_profile", profile)
    monkeypatch.setattr(cost, "read_profile", profile)
    monkeypatch.setattr(study, "read_saved", archive)
    return calls


def aliases() -> tuple[object, ...]:
    return (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )


def unchanged(_root: Path) -> dict[str, str]:
    return {"pinned": "same"}


def test_one_original_per_root_and_six_guarded_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = install(monkeypatch)
    before = aliases()
    root = Path(".")
    captures = [
        subject.GuardedSkip(root, lambda rows: None, unchanged) for _ in range(2)
    ]
    for capture in captures:
        saved = subject.read(root, Path("own.json"), capture)
        assert saved["status"] == "synthetic"
        assert [row["original_called"] for row in capture.rows] == [True] + [False] * 6
        assert [row["guarded_return"] for row in capture.rows] == [False] + [True] * 6
        assert all(row["after_archive"] == row["load"] for row in capture.rows)
        assert all(row["after_caller"] == row["load"] for row in capture.rows[:6])
    assert calls == [2]
    assert captures[0].donor is not captures[1].donor
    assert aliases() == before


@pytest.mark.parametrize("field", ["pin", "source", "receipt", "archive"])
def test_changed_byte_class_rejects_before_second_return(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    calls = install(monkeypatch)
    before = aliases()
    count = [0]

    def changing(_root: Path) -> dict[str, str]:
        count[0] += 1
        result = dict.fromkeys(("pin", "source", "receipt", "archive"), "same")
        if count[0] >= 4:
            result[field] = "different"
        return result

    capture = subject.GuardedSkip(Path("."), lambda rows: None, changing)
    with pytest.raises(ArithmeticError, match="pinned bytes changed"):
        subject.read(Path("."), Path("own.json"), capture)
    assert calls == [1]
    assert len(capture.rows) == 1
    assert aliases() == before


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"mutate": True}, "graph changed"),
        ({"wrong_argument": True}, "root or arguments changed"),
        ({"alias_drift": True}, "alias changed"),
        ({"original_failure": True}, "original load failed"),
        ({"archive_failure": True}, "archive failed"),
        ({"unsupported": True}, "unsupported graph shape"),
    ],
)
def test_failures_restore_aliases(
    monkeypatch: pytest.MonkeyPatch, change: dict[str, bool], message: str
) -> None:
    install(monkeypatch, **change)
    before = aliases()
    capture = subject.GuardedSkip(Path("."), lambda rows: None, unchanged)
    with pytest.raises((ArithmeticError, ValueError), match=message):
        subject.read(Path("."), Path("own.json"), capture)
    assert aliases() == before


def test_direct_first_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch)

    def wrong(root: Path, path: Path) -> tuple[dict[str, Any], HistoryInputs]:
        del path
        return {}, vars(study)["inputs"].prerequisites(root)

    monkeypatch.setattr(study, "read_saved", wrong)
    before = aliases()
    capture = subject.GuardedSkip(Path("."), lambda rows: None, unchanged)
    with pytest.raises(ArithmeticError, match="call order changed"):
        subject.read(Path("."), Path("own.json"), capture)
    assert aliases() == before


def test_snapshot_closes_over_historical_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = scientific.binding
    monkeypatch.setattr(
        scientific,
        "binding",
        lambda root, clean: binding(root, clean=False),
    )
    snapshot = subject.complete_snapshot(ROOT)
    assert len(snapshot) == 486
    assert "scripts/audit_window_fallback.py" in snapshot
    assert "scripts/inspect_controlled_reply.py" in snapshot
    assert "scripts/compare_guarded_prerequisite_skip.py" in snapshot
    assert snapshot["uv.lock"] == subject.LOCK_SHA256


def test_changed_historical_source_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    binding = scientific.binding
    monkeypatch.setattr(
        scientific,
        "binding",
        lambda root, clean: binding(root, clean=False),
    )
    original_digest = digest

    def changed(path: Path) -> str:
        if path.name == "audit_window_fallback.py":
            return "0" * 64
        return original_digest(path)

    monkeypatch.setattr(subject, "digest", changed)
    with pytest.raises(ArithmeticError, match="historical source bytes changed"):
        subject.complete_snapshot(ROOT)


def test_complete_adapter_uses_two_independent_donors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = install(monkeypatch)
    original = study.read_saved
    monkeypatch.setattr(current, "read_saved", original)

    class FakeGuardedSkip(subject.GuardedSkip):
        def __init__(self, root: Path, publish: Any) -> None:
            super().__init__(root, publish, unchanged)

    monkeypatch.setattr(
        comparison,
        "GuardedSkip",
        FakeGuardedSkip,
    )
    with comparison.observed_archives(tmp_path, "guarded_skip") as captures:
        left = vars(current)["read_saved"](comparison.ROOT, comparison.OWN)
        right = vars(current)["read_saved"](comparison.ROOT, comparison.OWN)
    assert left[0]["status"] == right[0]["status"] == "synthetic"
    assert calls == [2]
    assert len(captures) == 2
    assert [len(capture.rows) for capture in captures] == [7, 7]
    assert captures[0].objects[0] is not captures[1].objects[0]
    assert vars(current)["read_saved"] is original
    assert (tmp_path / "archive-0.json").is_file()
    assert (tmp_path / "archive-1.json").is_file()
