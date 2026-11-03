"""The reproduction command retains failed gates and never recursively runs itself."""

import json
import runpy
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "development,heldout", [(False, False), (True, False), (True, True)]
)
def test_pipeline_gate_and_independent_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, development: bool, heldout: bool
) -> None:
    namespace = runpy.run_path(str(ROOT / "scripts/reproduce_postflop_learning.py"))
    main = namespace["main"]
    main.__globals__["__file__"] = str(
        tmp_path / "scripts/reproduce_postflop_learning.py"
    )
    main.__globals__["source_provenance"] = lambda *args, **kwargs: {"test": True}
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        script = Path(command[1]).name
        assert script in {
            "train_postflop.py",
            "validate_postflop_learning.py",
            "report_postflop_learning.py",
        }
        if script == "train_postflop.py":
            phase = command[command.index("--phase") + 1]
            path = Path(command[command.index("--output") + 1])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "exact_acceptance": {
                            "passed": development if phase == "development" else heldout
                        }
                    }
                )
            )
            if phase == "heldout":
                assert development and "--development-independent" in command
        if script == "validate_postflop_learning.py":
            assert "--report" in command and "--output" in command
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert main() == (0 if development and heldout else 1)
    stages = [Path(c[1]).name for c in calls]
    assert stages.count("train_postflop.py") == (6 if development else 4)
    assert stages.count("validate_postflop_learning.py") == (6 if development else 4)
    assert stages.count("report_postflop_learning.py") == int(development)
    reproduction = next(
        (tmp_path / "results/holdem-learning/runs").glob("*/reproduction.json")
    )
    status = json.loads(reproduction.read_text())["status"]
    assert status == (
        "development_gate_failed"
        if not development
        else "passed"
        if heldout
        else "heldout_gate_failed"
    )
