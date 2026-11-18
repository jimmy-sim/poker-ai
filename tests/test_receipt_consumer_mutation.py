"""Synthetic boundary and failure checks; no archived reader is invoked."""

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_context_reuse as predecessor  # noqa: E402
import compare_validated_prerequisite_sharing as comparison  # noqa: E402
import profile_checkpoint_cpu as checkpoint_supervisor  # noqa: E402
import receipt_consumer_mutation_support as subject  # noqa: E402
import validated_prerequisite_sharing_support as sharing  # noqa: E402
from prerequisite_identity_support import Observation  # noqa: E402

from poker_ai.evaluation import batch_cost_inputs as cost
from poker_ai.evaluation import batch_current_inputs as current
from poker_ai.evaluation import batch_reduction_inputs as reduction
from poker_ai.evaluation import frozen_batch_inputs as frozen_inputs
from poker_ai.evaluation import frozen_batch_protocol as frozen
from poker_ai.evaluation import reduced_study_inputs as study_inputs
from poker_ai.evaluation import reduced_study_run as study
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs


@dataclass
class FakeInputs:
    value: int = 1


def fake_observe(value: HistoryInputs) -> tuple[None, Observation]:
    raw = str(cast(FakeInputs, value).value).encode()
    digest = hashlib.sha256(raw).hexdigest()
    return None, Observation(digest, digest, 1, 0)


def fake_sharing_observe(value: HistoryInputs) -> tuple[Any, Observation]:
    return object(), fake_observe(value)[1]


def install_fake_reader(
    monkeypatch: pytest.MonkeyPatch, *, mutate: bool = False
) -> None:
    def loader(*args: Any, **kwargs: Any) -> HistoryInputs:
        return cast(HistoryInputs, FakeInputs())

    def profile(*args: Any, **kwargs: Any) -> dict[str, Any]:
        data = vars(frozen)["inputs"].prerequisites(Path("."))
        if mutate:
            cast(FakeInputs, data).value += 1
        return {}

    def archive(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], HistoryInputs]:
        for _ in range(6):
            vars(reduction)["read_profile"](Path("."), Path("profile"))
        direct = vars(study)["inputs"].prerequisites(Path("."))
        return {"status": "synthetic"}, direct

    monkeypatch.setattr(subject, "observe", fake_observe)
    monkeypatch.setattr(frozen_inputs, "prerequisites", loader)
    monkeypatch.setattr(study_inputs, "prerequisites", loader)
    monkeypatch.setattr(reduction, "read_profile", profile)
    monkeypatch.setattr(cost, "read_profile", profile)
    monkeypatch.setattr(study, "read_saved", archive)


def test_six_nested_and_one_direct_restore_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_reader(monkeypatch)
    original = (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )
    events: list[str] = []
    capture = subject.Capture(lambda rows: events.append(json.dumps(rows)))
    assert subject.read(Path("."), capture)["status"] == "synthetic"
    assert len(capture.rows) == 7
    assert [row["kind"] for row in capture.rows] == ["nested"] * 6 + ["direct"]
    assert all(row["after_archive"] == row["load"] for row in capture.rows)
    assert all(row["after_caller"] == row["load"] for row in capture.rows[:6])
    assert events
    assert original == (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )


def test_mutated_consumer_rejects_and_restores(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_reader(monkeypatch, mutate=True)
    original = (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )
    capture = subject.Capture(lambda rows: None)
    with pytest.raises(ArithmeticError, match="graph changed"):
        subject.read(Path("."), capture)
    assert len(capture.rows) == 1
    assert original == (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )


def test_unknown_call_order_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_reader(monkeypatch)
    capture = subject.Capture(lambda rows: None)
    with subject.instrument(capture):
        with pytest.raises(ArithmeticError, match="outside receipt"):
            vars(frozen)["inputs"].prerequisites(Path("."))
        with pytest.raises(ArithmeticError, match="order changed"):
            capture.finish()


def test_archived_reader_failure_restores_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_reader(monkeypatch)
    original = (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )

    def failing_reader(
        *args: Any, **kwargs: Any
    ) -> tuple[dict[str, Any], HistoryInputs]:
        vars(reduction)["read_profile"](Path("."), Path("profile"))
        raise ValueError("synthetic primary failure")

    monkeypatch.setattr(study, "read_saved", failing_reader)
    capture = subject.Capture(lambda rows: None)
    with pytest.raises(ValueError, match="primary failure"):
        subject.read(Path("."), capture)
    assert len(capture.rows) == 1
    assert original == (
        vars(frozen)["inputs"],
        vars(study)["inputs"],
        vars(reduction)["read_profile"],
        vars(cost)["read_profile"],
    )


def install_sharing_fakes(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_reader(monkeypatch)
    monkeypatch.setattr(sharing, "observe", fake_sharing_observe)
    monkeypatch.setattr(sharing, "disjoint", lambda left, right: None)


def test_validated_share_runs_all_seven_original_loaders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_sharing_fakes(monkeypatch)
    original = frozen_inputs.prerequisites
    calls = 0

    def counted(*args: Any, **kwargs: Any) -> HistoryInputs:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(frozen_inputs, "prerequisites", counted)
    monkeypatch.setattr(study_inputs, "prerequisites", counted)
    captures = [sharing.ValidatedShare(lambda rows: None) for _ in range(2)]
    for capture in captures:
        assert (
            sharing.read(Path("."), Path("own.json"), capture)["status"] == "synthetic"
        )
        assert len(capture.rows) == 7
        assert [row["substituted"] for row in capture.rows] == [False] + [True] * 6
        assert all(data is capture.donor for data in capture.objects)
        assert all(row["after_archive"] == row["load"] for row in capture.rows)
    assert calls == 14
    assert captures[0].donor is not captures[1].donor
    assert vars(frozen)["inputs"] is frozen_inputs
    assert vars(study)["inputs"] is study_inputs


def test_validated_share_rejects_mutated_consumer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_reader(monkeypatch, mutate=True)
    monkeypatch.setattr(sharing, "observe", fake_sharing_observe)
    monkeypatch.setattr(sharing, "disjoint", lambda left, right: None)
    capture = sharing.ValidatedShare(lambda rows: None)
    with pytest.raises(ArithmeticError, match="graph changed"):
        sharing.read(Path("."), Path("own.json"), capture)
    assert vars(frozen)["inputs"] is frozen_inputs
    assert vars(study)["inputs"] is study_inputs


def test_validated_share_rejects_different_fresh_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_sharing_fakes(monkeypatch)
    calls = 0

    def changed(*args: Any, **kwargs: Any) -> HistoryInputs:
        nonlocal calls
        calls += 1
        return cast(HistoryInputs, FakeInputs(2 if calls == 2 else 1))

    monkeypatch.setattr(frozen_inputs, "prerequisites", changed)
    monkeypatch.setattr(study_inputs, "prerequisites", changed)
    capture = sharing.ValidatedShare(lambda rows: None)
    with pytest.raises(ArithmeticError, match="differs from donor"):
        sharing.read(Path("."), Path("own.json"), capture)
    assert calls == 2
    assert vars(frozen)["inputs"] is frozen_inputs


def test_validated_share_propagates_original_loader_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_sharing_fakes(monkeypatch)
    calls = 0

    def failing(*args: Any, **kwargs: Any) -> HistoryInputs:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("synthetic original loader failure")
        return cast(HistoryInputs, FakeInputs())

    monkeypatch.setattr(frozen_inputs, "prerequisites", failing)
    monkeypatch.setattr(study_inputs, "prerequisites", failing)
    capture = sharing.ValidatedShare(lambda rows: None)
    with pytest.raises(ValueError, match="original loader failure"):
        sharing.read(Path("."), Path("own.json"), capture)
    assert calls == 2
    assert vars(frozen)["inputs"] is frozen_inputs
    assert vars(study)["inputs"] is study_inputs


def test_validated_share_rejects_alias_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_sharing_fakes(monkeypatch)

    def conflict(left: object, right: object) -> None:
        raise ArithmeticError("synthetic shared storage")

    monkeypatch.setattr(sharing, "disjoint", conflict)
    capture = sharing.ValidatedShare(lambda rows: None)
    with pytest.raises(ArithmeticError, match="shared storage"):
        sharing.read(Path("."), Path("own.json"), capture)
    assert len(capture.rows) == 1
    assert vars(frozen)["inputs"] is frozen_inputs
    assert vars(study)["inputs"] is study_inputs


@pytest.mark.parametrize("mode", ["ordinary", "validated_share"])
def test_complete_pair_archive_alias_runs_two_roots_and_restores(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
) -> None:
    install_sharing_fakes(monkeypatch)
    original = study.read_saved
    monkeypatch.setattr(current, "read_saved", original)
    with comparison.observed_archives(tmp_path, mode) as captures:
        left = vars(current)["read_saved"](comparison.ROOT, comparison.OWN)
        right = vars(current)["read_saved"](comparison.ROOT, comparison.OWN)
    assert left[0]["status"] == right[0]["status"] == "synthetic"
    assert len(captures) == 2
    assert [len(capture.rows) for capture in captures] == [7, 7]
    assert vars(current)["read_saved"] is original
    assert (tmp_path / "archive-0.json").is_file()
    assert (tmp_path / "archive-1.json").is_file()
    if mode == "validated_share":
        assert captures[0].objects[0] is not captures[1].objects[0]


def test_complete_pair_archive_alias_restores_on_reader_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_fake_reader(monkeypatch, mutate=True)
    monkeypatch.setattr(sharing, "observe", fake_sharing_observe)
    monkeypatch.setattr(sharing, "disjoint", lambda left, right: None)
    original = study.read_saved
    monkeypatch.setattr(current, "read_saved", original)
    with pytest.raises(ArithmeticError, match="graph changed"):
        with comparison.observed_archives(tmp_path, "validated_share"):
            vars(current)["read_saved"](comparison.ROOT, comparison.OWN)
    assert vars(current)["read_saved"] is original
    assert (tmp_path / "archive-0.json").is_file()


def test_complete_pair_identity_includes_work_counters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = {"work_counter": 10, "result": 3}
    expected = hashlib.sha256(predecessor.canonical(identity)).hexdigest()
    monkeypatch.setattr(comparison, "PREDECESSOR_IDENTITY", expected)
    common = dict(
        status="complete_validated_share_pair_child",
        archive_roots=2,
        original_loads=14,
        input_sha256={"pin": "same"},
        context_identity_sha256="same",
    )
    ordinary: dict[str, Any] = dict(
        common,
        mode="ordinary",
        donor_substitutions=0,
        pid=10,
        result={"identity": identity},
    )
    shared: dict[str, Any] = dict(
        common,
        mode="validated_share",
        donor_substitutions=12,
        pid=11,
        result={"identity": dict(identity)},
    )
    assert comparison.pair_identity([ordinary, shared])["identity_sha256"] == expected
    shared["result"]["identity"]["work_counter"] = 9
    with pytest.raises(ArithmeticError, match="identity failed"):
        comparison.pair_identity([ordinary, shared])


@pytest.mark.parametrize("fail_first", [False, True])
def test_complete_pair_supervision_retains_failure_without_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fail_first: bool
) -> None:
    monkeypatch.setattr(comparison, "ROOT", tmp_path)
    monkeypatch.setattr(comparison, "source_checks", lambda: {})
    monkeypatch.setattr(comparison, "own_published", lambda: {})
    monkeypatch.setattr(predecessor, "contract", lambda root: {"caps": comparison.CAPS})
    monkeypatch.setattr(
        comparison,
        "pair_identity",
        lambda children: {"status": "synthetic_complete_identity"},
    )
    calls: list[tuple[str, float]] = []

    def supervise(command: list[str], output: Path, cap: float) -> dict[str, Any]:
        output.mkdir()
        mode = command[3]
        calls.append((mode, cap))
        (output / "child.json").write_text('{"status":"synthetic"}\n')
        return {"returncode": 1 if fail_first else 0, "cap_seconds": cap}

    monkeypatch.setattr(checkpoint_supervisor, "supervise", supervise)
    output = tmp_path / "results/runs/synthetic-pair"
    if fail_first:
        with pytest.raises(ArithmeticError, match="retained failed complete child"):
            comparison.pair(output)
        assert calls == [("ordinary", 900)]
        assert (
            json.loads((output / "pair.json").read_text())["status"]
            == "failed_retained"
        )
    else:
        comparison.pair(output)
        assert calls == [("ordinary", 900), ("validated_share", 900)]
        assert (
            json.loads((output / "pair.json").read_text())["status"]
            == "synthetic_complete_identity"
        )
