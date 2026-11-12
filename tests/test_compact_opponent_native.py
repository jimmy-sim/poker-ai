"""Native wrapper rejection/schema tests; no unpublished policy is solved."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import compact_opponent_native as worker
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.opponent_learning import validate_rows

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("change", ["source", "own_bytes", "unpublished"])
def test_native_worker_rejects_before_reference_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    path = tmp_path / "own.json"
    path.write_text("UNIT ONLY; no scientific policy")
    source = {"sha256": {"UNIT_ONLY": "a" * 64}}
    binding = sha(source["sha256"])
    monkeypatch.setattr(worker, "source", lambda *a: source)

    def not_published(*args: Any) -> None:
        raise ArithmeticError("UNIT own evidence unpublished")

    monkeypatch.setattr(worker, "published", not_published)
    with pytest.raises(ArithmeticError):
        worker.independent(
            0,
            partition(6, 3)[0],
            dict(
                root=str(tmp_path),
                own=str(path),
                source_sha256="b" * 64 if change == "source" else binding,
                own_sha256="c" * 64 if change == "own_bytes" else digest(path),
            ),
            lambda e: None,
        )


@pytest.mark.parametrize(
    "change",
    ["none", "missing", "bool_target", "native_value", "derived_error", "actions"],
)
def test_complete_already_public_native_schema_and_each_derived_field(
    change: str,
) -> None:
    # Authenticate an ALREADY PUBLIC full tiny dataset. This does not construct
    # a solver or substitute that old proof for the new source-bound rehearsal.
    folder = ROOT / "results/opponent-information/software"
    own = json.loads((folder / "own.json").read_text())
    native = json.loads((folder / "native.json").read_text())
    result = copy.deepcopy(native)
    if change == "none":
        verified = validate_rows(result, own)
        assert verified["profiles"] == 432
        return
    if change == "missing":
        result["profiles"].pop()
    elif change == "bool_target":
        result["fixed_conditions"][0]["target"] = False
    elif change == "native_value":
        result["profiles"][0]["native_metrics"]["value_player_zero_chips"] += 1
    elif change == "derived_error":
        result["profiles"][0]["maximum_error_chips"] += 1
    else:
        result["reference_actions_exported"] = True
    with pytest.raises((ValueError, ArithmeticError, KeyError)):
        validate_rows(result, own)
