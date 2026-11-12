"""Child dispatch; all operations remain behind source-bound prerequisites."""

import os
from pathlib import Path
from typing import Any

from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop.compact_full_clock import arguments
from poker_ai.postflop.compact_full_gate import admission, forecast, layout
from poker_ai.postflop.compact_full_run import replay, run


def child_main(root: Path, argv: list[str]) -> int:
    args = arguments(argv)
    output = root / args.output
    started = float(os.environ["POKER_COMPACT_STARTED"])
    result: dict[str, Any]
    try:
        if args.operation in ("software-own", "own", "layout"):
            if args.checks is None:
                raise ValueError(
                    "source-bound local/optional/hosted check receipt required"
                )
        if args.operation in ("software-own", "own"):
            result = run(
                root,
                output,
                software=args.operation == "software-own",
                started=started,
                admission=(root / args.admission) if args.admission else None,
                check_path=root / args.checks,
            )
        elif args.operation in ("software-native", "native"):
            from poker_ai.solver_validation.compact_full import run as audit

            if args.own is None:
                raise ValueError("explicit published own evidence required")
            result = audit(root, root / args.own, output, started=started)
        elif args.operation == "layout":
            result = layout(root, output, args.repetition, started, root / args.checks)
        elif args.operation in ("forecast", "admit"):
            if args.checks is None:
                raise ValueError("explicit checks required")
            result = (forecast if args.operation == "forecast" else admission)(
                root, root / args.checks
            )
        elif args.operation == "replay":
            if args.own is None:
                raise ValueError("explicit own evidence required")
            result = dict(status="completed", **replay(root, root / args.own))
        elif args.operation == "report":
            from poker_ai.postflop.compact_full_report import render

            if args.own is None or args.native is None:
                raise ValueError("explicit own and native artifacts required")
            result = render(root, root / args.own, root / args.native, output)
        else:
            raise ValueError("unsupported operation")
    except (Exception, KeyboardInterrupt) as error:
        result = dict(
            status="failed",
            failure=dict(type=type(error).__name__, reason=str(error)),
            actual_admission=False,
            fresh_global_admission=False,
        )
    artifacts.atomic(output, result)
    return 0 if result["status"] == "completed" else 1
