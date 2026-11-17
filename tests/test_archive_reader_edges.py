"""Exercise the fixed query with independent graph/source/output failures."""

import copy
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

import earlier_source_profile_support as original
import inspect_archive_reader as reader
import pytest


def graph() -> dict[str, Any]:
    # Reuse the independent shared-callee fixture without relying on pytest's
    # import mode or importing another installed package called "tests".
    factory = runpy.run_path(
        str(Path(__file__).with_name("test_earlier_source_profile.py"))
    )["graph"]
    result: dict[str, Any] = factory()
    return result


def fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "repo"
    folder = root / "producer/profile"
    folder.mkdir(parents=True)
    path = root / "fixture.py"
    path.write_text("def root():\n    pass\n")
    stats = graph()
    base = dict(pair="producer", input_sha256={}, producer_source_fingerprint="fixture")
    (folder / "child.json").write_text(
        json.dumps(
            dict(
                source=dict(
                    sha256={"fixture.py": hashlib.sha256(path.read_bytes()).hexdigest()}
                )
            )
        )
    )
    monkeypatch.setattr(reader, "original_contract", lambda r: base)
    monkeypatch.setattr(
        reader,
        "contract",
        lambda r: dict(selected=[["fixture.py", "root"]], prospective_issue="fixture"),
    )
    monkeypatch.setattr(
        original,
        "saved_graph",
        lambda r, c: (copy.deepcopy(stats), "authenticated fixture\n"),
    )
    return root, stats


def test_real_fixed_contract_has_all_seven_defining_coordinates() -> None:
    config = reader.contract(reader.ROOT)
    assert config["selected"] == [
        ["src/poker_ai/evaluation/reduced_study_run.py", "read_saved"],
        ["src/poker_ai/evaluation/reduced_study_protocol.py", "require_admission"],
        ["src/poker_ai/evaluation/reduced_study_protocol.py", "expected_admission"],
        ["src/poker_ai/evaluation/frozen_batch_inputs.py", "prerequisites"],
        ["src/poker_ai/evaluation/averaging_history_inputs.py", "load"],
        ["src/poker_ai/evaluation/frozen_batch_validation.py", "gather"],
        ["src/poker_ai/evaluation/frozen_batch_validation.py", "grid"],
    ]
    assert "6957605618" in config["prospective_issue"]


def test_changed_contract_rejected(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    (tmp_path / reader.CONFIG).write_text("{}")
    with pytest.raises(ArithmeticError, match="selection changed"):
        reader.contract(tmp_path)


def test_fixture_reuses_all_graph_edges_and_caller_costs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, stats = fixture(tmp_path, monkeypatch)
    saved, transcript = reader.analyze(root)
    assert saved["functions"] == stats["functions"]
    assert saved["callers"] == stats["callers"]
    assert saved["selected"][0]["accounted_seconds"] == 10
    assert saved["selected"][0]["outgoing"][0]["cumulative_seconds"] == 5
    assert saved["functions"][1]["cumulative_seconds"] == 8
    assert transcript == "authenticated fixture\n"


@pytest.mark.parametrize(
    "field,value", [("line", 4), ("qualname", "alias"), ("arguments", ["other"])]
)
def test_changed_coordinates_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    root, stats = fixture(tmp_path, monkeypatch)
    stats["functions"][0][field] = value
    with pytest.raises(ArithmeticError, match="coordinate differs"):
        reader.coordinates(root, stats, (("fixture.py", "root"),))


@pytest.mark.parametrize(
    "mode", ["bytes", "unlisted", "symlink", "missing", "duplicate", "decorator"]
)
def test_unpinned_or_ambiguous_definition_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    root, stats = fixture(tmp_path, monkeypatch)
    path = root / "fixture.py"
    selected = (("fixture.py", "root"),)
    if mode == "bytes":
        path.write_text("def root():\n    return 3\n")
    elif mode == "unlisted":
        selected = (("unlisted.py", "root"),)
    elif mode == "symlink":
        outside = tmp_path / "outside.py"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
    elif mode == "missing":
        stats["functions"] = stats["functions"][1:]
    elif mode == "duplicate":
        stats["functions"].append(copy.deepcopy(stats["functions"][0]))
    else:
        path.write_text("@decorator\ndef root():\n    pass\n")
        child = root / "producer/profile/child.json"
        data = json.loads(child.read_text())
        data["source"]["sha256"]["fixture.py"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        child.write_text(json.dumps(data))
    with pytest.raises(ArithmeticError):
        reader.coordinates(root, stats, selected)


@pytest.mark.parametrize("mutation", ["recursive", "bad_time"])
def test_query_keeps_original_graph_rejections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root, stats = fixture(tmp_path, monkeypatch)
    if mutation == "recursive":
        stats["functions"][0]["primitive_calls"] = 0
    else:
        stats["callers"][0]["cumulative_seconds"] += 1
    with pytest.raises(ArithmeticError):
        reader.analyze(root)


def test_export_retains_complete_data_and_refuses_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, stats = fixture(tmp_path, monkeypatch)
    out = tmp_path / "out"
    reader.write_report(root, out)
    assert {p.name for p in out.iterdir()} == {
        "all-functions.csv",
        "all-callers.csv",
        "selected-functions.csv",
        "selected-edges.csv",
        "summary.json",
        "authentication.log",
    }
    saved = json.loads((out / "summary.json").read_text())
    assert saved["frame_count"] == len(stats["functions"]) == 5
    assert saved["edge_count"] == len(stats["callers"]) == 4
    assert saved["poker_training_performed"] is False
    assert saved["reference_constructed"] is False
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        reader.write_report(root, out)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}


@pytest.mark.parametrize(
    "mode", ["inside", "raw_symlink", "output_symlink", "mutation"]
)
def test_export_protects_raw_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    root, _ = fixture(tmp_path, monkeypatch)
    out = tmp_path / "out"
    if mode == "inside":
        out = root / "producer/new"
    elif mode == "raw_symlink":
        (root / "producer/link").symlink_to(root / "fixture.py")
    elif mode == "output_symlink":
        out.symlink_to(tmp_path / "not-created")
    else:
        analyze = reader.analyze

        def changed(r: Path) -> tuple[dict[str, Any], str]:
            result = analyze(r)
            (root / "producer/added").write_text("changed")
            return result

        monkeypatch.setattr(reader, "analyze", changed)
    with pytest.raises((ArithmeticError, FileExistsError, ValueError)):
        reader.write_report(root, out)


@pytest.mark.parametrize("mode", ["list", "function", "output_function"])
def test_terminal_lists_or_shows_every_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
) -> None:
    root, _ = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(reader, "ROOT", root)
    args = ["inspect_archive_reader.py"]
    if mode != "list":
        args += ["--function", "1"]
    if mode == "output_function":
        args += ["--output", str(tmp_path / "out")]
    monkeypatch.setattr("sys.argv", args)
    assert reader.main() == 0
    text = capsys.readouterr().out
    assert "Historical elapsed-stack" in text and "inclusive 10.000000s" in text
    if mode != "list":
        assert "incoming (all direct edges)" in text
        assert "5.000000s; 1 calls" in text and "3.000000s; 1 calls" in text
