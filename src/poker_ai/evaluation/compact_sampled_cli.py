"""Operator commands; reference backend imports only on comparison commands."""

import json
import os
import time
from pathlib import Path

from poker_ai.evaluation.compact_sampled_clock import arguments
from poker_ai.postflop.compact_full_artifacts import atomic


def child(root: Path, argv: list[str]) -> int:
    args = arguments(argv)
    output = root / args.output
    started = float(os.environ.get("POKER_SAMPLED_STARTED", time.perf_counter()))
    try:
        operation = args.operation
        if operation in ("software-own", "study"):
            from poker_ai.evaluation.compact_sampled_own import run

            if args.checks is None:
                raise ValueError("--checks required")
            result = run(
                root,
                output,
                "software" if operation == "software-own" else "real",
                root / args.checks,
                started,
                root / args.admission if args.admission else None,
            )
        elif operation == "cost-own":
            from poker_ai.evaluation.compact_sampled_cost import run as cost

            if args.checks is None or args.repetition is None:
                raise ValueError("--checks and --repetition required")
            result = cost(root, output, args.repetition, root / args.checks, started)
        elif operation in ("software-native", "cost-native", "audit"):
            from poker_ai.solver_validation.compact_sampled import run as native

            if args.own is None:
                raise ValueError("--own required")
            result = native(root, root / args.own, output, started, operation)
        elif operation in ("forecast", "admit"):
            from poker_ai.evaluation.compact_sampled_gate import admit, forecast

            if args.checks is None:
                raise ValueError("--checks required")
            result = (forecast if operation == "forecast" else admit)(
                root, root / args.checks
            )
            atomic(output, result)
        elif operation == "report":
            from poker_ai.evaluation.compact_sampled_report import run as report

            if args.own is None or args.native is None:
                raise ValueError("--own and --native required")
            result = report(root, root / args.own, root / args.native, output, started)
        elif operation == "replay":
            from poker_ai.evaluation.compact_sampled_own import replay

            if args.own is None:
                raise ValueError("--own required")
            result = dict(
                status="completed", failure=None, **replay(root, root / args.own)
            )
            atomic(output, result)
        else:
            from poker_ai.evaluation.compact_sampled_own import partial

            if args.own is None:
                raise ValueError("--own required, identifying the partial manifest")
            result = dict(
                status="completed",
                failure=None,
                partial_evidence=partial((root / args.own).parent),
                actual_admission=False,
                fresh_global_admission=False,
            )
            atomic(output, result)
        print(
            json.dumps(
                {
                    k: result.get(k)
                    for k in (
                        "status",
                        "failure",
                        "actual_admission",
                        "fresh_global_admission",
                    )
                },
                sort_keys=True,
            )
        )
        return (
            0
            if result.get("status") == "completed" and result.get("failure") is None
            else 1
        )
    except (Exception, KeyboardInterrupt) as error:
        result = dict(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
            actual_admission=False,
            fresh_global_admission=False,
        )
        if not output.exists():
            atomic(output, result)
        print(json.dumps(result, sort_keys=True))
        return 1
