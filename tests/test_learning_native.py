"""Old OWN policies exercise the new archive/native path without poker training."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_old_profiles_stream_to_native_without_reference_policy_or_training(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.postflop.controlled_training import ControlledTrainer
    from poker_ai.solver_validation import controlled_learning as native
    from poker_ai.solver_validation.controlled_pipeline import license_record
    from poker_ai.solver_validation.reference import Reference

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("no new learning or reference strategies in this test")

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "train_to", forbidden)
    monkeypatch.setattr(Reference, "policy", forbidden)
    config = json.loads((ROOT / pipeline_cost.CONFIG).read_text())
    cases, protocol, _ = pipeline_cost.inputs(ROOT, config)
    contexts = pipeline_cost.contexts(ROOT, protocol["future_comparison"])
    assert (
        license_record(config)["sha256"] == config["native_reference"]["license_sha256"]
    )
    rows = []
    for index in (0, 15):
        case = cases[index]
        context = contexts[case["spot_file"], case["representation"]]
        policy = pipeline_cost.source_policy(context, case)
        metadata = dict(
            id=f"old-own-software-fixture-{index}",
            index=index,
            case={k: case[k] for k in ("spot_file", "representation")},
            labels=[["iteration", 4096]],
            **score_data(context, context.score(policy)),
        )
        file = f"old-{index}.json.gz"
        receipt = write_snapshot(tmp_path / file, context.partition, policy, metadata)
        rows.append(
            dict(**metadata, file=file, receipt=receipt, metadata_sha256=sha(metadata))
        )
    archive = tmp_path / "own-profiles.jsonl.gz"
    details_sha = write_archive(archive, tmp_path, rows)
    own = dict(rows=rows, details_file=archive.name, details_sha256=details_sha)
    own_path = tmp_path / "own.json"
    own_path.write_text(json.dumps(own))
    events: list[dict[str, Any]] = []
    summary = native.native_job(
        0,
        [0, 15],
        dict(
            root=str(ROOT),
            own_path=str(own_path),
            remaining_seconds=120,
            comparison=protocol["future_comparison"],
            own=own,
        ),
        events.append,
    )
    assert summary["snapshots"] == 2
    assert summary["maximum_error_chips"] < 1e-9
    workers = []
    assignments = partition(140, 3)
    for indices in assignments:
        selected = [e for e in events if e["kind"] == "cell" and e["index"] in indices]
        workers.append(
            dict(
                exitcode=0,
                messages=[
                    *selected,
                    dict(
                        kind="done",
                        summary=dict(
                            cells=len(indices),
                            snapshots=len(selected),
                            maximum_error_chips=max(
                                (e["maximum_error_chips"] for e in selected),
                                default=0.0,
                            ),
                        ),
                    ),
                ],
            )
        )
    saved: dict[str, Any] = dict(
        format=native.FORMAT,
        status="completed",
        failure=None,
        own_sha256=digest(own_path),
        details_sha256=details_sha,
        seconds=1.0,
        batch=dict(
            status="completed", failure=None, assignments=assignments, workers=workers
        ),
    )
    assert native.validate(saved, own, own_path)["snapshots"] == 2
    for mode in ("missing", "duplicate", "native_metric", "reply", "wrong_binding"):
        changed = copy.deepcopy(saved)
        messages = changed["batch"]["workers"][0]["messages"]
        if mode == "missing":
            messages.pop(0)
        elif mode == "duplicate":
            messages.insert(0, copy.deepcopy(messages[0]))
        elif mode == "native_metric":
            messages[0]["native_metrics"]["exact_exploitability_chips"] += 1
        elif mode == "reply":
            messages[0]["responses"][0]["achieved_exact_chips"] += 1
        else:
            changed["own_sha256"] = "0" * 64
        with pytest.raises(ArithmeticError):
            native.validate(changed, own, own_path)
