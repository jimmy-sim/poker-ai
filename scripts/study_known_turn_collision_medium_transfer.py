"""Run fixed fictional proof, 5m profiles, admission or 40m own grid."""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from known_turn_collision_medium_transfer.forecast import forecast
from known_turn_collision_medium_transfer.gate import (
    PROFILE,
    PROOF,
    SOURCE,
    clean_revision,
    require_admission,
    require_archive,
    source_fingerprint,
)
from known_turn_collision_medium_transfer.plan import (
    LABELS,
    MAX_RSS,
    PROFILE_WORK,
    context,
    contract,
    paths,
)
from turn_exact_transfer.capture import capture_path, replay_path
from turn_exact_transfer.learning import PathSpec

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, value: dict[str, Any]) -> None:
    """Write a durable new record without overwriting partial evidence."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain earlier conditional transfer record")
    with temporary.open("w") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Keep wet and dry paths for each arm in the frozen worker partition."""
    root = Path(payload["root"])
    output = Path(payload["output"])
    deadline: Deadline = payload["deadline"]
    profile = payload["stage"] == "profile"
    summaries: list[dict[str, Any]] = []
    for index in indices:
        deadline.check()
        started = time.perf_counter()
        spec = paths()[index % len(paths())]
        repeat = index // len(paths())
        labels = (PROFILE_WORK,) if profile else LABELS
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
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
            1 if sys.platform == "darwin" else 1024
        )
        summary = dict(
            index=index,
            repeat=repeat,
            path=saved["path"],
            final_work=saved["final_work"],
            captures=len(saved["captures"]),
            whole_path_seconds=time.perf_counter() - started,
            worker_peak_rss_bytes=rss,
        )
        summaries.append(summary)
        if rss > MAX_RSS:
            raise ArithmeticError("fixed per-worker RSS cap exceeded")
        send(
            dict(kind="cell", phase="completed", index=index, repeat=repeat, slot=slot)
        )
    return dict(slot=slot, summaries=summaries)


def _done(record: dict[str, Any], count: int) -> list[dict[str, Any]]:
    """Require complete fixed worker grid and return each retained summary."""
    if record["status"] != "completed" or record["worker_count"] != 2:
        raise ArithmeticError("incomplete conditional transfer worker grid")
    rows = [
        item
        for worker_row in record["workers"]
        for message in worker_row["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    if len(rows) != count or {row["index"] for row in rows} != set(range(count)):
        raise ArithmeticError("fixed profile/own path summaries missing")
    return rows


def run_stage(stage: str, root: Path, output: Path) -> None:
    """Require each published prerequisite before crossing into real paths."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    from known_turn_collision_medium_transfer.gate import require_frozen

    if stage in ("proof", "profile", "study"):
        require_frozen(root, fingerprint)
    if stage in ("profile", "study"):
        require_archive(root, root / PROOF, "proof_passed", fingerprint)
    if stage == "study":
        require_admission(root, fingerprint)
    deadline = Deadline({"proof": 180, "profile": 780, "study": 7080}[stage])
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
            for index, arm in enumerate((paths()[0].arm, paths()[1].arm)):
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
                arms=(paths()[0].arm, paths()[1].arm),
                captures_per_arm=6,
                final_work=summaries[0]["final_work"],
            )
        else:
            count = len(paths()) * 3 if stage == "profile" else len(paths())
            payload = dict(
                root=str(root),
                output=str(output),
                stage=stage,
                deadline=deadline,
                fingerprint=fingerprint,
            )
            run_batch(count, 2, worker, payload, deadline, record)
            rows = _done(record, count)
            if any(
                row["captures"] != (2 if stage == "profile" else 6)
                or row["worker_peak_rss_bytes"] > MAX_RSS
                for row in rows
            ):
                raise ArithmeticError("fixed known-turn readouts or memory cap failed")
            if stage == "profile":
                save(output / "forecast.json", forecast(record))
            else:
                for first in range(0, len(paths()), 2):
                    control = json.loads(
                        (
                            output / "study" / f"path{first:02d}" / "summary.json"
                        ).read_bytes()
                    )
                    candidate = json.loads(
                        (
                            output / "study" / f"path{first + 1:02d}" / "summary.json"
                        ).read_bytes()
                    )
                    if control["path"]["game"] != candidate["path"]["game"]:
                        raise ArithmeticError("matched game identity changed")
                    for work in LABELS:
                        actual = [
                            {
                                row["metadata"]["total_work"]
                                for row in summary["captures"]
                                if row["metadata"]["work_label"] == work
                            }
                            for summary in (control, candidate)
                        ]
                        if len(actual[0]) != 1 or actual[0] != actual[1]:
                            raise ArithmeticError("paired charged work mismatch")
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
    """Recompute the strict forecast from complete published profile bytes."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    from known_turn_collision_medium_transfer.gate import require_frozen

    require_frozen(root, fingerprint)
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
        raise ArithmeticError("strict conditional transfer forecast rejected")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("proof", "profile", "admit", "study"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain earlier conditional transfer output")
    os.environ.pop("PYTHONPATH", None)
    if args.stage == "admit":
        admit(root, args.output.resolve())
    else:
        run_stage(args.stage, root, args.output.resolve())


if __name__ == "__main__":
    main()
