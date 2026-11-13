"""Formal toy parity rejects changed vectors even after archive hashes update."""

import base64
import copy
import gzip
import importlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_design import COST
from poker_ai.postflop.river_study import Deadline, digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "damage",
    [None, "numeric", "metadata_only", "missing", "wrong_scope", "wrong_baseline"],
)
def test_formal_full_vector_parity(
    damage: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    tool = importlib.import_module("compact_cached.parity")
    old_folder = ROOT / tool.OLD_FOLDER
    own: dict[str, Any] = copy.deepcopy(
        json.loads((old_folder / "own.json").read_text())
    )
    # Already-public OWN toy arrays only; this is an isolated guard test, not
    # a new training/source-admission proof or reference strategy.
    for name in tool.EXPECTED:
        shutil.copyfile(
            old_folder / own[name + "_file"], tmp_path / own[name + "_file"]
        )
    if damage in ("numeric", "metadata_only"):
        path = tmp_path / own["captures_file"]
        with gzip.open(path, "rt") as stream:
            lines = [json.loads(line) for line in stream]
        payload = json.loads(gzip.decompress(base64.b64decode(lines[1]["blob"])))
        if damage == "numeric":
            payload["policy"][0][0] += 0.125
        else:
            payload["metadata"]["source_sha256"] = "b" * 64
        lines[1]["blob"] = base64.b64encode(
            gzip.compress(json.dumps(payload).encode())
        ).decode()
        with gzip.open(path, "wt") as stream:
            for line in lines:
                stream.write(json.dumps(line) + "\n")
        own["captures_sha256"] = digest(path)
    elif damage == "missing":
        own["captures"].pop()
    elif damage == "wrong_scope":
        own["scope"] = COST
    elif damage == "wrong_baseline":
        monkeypatch.setattr(tool, "OLD_COMMIT", "UNIT_NOT_A_COMMIT")
    if damage not in (None, "metadata_only"):
        with pytest.raises(ArithmeticError):
            tool.vectors(ROOT, tmp_path, own, Deadline(180))
    else:
        result = tool.vectors(ROOT, tmp_path, own, Deadline(180))
        assert {k: v["count"] for k, v in result["streams"].items()} == dict(
            captures=324, masses=216, warms=30
        )
