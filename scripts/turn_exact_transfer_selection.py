"""Freeze the fixed turn-exact cohort before any tree or policy outcomes."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator
from river_generalization.selection import (
    rank_signature,
    texture_matches,
    tracked_known_spots,
)

from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot

CONFIG = Path("configs/turn-exact-transfer.json")
PROTOCOL_COMMIT = "b7fb1442a7fddb66ff0bcaf881a3aedff1c7ba73"
CONFIG_SHA256 = "311572209b135d8098781e49b5b0d65e3c1f91f4ab6be83b0be3e974804ed6b0"
SELECTION_SOURCES = (
    "scripts/turn_exact_transfer_selection.py",
    "scripts/prepare_turn_exact_transfer.py",
    "scripts/river_generalization/selection.py",
    "src/poker_ai/cards.py",
    "src/poker_ai/postflop/game.py",
    "uv.lock",
)
EXPECTED_STRATA = (
    (
        "turn_exact_new_medium_dry_oop",
        "dry",
        "oop",
        "configs/learning-spots/dev_medium_oop.json",
    ),
    (
        "turn_exact_new_medium_wet_oop",
        "wet",
        "oop",
        "configs/learning-spots/dev_medium_oop.json",
    ),
    (
        "turn_exact_new_low_wet_ip",
        "wet",
        "ip",
        "configs/learning-spots/heldout_low_oop.json",
    ),
)


def digest(path: Path) -> str:
    """Hash exact tracked source/input bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contract(root: Path) -> tuple[dict[str, Any], list[Path]]:
    """Bind the prospective GitHub-published contract and closed known inputs."""
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ArithmeticError("published exact-turn contract bytes changed")
    published = subprocess.check_output(
        ["git", "show", f"{PROTOCOL_COMMIT}:{CONFIG.as_posix()}"], cwd=root
    )
    if raw != published:
        raise ArithmeticError("prospective contract differs from publication")
    config: dict[str, Any] = json.loads(raw)
    if (
        config["schema_version"] != 1
        or config["parent_merge"] != "fe8ffb7021ee4a39f77de22aaf81990a1aeff047"
        or config["selection_seed"] != 20261520
        or config["known_spot_count"] != 21
        or config["maximum_selection_attempts_per_spot"] != 10_000
        or config["maximum_tree_nodes"] != 200_000
        or config["known_spot_directories"]
        != [
            "configs/learning-spots",
            "configs/fresh-spots",
            "configs/spots",
            "configs/river-generalization-spots",
            "configs/river-uniform-readout-spots",
            "configs/river-full-broader-spots",
        ]
        or tuple(
            (row["name"], row["texture"], row["position"], row["template"])
            for row in config["strata"]
        )
        != EXPECTED_STRATA
        or config["spot_directory"] != "configs/turn-exact-transfer-spots"
        or config["freeze_file"] != "configs/turn-exact-transfer-freeze.json"
    ):
        raise ArithmeticError("prospective selection grid changed")
    for name, expected in config["selection_input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned selection input changed: {name}")
    known = tracked_known_spots(root, config["known_spot_directories"])
    if len(known) != 21:
        raise ArithmeticError("closed prior-spot inventory changed")
    known_names = {path.relative_to(root).as_posix() for path in known}
    if {row["template"] for row in config["strata"]} - known_names:
        raise ArithmeticError("public template missing from known inputs")
    old: dict[str, Any] = json.loads(
        (root / "configs/river-full-broader-freeze.json").read_bytes()
    )
    mechanistic = config["known_mechanistic_spot"]
    if mechanistic not in known_names or old["spot_sha256"].get(mechanistic) != digest(
        root / mechanistic
    ):
        raise ArithmeticError("known mechanistic input changed")
    return config, known


def draw_board(
    rng: Generator,
    texture: str,
    forbidden: set[tuple[tuple[int, ...], int]],
    maximum_attempts: int,
) -> tuple[list[int], int, tuple[tuple[int, ...], int]]:
    """Draw once by public structure; never inspect a tree or policy."""
    for attempt in range(1, maximum_attempts + 1):
        board = [int(card) for card in rng.choice(52, 4, replace=False)]
        signature = rank_signature(board)
        if texture_matches(board, texture) and signature not in forbidden:
            forbidden.add(signature)
            return board, attempt, signature
    raise ArithmeticError("declared structural selection attempt cap exceeded")


def select(root: Path) -> dict[str, Any]:
    """Freeze one cohort from a clean published source without replacement."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("select only from a clean published source")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("prospective protocol absent from history")
    config, known = validate_contract(root)
    freeze = root / config["freeze_file"]
    filenames = [
        root / config["spot_directory"] / f"{row['name']}.json"
        for row in config["strata"]
    ]
    if (
        freeze.exists()
        or freeze.is_symlink()
        or any(path.exists() or path.is_symlink() for path in filenames)
    ):
        raise FileExistsError("retain selected cohort; refusing replacement")
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
        board, attempts, signature = draw_board(
            rng,
            row["texture"],
            forbidden,
            config["maximum_selection_attempts_per_spot"],
        )
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
                selection_attempts=attempts,
                template=row["template"],
                position=row["position"],
                board_rank_signature=signature,
            )
        )
    for filename, raw in selected:
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
        load_spot(filename)  # Input syntax only; no game tree, policy or score.
    frozen = dict(
        format="turn-exact-transfer-cohort-v1",
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
