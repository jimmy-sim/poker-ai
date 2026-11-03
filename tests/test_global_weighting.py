"""Global weighting checkpoints resume exactly and remain usable by own inference."""

import hashlib
import json
import runpy
import shutil
from pathlib import Path
from typing import Any

import pytest

from poker_ai.agents.no_limit import ENCODER_FILES, OwnNoLimitAgent

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("weighting", ["uniform", "linear"])
def test_global_worker_resume_and_inference(tmp_path: Path, weighting: str) -> None:
    namespace = runpy.run_path(str(ROOT / "scripts/train_holdem.py"))
    config = json.loads(
        (ROOT / f"configs/global-strength-{weighting}.json").read_text()
    )
    config.update({"checkpoints": [1, 3], "seeds": [41]})
    source = {
        "sha256": {
            f"src/poker_ai/{name}": hashlib.sha256(
                (ROOT / "src/poker_ai" / name).read_bytes()
            ).hexdigest()
            for name in ENCODER_FILES
        }
    }
    task: dict[str, Any] = {
        "config": config,
        "root": str(ROOT),
        "model": config["models"][0],
        "method": "external",
        "seed": 41,
        "source": source,
        "implementation_sha256": "unit-test",
        "checkpoint_dir": str(tmp_path / "direct"),
        "resume_dir": None,
    }
    direct = namespace["worker"](task)
    assert direct["error"] is None and len(direct["rows"]) == 2
    first = Path(direct["rows"][0]["checkpoint"])
    resume = tmp_path / "resume"
    resume.mkdir()
    shutil.copy2(first, resume / first.name)
    if weighting == "linear":
        shutil.copy2(
            first.with_suffix(".visits.json"),
            resume / first.with_suffix(".visits.json").name,
        )
    resumed = namespace["worker"](
        {
            **task,
            "resume_dir": str(resume),
            "checkpoint_dir": str(tmp_path / "continued"),
        }
    )
    assert resumed["error"] is None and resumed["rows"][0]["starting_iteration"] == 1
    a = Path(direct["rows"][-1]["checkpoint"])
    b = Path(resumed["rows"][-1]["checkpoint"])
    assert a.read_bytes() == b.read_bytes()
    agent = OwnNoLimitAgent.load(a, ROOT / config["models"][0])
    assert len(agent.rows) > 0
