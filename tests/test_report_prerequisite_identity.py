"""Data-only prerequisite report checks; no archived reader invocation."""

import ast
import json
import shutil
from pathlib import Path

import pytest
import report_prerequisite_identity as tool


def test_published_raw_report_and_output_retention(tmp_path: Path) -> None:
    output = tmp_path / "report"
    tool.report(output)
    summary = json.loads((output / "summary.json").read_text())
    assert summary["runtime_count"] == 2
    assert summary["calls_per_runtime"] == 7
    assert summary["within_runtime_complete_graph_equal"] is True
    assert summary["cross_runtime_complete_graph_equal"] is True
    assert summary["reused_result_safety_in_complete_reader_proven"] is False
    assert len((output / "calls.csv").read_text().splitlines()) == 15
    with pytest.raises(FileExistsError):
        tool.report(output)


def test_changed_raw_member_rejects_before_export(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    shutil.copytree(tool.RAW, raw)
    (raw / "311" / "child.log").write_text("tampered\n")
    output = tmp_path / "rejected"
    with pytest.raises(ArithmeticError, match="raw prerequisite member changed"):
        tool.report(output, raw)
    assert not output.exists()


def test_report_has_only_standard_library_imports() -> None:
    tree = ast.parse(Path(tool.__file__).read_text())
    roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    roots.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert roots <= {"csv", "hashlib", "json", "subprocess", "sys", "pathlib", "typing"}
