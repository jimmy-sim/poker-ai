"""Run the prospectively bounded own river-uniform-readout stages on fresh outputs."""

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

from river_uniform_readout.capture import capture_path, replay_path
from river_uniform_readout.forecast import forecast
from river_uniform_readout.gate import (
    PROFILE,
    clean_revision,
    require_admission,
    require_archive,
    source_fingerprint,
)
from river_uniform_readout.learning import (
    CONFIG_SHA256,
    LABELS,
    PathSpec,
    context,
    contract,
    paths,
)

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment

SOURCE = Path("results/river-uniform-readout/source-checks")
PROOF = Path("results/river-uniform-readout/own-proof")


def _save(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain existing river-uniform-readout stage receipt")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


def _worker(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    root = Path(payload["root"])
    output = Path(payload["output"])
    labels = tuple(payload["labels"])
    profile = payload["stage"] == "profile"
    deadline: Deadline = payload["deadline"]
    summaries = []
    for index in indices:
        deadline.check()
        started = time.perf_counter()
        spec = paths()[index % 12]
        repeat = index // 12
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
            dict(
                kind="cell",
                phase="completed",
                index=index,
                repeat=repeat,
                folder=str(folder.relative_to(output)),
            )
        )
    return dict(slot=slot, summaries=summaries)


def run_stage(stage: str, root: Path, output: Path) -> None:
    deadline = Deadline({"proof": 180, "profile": 900, "study": 7200}[stage])
    config = contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    if stage in ("profile", "study"):
        require_archive(root, root / PROOF, "own_proof_passed", fingerprint)
    if stage == "study":
        require_admission(root, fingerprint)
    output.mkdir(parents=True, exist_ok=False)
    base = dict(
        status="running",
        stage=stage,
        head=head,
        source_fingerprint=fingerprint,
        runtime=runtime_environment(),
        config_sha256=CONFIG_SHA256,
        output=str(output),
    )
    _save(output / "started.json", base)
    record: dict[str, Any] = {}
    try:
        if stage == "proof":
            scoring = software_context(0).scoring["coarse"]
            saved = capture_path(
                scoring,
                PathSpec(0, "FICTIONAL_SIGNAL_GAME", config["seeds"][0], "coarse"),
                output / "toy",
                fingerprint,
                (80, 240, 720),
                deadline,
            )
            replay_path(scoring, output / "toy")
            record = dict(
                status="completed",
                fixture="fictional signal game",
                captures=len(saved["captures"]),
                final_work=saved["final_work"],
            )
        else:
            count = 36 if stage == "profile" else 12
            labels = (100_000,) if stage == "profile" else LABELS
            payload = dict(
                root=str(root),
                output=str(output),
                labels=labels,
                stage=stage,
                deadline=deadline,
                fingerprint=fingerprint,
            )
            run_batch(count, 3, _worker, payload, deadline, record)
            if record["status"] != "completed":
                raise ArithmeticError("incomplete river-uniform-readout worker grid")
            expected = count * len(labels) * 3
            actual = sum(
                len(path["summary"]["summaries"]) * len(labels) * 3
                for path in (
                    next(m for m in worker["messages"] if m["kind"] == "done")
                    for worker in record["workers"]
                )
            )
            if actual != expected:
                raise ArithmeticError("missing fixed path readouts")
            if stage == "profile":
                estimate = forecast(record)
                _save(output / "forecast.json", estimate)
                if estimate["status"] != "admitted":
                    raise ArithmeticError("predeclared long-run forecast failed")
        deadline.check()
        record["stage"] = stage
        record["source_fingerprint"] = fingerprint
        record["head"] = head
        _save(output / "result.json", record)
    except BaseException as error:
        record.update(
            status="failed_retained",
            stage=stage,
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        _save(output / "failure.json", record)
        raise


def admit_stage(root: Path, output: Path) -> None:
    """Recompute the complete published profile; write no learner or policy."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / PROOF, "own_proof_passed", fingerprint)
    require_archive(root, root / PROFILE, "profile_published", fingerprint)
    profile: dict[str, Any] = json.loads((root / PROFILE / "result.json").read_bytes())
    if profile["stage"] != "profile" or profile["source_fingerprint"] != fingerprint:
        raise ArithmeticError("published profile source binding changed")
    decision = forecast(profile)
    output.mkdir(parents=True, exist_ok=False)
    _save(output / "decision.json", decision)
    _save(
        output / "receipt.json",
        dict(
            head=head,
            source_fingerprint=fingerprint,
            profile=PROFILE.as_posix(),
            decision_status=decision["status"],
        ),
    )
    if decision["status"] != "admitted":
        raise ArithmeticError("predeclared long-run forecast failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("proof", "profile", "admit", "study"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain existing river-uniform-readout output")
    # Thread requests apply only within the spawned worker cohort.
    os.environ.pop("PYTHONPATH", None)
    if args.stage == "admit":
        admit_stage(root, args.output.resolve())
    else:
        run_stage(args.stage, root, args.output.resolve())


if __name__ == "__main__":
    main()
