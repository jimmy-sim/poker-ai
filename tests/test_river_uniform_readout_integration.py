"""Fixed same-path grid, toy replay, and independent classification gates."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from river_uniform_readout.diagnostics import _case, top_infos  # noqa: E402
from river_uniform_readout.forecast import forecast  # noqa: E402
from river_uniform_readout.learning import (  # noqa: E402
    GAMES,
    LABELS,
    READOUTS,
    SEEDS,
    paths,
)


def _script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _script("study_river_uniform_readout")
reporter = _script("report_river_uniform_readout")


def test_toy_worker_replays_once_and_preserves_failed_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        runner, "context", lambda root, game: software_context(0).scoring["coarse"]
    )
    events: list[dict[str, Any]] = []
    payload = dict(
        root=str(ROOT),
        output=str(tmp_path),
        labels=(80,),
        stage="profile",
        deadline=Deadline(10),
        fingerprint="a" * 64,
    )
    summary = runner._worker(0, [0], payload, events.append)
    assert len(summary["summaries"]) == 1
    assert summary["summaries"][0]["captures"] == 3
    assert [event["phase"] for event in events] == ["started", "completed"]
    with pytest.raises(FileExistsError):
        runner._worker(0, [0], payload, events.append)


def test_profile_forecast_requires_all_fixed_repeats() -> None:
    assert len(paths()) == 12
    assert [spec.index for spec in paths()] == list(range(12))
    assert {spec.seed for spec in paths()} == set(SEEDS)
    with pytest.raises(ArithmeticError, match="complete capped"):
        forecast(dict(status="completed", seconds=1.0, workers=[]))


def test_conservative_profile_uses_slowest_repeat_and_rejects_over_cap() -> None:
    def record(seconds: float) -> dict[str, Any]:
        return dict(
            status="completed",
            worker_count=3,
            assignments=[list(range(i, 36, 3)) for i in range(3)],
            seconds=50.0,
            workers=[
                dict(
                    exitcode=0,
                    messages=[
                        dict(
                            kind="done",
                            summary=dict(
                                summaries=[
                                    dict(
                                        index=index,
                                        repeat=index // 12,
                                        path=vars(paths()[index % 12]),
                                        captures=3,
                                        final_work=100_000,
                                        whole_path_seconds=seconds,
                                    )
                                    for index in range(slot, 36, 3)
                                ]
                            ),
                        )
                    ],
                )
                for slot in range(3)
            ],
        )

    admitted = forecast(record(1.0))
    assert admitted["status"] == "admitted"
    assert admitted["T_seconds"] == pytest.approx(400.0)
    assert admitted["strict_bound_seconds"] == pytest.approx(2800.0)
    rejected = record(1.0)
    rejected["workers"][0]["messages"][0]["summary"]["summaries"][0][
        "whole_path_seconds"
    ] = 12.0
    decision = forecast(rejected)
    assert decision["status"] == "rejected"
    assert decision["per_path_maxima"][0]["maximum_seconds"] == pytest.approx(1200.0)


def _fixture(root: Path, *, bad_candidate: bool = False) -> tuple[Path, Path]:
    own, native = root / "own", root / "native"
    native.mkdir(parents=True)
    audit: list[dict[str, Any]] = []
    for game in GAMES:
        spot = root / "configs/river-uniform-readout-spots" / f"{game}.json"
        spot.parent.mkdir(parents=True, exist_ok=True)
        spot.write_text(json.dumps(dict(pot=100)))
    for spec in paths():
        captures = []
        for label in LABELS:
            for readout in READOUTS:
                fraction = 0.008
                if readout == "uniform_average":
                    fraction = 0.005 if spec.game in GAMES[:2] else 0.008
                    if bad_candidate and spec.game == GAMES[0]:
                        fraction = 0.04
                digest = f"{spec.index}-{label}-{readout}"
                captures.append(
                    dict(
                        metadata=dict(
                            work_label=label,
                            readout=readout,
                            total_work=label + 4,
                            overshoot=4,
                        ),
                        score=dict(
                            metrics=dict(
                                exact_exploitability_chips=fraction * 100,
                                within_partition_gain_chips=0.0,
                                extra_information_gap_chips=0.0,
                                river_only_gain_exact_prefix_chips=0.0,
                            )
                        ),
                        support=None
                        if readout == "current"
                        else dict(
                            whole=dict(
                                all={"uniform_reach_fraction": 1.0},
                                river={"positive_rows": 10},
                            ),
                            post_warm=dict(
                                all={"uniform_reach_fraction": 0.8},
                                river={"positive_rows": 8},
                            ),
                        ),
                        information_rows=7,
                        tree_nodes=20,
                        padded_width=3,
                        receipt=dict(policy_sha256=digest),
                    )
                )
                audit.append(
                    dict(
                        path_index=spec.index,
                        work_label=label,
                        readout=readout,
                        own_policy_sha256=digest,
                        native=dict(maximum_error_chips=0.0),
                    )
                )
        folder = own / "study" / f"path{spec.index:02d}"
        folder.mkdir(parents=True)
        (folder / "summary.json").write_text(
            json.dumps(
                dict(
                    status="completed",
                    path=vars(spec),
                    labels=LABELS,
                    recall_violations=0,
                    captures=captures,
                )
            )
        )
    own_record = dict(
        status="completed",
        stage="study",
        worker_count=3,
        assignments=[list(range(i, 12, 3)) for i in range(3)],
        workers=[
            dict(
                exitcode=0,
                messages=[
                    dict(
                        kind="done",
                        summary=dict(
                            summaries=[
                                dict(
                                    index=spec.index,
                                    repeat=0,
                                    path=vars(spec),
                                    captures=9,
                                    final_work=10_000_004,
                                    whole_path_seconds=float(spec.index + 1),
                                    worker_peak_rss_bytes=123_456,
                                )
                                for spec in paths()
                                if spec.index % 3 == slot
                            ]
                        ),
                    )
                ],
            )
            for slot in range(3)
        ],
    )
    (own / "result.json").write_text(json.dumps(own_record))
    (native / "result.json").write_text(
        json.dumps(dict(status="completed", rows=audit))
    )
    return own, native


def test_same_path_readout_classification_and_absolute_gate(tmp_path: Path) -> None:
    own, native = _fixture(tmp_path)
    result = reporter.report(tmp_path, own, native)
    assert result["classification"] == "positive"
    assert len(result["rows"]) == 108
    assert len(result["primary_paired"]) == 12
    assert all(
        result["primary_spot_medians"][game] == pytest.approx(-0.003)
        for game in GAMES[:2]
    )
    assert all(row["table_bytes"] == 7 * 3 * 4 * 8 for row in result["rows"])
    bad_root = tmp_path / "bad"
    bad_own, bad_native = _fixture(bad_root, bad_candidate=True)
    bad = reporter.report(bad_root, bad_own, bad_native)
    assert bad["classification"] == "negative"
    assert not next(
        gate["median_pass"]
        for gate in bad["gates"]
        if gate["game"] == GAMES[0] and gate["readout"] == "uniform_average"
    )


def test_diagnostic_ranking_and_saved_trace_accounting() -> None:
    import numpy as np
    from river_generalization.learning import context as prior_context
    from river_generalization.learning import paths as prior_paths

    assert top_infos(
        np.array([0.2, 0.2, 0.5, 0.1]),
        np.array([1.0, 1.0, 0.0, 1.0]),
        ("TURN", "TURN", "RIVER", "RIVER"),
        "TURN",
    ) == [0, 1]
    spec = prior_paths()[1]
    scoring = prior_context(ROOT, spec.game, spec.arm)
    own = ROOT / "results/river-generalization/own"
    summary = json.loads(
        (own / "study" / f"path{spec.index:02d}" / "summary.json").read_bytes()
    )
    saved = next(
        row
        for row in summary["captures"]
        if row["metadata"]["work_label"] == 10_000_000
        and row["metadata"]["readout"] == "linear_average"
    )
    case = _case(
        ROOT,
        own,
        scoring,
        spec,
        "linear_average",
        dict(
            policy_sha256=saved["receipt"]["policy_sha256"],
            exploitability_chips=saved["score"]["metrics"][
                "exact_exploitability_chips"
            ],
        ),
        Deadline(60),
    )
    assert case["exploitability_chips"] == pytest.approx(
        saved["score"]["metrics"]["exact_exploitability_chips"], abs=1e-9
    )
    assert all(trace.accounting_error <= 1e-9 for trace in case["traces"])
