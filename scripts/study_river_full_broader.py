"""Run fixed fictional proof, mixed profile, admission and one own study."""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from medium_dry_full.capture import capture_path as full_capture
from medium_dry_full.capture import replay_path as full_replay
from river_full_broader.control_capture import capture_path as control_capture
from river_full_broader.control_capture import replay_path as control_replay
from river_full_broader.forecast import forecast
from river_full_broader.gate import (
    PROFILE,
    PROOF,
    SOURCE,
    clean_revision,
    require_admission,
    require_archive,
    source_fingerprint,
)
from river_full_broader.learning import (
    CANDIDATE,
    CONFIG_SHA256,
    LABELS,
    SEEDS,
    PathSpec,
    context,
    contract,
    paths,
)

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, payload: dict[str, Any]) -> None:
    """Write one immutable stage record, retaining prior and partial bytes."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain existing broader-full stage receipt")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Run only fixed path indices and retain each path before the next."""
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
        labels = (
            ((1_000_000,) if spec.arm == CANDIDATE else (100_000,))
            if profile
            else LABELS
        )
        folder = (
            output
            / (f"repeat{repeat}" if profile else "study")
            / f"path{spec.index:02d}"
        )
        send(dict(kind="cell", phase="started", index=index, repeat=repeat, slot=slot))
        scoring = context(root, spec.game)
        if spec.arm == CANDIDATE:
            saved = full_capture(
                scoring,
                spec.index,
                spec.game,
                folder,
                payload["fingerprint"],
                labels,
                deadline,
            )
            full_replay(scoring, folder)
        else:
            saved = control_capture(
                scoring, spec, folder, payload["fingerprint"], labels, deadline
            )
            control_replay(scoring, folder)
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
    """Enforce published stages before one capped own experiment stage."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    if stage in ("profile", "study"):
        require_archive(root, root / PROOF, "own_proof_passed", fingerprint)
    if stage == "study":
        require_admission(root, fingerprint)
    # The 120-second tail of the 7200-second cap is reserved for failure-save.
    deadline = Deadline({"proof": 180, "profile": 900, "study": 7080}[stage])
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
        if stage == "proof":
            scoring = software_context(0).scoring["coarse"]
            control = PathSpec(
                0, "FICTIONAL_SIGNAL_GAME", SEEDS[0], "signed_external_b4"
            )
            b4 = control_capture(
                scoring,
                control,
                output / "toy" / "control",
                fingerprint,
                (80, 240, 720),
                deadline,
            )
            control_replay(scoring, output / "toy" / "control")
            full = full_capture(
                scoring,
                1,
                "FICTIONAL_SIGNAL_GAME",
                output / "toy" / "full",
                fingerprint,
                (80, 240, 720),
                deadline,
            )
            full_replay(scoring, output / "toy" / "full")
            record = dict(
                status="completed",
                fixture="fictional signal game",
                rows=[
                    dict(
                        arm=control.arm,
                        captures=len(b4["captures"]),
                        final_work=b4["final_work"],
                    ),
                    dict(
                        arm=CANDIDATE,
                        captures=len(full["captures"]),
                        final_work=full["final_work"],
                    ),
                ],
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
                raise ArithmeticError("incomplete broader-full worker grid")
            done = [
                m["summary"]["summaries"]
                for worker_row in record["workers"]
                for m in worker_row["messages"]
                if m["kind"] == "done"
            ]
            if len(done) != 3 or sum(map(len, done)) != count:
                raise ArithmeticError("missing fixed broader-full path summaries")
            if any(
                row["captures"] != (2 if stage == "profile" else 6)
                for part in done
                for row in part
            ):
                raise ArithmeticError("missing fixed broader-full readouts")
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
    """Recompute complete published profile without any training or scoring."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / PROOF, "own_proof_passed", fingerprint)
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
    parser.add_argument("stage", choices=("proof", "profile", "admit", "study"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain previous broader-full output")
    os.environ.pop("PYTHONPATH", None)
    if args.stage == "admit":
        admit(root, args.output.resolve())
    else:
        run_stage(args.stage, root, args.output.resolve())


if __name__ == "__main__":
    main()
