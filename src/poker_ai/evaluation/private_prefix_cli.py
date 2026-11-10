"""Whole-command clocks and fresh destinations around gated child stages.

Scientific workers and seeds are unchanged. A hard child timeout contains the
whole stage; raw fsynced event journals survive even a killed child. Existing
attempts are never replaced. Admission remains a separate published receipt.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from poker_ai.evaluation import private_prefix_admission as admission
from poker_ai.evaluation.matched_update_lifecycle import CAPS, finish, fresh, measured
from poker_ai.evaluation.private_prefix_design import TOY
from poker_ai.evaluation.private_prefix_io import destinations
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline

KINDS = {
    "fixture-own": "tiny_own",
    "fixture-native": "tiny_native",
    "profile": "profile",
    "timing-native": "timing_native",
    "study": "study",
    "real-native": "real_native",
}
OUTPUTS = {
    "fixture-own": admission.SOFTWARE,
    "fixture-native": admission.SOFTWARE_NATIVE,
    "profile": admission.PROFILE,
    "timing-native": admission.OLD_NATIVE,
    "study": "results/private-prefix/study/own.json",
    "real-native": "results/private-prefix/study/native.json",
    "admit": admission.ADMISSION,
    "code-checks": "results/private-prefix/pipeline-code-checks.json",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "operation", choices=(*KINDS, "code-checks", "admit", "replay", "report")
    )
    for name in ("output", "own", "ci", "local"):
        p.add_argument("--" + name, type=Path)
    p.add_argument("--no-plots", action="store_true")
    p.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    return p


def child(root: Path, args: argparse.Namespace, output: Path) -> None:
    own = root / args.own if args.own else None
    if args.operation == "fixture-own":
        from poker_ai.evaluation.private_prefix_run import tiny

        tiny(root, output)
    elif args.operation == "profile":
        from poker_ai.evaluation.private_prefix_profile import run

        run(root, output)
    elif args.operation == "study":
        from poker_ai.evaluation.private_prefix_run import study

        study(root, output)
    else:
        from poker_ai.solver_validation.private_prefix_run import audit

        if own is None:
            raise ValueError("native comparison requires explicit --own")
        audit(root, own, output, KINDS[args.operation])


def preflight(output: Path, operation: str) -> None:
    paths = destinations(output)
    if operation.endswith("native"):
        paths = [p for p in paths if p != output.parent / "report"]
    if operation == "profile":
        paths.extend(destinations(output.parent / "overhead/own.json"))
    fresh(paths)


def execute(root: Path, argv: list[str]) -> int:
    started = time.perf_counter()
    args = parser().parse_args(argv)
    operation = args.operation
    output = root / (
        args.output or OUTPUTS.get(operation, "results/private-prefix/report")
    )
    if args.child:
        child(root, args, output)
        return 0
    if operation not in KINDS:
        if operation == "replay":
            from poker_ai.evaluation.private_prefix_read import read

            if args.own is None:
                raise ValueError("replay requires --own")
            saved, _ = read(root, root / args.own, Deadline(900))
            print(json.dumps(saved["replayed_now"], sort_keys=True))
            return 0
        if operation == "report":
            from poker_ai.evaluation.private_prefix_read import read
            from poker_ai.evaluation.private_prefix_report import write

            if args.own is None or args.output is None:
                raise ValueError("report requires --own and fresh --output")
            fresh([output])
            saved, _ = read(root, root / args.own, Deadline(900))
            pots = {
                p: 2.0
                if saved["scope"] == TOY
                else float(json.loads((root / p).read_text())["pot"])
                for p in {r["case"]["spot_file"] for r in saved["rows"]}
            }
            print(json.dumps(write(saved, output, pots, no_plots=args.no_plots)))
            return 0
        fresh([output, output.with_suffix(".tmp")])
        if operation == "admit":
            result = admission.record(root)
        else:
            from poker_ai.evaluation.private_prefix_gates import record

            if args.ci is None or args.local is None:
                raise ValueError("code-checks requires --ci and --local")
            result = record(
                root,
                json.loads((root / args.ci).read_text()),
                json.loads((root / args.local).read_text()),
            )
        persist(output, result)
        print(json.dumps({"status": result["status"], "output": str(output)}))
        return 0
    kind = KINDS[operation]
    own = root / args.own if args.own else None
    command = [
        sys.executable,
        "-m",
        "poker_ai.evaluation.private_prefix_cli",
        *argv,
        "--child",
    ]
    try:
        preflight(output, operation)
        if operation.endswith("native") and own is None:
            raise ValueError("native comparison requires --own")
        launched = subprocess.Popen(
            command,
            cwd=root,
            env={**os.environ, "PYTHONPATH": "src"},
            start_new_session=True,
        )
        try:
            returncode = launched.wait(
                timeout=max(0.001, CAPS[kind] - (time.perf_counter() - started))
            )
        except subprocess.TimeoutExpired:
            os.killpg(launched.pid, signal.SIGTERM)
            try:
                launched.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(launched.pid, signal.SIGKILL)
                launched.wait(timeout=1)
            raise
        if output.exists():
            finish(output, kind, command, started, returncode, own)
        if returncode:
            return returncode
        measured(root, output, kind)
        if operation == "profile":
            admission.profile_screen(root)
        print(json.dumps({"status": "completed_whole_command", "output": str(output)}))
        return 0
    except BaseException as error:
        rejection = (
            output.parent
            / "rejections"
            / (output.stem + "-" + str(time.time_ns()) + ".json")
        )
        persist(
            rejection,
            dict(
                status="failed_whole_command_not_admitted",
                operation=operation,
                failure=dict(type=type(error).__name__, reason=str(error)),
                seconds=time.perf_counter() - started,
                command=command,
                retained_output_exists=output.exists(),
                training_status="inspect_retained_output_and_raw_event_journal",
                long_run_admitted=False,
            ),
        )
        raise


def main() -> int:
    return execute(Path(__file__).resolve().parents[3], sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
