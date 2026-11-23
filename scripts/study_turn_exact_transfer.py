"""Run the frozen exact-turn inventory, proof, profile and own study."""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
from turn_exact_transfer.capture import capture_path, replay_path
from turn_exact_transfer.forecast import forecast
from turn_exact_transfer.gate import (
    PROFILE,
    PROOF,
    SOURCE,
    clean_revision,
    require_admission,
    require_archive,
    require_inventory,
    source_fingerprint,
)
from turn_exact_transfer.learning import (
    CANDIDATE,
    CONFIG_SHA256,
    CONTROL,
    GAMES,
    LABELS,
    PathSpec,
    context,
    contract,
    paths,
)

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, payload: dict[str, Any]) -> None:
    """Write one immutable stage record and keep any earlier partial bytes."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain existing exact-turn stage record")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


def inventory(root: Path, deadline: Deadline) -> dict[str, Any]:
    """Count only frozen turn-key collisions; no training or scoring."""
    rows = []
    for game in GAMES:
        deadline.check()
        scoring = context(root, game, CONTROL)
        tree = scoring.exact
        control = scoring.partition
        if not isinstance(tree, MatrixTree) or not isinstance(control, MatrixTree):
            raise ArithmeticError("frozen inventory requires matrix trees")
        turn = np.zeros(len(tree.keys), dtype=np.bool_)
        river = np.zeros(len(tree.keys), dtype=np.bool_)
        for i, node in enumerate(tree.source.representatives):
            state = tree.source.states[node]
            if state.dealer is None:
                raise ArithmeticError("decision representative missing observation")
            street = len(state.dealer.board)
            if street == 4:
                turn[i] = True
            elif street == 5:
                river[i] = True
            else:
                raise ArithmeticError("outside frozen turn-start game")
        mapping = control.exact_to_abstract
        sizes = np.bincount(mapping, minlength=len(control.keys))[mapping]
        collided = sizes > 1
        if np.any(river & collided):
            raise ArithmeticError("historical exact river unexpectedly collided")
        rows.append(
            dict(
                game=game,
                tree_nodes=len(tree.player),
                exact_information_rows=len(tree.keys),
                q8_information_rows=len(control.keys),
                turn_exact_rows=int(np.count_nonzero(turn)),
                turn_collided_exact_rows=int(np.count_nonzero(turn & collided)),
                turn_collided_abstract_groups=len(
                    {int(mapping[i]) for i in np.flatnonzero(turn & collided)}
                ),
                river_exact_rows=int(np.count_nonzero(river)),
                river_collided_exact_rows=0,
            )
        )
    opportunity = sum(cast(int, row["turn_collided_exact_rows"]) for row in rows[1:])
    return dict(
        status="inventory_complete" if opportunity > 0 else "structural_stop",
        spots=rows,
        selected_turn_collided_exact_rows=opportunity,
        no_policy_or_score_read=True,
    )


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Run only fixed path indices, retaining each before another starts."""
    root = Path(payload["root"])
    output = Path(payload["output"])
    deadline: Deadline = payload["deadline"]
    profile = payload["stage"] == "profile"
    summaries: list[dict[str, Any]] = []
    for index in indices:
        deadline.check()
        started = time.perf_counter()
        spec = paths()[index % 8]
        repeat = index // 8
        labels = (1_000_000,) if profile else LABELS
        folder = (
            output
            / (f"repeat{repeat}" if profile else "study")
            / f"path{spec.index:02d}"
        )
        send(dict(kind="cell", phase="started", index=index, repeat=repeat, slot=slot))
        scoring = context(root, spec.game, spec.arm)
        saved = capture_path(
            scoring, spec, folder, payload["fingerprint"], labels, deadline
        )
        replay_path(scoring, folder)
        summaries.append(
            dict(
                index=index,
                repeat=repeat,
                path=saved["path"],
                final_work=saved["final_work"],
                captures=len(saved["captures"]),
                whole_path_seconds=time.perf_counter() - started,
                worker_peak_rss_bytes=(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    * (1 if sys.platform == "darwin" else 1024)
                ),
            )
        )
        send(
            dict(kind="cell", phase="completed", index=index, repeat=repeat, slot=slot)
        )
    return dict(slot=slot, summaries=summaries)


def run_stage(stage: str, root: Path, output: Path) -> None:
    """Respect source, inventory, proof and admission publication order."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    if stage in ("proof", "profile", "study"):
        require_inventory(root, fingerprint)
    if stage in ("profile", "study"):
        require_archive(root, root / PROOF, "proof_passed", fingerprint)
    if stage == "study":
        require_admission(root, fingerprint)
    deadline = Deadline(
        {"inventory": 900, "proof": 180, "profile": 900, "study": 7080}[stage]
    )
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "started.json",
        dict(
            stage=stage,
            status="running",
            head=head,
            source_fingerprint=fingerprint,
            config_sha256=CONFIG_SHA256,
            runtime=runtime_environment(),
        ),
    )
    record: dict[str, Any] = {}
    try:
        if stage == "inventory":
            record = inventory(root, deadline)
        elif stage == "proof":
            scoring = software_context(0).scoring["coarse"]
            summaries = []
            for index, arm in enumerate((CONTROL, CANDIDATE)):
                spec = PathSpec(index, "FICTIONAL_SIGNAL_GAME", arm)
                folder = output / "toy" / f"path{index:02d}"
                saved = capture_path(
                    scoring, spec, folder, fingerprint, (80, 240, 720), deadline
                )
                replay_path(scoring, folder)
                summaries.append(saved)
            if summaries[0]["final_work"] != summaries[1]["final_work"] or [
                row["score"] for row in summaries[0]["captures"]
            ] != [row["score"] for row in summaries[1]["captures"]]:
                raise ArithmeticError("fictional paired full-work paths differ")
            record = dict(
                status="completed",
                fixture="fictional signal game",
                arms=[CONTROL, CANDIDATE],
                captures_per_arm=6,
                final_work=summaries[0]["final_work"],
            )
        else:
            count = 24 if stage == "profile" else 8
            payload = dict(
                root=str(root),
                output=str(output),
                stage=stage,
                deadline=deadline,
                fingerprint=fingerprint,
            )
            run_batch(count, 3, worker, payload, deadline, record)
            if record["status"] != "completed":
                raise ArithmeticError("incomplete exact-turn worker grid")
            done = [
                message["summary"]["summaries"]
                for row in record["workers"]
                for message in row["messages"]
                if message["kind"] == "done"
            ]
            if len(done) != 3 or sum(map(len, done)) != count:
                raise ArithmeticError("missing fixed exact-turn path summaries")
            if any(
                row["captures"] != (2 if stage == "profile" else 6)
                for part in done
                for row in part
            ):
                raise ArithmeticError("missing fixed exact-turn readouts")
            if stage == "profile":
                save(output / "forecast.json", forecast(record))
        deadline.check()
        record.update(stage=stage, head=head, source_fingerprint=fingerprint)
        save(output / "result.json", record)
    except BaseException as error:
        record.update(
            status="failed_retained",
            stage=stage,
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        save(output / "failure.json", record)
        raise


def admit(root: Path, output: Path) -> None:
    """Recompute the complete published profile without any training."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_inventory(root, fingerprint)
    require_archive(root, root / PROOF, "proof_passed", fingerprint)
    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    decision = forecast(profile)
    output.mkdir(parents=True, exist_ok=False)
    save(output / "decision.json", decision)
    save(
        output / "receipt.json",
        dict(
            head=head,
            source_fingerprint=fingerprint,
            profile=PROFILE.as_posix(),
            decision_status=decision["status"],
        ),
    )
    if decision["status"] != "admitted":
        raise ArithmeticError("predeclared conservative forecast rejected")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage", choices=("inventory", "proof", "profile", "admit", "study")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain previous exact-turn output")
    os.environ.pop("PYTHONPATH", None)
    if args.stage == "admit":
        admit(root, args.output.resolve())
    else:
        run_stage(args.stage, root, args.output.resolve())


if __name__ == "__main__":
    main()
