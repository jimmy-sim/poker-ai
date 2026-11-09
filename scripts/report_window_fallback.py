"""Read-only replay and report of all saved-window fallback intervention cases."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.window_fallback_report import write_report
from poker_ai.evaluation.window_fallback_run import replay
from poker_ai.postflop.pipeline_report import check_source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/window-fallback/own.json")
    )
    parser.add_argument(
        "--native", type=Path, default=Path("results/window-fallback/native.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/window-fallback-report")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved, data, proof = replay(root, root / args.own)
    print(json.dumps(proof, sort_keys=True))
    if (root / args.native).exists():
        from poker_ai.solver_validation.window_fallback import validate

        native = json.loads((root / args.native).read_text())
        check_source(root, native["source"])
        print(
            json.dumps(validate(native, saved, root / args.own, data), sort_keys=True)
        )
    else:
        print(
            "Native audit absent; own-only report, "
            "no completed external validation claim."
        )
    result = write_report(
        root, data, saved, root / args.output, plots=not args.no_plots
    )
    print(
        f"{result['self_profiles']} profiles; "
        f"{result['fixed_target_conditions']} fixed targets; report: {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
