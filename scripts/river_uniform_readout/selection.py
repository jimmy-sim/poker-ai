"""Freeze the fixed four-spot cohort by structure, before any outcomes."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator
from river_generalization.selection import (
    rank_signature as rank_signature,
)
from river_generalization.selection import (
    texture_matches as texture_matches,
)
from river_generalization.selection import (
    tracked_known_spots as tracked_known_spots,
)

from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot

CONFIG = Path("configs/river-uniform-readout-spots.json")
CONFIG_SHA256 = "ca45d9a8a1b0b24490911c3e54e2707cd0c2c4f92650401e51ba3bcbde414745"
SELECTION_SOURCES = (
    "scripts/river_uniform_readout/__init__.py",
    "scripts/river_uniform_readout/selection.py",
    "scripts/prepare_river_uniform_readout.py",
    "scripts/river_generalization/selection.py",
    "src/poker_ai/cards.py",
    "src/poker_ai/postflop/game.py",
    "uv.lock",
)


def digest(path: Path) -> str:
    """Return the SHA-256 of exact source or input bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selection_inputs(root: Path, config: dict[str, Any]) -> list[Path]:
    """Check the immutable contract and all preexisting tracked spot inputs."""
    if digest(root / CONFIG) != CONFIG_SHA256:
        raise ArithmeticError("prospective uniform-readout contract changed")
    for name, expected in config["input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned selection input changed: {name}")
    known = tracked_known_spots(root, config["known_spot_directories"])
    if {row["template"] for row in config["strata"]} - {
        path.relative_to(root).as_posix() for path in known
    }:
        raise ArithmeticError("known public template missing")
    return known


def select(root: Path) -> dict[str, Any]:
    """Select once from a clean published source without scoring or replacement."""
    if subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    ):
        raise RuntimeError("select only from a clean published source checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    config: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        config["schema_version"] != 1
        or config["selection_seed"] != 20261410
        or config["maximum_selection_attempts_per_spot"] != 10_000
        or [(row["name"], row["texture"], row["position"]) for row in config["strata"]]
        != [
            ("uniform_medium_dry_oop_a", "dry", "oop"),
            ("uniform_medium_dry_oop_b", "dry", "oop"),
            ("uniform_medium_wet_oop", "wet", "oop"),
            ("uniform_low_wet_ip", "wet", "ip"),
        ]
    ):
        raise ArithmeticError("prospective spot-selection grid changed")
    known = selection_inputs(root, config)
    freeze = root / config["freeze_file"]
    filenames = [
        root / config["spot_directory"] / f"{row['name']}.json"
        for row in config["strata"]
    ]
    if freeze.exists() or any(path.exists() or path.is_symlink() for path in filenames):
        raise FileExistsError("retain fixed selected cohort, refusing replacement")
    forbidden = {
        rank_signature(
            [parse_card(card) for card in json.loads(path.read_bytes())["board"]]
        )
        for path in known
    }
    rng = Generator(PCG64(config["selection_seed"]))
    selected: list[tuple[Path, dict[str, Any]]] = []
    records: list[dict[str, Any]] = []
    for row, filename in zip(config["strata"], filenames, strict=True):
        for _attempt in range(1, config["maximum_selection_attempts_per_spot"] + 1):
            board = [int(card) for card in rng.choice(52, 4, replace=False)]
            signature = rank_signature(board)
            if texture_matches(board, row["texture"]) and signature not in forbidden:
                forbidden.add(signature)
                break
        else:
            raise ArithmeticError("declared structural selection attempt cap exceeded")
        available = np.array([card for card in range(52) if card not in board])
        holes = [int(card) for card in rng.choice(available, 8, replace=False)]
        weights = [int(weight) for weight in rng.integers(1, 4, size=4)]
        raw: dict[str, Any] = json.loads((root / row["template"]).read_bytes())
        raw.update(
            name=row["name"],
            board=[format_card(card) for card in board],
            texture=row["texture"],
            max_tree_nodes=config["maximum_tree_nodes"],
        )
        desired = raw["button"] if row["position"] == "ip" else 1 - raw["button"]
        if raw["actor"] != desired:
            raw["prefix_actions"].append({"kind": "check"})
        raw.update(actor=desired, hero=desired)
        raw["ranges"] = [
            [
                {
                    "cards": [
                        format_card(card)
                        for card in holes[
                            4 * seat + 2 * index : 4 * seat + 2 * index + 2
                        ]
                    ],
                    "weight": weights[2 * seat + index],
                }
                for index in range(2)
            ]
            for seat in range(2)
        ]
        selected.append((filename, raw))
        records.append(
            dict(
                spot_file=filename.relative_to(root).as_posix(),
                selection_attempts=_attempt,
                template=row["template"],
                position=row["position"],
                board_rank_signature=signature,
            )
        )
    for filename, raw in selected:
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
        load_spot(filename)  # Legal input only; no tree, policy or value.
    frozen: dict[str, Any] = dict(
        format="river-uniform-readout-cohort-v1",
        config_sha256=digest(root / CONFIG),
        selection_source_commit=head,
        selection_source_sha256={
            name: digest(root / name) for name in SELECTION_SOURCES
        },
        known_spot_sha256={
            path.relative_to(root).as_posix(): digest(path) for path in known
        },
        spot_sha256={
            path.relative_to(root).as_posix(): digest(path) for path in filenames
        },
        selection=records,
    )
    freeze.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    return frozen
