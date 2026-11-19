"""Data-only report honors the complete fixed panel and signed pairing."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from river_strength.learning import LABELS, READOUTS, paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "river_strength_report", ROOT / "scripts/report_river_strength.py"
)
assert SPEC is not None and SPEC.loader is not None
reporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reporter)


def fixture(root: Path) -> tuple[Path, Path]:
    own, native = root / "own", root / "native"
    native.mkdir()
    audit: list[dict[str, Any]] = []
    for spec in paths():
        captures = []
        for label in LABELS:
            for readout in READOUTS:
                epsilon = 1.0 if spec.arm == "texture_range_q8_b8" else 0.5
                epsilon += (spec.seed - 20261301) * 0.1
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
                                exact_exploitability_chips=epsilon,
                                within_partition_gain_chips=epsilon / 2,
                                extra_information_gap_chips=epsilon / 2,
                                river_only_gain_exact_prefix_chips=epsilon / 4,
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
                    path=dict(
                        index=spec.index, game=spec.game, seed=spec.seed, arm=spec.arm
                    ),
                    labels=LABELS,
                    captures=captures,
                )
            )
        )
    (native / "result.json").write_text(
        json.dumps(dict(status="completed", rows=audit))
    )
    return own, native


def test_complete_report_retains_all_profiles_and_signed_contrast(
    tmp_path: Path,
) -> None:
    own, native = fixture(tmp_path)
    result = reporter.report(ROOT, own, native)
    assert len(result["rows"]) == 108
    assert result["primary_direction"] == "positive"
    assert result["primary_median_candidate_minus_control_fraction_initial_pot"] < 0
    assert [r["candidate_minus_control_chips"] for r in result["primary_paired"]] == (
        pytest.approx([-0.5] * 3)
    )
    assert all(r["table_bytes"] == 7 * 3 * 3 * 8 for r in result["rows"])
    assert all(
        r["initial_only_river_rows"] == 2
        for r in result["rows"]
        if r["readout"] != "current"
    )
    assert len(result["gates"]) == 4


def test_report_rejects_missing_native_scalar(tmp_path: Path) -> None:
    own, native = fixture(tmp_path)
    record = json.loads((native / "result.json").read_bytes())
    record["rows"].pop()
    (native / "result.json").write_text(json.dumps(record))
    with pytest.raises(ArithmeticError, match="108-scalar"):
        reporter.report(ROOT, own, native)
