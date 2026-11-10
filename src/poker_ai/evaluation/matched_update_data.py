"""Verified immutable inputs shared by the matched-update report and browser."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.matched_update_lifecycle import measured
from poker_ai.evaluation.matched_update_parent_io import activate
from poker_ai.evaluation.matched_update_replay import reused
from poker_ai.evaluation.matched_update_run import read_saved
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.matched_updates import read as read_native

CONFIG = "configs/matched-update-viewer.json"
CONFIG_SHA = "3e0bc4d1a36e4b287223f0e858f61b9b031f0853c7e5fb962d14a55c36e88487"
OWN = "results/matched-update-study/own.json"
READOUTS = ("current", "uniform_average", "linear_average")
SEEDS = (20261301, 20261302, 20261303)


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("matched presentation contract changed")
    saved: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if any(digest(root / p) != h for p, h in saved["source_sha256"].items()):
        raise ArithmeticError("published matched own/native receipt bytes changed")
    return saved


@dataclass(frozen=True)
class Data:
    root: Path
    own: dict[str, Any]
    sources: inputs.Sources
    native: dict[str, Any]
    right: dict[str, dict[str, Any]]
    final_b1: dict[tuple[int, str], dict[str, Any]]
    pots: dict[str, float]


def load(root: Path, progress: Callable[[str], object] = print) -> Data:
    contract(root)
    progress("1/3 Checking saved admission/source; this can take a few minutes.")
    path = root / OWN
    measured(root, path, "study")
    measured(root, path.with_name("native.json"), "real_native")
    with activate(root):
        saved, sources = read_saved(root, path)
        native = read_native(root, path.with_name("native.json"), path, saved)
    progress("2/3 Own/native receipts verified; joining all declared endpoints.")
    right_rows, _ = reused(sources)
    final = final_endpoints(sources)
    games = {r["case"]["spot_file"] for r in saved["rows"]}
    pots = {g: float(json.loads((root / g).read_text())["pot"]) for g in games}
    progress(
        "3/3 Saved data ready. Subsequent browsing uses memory and saved archive bytes."
    )
    return Data(
        root, saved, sources, native, {r["id"]: r for r in right_rows}, final, pots
    )


def final_endpoints(sources: inputs.Sources) -> dict[tuple[int, str], dict[str, Any]]:
    """Rekey explicit row IDs; the older loader uses tuple-valued index keys."""
    final: dict[tuple[int, str], dict[str, Any]] = {}
    scored = {r["id"]: r for r in sources.scored_currents.values()}
    for i in range(24):
        for readout in READOUTS:
            if readout == "current":
                raw = sources.currents[i, 10_000_000]
                row = scored[raw["id"]]
            else:
                row = sources.averages[i, readout.removesuffix("_average"), 10_000_000]
            final[i, readout] = row
    return final
