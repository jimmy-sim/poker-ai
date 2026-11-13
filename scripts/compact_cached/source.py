"""Bind the actual private adapter AND every historical scientific dependency."""

from pathlib import Path
from typing import Any

from compact_cached.contract import CONFIG, variant
from poker_ai.evaluation.compact_opponent_source import source as original_source
from poker_ai.postflop.compact_full_artifacts import commit_sources
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

ENTRY = "scripts/validate_cached_compact.py"
PACKAGE = "scripts/compact_cached"
MODULES = (
    "__init__",
    "admission",
    "cache",
    "cli",
    "clock",
    "contract",
    "native",
    "parity",
    "publication",
    "source",
    "workers",
)
HISTORICAL = (
    "scripts/compare_recall_cache.py",
    "scripts/recall_cache_support.py",
    "configs/recall-proof-cache.json",
    "scripts/profile_compact_replay.py",
    "configs/compact-replay-profile.json",
)


def source(root: Path, *, clean: bool = False) -> dict[str, Any]:
    if not Path(__file__).resolve().is_relative_to(root.resolve() / PACKAGE):
        raise ArithmeticError("cached adapter imported outside stated checkout")
    c = variant(root)
    files = tuple(f"{PACKAGE}/{name}.py" for name in MODULES)
    actual = {str(p.relative_to(root)) for p in (root / PACKAGE).rglob("*.py")}
    if actual != set(files) or any((root / name).is_symlink() for name in files):
        raise ArithmeticError("complete explicit adapter module inventory required")
    old = original_source(root)
    if old["fingerprint"] != c["original_scientific_source"]:
        raise ArithmeticError("unchanged original scientific aggregate required")
    historical = dict(old["sha256"])
    historical.update({name: digest(root / name) for name in HISTORICAL})
    if sha(historical) != c["cache_source"]:
        raise ArithmeticError("pinned historical cache source changed")
    saved: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, *files))
    )
    saved["sha256"].update(historical)
    saved["fingerprint"] = sha(saved["sha256"])
    if clean and saved["dirty"] is not False:
        raise ValueError("publish exact clean effective cached source first")
    return saved


def check_source(root: Path, saved: dict[str, Any]) -> None:
    if (
        saved["fingerprint"] != sha(saved["sha256"])
        or source(root)["fingerprint"] != saved["fingerprint"]
    ):
        raise ArithmeticError("effective cached implementation source changed")
    commit_sources(root, saved["git_commit"], saved["sha256"])
