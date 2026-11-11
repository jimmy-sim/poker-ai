"""Complete fictional report grid; means/ranges are not confidence intervals."""

import copy
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location(
    "refinement_report_draft",
    Path(__file__).resolve().parents[1] / "scripts/report_river_refinement.py",
)
assert SPEC is not None and SPEC.loader is not None
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def profiles() -> list[dict[str, Any]]:
    result = []
    for seed in REPORT.SEEDS:
        for role in REPORT.ROLES:
            responses = []
            for target in (0, 1):
                responses.append(
                    dict(
                        target=target,
                        river_infos=4,
                        supported_infos=3,
                        unsupported_infos=1,
                        probes=[
                            dict(
                                probe=probe,
                                groups=2 if probe == "q8" else 4,
                                panels={
                                    suffix: dict(
                                        local_sharing_cost_chips_per_cf_decision=0.75
                                        if probe == "q8"
                                        else 0.0,
                                        unresolved_parents=1 if probe == "q8" else 0,
                                        supported_groups=2,
                                    )
                                    for suffix in REPORT.SUFFIXES
                                },
                            )
                            for probe in REPORT.PROBES
                        ],
                    )
                )
            result.append(dict(seed=seed, role=role, responses=responses))
    return result


def test_all_144_conditions_keep_seed_seat_method_suffix_and_probe() -> None:
    rows = REPORT.flat(profiles())
    assert len(rows) == 144
    assert sum(r[REPORT.VALUE] for r in rows) == 27
    assert {r["target"] for r in rows} == {0, 1}
    assert {r["role"] for r in rows} == set(REPORT.ROLES)


@pytest.mark.parametrize(
    "bad",
    [
        "missing_seed",
        "duplicate",
        "missing_seat",
        "missing_suffix",
        "missing_probe",
        "nan",
    ],
)
def test_incomplete_or_nonfinite_tables_rejected(bad: str) -> None:
    data = profiles()
    if bad == "missing_seed":
        data = data[:-3]
    elif bad == "duplicate":
        data[-1] = data[0]
    elif bad == "missing_seat":
        data[0]["responses"].pop()
    elif bad == "missing_suffix":
        data[0]["responses"][0]["probes"][0]["panels"].pop("exact")
    elif bad == "missing_probe":
        data[0]["responses"][0]["probes"].pop()
    else:
        data[0]["responses"][0]["probes"][0]["panels"]["exact"][REPORT.VALUE] = float(
            "nan"
        )
    with pytest.raises((ArithmeticError, KeyError)):
        REPORT.flat(data)


def test_existing_report_folder_preserved_before_reading_inputs(tmp_path: Path) -> None:
    output = tmp_path / "report"
    output.mkdir()
    marker = output / "keep"
    marker.write_text("original")
    with pytest.raises(FileExistsError):
        REPORT.report(tmp_path, tmp_path / "absent", output, plots=False)
    assert marker.read_text() == "original"


def test_optional_figure_from_fictional_complete_grid(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    data = [
        dict(
            suffix=suffix,
            role=role,
            probe=probe,
            mean=0.75 if probe == "q8" else 0.0,
            minimum=0.0,
            maximum=1.0 if probe == "q8" else 0.0,
        )
        for suffix in REPORT.SUFFIXES
        for role in REPORT.ROLES
        for probe in REPORT.PROBES
    ]
    output = tmp_path / "plot.png"
    REPORT.draw(data, output)
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_complete_actual_saved_data_receipt_replays_all_rows() -> None:
    data = REPORT.checked(ROOT, ROOT / "results/river-refinement")
    assert len(REPORT.flat(data)) == 144
    assert sum(r["river_infos"] for p in data for r in p["responses"]) == 29808
    for p in data:
        for r in p["responses"]:
            assert r["q8_exact_mass_same_partition"] is True
            assert r["supported_infos"] == r["river_infos"] == 1656
            # This retained negative result must not become an inferred improvement.
            for suffix in REPORT.SUFFIXES:
                panels = [q["panels"][suffix] for q in r["probes"]]
                assert panels[0] == panels[1] == panels[2]
                assert panels[3][REPORT.VALUE] == 0


@pytest.mark.parametrize(
    "bad", ["failure", "training", "inventory", "hash", "source_sha"]
)
def test_changed_actual_receipt_rejected(tmp_path: Path, bad: str) -> None:
    folder = tmp_path / "report"
    shutil.copytree(
        ROOT / "results/river-refinement",
        folder,
        ignore=shutil.ignore_patterns("checks", "report"),
    )
    path = folder / "manifest.json"
    manifest = json.loads(path.read_text())
    if bad == "failure":
        (folder / "failure.json").write_text("{}")
    elif bad == "training":
        manifest["training_performed"] = True
    elif bad == "inventory":
        manifest["outputs"].pop("rows.json.gz")
    elif bad == "hash":
        manifest["outputs"]["summary.json"] = "0" * 64
    else:
        manifest["source_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(ArithmeticError):
        REPORT.checked(ROOT, folder)


def test_replay_roundoff_is_only_for_local_costs_and_inputs_unchanged() -> None:
    saved = dict(
        target=0,
        total_counterfactual_mass=1.0,
        probes=profiles()[0]["responses"][0]["probes"],
    )
    actual = copy.deepcopy(saved)
    actual["probes"][0]["panels"]["exact"][REPORT.VALUE] += 1e-13
    before = copy.deepcopy(actual)
    assert 0 < REPORT.replay_summary(actual, saved) < 1e-12
    assert actual == before


@pytest.mark.parametrize(
    "bad", ["cost", "support", "count", "probe", "singleton", "nan"]
)
def test_roundoff_does_not_hide_changed_costs_or_structural_failures(bad: str) -> None:
    saved = dict(
        target=0,
        total_counterfactual_mass=1.0,
        probes=profiles()[0]["responses"][0]["probes"],
    )
    actual = copy.deepcopy(saved)
    if bad == "cost":
        actual["probes"][0]["panels"]["exact"][REPORT.VALUE] += 1e-10
    elif bad == "support":
        actual["total_counterfactual_mass"] += 1e-13
    elif bad == "count":
        actual["probes"][0]["groups"] += 1
    elif bad == "probe":
        actual["probes"].pop()
    elif bad == "singleton":
        actual["probes"][-1]["panels"]["exact"][REPORT.VALUE] = 1e-13
    else:
        actual["probes"][0]["panels"]["exact"][REPORT.VALUE] = float("nan")
    with pytest.raises(ArithmeticError):
        REPORT.replay_summary(actual, saved)
