"""Select two fixed card/range inputs by structure alone, then freeze them."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot

CONFIG = Path("configs/river-generalization-fixed-spots.json")
SELECTION_SOURCES = (
    "scripts/river_generalization/selection.py",
    "scripts/river_generalization/__init__.py",
    "scripts/prepare_river_generalization.py",
    "src/poker_ai/cards.py",
    "src/poker_ai/postflop/game.py",
    "uv.lock",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_signature(board: list[int]) -> tuple[tuple[int, ...], int]:
    """Exclude old turn-board ranks even if suits differ."""
    if len(board) != 4 or len(set(board)) != 4:
        raise ValueError("four distinct physical turn-board cards required")
    return tuple(sorted(card // 4 + 2 for card in board[:3])), board[3] // 4 + 2


def texture_matches(board: list[int], texture: str) -> bool:
    """Use the published fresh-cohort structural texture rules exactly."""
    ranks = [card // 4 + 2 for card in board]
    suits = [card % 4 for card in board[:3]]
    if len(ranks) != 4 or len(set(ranks)) != 4:
        return False
    if texture == "wet":
        return len(set(suits)) == 2 and max(ranks[:3]) - min(ranks[:3]) <= 4
    if texture == "dry":
        return len(set(suits)) == 3 and all(
            abs(left - right) >= 3
            for index, left in enumerate(ranks[:3])
            for right in ranks[index + 1 : 3]
        )
    raise ValueError("unknown fixed texture")


def tracked_known_spots(root: Path, directories: list[str]) -> list[Path]:
    """Read only tracked spot inputs, never unrelated local files."""
    paths: list[Path] = []
    for directory in directories:
        raw = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-z", "--", directory]
        )
        paths.extend(
            root / name.decode()
            for name in raw.split(b"\0")
            if name and name.endswith(b".json")
        )
    if not paths or len(paths) != len(set(paths)):
        raise ArithmeticError("tracked known spot inventory missing or duplicated")
    return sorted(paths)


def selection_inputs(root: Path, config: dict[str, Any]) -> list[Path]:
    """Validate the published contract and prior-spot exclusion inventory."""
    for name, expected in config["input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned selection input changed: {name}")
    known = tracked_known_spots(root, config["known_spot_directories"])
    if {stratum["template"] for stratum in config["strata"]} - {
        path.relative_to(root).as_posix() for path in known
    }:
        raise ArithmeticError("known public template missing")
    return known


def select(root: Path) -> dict[str, Any]:
    """Generate once with no scoring, tree construction or case replacement."""
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    )
    if status:
        raise RuntimeError("select only from a clean published source checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    config: dict[str, Any] = json.loads((root / CONFIG).read_bytes())
    if (
        config["schema_version"] != 1
        or config["selection_seed"] != 20261370
        or config["maximum_selection_attempts_per_spot"] != 10_000
        or config["known_spot_directories"]
        != ["configs/learning-spots", "configs/fresh-spots", "configs/spots"]
        or [(row["name"], row["texture"], row["position"]) for row in config["strata"]]
        != [("new_low_wet_ip", "wet", "ip"), ("new_medium_dry_oop", "dry", "oop")]
    ):
        raise ArithmeticError("prospective spot-selection contract changed")
    known = selection_inputs(root, config)
    freeze = root / config["freeze_file"]
    filenames = [
        root / config["spot_directory"] / f"{s['name']}.json" for s in config["strata"]
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
    for stratum, filename in zip(config["strata"], filenames, strict=True):
        for _attempt in range(1, config["maximum_selection_attempts_per_spot"] + 1):
            board = [int(card) for card in rng.choice(52, 4, replace=False)]
            signature = rank_signature(board)
            if (
                texture_matches(board, stratum["texture"])
                and signature not in forbidden
            ):
                forbidden.add(signature)
                break
        else:
            raise ArithmeticError("declared structural selection attempt cap exceeded")
        available = np.array([card for card in range(52) if card not in board])
        holes = [int(card) for card in rng.choice(available, 8, replace=False)]
        weights = [int(weight) for weight in rng.integers(1, 4, size=4)]
        raw: dict[str, Any] = json.loads((root / stratum["template"]).read_bytes())
        raw.update(
            name=stratum["name"],
            board=[format_card(card) for card in board],
            texture=stratum["texture"],
            max_tree_nodes=config["maximum_tree_nodes"],
        )
        desired = raw["button"] if stratum["position"] == "ip" else 1 - raw["button"]
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
                template=stratum["template"],
                position=stratum["position"],
                board_rank_signature=signature,
            )
        )
    # Finish all structural selection before writing either case.
    for filename, raw in selected:
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
        load_spot(filename)  # Legality only; no tree, policy or value.
    frozen: dict[str, Any] = dict(
        format="river-generalization-cohort-v1",
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
