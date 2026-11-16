"""Bind the actual private adapter AND every historical scientific dependency."""

import json
from pathlib import Path
from typing import Any

from compact_suit.contract import CONFIG, variant
from poker_ai.postflop.compact_full_artifacts import commit_sources
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

ENTRY = "scripts/validate_suit_compact.py"
PACKAGE = "scripts/compact_suit"
MODULES = (
    "__init__",
    "admission",
    "cache",
    "card_contract",
    "cli",
    "clock",
    "contract",
    "native",
    "normalization",
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
    # Read source metadata only. Importing the diagnostic runner here would pull
    # pure reference validators into an otherwise reference-free training worker.
    proof = json.loads(
        (root / "results/suit-candidates/software/proof.json").read_text()
    )
    anchor = root / "results/suit-candidates/software/child/child.json"
    if digest(anchor) != proof["measurement"]["child_sha256"]:
        raise ArithmeticError("pinned predecessor source anchor changed")
    old = json.loads(anchor.read_text())["source"]
    if (
        old["fingerprint"] != c["predecessor_source"]
        or old["fingerprint"] != sha(old["sha256"])
        or len(old["sha256"]) != c["predecessor_source_files"]
        or any(
            (root / name).is_symlink()
            or not (root / name).resolve().is_relative_to(root.resolve())
            or digest(root / name) != expected
            for name, expected in old["sha256"].items()
        )
    ):
        raise ArithmeticError("unchanged complete predecessor source required")
    commit_sources(root, old["git_commit"], old["sha256"])
    historical = dict(old["sha256"])
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
