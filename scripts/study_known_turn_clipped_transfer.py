"""Run the fixed fictional proof, twelve profiles, admission or four own paths."""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from known_turn_clipped_transfer.capture import capture_path
from known_turn_clipped_transfer.forecast import forecast
from known_turn_clipped_transfer.gate import (
    PROFILE,
    clean_head,
    require_admission,
    require_proof,
    require_source,
    source_fingerprint,
)
from known_turn_clipped_transfer.plan import (
    EXPECTED_WORK,
    LABELS,
    MAX_RSS,
    PROFILE_WORK,
    context,
    contract,
    paths,
)
from known_turn_clipped_transfer.proof import fictional_math
from river_generalization.gate import require_archive
from turn_exact_transfer.capture import replay_path
from turn_exact_transfer.learning import PathSpec

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def save(path: Path, value: dict[str, Any]) -> None:
    """Write a never-overwritten, fsynced result or retained failure."""
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def verify_work(saved: dict[str, Any], spec: PathSpec, labels: tuple[int, ...]) -> None:
    """Reject any candidate charged-work crossing unlike the old control."""
    expected = dict(zip(LABELS, EXPECTED_WORK, strict=True))
    if (
        saved["path"] != dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
        or saved["labels"] != list(labels)
        or len(saved["captures"]) != 2 * len(labels)
    ):
        raise ArithmeticError("fixed candidate path identity or readouts changed")
    if labels == LABELS and saved["final_work"] != EXPECTED_WORK[-1]:
        raise ArithmeticError("candidate/control final charged work differs")
    for row in saved["captures"]:
        label = row["metadata"]["work_label"]
        if labels == LABELS and row["metadata"]["total_work"] != expected[label]:
            raise ArithmeticError("candidate/control work crossing differs")


def worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Run fixed dry A/B or wet A/B paths, preserving each complete path."""
    root = Path(payload["root"])
    output = Path(payload["output"])
    deadline: Deadline = payload["deadline"]
    profile = payload["stage"] == "profile"
    summaries: list[dict[str, Any]] = []
    specs = paths()
    for index in indices:
        deadline.check()
        started = time.perf_counter()
        spec = specs[index % len(specs)]
        repeat = index // len(specs)
        labels = (PROFILE_WORK,) if profile else LABELS
        folder = (
            output
            / (f"repeat{repeat}" if profile else "study")
            / f"path{spec.index:02d}"
        )
        send(dict(kind="cell", phase="started", index=index, repeat=repeat, slot=slot))
        scoring = context(root, spec.game)
        saved = capture_path(
            scoring, spec, folder, payload["fingerprint"], labels, deadline
        )
        verify_work(saved, spec, labels)
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
        if rss >= MAX_RSS:
            raise MemoryError("strict per-worker RSS cap reached")
        send(
            dict(kind="cell", phase="completed", index=index, repeat=repeat, slot=slot)
        )
    return dict(slot=slot, summaries=summaries)


def done(record: dict[str, Any], count: int) -> list[dict[str, Any]]:
    """Require every registered worker summary exactly once."""
    if record.get("status") != "completed" or record.get("worker_count") != 2:
        raise ArithmeticError("incomplete clipped-regret worker grid")
    rows = [
        item
        for worker_row in record["workers"]
        for message in worker_row["messages"]
        if message["kind"] == "done"
        for item in message["summary"]["summaries"]
    ]
    if len(rows) != count or {row["index"] for row in rows} != set(range(count)):
        raise ArithmeticError("fixed candidate path summaries missing")
    return rows


def run_stage(stage: str, root: Path, output: Path) -> None:
    """Honor source, fictional proof and admission publications in order."""
    contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_source(root, fingerprint)
    if stage in ("profile", "study"):
        require_proof(root, fingerprint)
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
            math_record = fictional_math()
            scoring = software_context(0).scoring["coarse"]
            spec = PathSpec(0, "FICTIONAL_SIGNAL_GAME", paths()[0].arm)
            folder = output / "toy" / "path00"
            saved = capture_path(
                scoring, spec, folder, fingerprint, (80, 240, 720), deadline
            )
            replay_path(scoring, folder)
            from known_turn_clipped_transfer.learning import RULES

            if (
                len(saved["captures"]) != 6
                or RULES.regret_rule != "clipped"
                or RULES.regret_weight != "linear"
            ):
                raise ArithmeticError("fictional clipped-regret proof incomplete")
            record = {
                **math_record,
                "status": "completed",
                "regret_rule": "clipped",
                "regret_weight": "linear",
                "captures": 6,
                "final_work": saved["final_work"],
                "real_policy_opened": False,
            }
        else:
            count = 12 if stage == "profile" else 4
            payload = dict(
                root=str(root),
                output=str(output),
                stage=stage,
                deadline=deadline,
                fingerprint=fingerprint,
            )
            run_batch(count, 2, worker, payload, deadline, record)
            rows = done(record, count)
            if any(
                row["captures"] != (2 if stage == "profile" else 6)
                or row["worker_peak_rss_bytes"] >= MAX_RSS
                for row in rows
            ):
                raise ArithmeticError("fixed readouts or memory cap failed")
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
    """Recompute strict forecast only from published profile evidence."""
    contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_proof(root, fingerprint)
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
            decision_status=decision["status"],
        ),
    )
    if decision["status"] != "admitted":
        raise ArithmeticError("strict clipped-regret forecast rejected")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("proof", "profile", "admit", "study"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain earlier clipped-regret stage output")
    os.environ.pop("PYTHONPATH", None)
    if args.stage == "admit":
        admit(root, args.output.resolve())
    else:
        run_stage(args.stage, root, args.output.resolve())


if __name__ == "__main__":
    main()
