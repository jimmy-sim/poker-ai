"""One fictional proof, six fixed profile paths and two admitted own paths."""

import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from medium_dry_full.capture import READOUTS, capture_path, replay_path
from medium_dry_full.forecast import forecast
from medium_dry_full.gate import (
    ADMISSION,
    ARM,
    PROFILE,
    PROFILE_WORK,
    PROOF,
    SOURCE,
    WORK,
    clean_head,
    fingerprint,
    fixed_contract,
    paths,
    require_stage,
)
from medium_dry_full.learning import context
from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, data: dict[str, Any]) -> None:
    """Write one immutable stage receipt; preserve any earlier partial file."""
    if path.exists() or path.is_symlink():
        raise FileExistsError("retain existing full-pass receipt")
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.exists():
        raise FileExistsError("retain partial full-pass receipt")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Run only fixed serial paths, retaining each path before the next."""
    root = Path(payload["root"])
    output = Path(payload["output"])
    deadline: Deadline = payload["deadline"]
    profile = payload["stage"] == "profile"
    labels = (PROFILE_WORK,) if profile else WORK
    summaries: list[dict[str, Any]] = []
    for index in indices:
        deadline.check()
        started = time.perf_counter()
        path_index, game, arm = paths()[index % 2]
        repeat = index // 2
        folder = (
            output
            / (f"repeat{repeat}" if profile else "study")
            / f"path{path_index:02d}"
        )
        send(dict(kind="cell", phase="started", index=index, repeat=repeat, slot=slot))
        scoring = context(root, game, arm)
        saved = capture_path(
            scoring, path_index, game, folder, payload["fingerprint"], labels, deadline
        )
        replay_path(scoring, folder)
        row = dict(
            index=index,
            repeat=repeat,
            path=saved["path"],
            final_work=saved["final_work"],
            captures=len(saved["captures"]),
            whole_path_seconds=time.perf_counter() - started,
            worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024),
        )
        summaries.append(row)
        send(
            dict(
                kind="cell",
                phase="completed",
                index=index,
                repeat=repeat,
                slot=slot,
                folder=str(folder.relative_to(output)),
            )
        )
    return dict(slot=slot, summaries=summaries)


def run_stage(stage: str, root: Path, output: Path) -> None:
    """Enforce all earlier published gates before one fresh stage."""
    fixed_contract(root)
    head = clean_head(root)
    source = fingerprint(root)
    require_stage(root, SOURCE, "source_qualified")
    if stage in ("profile", "study"):
        require_stage(root, PROOF, "own_proof_passed")
    if stage == "study":
        require_stage(root, PROFILE, "profile_published")
        require_stage(root, ADMISSION, "admitted")
        profile = json.loads((root / PROFILE / "result.json").read_bytes())
        admitted = json.loads((root / ADMISSION / "decision.json").read_bytes())
        if forecast(profile) != admitted or admitted["status"] != "admitted":
            raise ArithmeticError("published conservative admission changed")
    deadline = Deadline({"proof": 180, "profile": 900, "study": 7200}[stage])
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "started.json",
        dict(
            stage=stage,
            status="running",
            head=head,
            source_fingerprint=source,
            runtime=runtime_environment(),
        ),
    )
    record: dict[str, Any] = {}
    try:
        if stage == "proof":
            scoring = software_context(0).scoring["coarse"]
            saved = capture_path(
                scoring,
                0,
                "FICTIONAL_SIGNAL_GAME",
                output / "toy" / ARM,
                source,
                (80, 240, 720),
                deadline,
            )
            replay_path(scoring, output / "toy" / ARM)
            record = dict(
                status="completed",
                fixture="fictional signal game",
                rows=[
                    dict(
                        arm=ARM,
                        captures=len(saved["captures"]),
                        final_work=saved["final_work"],
                    )
                ],
            )
        else:
            count = 6 if stage == "profile" else 2
            labels = (PROFILE_WORK,) if stage == "profile" else WORK
            payload = dict(
                root=str(root),
                output=str(output),
                labels=labels,
                stage=stage,
                deadline=deadline,
                fingerprint=source,
            )
            run_batch(count, 1, worker, payload, deadline, record)
            if record["status"] != "completed":
                raise ArithmeticError("incomplete fixed full-pass worker grid")
            worker_rows = [
                message["summary"]["summaries"]
                for worker_row in record["workers"]
                for message in worker_row["messages"]
                if message["kind"] == "done"
            ]
            if len(worker_rows) != 1 or len(worker_rows[0]) != count:
                raise ArithmeticError("missing full-pass path summaries")
            if any(
                row["captures"] != len(labels) * len(READOUTS) for row in worker_rows[0]
            ):
                raise ArithmeticError("missing fixed full-pass readouts")
            if stage == "profile":
                save(output / "forecast.json", forecast(record))
        deadline.check()
        record.update(stage=stage, source_fingerprint=source, head=head)
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
    """Recompute the complete published profile without any learner run."""
    fixed_contract(root)
    head = clean_head(root)
    require_stage(root, SOURCE, "source_qualified")
    require_stage(root, PROOF, "own_proof_passed")
    require_stage(root, PROFILE, "profile_published")
    profile = json.loads((root / PROFILE / "result.json").read_bytes())
    decision = forecast(profile)
    output.mkdir(parents=True, exist_ok=False)
    save(output / "decision.json", decision)
    save(
        output / "receipt.json",
        dict(
            head=head,
            source_fingerprint=fingerprint(root),
            profile=PROFILE.as_posix(),
            decision_status=decision["status"],
        ),
    )
    if decision["status"] != "admitted":
        raise ArithmeticError("predeclared conservative forecast failed")


def main(stage: str, output: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous full-pass stage")
    os.environ.pop("PYTHONPATH", None)
    if stage == "admit":
        admit(root, output.resolve())
    else:
        run_stage(stage, root, output.resolve())
