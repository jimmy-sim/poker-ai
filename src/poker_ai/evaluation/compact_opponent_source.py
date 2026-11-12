"""New exact-source binding, separate from all unchanged historical guards."""

from pathlib import Path
from typing import Any

from poker_ai.evaluation.compact_opponent_contract import CONFIG, COST_CONFIG, contract
from poker_ai.postflop.compact_full_artifacts import commit_sources
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

ENTRY = "scripts/validate_compact_opponents.py"


def source(root: Path, *, clean: bool = False) -> dict[str, Any]:
    if not Path(__file__).resolve().is_relative_to(root.resolve() / "src"):
        raise ArithmeticError("compact pipeline imported outside stated checkout")
    saved: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    saved["sha256"][COST_CONFIG] = digest(root / COST_CONFIG)
    saved["fingerprint"] = sha(saved["sha256"])
    if clean and saved["dirty"] is not False:
        raise ValueError("publish exact clean compact pipeline source first")
    contract(root)
    return saved


def check_source(root: Path, saved: dict[str, Any]) -> None:
    if (
        saved["fingerprint"] != sha(saved["sha256"])
        or source(root, clean=False)["fingerprint"] != saved["fingerprint"]
    ):
        raise ArithmeticError("compact pipeline source changed")
    commit_sources(root, saved["git_commit"], saved["sha256"])
