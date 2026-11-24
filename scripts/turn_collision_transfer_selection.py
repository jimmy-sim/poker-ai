"""One-time, score-free structural selection for collision-conditioned transfer."""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator
from river_generalization.selection import (
    rank_signature,
    texture_matches,
    tracked_known_spots,
)
from river_strength.representation import build_river_candidate
from turn_exact_transfer.representation import exact_turn_candidate

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment

CONFIG = Path("configs/turn-collision-transfer.json")
PROTOCOL_COMMIT = "b5fc4c7ff001526435a5c41e4e010b31126e492b"
CONFIG_SHA256 = "96e131328164f0e8ca9c4e25613aeb058df6d559f6bd3c1f11ab392a02856165"
PARENT_SOURCE = "6e09c02673ca596e6082ea8d0a57ba12cd2533acfaf2c777991c4d29f395e0f4"
SELECTION_SOURCES = (
    "scripts/turn_collision_transfer_selection.py",
    "scripts/prepare_turn_collision_transfer.py",
    "scripts/river_generalization/selection.py",
    "scripts/turn_exact_transfer/representation.py",
    "scripts/river_strength/representation.py",
    "tests/test_turn_collision_transfer_selection.py",
    "src/poker_ai/postflop/tree.py",
    "src/poker_ai/postflop/game.py",
    "uv.lock",
)


def digest(path: Path) -> str:
    """Hash one pinned input or retained raw candidate."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, row: dict[str, Any]) -> None:
    """Write one new record without replacing partial or failed evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(row, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def event(path: Path, row: dict[str, Any]) -> None:
    """Flush each draw or inventory before attempting the next candidate."""
    with path.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def contract(root: Path) -> tuple[dict[str, Any], list[Path]]:
    """Bind the immutable published plan and all 24 prior case bytes."""
    if digest(root / CONFIG) != CONFIG_SHA256:
        raise ArithmeticError("prospective transfer contract changed")
    published = subprocess.check_output(
        ["git", "show", f"{PROTOCOL_COMMIT}:{CONFIG.as_posix()}"], cwd=root
    )
    if (root / CONFIG).read_bytes() != published:
        raise ArithmeticError("prospective transfer contract differs from publication")
    config: dict[str, Any] = json.loads(published)
    if (
        config["schema_version"] != 1
        or config["parent_merge"] != "71ab64fa5e9a76eb7c94cc42942024fc8db622b1"
        or config["selection_seed"] != 20261624
        or config["selection"]["max_candidates_per_stratum"] != 20
        or config["selection"]["max_board_draws_per_candidate"] != 10000
        or config["selection"]["minimum_collided_turn_exact_rows"] != 4
        or config["selection"]["max_tree_nodes"] != 200000
        or config["selection"]["private_combos_per_seat"] != 5
        or config["selection"]["max_seconds"] != 900
        or config["known_directories"]
        != [
            "configs/learning-spots",
            "configs/fresh-spots",
            "configs/spots",
            "configs/river-generalization-spots",
            "configs/river-uniform-readout-spots",
            "configs/river-full-broader-spots",
            "configs/turn-exact-transfer-spots",
        ]
        or [(row["name"], row["texture"], row["position"]) for row in config["strata"]]
        != [
            ("collision_medium_dry_oop", "dry", "oop"),
            ("collision_medium_wet_oop", "wet", "oop"),
            ("collision_low_wet_ip", "wet", "ip"),
        ]
    ):
        raise ArithmeticError("prospective transfer selection rule changed")
    for name, expected in config["prerequisite_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError("pinned transfer prerequisite changed: " + name)
    known = tracked_known_spots(root, config["known_directories"])
    actual = {path.relative_to(root).as_posix(): digest(path) for path in known}
    if actual != config["known_spot_sha256"] or len(known) != 24:
        raise ArithmeticError("24 prior inspected spot bytes or inventory changed")
    if {row["template"] for row in config["strata"]} - set(actual):
        raise ArithmeticError("registered public template absent from prior inventory")
    from known_turn_mechanism.gate import source_fingerprint

    if source_fingerprint(root) != PARENT_SOURCE:
        raise ArithmeticError("qualified known-turn source changed")
    return config, known


def clean_source(root: Path) -> str:
    """Require a clean published selector descendant before one-time use."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("selection requires clean published source")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("prospective protocol absent from selector history")
    if any(not (root / name).is_file() for name in SELECTION_SOURCES):
        raise FileNotFoundError("closed selector source missing")
    return head


def draw_board(
    rng: Generator,
    texture: str,
    forbidden: set[tuple[tuple[int, ...], int]],
    maximum: int,
    deadline: Deadline,
) -> tuple[list[int], tuple[tuple[int, ...], int], int]:
    """Draw first novel board with the registered texture, recording draws."""
    for attempt in range(1, maximum + 1):
        deadline.check()
        board = [int(card) for card in rng.choice(52, 4, replace=False)]
        if not texture_matches(board, texture):
            continue
        signature = rank_signature(board)
        if signature not in forbidden:
            forbidden.add(signature)
            return board, signature, attempt
    raise ArithmeticError("fixed 10000-board draw cap exhausted")


def candidate(
    root: Path, row: dict[str, Any], board: list[int], rng: Generator, maximum: int
) -> dict[str, Any]:
    """Copy only the public template and draw five private combos per seat."""
    available = np.array([card for card in range(52) if card not in board])
    holes = [int(card) for card in rng.choice(available, 20, replace=False)]
    weights = [int(weight) for weight in rng.integers(1, 4, size=10)]
    raw: dict[str, Any] = json.loads((root / row["template"]).read_bytes())
    raw.update(
        name=row["name"],
        board=[format_card(card) for card in board],
        texture=row["texture"],
        max_tree_nodes=maximum,
    )
    desired = raw["button"] if row["position"] == "ip" else 1 - raw["button"]
    if raw["actor"] != desired:
        raw["prefix_actions"].append({"kind": "check"})
    raw.update(actor=desired, hero=desired)
    raw["ranges"] = [
        [
            dict(
                cards=[
                    format_card(holes[10 * seat + 2 * index + offset])
                    for offset in (0, 1)
                ],
                weight=weights[5 * seat + index],
            )
            for index in range(5)
        ]
        for seat in range(2)
    ]
    return raw


def collision_counts(exact: MatrixTree, control: MatrixTree) -> dict[str, int]:
    """Count only acting-turn key collisions; reject any river mismatch."""
    if exact.source is not control.source or len(exact.keys) != len(
        control.exact_to_abstract
    ):
        raise ArithmeticError("exact and q8 trees do not share source rows")
    mapping = control.exact_to_abstract
    turn = np.zeros(len(exact.keys), dtype=np.bool_)
    river = np.zeros(len(exact.keys), dtype=np.bool_)
    for index, node in enumerate(exact.source.representatives):
        state = exact.source.states[node]
        if state.dealer is None:
            raise ArithmeticError("decision representative lacks observation")
        street = len(state.dealer.board)
        if street == 4:
            turn[index] = True
        elif street == 5:
            river[index] = True
        else:
            raise ArithmeticError("outside registered turn-start game")
    summary = collision_summary(mapping, turn, river, len(control.keys))
    return dict(
        tree_nodes=len(exact.player),
        exact_information_rows=len(exact.keys),
        q8_information_rows=len(control.keys),
        turn_exact_rows=int(np.count_nonzero(turn)),
        river_exact_rows=int(np.count_nonzero(river)),
        **summary,
    )


def collision_summary(
    mapping: np.ndarray[Any, Any],
    turn: np.ndarray[Any, Any],
    river: np.ndarray[Any, Any],
    abstract_count: int,
) -> dict[str, int]:
    """Count exact rows in shared q8 groups, never mixing with river rows."""
    if (
        mapping.ndim != 1
        or turn.shape != mapping.shape
        or river.shape != mapping.shape
        or abstract_count < 1
        or np.any(mapping < 0)
        or np.any(mapping >= abstract_count)
        or np.any(turn & river)
        or np.any(~(turn | river))
    ):
        raise ValueError("invalid exact-row street or q8 mapping")
    sizes = np.bincount(mapping, minlength=abstract_count)[mapping]
    if np.any(river & (sizes > 1)):
        raise ArithmeticError("unchanged exact river key collided")
    collided = turn & (sizes > 1)
    return dict(
        turn_collided_exact_rows=int(np.count_nonzero(collided)),
        turn_collided_abstract_groups=len(
            {int(mapping[i]) for i in np.flatnonzero(collided)}
        ),
        river_collided_exact_rows=0,
    )


def screen(root: Path, output: Path) -> dict[str, Any]:
    """Run the single bounded structural screen; never evaluate a policy."""
    config, known = contract(root)
    head = clean_source(root)
    if (root / config["freeze_file"]).exists() or (
        root / config["spot_directory"]
    ).exists():
        raise FileExistsError("retain prior frozen selection; no redraw")
    deadline = Deadline(900)
    started_clock = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    started = dict(
        status="started",
        head=head,
        config_sha256=CONFIG_SHA256,
        runtime=runtime_environment(),
        no_policy_or_score_read=True,
    )
    save(output / "started.json", started)
    events = output / "events.jsonl"
    forbidden = {
        rank_signature(
            [parse_card(card) for card in json.loads(path.read_bytes())["board"]]
        )
        for path in known
    }
    rng = Generator(PCG64(config["selection_seed"]))
    chosen: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    try:
        model = CardAbstraction.load(root / "results/card-models/potential-8.json")
        for stratum in config["strata"]:
            selected = None
            for index in range(1, 21):
                deadline.check()
                board, signature, draws = draw_board(
                    rng, stratum["texture"], forbidden, 10000, deadline
                )
                raw = candidate(root, stratum, board, rng, 200000)
                path = output / "attempts" / f"{stratum['name']}-{index:02d}.json"
                save(path, raw)
                receipt: dict[str, Any] = dict(
                    stratum=stratum["name"],
                    attempt=index,
                    board_draws=draws,
                    board_signature=signature,
                    file=path.relative_to(output).as_posix(),
                    sha256=digest(path),
                )
                event(events, dict(kind="drawn", **receipt))
                spot = load_spot(path)
                source = SpotTree.build(spot)
                control = build_river_candidate(source, model)
                exact = exact_turn_candidate(source, control)
                counts = collision_counts(exact, control)
                if counts["tree_nodes"] > 200000:
                    raise ArithmeticError("fixed 200000-node tree cap exceeded")
                receipt.update(counts)
                attempts.append(receipt)
                event(events, dict(kind="screened", **receipt))
                deadline.check()
                if counts["turn_collided_exact_rows"] >= 4:
                    selected = receipt
                    chosen.append(receipt)
                    break
            if selected is None:
                result = dict(
                    status="structural_stop",
                    head=head,
                    config_sha256=CONFIG_SHA256,
                    attempts=attempts,
                    selected=chosen,
                    exhausted_stratum=stratum["name"],
                    seconds=time.perf_counter() - started_clock,
                    no_policy_or_score_read=True,
                )
                save(output / "result.json", result)
                return result
        result = dict(
            status="selected",
            head=head,
            config_sha256=CONFIG_SHA256,
            attempts=attempts,
            selected=chosen,
            seconds=time.perf_counter() - started_clock,
            no_policy_or_score_read=True,
        )
        save(output / "result.json", result)
        return result
    except BaseException as error:
        save(
            output / "failure.json",
            dict(
                status="failed_retained",
                head=head,
                config_sha256=CONFIG_SHA256,
                completed_attempts=len(attempts),
                selected=chosen,
                seconds=time.perf_counter() - started_clock,
                failure=dict(type=type(error).__name__, reason=str(error)),
            ),
        )
        raise


def validate_complete_screen(
    result: dict[str, Any], strata: list[dict[str, Any]], output: Path
) -> None:
    """Prove all attempt bytes and the first eligible choice in each stratum."""
    attempts = result["attempts"]
    selected = result["selected"]
    if (
        result["status"] != "selected"
        or result["config_sha256"] != CONFIG_SHA256
        or result["no_policy_or_score_read"] is not True
        or len(selected) != len(strata)
        or len(attempts) > 20 * len(strata)
        or not 0 < result["seconds"] < 900
    ):
        raise ArithmeticError("incomplete or altered structural screen")
    consumed = 0
    for row, chosen in zip(strata, selected, strict=True):
        group = [item for item in attempts if item["stratum"] == row["name"]]
        if (
            not 1 <= len(group) <= 20
            or chosen != group[-1]
            or [item["attempt"] for item in group] != list(range(1, len(group) + 1))
            or any(item["turn_collided_exact_rows"] >= 4 for item in group[:-1])
            or chosen["turn_collided_exact_rows"] < 4
        ):
            raise ArithmeticError("first eligible structural candidate changed")
        for item in group:
            path = output / item["file"]
            if (
                path.is_symlink()
                or not path.is_file()
                or digest(path) != item["sha256"]
                or item["river_collided_exact_rows"] != 0
                or item["tree_nodes"] > 200000
            ):
                raise ArithmeticError("retained structural attempt changed")
        if attempts[consumed : consumed + len(group)] != group:
            raise ArithmeticError("structural stratum order changed")
        consumed += len(group)
    if consumed != len(attempts):
        raise ArithmeticError("extra structural attempts after selection")


def freeze(root: Path, output: Path) -> dict[str, Any]:
    """Copy only the one complete published-source screen to tracked inputs."""
    config, known = contract(root)
    head = clean_source(root)
    result: dict[str, Any] = json.loads((output / "result.json").read_bytes())
    if result["head"] != head:
        raise ArithmeticError("complete same-source screen required")
    validate_complete_screen(result, config["strata"], output)
    filenames = [
        root / config["spot_directory"] / f"{row['name']}.json"
        for row in config["strata"]
    ]
    target = root / config["freeze_file"]
    if (
        target.exists()
        or target.is_symlink()
        or any(p.exists() or p.is_symlink() for p in filenames)
    ):
        raise FileExistsError("retain frozen cohort; no replacement")
    for selected, stratum in zip(result["selected"], config["strata"], strict=True):
        if (
            selected["stratum"] != stratum["name"]
            or selected["turn_collided_exact_rows"] < 4
        ):
            raise ArithmeticError("selected stratum or opportunity changed")
        path = output / selected["file"]
        if digest(path) != selected["sha256"]:
            raise ArithmeticError("retained candidate bytes changed")
    for selected, filename in zip(result["selected"], filenames, strict=True):
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_bytes((output / selected["file"]).read_bytes())
    frozen = dict(
        format="turn-collision-transfer-cohort-v1",
        config_sha256=CONFIG_SHA256,
        selection_source_commit=head,
        selection_source_sha256={
            name: digest(root / name) for name in SELECTION_SOURCES
        },
        known_spot_sha256={p.relative_to(root).as_posix(): digest(p) for p in known},
        screen_result_sha256=digest(output / "result.json"),
        spot_sha256={p.relative_to(root).as_posix(): digest(p) for p in filenames},
        selected=result["selected"],
        total_screened=len(result["attempts"]),
    )
    save(target, frozen)
    return frozen
