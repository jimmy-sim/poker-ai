"""Run fixed known-case exact-turn proof, profile, admission and own pair."""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from known_turn_mechanism.forecast import forecast
from known_turn_mechanism.gate import (
    PROFILE,
    PROOF,
    SOURCE,
    clean_revision,
    require_admission,
    require_archive,
    source_fingerprint,
)
from known_turn_mechanism.plan import ARMS, GAME, LABELS, context, contract, paths
from turn_exact_transfer.capture import capture_path, replay_path
from turn_exact_transfer.learning import PathSpec

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, payload: dict[str, Any]) -> None:
    """Never overwrite a prior stage result or partial record."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain earlier known-turn stage result")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Run path indices modulo two, retaining each before another starts."""
    root = Path(payload["root"])
    output = Path(payload["output"])
    deadline: Deadline = payload["deadline"]
    profile = payload["stage"] == "profile"
    summaries: list[dict[str, Any]] = []
    for index in indices:
        deadline.check()
        started = time.perf_counter()
        spec = paths()[index % 2]
        repeat = index // 2
        labels = (1_000_000,) if profile else LABELS
        folder = (
            output
            / (f"repeat{repeat}" if profile else "study")
            / f"path{spec.index:02d}"
        )
        send(dict(kind="cell", phase="started", index=index, repeat=repeat, slot=slot))
        scoring = context(root, GAME, spec.arm)
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
                worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * (1 if sys.platform == "darwin" else 1024),
            )
        )
        send(
            dict(kind="cell", phase="completed", index=index, repeat=repeat, slot=slot)
        )
    return dict(slot=slot, summaries=summaries)


def run_stage(stage: str, root: Path, output: Path) -> None:
    """Require published source/proof/admission stages before real policies."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    if stage in ("profile", "study"):
        require_archive(root, root / PROOF, "proof_passed", fingerprint)
    if stage == "study":
        require_admission(root, fingerprint)
    deadline = Deadline({"proof": 180, "profile": 900, "study": 7080}[stage])
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "started.json",
        dict(
            stage=stage,
            status="running",
            head=head,
            source_fingerprint=fingerprint,
            runtime=runtime_environment(),
        ),
    )
    record: dict[str, Any] = {}
    try:
        if stage == "proof":
            scoring = software_context(0).scoring["coarse"]
            summaries = []
            for index, arm in enumerate(ARMS):
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
                arms=ARMS,
                captures_per_arm=6,
                final_work=summaries[0]["final_work"],
            )
        else:
            count = 6 if stage == "profile" else 2
            payload = dict(
                root=str(root),
                output=str(output),
                stage=stage,
                deadline=deadline,
                fingerprint=fingerprint,
            )
            run_batch(count, 2, worker, payload, deadline, record)
            if record["status"] != "completed":
                raise ArithmeticError("incomplete known-turn worker grid")
            done = [
                message["summary"]["summaries"]
                for row in record["workers"]
                for message in row["messages"]
                if message["kind"] == "done"
            ]
            if len(done) != 2 or sum(map(len, done)) != count:
                raise ArithmeticError("missing known-turn path summaries")
            if any(
                row["captures"] != (2 if stage == "profile" else 6)
                for part in done
                for row in part
            ):
                raise ArithmeticError("missing fixed known-turn readouts")
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
    """Independently recompute strict profile forecast from published bytes."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    for stage, status in (
        (SOURCE, "source_qualified"),
        (PROOF, "proof_passed"),
        (PROFILE, "profile_published"),
    ):
        require_archive(root, root / stage, status, fingerprint)
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
    parser.add_argument("stage", choices=("proof", "profile", "admit", "study"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain earlier known-turn output")
    os.environ.pop("PYTHONPATH", None)
    if args.stage == "admit":
        admit(root, args.output.resolve())
    else:
        run_stage(args.stage, root, args.output.resolve())


if __name__ == "__main__":
    main()
