"""One bounded read-only trace of four published mixed policies."""

import gc
import json
import math
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from known_turn_half_policy_mixture.plan import (
    ARMS,
    GAMES,
    parent_context,
    parent_policy,
)
from known_turn_half_policy_mixture.plan import (
    contract as prior_contract,
)
from medium_dry_b8.report import row_identity

from known_mixture_residual_map.gate import (
    clean_head,
    require_admission,
    source_fingerprint,
)
from known_mixture_residual_map.math import summarize
from known_mixture_residual_map.plan import contract
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, record: dict[str, Any]) -> None:
    """Write an immutable result/failure and fsync before another game."""
    with path.open("x") as stream:
        json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def rss_bytes() -> int:
    """Return process high-water RSS in bytes on macOS and Linux."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if sys.platform == "darwin" else 1024
    )


def fixed_parent_rows(prior: dict[str, Any], game: str) -> set[int]:
    """Use only PR #116's already published control-ranked street rows."""
    selected = {
        int(row["exact_info"])
        for row in prior["diagnostics"]
        if row["game"] == game and row["control_final_rank_within_street"] is not None
    }
    if len(selected) != 6:
        raise ArithmeticError("published control-ranked row set changed")
    return selected


def trace_one(
    root: Path,
    index: int,
    data: dict[str, Any],
    prior: dict[str, Any],
    own: dict[str, Any],
) -> dict[str, Any]:
    """Trace a single exact mixed policy; parent data are read only."""
    game = GAMES[index]
    published = own["rows"][index]
    if published["game"] != game or published["index"] != index:
        raise ArithmeticError("published mixed case order changed")
    scoring = parent_context(root, game, ARMS[1])
    tree = scoring.exact
    if (
        not isinstance(tree, MatrixTree)
        or len(tree.keys) != data["mixed_rows_per_game"]
    ):
        raise ArithmeticError("fixed exact tree changed")
    file = data["mixed_files"][index]
    if published["receipt"]["sha256"] != file["sha256"]:
        raise ArithmeticError("mixed snapshot receipt mismatch")
    metadata = published["metadata"]
    if (
        metadata["game"] != game
        or metadata["index"] != index
        or metadata["weight_control"] != 0.5
        or metadata["weight_other"] != 0.5
        or metadata["readout"] != "linear_average"
        or metadata["work_label"] != 40_000_000
        or published["recall_violations"] != 0
    ):
        raise ArithmeticError("fixed mixed metadata changed")
    mixed = read_snapshot(root / file["path"], tree, published["receipt"], metadata)
    traces = [
        trace_losses(tree, mixed, seat, tolerance=data["arithmetic_tolerance_chips"])
        for seat in (0, 1)
    ]
    gains = (traces[0].losses + traces[1].losses) / 2
    scalar = published["score"]["metrics"]["exact_exploitability_chips"]
    if (
        abs(math.fsum(t.gain for t in traces) / 2 - scalar)
        > data["arithmetic_tolerance_chips"]
    ):
        raise ArithmeticError("mixed seat gains do not match published score")
    identities = [row_identity(tree, i) for i in range(len(tree.keys))]
    streets = tuple(str(row["street"]) for row in identities)
    summary = summarize(gains, streets, scalar)
    selected = set(summary["streets"]["TURN"]["top_five_indices"])
    selected.update(summary["streets"]["RIVER"]["top_five_indices"])
    selected.update(fixed_parent_rows(prior, game))
    decisions: list[dict[str, Any]] = []
    for info in sorted(selected):
        identity = identities[info]
        seat = int(identity["seat"])
        width = len(identity["legal_actions"])
        trace = traces[seat]
        decisions.append(
            {
                **identity,
                "mixed_probabilities": mixed[info, :width].tolist(),
                "mixed_counterfactual_reach": float(trace.counterfactual_mass[info]),
                "mixed_saved_prefix_reach": float(trace.saved_reach_mass[info]),
                "mixed_alternative_action_values_chips": trace.conditional_values[
                    info, :width
                ].tolist(),
                "mixed_additive_gain_chips": float(gains[info]),
            }
        )
    del traces
    gc.collect()
    q8_context = parent_context(root, game, ARMS[0])
    prior_inputs = prior_contract(root)["inputs"]
    q8 = q8_context.expand(parent_policy(root, prior_inputs[2 * index], q8_context))
    exact = parent_policy(root, prior_inputs[2 * index + 1], scoring)
    for row in decisions:
        info = int(row["exact_info"])
        width = len(row["legal_actions"])
        row["q8_parent_probabilities"] = q8[info, :width].tolist()
        row["exact_turn_parent_probabilities"] = exact[info, :width].tolist()
    if rss_bytes() >= data["peak_rss_bytes_exclusive"]:
        raise MemoryError("residual-map peak RSS cap reached")
    return {
        "game": game,
        "index": index,
        "mixed_policy_sha256": published["receipt"]["policy_sha256"],
        "published_exploitability_chips": scalar,
        "summary": summary,
        "mixed_row_gains_chips": gains.tolist(),
        "decisions": decisions,
        "peak_rss_bytes": rss_bytes(),
    }


def run(root: Path, output: Path) -> None:
    """Retain each completed game and any failure without retrying."""
    started = time.perf_counter()
    data = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_admission(root, fingerprint)
    if output.exists():
        raise FileExistsError("retain existing residual-map own attempt")
    output.mkdir(parents=True)
    save(
        output / "started.json",
        {
            "head": head,
            "source_fingerprint": fingerprint,
            "runtime": runtime_environment(),
        },
    )
    deadline = Deadline(data["own_cap_seconds"] - data["failure_save_reserve_seconds"])
    prior: dict[str, Any] = json.loads(
        (
            root / "results/known-turn-collision-medium-transfer/report/report.json"
        ).read_bytes()
    )
    own: dict[str, Any] = json.loads(
        (root / "results/known-turn-half-policy-mixture/own/result.json").read_bytes()
    )
    if prior["status"] != "completed" or own["status"] != "completed":
        raise ArithmeticError("published prior result incomplete")
    completed: list[str] = []
    try:
        for index, game in enumerate(GAMES):
            deadline.check()
            row = trace_one(root, index, data, prior, own)
            save(output / f"game{index:02d}.json", row)
            completed.append(game)
            deadline.check()
        save(
            output / "result.json",
            {
                "status": "completed",
                "head": head,
                "source_fingerprint": fingerprint,
                "games": completed,
                "seconds": time.perf_counter() - started,
                "peak_rss_bytes": rss_bytes(),
            },
        )
    except BaseException as error:
        save(
            output / "failure.json",
            {
                "status": "failed",
                "head": head,
                "completed_games": completed,
                "error_type": type(error).__name__,
                "error": str(error),
                "seconds": time.perf_counter() - started,
                "peak_rss_bytes": rss_bytes(),
            },
        )
        raise
