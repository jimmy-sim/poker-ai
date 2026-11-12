"""Diagnostic command dispatch; solver backend is imported for native only."""

import json
import os
import time
from pathlib import Path

from poker_ai.evaluation.compact_fixed_clock import arguments
from poker_ai.postflop.compact_full_artifacts import atomic


def child(root: Path, argv: list[str]) -> int:
    args = arguments(argv)
    out = root / args.output
    started = float(os.environ.get("POKER_FIXED_STARTED", time.perf_counter()))
    try:
        if args.operation in ("own", "software-own"):
            from poker_ai.evaluation.compact_fixed_run import run

            if args.checks is None:
                raise ValueError("--checks required")
            result = run(
                root, out, args.operation == "software-own", root / args.checks, started
            )
        elif args.operation in ("native", "software-native"):
            from poker_ai.solver_validation.compact_fixed import run as native

            if args.own is None:
                raise ValueError("--own required")
            result = native(
                root, root / args.own, out, started, args.operation == "software-native"
            )
        elif args.operation == "report":
            from poker_ai.evaluation.compact_fixed_report import run as report

            if args.own is None or args.native is None:
                raise ValueError("--own and --native required")
            result = report(root, root / args.own, root / args.native, out, started)
        else:
            from poker_ai.evaluation.compact_fixed_run import replay

            if args.own is None:
                raise ValueError("--own required")
            result = dict(
                status="completed", failure=None, **replay(root, root / args.own)
            )
            atomic(out, result)
        print(
            json.dumps(
                {
                    k: result.get(k)
                    for k in ("status", "failure", "new_training", "actual_admission")
                },
                sort_keys=True,
            )
        )
        return 0 if result["status"] == "completed" and result["failure"] is None else 1
    except (Exception, KeyboardInterrupt) as error:
        result = dict(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
            actual_admission=False,
            new_training=False,
        )
        if not out.exists():
            atomic(out, result)
        print(json.dumps(result, sort_keys=True))
        return 1
