"""Single score-free collision-conditioned screen and immutable cohort freeze."""

import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator
from river_strength.representation import build_river_candidate
from turn_collision_transfer_selection import candidate, collision_counts, draw_board
from turn_exact_transfer.representation import exact_turn_candidate

from known_turn_collision_medium_transfer.gate import (
    FREEZE,
    SCREEN,
    SOURCE,
    clean_revision,
    require_archive,
    source_fingerprint,
)
from known_turn_collision_medium_transfer.plan import (
    GAMES,
    MAX_RSS,
    SPOTS,
    contract,
    digest,
    forbidden_signatures,
)
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import format_card
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import recall_violations
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment


def save(path: Path, row: dict[str, Any]) -> None:
    """Atomically write a new durable JSON record without replacing evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain earlier conditional transfer evidence")
    with temporary.open("x") as stream:
        stream.write(json.dumps(row, sort_keys=True, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def event(path: Path, row: dict[str, Any]) -> None:
    """Flush each drawn and screened candidate before the next one."""
    with path.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def peak_rss_bytes() -> int:
    """Use the platform's documented ru_maxrss units."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if sys.platform == "darwin" else 1024
    )


def screen(root: Path, output: Path) -> dict[str, Any]:
    """Draw first eligible medium spots once, reading no strategy or score."""
    data = contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    if (root / FREEZE).exists() or (root / SPOTS).exists():
        raise FileExistsError("retain previous conditional transfer cohort")
    select = data["selection"]
    deadline = Deadline(
        select["whole_cap_seconds"] - select["failure_save_reserve_within_cap_seconds"]
    )
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "started.json",
        dict(
            status="started",
            head=head,
            source_fingerprint=fingerprint,
            runtime=runtime_environment(),
            no_policy_or_score_read=True,
        ),
    )
    events = output / "events.jsonl"
    forbidden = forbidden_signatures(root, data)
    rng = Generator(PCG64(select["seed"]))
    attempts: list[dict[str, Any]] = []
    chosen: list[dict[str, Any]] = []
    try:
        model = CardAbstraction.load(root / "results/card-models/potential-8.json")
        for stratum in select["strata"]:
            selected = False
            for index in range(1, select["max_candidates_per_stratum"] + 1):
                deadline.check()
                attempt_started = time.perf_counter()
                board, signature, draws = draw_board(
                    rng,
                    stratum["texture"],
                    forbidden,
                    select["max_board_draws_per_candidate"],
                    deadline,
                )
                event(
                    events,
                    dict(
                        kind="board_drawn",
                        stratum=stratum["name"],
                        attempt=index,
                        board=[format_card(card) for card in board],
                        board_signature=signature,
                        board_draws=draws,
                        elapsed_seconds=time.perf_counter() - attempt_started,
                    ),
                )
                raw = candidate(root, stratum, board, rng, select["max_tree_nodes"])
                path = output / "attempts" / f"{stratum['name']}-{index:02d}.json"
                save(path, raw)
                row: dict[str, Any] = dict(
                    stratum=stratum["name"],
                    attempt=index,
                    board_draws=draws,
                    elapsed_seconds=time.perf_counter() - attempt_started,
                    board_signature=signature,
                    file=path.relative_to(output).as_posix(),
                    sha256=digest(path),
                )
                event(events, dict(kind="drawn", **row))
                source = SpotTree.build(load_spot(path))
                control = build_river_candidate(source, model)
                exact = exact_turn_candidate(source, control)
                counts = collision_counts(exact, control)
                if (
                    recall_violations(control)
                    or recall_violations(exact)
                    or counts["turn_exact_rows"]
                    < select["minimum_collided_exact_turn_rows"]
                    or counts["river_exact_rows"] == 0
                    or counts["tree_nodes"] > select["max_tree_nodes"]
                    or counts["river_collided_exact_rows"] != 0
                    or peak_rss_bytes() > MAX_RSS
                ):
                    raise ArithmeticError("selection tree, river or memory cap failed")
                row.update(counts)
                row["elapsed_seconds"] = time.perf_counter() - attempt_started
                row["outcome"] = (
                    "selected"
                    if counts["turn_collided_exact_rows"]
                    >= select["minimum_collided_exact_turn_rows"]
                    else "ineligible"
                )
                attempts.append(row)
                event(events, dict(kind="screened", **row))
                deadline.check()
                if (
                    counts["turn_collided_exact_rows"]
                    >= select["minimum_collided_exact_turn_rows"]
                ):
                    chosen.append(row)
                    selected = True
                    break
            if not selected:
                result = dict(
                    status="structural_stop",
                    head=head,
                    source_fingerprint=fingerprint,
                    no_policy_or_score_read=True,
                    exhausted_stratum=stratum["name"],
                    attempts=attempts,
                    selected=chosen,
                    seconds=time.perf_counter() - started,
                    peak_rss_bytes=peak_rss_bytes(),
                )
                save(output / "result.json", result)
                return result
        deadline.check()
        result = dict(
            status="selected",
            head=head,
            source_fingerprint=fingerprint,
            no_policy_or_score_read=True,
            attempts=attempts,
            selected=chosen,
            seconds=time.perf_counter() - started,
            peak_rss_bytes=peak_rss_bytes(),
        )
        save(output / "result.json", result)
        return result
    except BaseException as error:
        save(
            output / "failure.json",
            dict(
                status="failed_retained",
                head=head,
                source_fingerprint=fingerprint,
                attempts=attempts,
                selected=chosen,
                seconds=time.perf_counter() - started,
                peak_rss_bytes=peak_rss_bytes(),
                failure=dict(type=type(error).__name__, reason=str(error)),
            ),
        )
        raise


def validate_screen(root: Path, result: dict[str, Any]) -> None:
    """Prove complete first eligibility and retained raw board/row bindings."""
    data = contract(root)
    select = data["selection"]
    attempts: list[dict[str, Any]] = result["attempts"]
    chosen: list[dict[str, Any]] = result["selected"]
    if (
        result["status"] != "selected"
        or result["no_policy_or_score_read"] is not True
        or len(chosen) != len(GAMES)
        or not 0 < result["seconds"] < select["whole_cap_seconds"]
        or not 0 < result["peak_rss_bytes"] <= MAX_RSS
    ):
        raise ArithmeticError("incomplete conditional structural screen")
    forbidden = forbidden_signatures(root, data)
    consumed = 0
    for stratum, winner in zip(select["strata"], chosen, strict=True):
        group = [row for row in attempts if row["stratum"] == stratum["name"]]
        if (
            not 1 <= len(group) <= select["max_candidates_per_stratum"]
            or attempts[consumed : consumed + len(group)] != group
            or [row["attempt"] for row in group] != list(range(1, len(group) + 1))
            or winner != group[-1]
            or winner["outcome"] != "selected"
            or any(row["outcome"] != "ineligible" for row in group[:-1])
            or any(
                row["turn_collided_exact_rows"]
                >= select["minimum_collided_exact_turn_rows"]
                for row in group[:-1]
            )
            or winner["turn_collided_exact_rows"]
            < select["minimum_collided_exact_turn_rows"]
        ):
            raise ArithmeticError("conditional first-eligible choice changed")
        for row in group:
            path = root / SCREEN / row["file"]
            if (
                path.is_symlink()
                or not path.is_file()
                or digest(path) != row["sha256"]
                or row["river_collided_exact_rows"] != 0
                or row["tree_nodes"] > select["max_tree_nodes"]
            ):
                raise ArithmeticError("retained screened input changed")
            raw = json.loads(path.read_bytes())
            from river_generalization.selection import rank_signature, texture_matches

            from poker_ai.cards import parse_card

            board = [parse_card(card) for card in raw["board"]]
            signature = rank_signature(board)
            if (
                signature in forbidden
                or tuple(row["board_signature"][0]) != signature[0]
                or row["board_signature"][1] != signature[1]
                or not texture_matches(board, stratum["texture"])
                or raw["name"] != stratum["name"]
            ):
                raise ArithmeticError("screened board exclusion/texture changed")
            forbidden.add(signature)
        consumed += len(group)
    if consumed != len(attempts):
        raise ArithmeticError("extra conditional screen attempts")


def freeze(root: Path) -> dict[str, Any]:
    """Copy the published first-eligible cohort into tracked immutable spots."""
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / SCREEN, "screen_selected", fingerprint)
    result: dict[str, Any] = json.loads((root / SCREEN / "result.json").read_bytes())
    validate_screen(root, result)
    if (
        (root / FREEZE).exists()
        or (root / FREEZE).is_symlink()
        or (root / SPOTS).exists()
    ):
        raise FileExistsError("retain earlier conditional cohort")
    spots = {}
    for game, row in zip(GAMES, result["selected"], strict=True):
        if row["stratum"] != game:
            raise ArithmeticError("selected stratum order changed")
        source = root / SCREEN / row["file"]
        target = root / SPOTS / f"{game}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        spots[target.relative_to(root).as_posix()] = digest(target)
    frozen = dict(
        status="frozen",
        head=head,
        source_fingerprint=fingerprint,
        screen_result_sha256=digest(root / SCREEN / "result.json"),
        selected=result["selected"],
        spot_sha256=spots,
    )
    save(root / FREEZE, frozen)
    return frozen
