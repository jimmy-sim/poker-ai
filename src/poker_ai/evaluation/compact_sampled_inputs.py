"""Fixed sampled design and source binding; no reference or learner construction."""

import json
from pathlib import Path
from typing import Any, cast

from poker_ai.postflop.compact_full_artifacts import commit_sources
from poker_ai.postflop.compact_full_context import Context, contexts
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.public_range_definition import check_inputs, contract
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/compact-sampled.json"
CONFIG_SHA = "ccd5c244224b9fe3852f4d1f912194207f6f3ef5e1de33093695957376ed43e4"
SPEC_SHA = "fece67d499601ab95a0fb4d432ff91631410376da8368599c2b237b73b43d8a0"
FOLDER = "results/compact-sampled"
ENTRY = "scripts/validate_compact_sampled.py"
IDENTITY = ("spot_file", "representation", "seed", "work_checkpoint", "readout")
POINT = IDENTITY[:-1]
PATH = IDENTITY[:3]
READOUTS = ("current", "uniform", "linear")
SCOPES = ("software", "real", "cost")


def protocol(root: Path) -> dict[str, Any]:
    path = root / CONFIG
    saved: dict[str, Any] = json.loads(path.read_text())
    if digest(path) != CONFIG_SHA or sha(saved) != SPEC_SHA:
        raise ArithmeticError("published sampled protocol changed")
    base = contract(root)
    check_inputs(root, base)
    for name, checksum in saved["input_sha256"].items():
        if digest(root / name) != checksum:
            raise ArithmeticError("sampled prior/config/timing input changed")
    return saved


def source(root: Path, *, clean: bool = True) -> dict[str, Any]:
    if not Path(__file__).resolve().is_relative_to((root / "src").resolve()):
        raise ArithmeticError("sampled imports are outside the stated checkout")
    saved = source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    if clean and saved["dirty"] is not False:
        raise ValueError("publish sampled source first; clean checkout required")
    saved["fingerprint"] = sha(saved["sha256"])
    return saved


def check_source(root: Path, saved: dict[str, Any]) -> None:
    if (
        sha(saved["sha256"]) != saved["fingerprint"]
        or source(root, clean=False)["fingerprint"] != saved["fingerprint"]
    ):
        raise ArithmeticError("sampled source fingerprint changed")
    commit_sources(root, saved["git_commit"], saved["sha256"])
    protocol(root)


def labels(root: Path, scope: str) -> list[int]:
    if scope not in SCOPES:
        raise ValueError("unknown sampled scope")
    return cast(
        list[int],
        protocol(root)["software_work_labels"]
        if scope == "software"
        else contract(root)["sampled"]["node_work_checkpoints"],
    )


def cases(root: Path, scope: str) -> list[dict[str, Any]]:
    protocol(root)
    if scope not in SCOPES:
        raise ValueError("unknown sampled scope")
    base = contract(root)
    spots = (
        ["software-kuhn-1", "software-kuhn--1"]
        if scope == "software"
        else base["spot_files"]
    )
    return [
        dict(spot_file=s, representation=r, seed=seed)
        for s in spots
        for r in base["representations"]
        for seed in base["sampled"]["seeds"]
    ]


def game_contexts(root: Path, scope: str) -> dict[tuple[str, str], Context]:
    if scope not in SCOPES:
        raise ValueError("unknown sampled scope")
    return {
        (c.spot_file, c.representation): c
        for c in contexts(root, software=scope == "software")
    }


def expected(root: Path, scope: str, *, readouts: bool) -> set[tuple[Any, ...]]:
    return {
        tuple(c[k] for k in PATH) + (w,) + ((b,) if readouts else ())
        for c in cases(root, scope)
        for w in labels(root, scope)
        for b in (READOUTS if readouts else (None,))
    }


def identity(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[Any, ...]:
    for key in fields:
        value = row[key]
        if key in ("seed", "work_checkpoint"):
            if type(value) is not int or value <= 0:
                raise ValueError("strict positive integer sampled identity required")
        elif type(value) is not str or not value:
            raise ValueError("nonempty string sampled identity required")
    return tuple(row[k] for k in fields)
