"""Check the fixed complete pair's accepted identity and work boundary."""

import copy
import json
import sys
import tarfile
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_context_reuse as predecessor  # noqa: E402
import compare_guarded_prerequisite_skip as subject  # noqa: E402
import profile_checkpoint_cpu as supervisor  # noqa: E402

RAW = (
    Path(__file__).resolve().parents[1]
    / "results/validated-sharing-count-gate/pair-raw/raw.tar.gz"
)


def published_identity() -> dict[str, Any]:
    with tarfile.open(RAW, "r:gz") as archive:
        member = archive.extractfile("raw/ordinary/child.json")
        assert member is not None
        child: dict[str, Any] = json.loads(member.read())
        identity: dict[str, Any] = child["result"]["identity"]
        return identity


def pair_children() -> list[dict[str, Any]]:
    identity = published_identity()
    return [
        dict(
            mode=mode,
            status="complete_guarded_skip_pair_child",
            archive_roots=2,
            original_loads=14 if mode == "ordinary" else 2,
            guarded_returns=0 if mode == "ordinary" else 12,
            pid=100 + index,
            input_sha256={"pinned": "same"},
            context_identity_sha256="same",
            result={"identity": copy.deepcopy(identity)},
        )
        for index, mode in enumerate(subject.ORDER)
    ]


def test_exact_published_result_and_declared_skip_work_pass() -> None:
    result = subject.pair_identity(pair_children())
    assert result["status"] == "exact_complete_result_and_work_identity"
    assert result["identity_sha256"] == subject.PREDECESSOR_IDENTITY


def test_changed_saved_work_counter_rejected() -> None:
    children = pair_children()
    children[1]["result"]["identity"]["validation_cache"]["hits"] += 1
    with pytest.raises(ArithmeticError, match="identity failed"):
        subject.pair_identity(children)


@pytest.mark.parametrize("field", ["original_loads", "guarded_returns"])
def test_undeclared_skip_count_rejected(field: str) -> None:
    children = pair_children()
    children[1][field] -= 1
    with pytest.raises(ArithmeticError, match="identity failed"):
        subject.pair_identity(children)


@pytest.mark.parametrize("fail_first", [False, True])
def test_pair_stops_after_failed_ordinary_without_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fail_first: bool
) -> None:
    monkeypatch.setattr(subject, "ROOT", tmp_path)
    monkeypatch.setattr(subject, "source_checks", lambda: {})
    monkeypatch.setattr(subject, "own_published", lambda: {})
    monkeypatch.setattr(predecessor, "contract", lambda root: {"caps": subject.CAPS})
    monkeypatch.setattr(
        subject,
        "pair_identity",
        lambda children: {"status": "synthetic_complete_identity"},
    )
    calls: list[tuple[str, float]] = []

    def supervise(command: list[str], output: Path, cap: float) -> dict[str, Any]:
        output.mkdir()
        calls.append((command[3], cap))
        (output / "child.json").write_text('{"status":"synthetic"}\n')
        return {"returncode": 1 if fail_first else 0, "cap_seconds": cap}

    monkeypatch.setattr(supervisor, "supervise", supervise)
    output = tmp_path / "results/runs/synthetic-pair"
    if fail_first:
        with pytest.raises(ArithmeticError, match="retained failed complete child"):
            subject.pair(output)
        assert calls == [("ordinary", 900)]
        assert (
            json.loads((output / "pair.json").read_bytes())["status"]
            == "failed_retained"
        )
    else:
        subject.pair(output)
        assert calls == [("ordinary", 900), ("guarded_skip", 900)]
        assert (
            json.loads((output / "pair.json").read_bytes())["status"]
            == "synthetic_complete_identity"
        )
