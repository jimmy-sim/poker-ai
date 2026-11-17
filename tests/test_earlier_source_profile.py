"""Independent small call graph: root10s and other4s share callee8s."""

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import earlier_source_profile_support as reader
import pytest


def sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def graph() -> dict[str, Any]:
    functions = []
    for i, (name, calls, own, total) in enumerate(
        (
            ("root", 1, 2.0, 10.0),
            ("shared", 2, 2.0, 8.0),
            ("other_child", 1, 3.0, 3.0),
            ("leaf", 2, 6.0, 6.0),
            ("other", 1, 1.0, 4.0),
        )
    ):
        meta = dict(
            file="fixture.py",
            line=i + 1,
            name=name,
            qualname=name,
            arguments=[],
            code_sha256="a" * 64,
        )
        code_id = sha(meta)
        functions.append(
            dict(
                **meta,
                code_id=code_id,
                entry_index=i,
                id=sha([code_id, i]),
                primitive_calls=calls,
                total_calls=calls,
                self_seconds=own,
                cumulative_seconds=total,
            )
        )
    callers = []
    for a, b, calls, own, total in (
        (0, 1, 1, 1.0, 5.0),
        (0, 2, 1, 3.0, 3.0),
        (1, 3, 2, 6.0, 6.0),
        (4, 1, 1, 1.0, 3.0),
    ):
        callers.append(
            dict(
                caller=functions[a]["id"],
                callee=functions[b]["id"],
                primitive_calls=calls,
                total_calls=calls,
                self_seconds=own,
                cumulative_seconds=total,
            )
        )
    return dict(
        functions=functions,
        callers=callers,
        frame_count=5,
        edge_count=4,
        total_self_seconds=14.0,
    )


def test_direct_caller_cost_is_not_global_shared_function_cost() -> None:
    stats = graph()
    before = copy.deepcopy(stats)
    saved = reader.direct_calls(
        stats, (("fixture.py", "root"), ("fixture.py", "shared"))
    )
    assert (
        stats == before
        and saved["functions"] == stats["functions"]
        and saved["callers"] == stats["callers"]
    )
    a, b = saved["selected"]
    assert a["accounted_seconds"] == 10 and a["residual_seconds"] == 0
    assert a["outgoing"][0]["cumulative_seconds"] == 5
    assert b["frame"]["cumulative_seconds"] == 8 and len(b["incoming"]) == 2
    assert b["accounted_seconds"] == 8
    assert saved["units"] == "elapsed_stack_seconds_including_blocked_waits"


@pytest.mark.parametrize(
    "selected", [(), (("fixture.py", "root"), ("fixture.py", "root"))]
)
def test_bad_selection(selected: tuple[tuple[str, str], ...]) -> None:
    with pytest.raises(ValueError):
        reader.direct_calls(graph(), selected)


def test_missing_frame_is_not_substituted() -> None:
    with pytest.raises(ArithmeticError, match="missing or ambiguous"):
        reader.direct_calls(graph(), (("fixture.py", "absent"),))


def test_duplicate_labels_retained_not_merged() -> None:
    stats = graph()
    row = copy.deepcopy(stats["functions"][1])
    row["entry_index"] = 5
    row["id"] = sha([row["code_id"], 5])
    stats["functions"].append(row)
    stats["frame_count"] = 6
    stats["total_self_seconds"] += row["self_seconds"]
    saved = reader.direct_calls(stats, (("fixture.py", "root"),))
    assert (
        len(saved["functions"]) == 6
        and saved["functions"][1]["code_id"] == saved["functions"][5]["code_id"]
    )
    assert saved["functions"][1]["id"] != saved["functions"][5]["id"]
    with pytest.raises(ArithmeticError, match="missing or ambiguous"):
        reader.direct_calls(stats, (("fixture.py", "shared"),))


def test_recursion_rejected() -> None:
    stats = graph()
    stats["functions"][0]["primitive_calls"] = 0
    with pytest.raises(ArithmeticError, match="recursive selected"):
        reader.direct_calls(stats, (("fixture.py", "root"),))


def test_missing_edge_breaks_accounting() -> None:
    stats = graph()
    stats["callers"].pop(1)
    stats["edge_count"] -= 1
    with pytest.raises(ArithmeticError, match="do not recover"):
        reader.direct_calls(stats, (("fixture.py", "root"),))


def test_foreign_edge_and_tampered_identity_reject() -> None:
    for field, value in (("id", "b" * 64), ("code_sha256", "c" * 64)):
        stats = graph()
        stats["functions"][0][field] = value
        with pytest.raises(ArithmeticError):
            reader.direct_calls(stats, (("fixture.py", "root"),))


def test_nonfinite_seconds_reject() -> None:
    stats = graph()
    stats["callers"][0]["cumulative_seconds"] = float("nan")
    with pytest.raises(ArithmeticError):
        reader.direct_calls(stats, (("fixture.py", "root"),))


def test_every_edge_retained_with_distinct_caller_and_callee_ids() -> None:
    saved = reader.direct_calls(
        graph(), (("fixture.py", "root"), ("fixture.py", "shared"))
    )
    rows = reader.edge_rows(saved)
    assert (
        len(rows) == 5
    )  # root2 outgoing, shared2 incoming and1 outgoing; directions overlap.
    assert all(row["units"] == reader.UNITS for row in rows)
    assert {row["direction"] for row in rows} == {"incoming", "outgoing"}
    assert (
        sum(row["cumulative_seconds"] for row in rows if row["selected_name"] == "root")
        == 8
    )


@pytest.mark.parametrize(
    "bad", [None, "bytes", "line", "arguments", "missing_pin", "duplicate", "symlink"]
)
def test_source_coordinates_are_bound_to_pinned_ast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad: str | None
) -> None:
    monkeypatch.setattr(reader, "SELECTED", (("fixture.py", "load"),))
    raw = b"def load(root):\n    return root\n"
    path = tmp_path / "fixture.py"
    path.write_bytes(raw)
    pins = {"fixture.py": hashlib.sha256(raw).hexdigest()}
    stats = dict(
        functions=[
            dict(
                file="fixture.py",
                name="load",
                qualname="load",
                line=1,
                arguments=["root"],
            )
        ]
    )
    if bad is None:
        reader.source_coordinates(stats, tmp_path, pins)
        return
    if bad == "bytes":
        path.write_bytes(raw + b"\n")
    if bad == "line":
        stats["functions"][0]["line"] = 2
    if bad == "arguments":
        stats["functions"][0]["arguments"] = ["different"]
    if bad == "missing_pin":
        pins.clear()
    if bad == "duplicate":
        stats["functions"].append(dict(stats["functions"][0]))
    if bad == "symlink":
        original = tmp_path / "actual.py"
        original.write_bytes(raw)
        path.unlink()
        path.symlink_to(original)
    with pytest.raises(ArithmeticError):
        reader.source_coordinates(stats, tmp_path, pins)


def saved_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], list[Path]]:
    from types import ModuleType

    monkeypatch.setattr(reader, "SELECTED", (("fixture.py", "root"),))
    source = tmp_path / "fixture.py"
    source.write_text("def root():\n    pass\n")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    pair = tmp_path / "pair"
    (pair / "profile").mkdir(parents=True)
    child = pair / "profile/child.json"
    child.write_text(
        json.dumps(
            dict(source=dict(fingerprint="f" * 64, sha256={"fixture.py": source_sha}))
        )
    )
    config = dict(
        scope="independent_fixture_not_measurement",
        units=reader.UNITS,
        selected=[["fixture.py", "root"]],
        absolute_accounting_tolerance_seconds=1e-7,
        producer_source_fingerprint="f" * 64,
        pair="pair",
        reference_constructed=False,
        poker_training_performed=False,
        admission_evidence=False,
        input_sha256={
            str(p.relative_to(tmp_path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (source, child)
        },
    )
    module = ModuleType("report_cached_native")
    monkeypatch.setattr(module, "ROOT", tmp_path, raising=False)
    calls: list[Path] = []

    def gather(folder: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        assert folder == pair
        calls.append(folder)
        print("synthetic authentication; no producer")
        return [], graph()

    monkeypatch.setattr(module, "gather", gather, raising=False)
    monkeypatch.setitem(sys.modules, "report_cached_native", module)
    return config, calls


def test_saved_export_all_rows_and_unchanged_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import csv

    config, calls = saved_fixture(tmp_path, monkeypatch)
    before = {n: (tmp_path / n).read_bytes() for n in config["input_sha256"]}
    result = reader.write_report(tmp_path, tmp_path / "report", config)
    assert len(calls) == 1 and result["frame_count"] == 5 and result["edge_count"] == 4
    assert all((tmp_path / n).read_bytes() == raw for n, raw in before.items())
    for name, count in (
        ("all-functions.csv", 5),
        ("all-callers.csv", 4),
        ("selected-edges.csv", 2),
        ("selected-functions.csv", 1),
    ):
        with (tmp_path / "report" / name).open(newline="") as f:
            assert len(list(csv.DictReader(f))) == count
    assert (
        tmp_path / "report/authentication.log"
    ).read_text() == "synthetic authentication; no producer\n"
    assert (
        result["reference_constructed"] is False
        and result["poker_training_performed"] is False
    )


@pytest.mark.parametrize(
    "bad", ["unit", "tolerance", "scope", "selection", "hash", "producer"]
)
def test_saved_input_contract_rejects_before_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    config, calls = saved_fixture(tmp_path, monkeypatch)
    if bad == "unit":
        config["units"] = "CPU seconds"
    if bad == "tolerance":
        config["absolute_accounting_tolerance_seconds"] = 0.1
    if bad == "scope":
        config["reference_constructed"] = True
    if bad == "selection":
        config["selected"] = [["fixture.py", "different"]]
    if bad == "hash":
        (tmp_path / "fixture.py").write_text("changed\n")
    if bad == "producer":
        config["producer_source_fingerprint"] = "d" * 64
    with pytest.raises(ArithmeticError):
        reader.write_report(tmp_path, tmp_path / "report", config)
    assert not (tmp_path / "report").exists() and not calls


def test_existing_output_is_retained_before_source_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, calls = saved_fixture(tmp_path, monkeypatch)
    out = tmp_path / "report"
    out.mkdir()
    (out / "prior.json").write_text("retained")
    with pytest.raises(FileExistsError):
        reader.write_report(tmp_path, out, config)
    assert (out / "prior.json").read_text() == "retained" and not calls


def test_raw_changes_outside_six_pins_are_detected_and_partial_output_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, calls = saved_fixture(tmp_path, monkeypatch)
    raw = tmp_path / "pair/retained-raw.json"
    raw.write_text("original")
    module = sys.modules["report_cached_native"]
    original: Any = vars(module)["gather"]

    def changed(folder: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        result: tuple[list[dict[str, Any]], dict[str, Any]] = original(folder)
        raw.write_text("changed fixture")
        return result

    monkeypatch.setattr(module, "gather", changed)
    with pytest.raises(ArithmeticError, match="changed during analysis"):
        reader.write_report(tmp_path, tmp_path / "report", config)
    assert (tmp_path / "report/summary.json").exists() and len(calls) == 1


def test_output_cannot_modify_historical_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, calls = saved_fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="historical producer"):
        reader.write_report(tmp_path, tmp_path / "pair/new-output", config)
    assert not calls and not (tmp_path / "pair/new-output").exists()


def test_reader_root_and_pair_escape_reject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, calls = saved_fixture(tmp_path, monkeypatch)
    module = sys.modules["report_cached_native"]
    monkeypatch.setattr(module, "ROOT", tmp_path / "other-root")
    with pytest.raises(ArithmeticError, match="this repository"):
        reader.write_report(tmp_path, tmp_path / "report", config)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    config["pair"] = "../foreign-producer"
    with pytest.raises(ArithmeticError, match="within repository"):
        reader.write_report(tmp_path, tmp_path / "report", config)
    assert not calls


def test_cli_lists_saved_functions_and_every_direct_edge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import inspect_earlier_source_profile as cli

    calls: list[Path] = []

    def read(root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], str]:
        calls.append(root)
        return graph(), "synthetic existing-data authentication"

    def select(stats: dict[str, Any]) -> dict[str, Any]:
        return reader.direct_calls(stats, (("fixture.py", "root"),))

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "contract", lambda root: {"fixture": True})
    monkeypatch.setattr(cli, "saved_graph", read)
    monkeypatch.setattr(cli, "direct_calls", select)
    monkeypatch.setattr(
        sys, "argv", ["inspect_earlier_source_profile.py", "--function", "1"]
    )
    assert cli.main() == 0
    text = capsys.readouterr().out
    assert calls == [tmp_path]
    assert "including waits" in text and "not current CPU or strength" in text
    assert "inclusive 10.000000s" in text
    assert "5.000000s inclusive" in text and "3.000000s inclusive" in text
    assert "8.000000s inclusive" not in text


def test_cli_invalid_selection_rejects_before_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import inspect_earlier_source_profile as cli

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("invalid menu choice reached source or data loading")

    monkeypatch.setattr(cli, "contract", forbidden)
    monkeypatch.setattr(cli, "saved_graph", forbidden)
    monkeypatch.setattr(
        sys, "argv", ["inspect_earlier_source_profile.py", "--function", "6"]
    )
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
