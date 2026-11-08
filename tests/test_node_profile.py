"""Synthetic node timings exercise schemas; they are never benchmark evidence."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import controlled_profile as original
from poker_ai.postflop import node_profile as study
from poker_ai.validation.five_card import source_provenance

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def receipt() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads((ROOT / study.CONFIG).read_text())
    _, protocol = study.inputs(ROOT, config)
    old = json.loads((ROOT / config["parent_profile"]).read_text())
    candidates = {
        (original.identity(r), r["repeat"]): r for r in old["timings"]["rows"]
    }
    reference = [
        copy.deepcopy(
            r
            if r["traversal"] == "full"
            else candidates[original.identity(r), r["repeat"]]
        )
        for r in old["timings"]["dense"]
    ]
    nodes = copy.deepcopy(old["timings"]["rows"])
    for group, seconds in ((reference, 1.0), (nodes, 0.5)):
        for row in group:
            row["initialization_seconds"] = 0.5
            row["incremental_seconds"] = seconds
    roles = {"dense": "parent", "rows": "nodes"}
    orders = [
        {**o, "order": [roles[k] for k in o["order"]]} for o in old["pair_orders"]
    ]
    diagnostics = copy.deepcopy(old["cache_diagnostics"])
    index = {(original.identity(r), r["repeat"]): r for r in nodes}
    for d in diagnostics:
        d["node_records_prepared"] = index[original.identity(d), d["repeat"]][
            "tree_nodes"
        ]
        d["node_setup_seconds"] = 0.1
    profiles = []
    for p in old["profiles"]:
        if p["traversal"] == "full" or p["engine"] == "rows":
            for engine in (
                ["parent"] if p["traversal"] == "full" else ["parent", "nodes"]
            ):
                row = copy.deepcopy(p)
                row["engine"] = engine
                row["initialization_seconds"] = 0.5
                row["incremental_seconds"] = 1.0 if engine == "parent" else 0.5
                row["hotspots"] = [
                    dict(
                        file="synthetic.py",
                        line=i,
                        function="fixture",
                        calls=1,
                        primitive_calls=1,
                        self_seconds=0.0,
                        cumulative_seconds=0.01,
                    )
                    for i in range(25)
                ]
                profiles.append(row)
    checks = []
    for game, name in sorted(
        {(r["spot_file"], r["representation"]) for r in reference}
    ):
        n = next(
            r["tree_nodes"]
            for r in reference
            if r["spot_file"] == game and r["representation"] == name
        )
        checks.append(
            dict(
                spot_file=game,
                representation=name,
                nodes=n,
                edges=n - 1,
                decision_nodes=n // 2,
                invalid_property_errors=3 * n - n // 2,
                invalid_action_pairs=2 * n,
            )
        )
    source = source_provenance(ROOT, ROOT / study.CONFIG, entrypoints=(study.ENTRY,))
    source["dirty"] = False  # Explicit synthetic test data, never published.
    saved: dict[str, Any] = dict(
        format=study.FORMAT,
        status="completed",
        failure=None,
        source=source,
        config=config,
        adapter_checks=checks,
        parity=copy.deepcopy(old["parity"]),
        timings={"parent": reference, "nodes": nodes},
        pair_orders=orders,
        cache_diagnostics=diagnostics,
        profiles=profiles,
        seconds=1000.0,
        strength_comparison_performed=False,
    )
    return saved, protocol


def test_schema_role_adapter_preserves_values_and_forecast_full_cells(
    receipt: tuple[dict[str, Any], dict[str, Any]],
    tmp_path: Path,
) -> None:
    saved, protocol = receipt
    before = copy.deepcopy(saved)
    study.validate(saved, protocol)
    adapted = study.canonical_roles(saved)
    assert adapted["timings"]["dense"] == saved["timings"]["parent"]
    assert adapted["timings"]["rows"] == saved["timings"]["nodes"]
    assert saved == before
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(saved))
    _, summary = study.report(ROOT, path)
    assert summary["median_paired_ratio"] == 2.0
    assert summary["adapter_nodes"] == 48604
    assert summary["adapter_edges"] == 48600
    assert summary["timing_rows"] == 708
    assert summary["parity_checkpoints"] == 576
    a, b = (
        summary["forecasts"]["parent"]["cells"],
        summary["forecasts"]["nodes"]["cells"],
    )
    assert [r for r in a if r["traversal"] == "full"] == [
        r for r in b if r["traversal"] == "full"
    ]
    assert "separate from unchanged CFR visits" in study.tables(summary)


@pytest.mark.parametrize(
    "change",
    ["interface", "edge", "error", "records", "prep_time", "state", "order", "parity"],
)
def test_reject_partial_or_changed_node_evidence(
    receipt: tuple[dict[str, Any], dict[str, Any]], change: str
) -> None:
    saved, protocol = receipt
    if change == "interface":
        saved["adapter_checks"].pop()
    elif change == "edge":
        saved["adapter_checks"][0]["edges"] -= 1
    elif change == "error":
        saved["adapter_checks"][0]["invalid_property_errors"] = 0
    elif change == "records":
        saved["cache_diagnostics"][0]["node_records_prepared"] = 0
    elif change == "prep_time":
        saved["cache_diagnostics"][0]["node_setup_seconds"] = 1.0
    elif change == "state":
        saved["timings"]["nodes"][0]["state_sha256"] = "b" * 64
    elif change == "order":
        saved["pair_orders"][0]["order"].reverse()
    else:
        saved["parity"].pop()
    with pytest.raises(ArithmeticError):
        study.validate(saved, protocol)


def test_reject_incomplete_source_claim_and_time(
    receipt: tuple[dict[str, Any], dict[str, Any]], tmp_path: Path
) -> None:
    saved, _ = receipt
    for change in ("source", "status", "claim", "time"):
        altered = copy.deepcopy(saved)
        if change == "source":
            altered["source"]["sha256"] = {}
        elif change == "status":
            altered["status"] = "incomplete"
        elif change == "claim":
            altered["strength_comparison_performed"] = True
        else:
            altered["seconds"] = 0
        path = tmp_path / "invalid.json"
        path.write_text(json.dumps(altered))
        with pytest.raises(ArithmeticError):
            study.report(ROOT, path)
