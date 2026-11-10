"""Record exact-source checks, run/replay tiny proof, or check real study admission."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation import matched_update_admission as admission
from poker_ai.evaluation import matched_update_code_gate as gate
from poker_ai.evaluation import matched_update_software as software
from poker_ai.postflop.learning_run import persist


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/matched-update-software/own.json"),
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--replay", type=Path)
    actions.add_argument("--record-checks", nargs=2, type=Path, metavar=("CI", "LOCAL"))
    actions.add_argument("--admit", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.replay is not None:
        result = software.read(root, root / args.replay)[2]
    elif args.record_checks is not None:
        if (root / args.output).exists():
            raise FileExistsError("retain observed code checks")
        ci, local = [json.loads(p.read_text()) for p in args.record_checks]
        result = gate.record(root, ci, local)
        persist(root / args.output, result)
    elif args.admit:
        if (root / args.output).exists():
            raise FileExistsError("retain published admission")
        result = admission.record(root)
        persist(root / args.output, result)
    else:
        saved = software.run(root, root / args.output)
        result = dict(
            status=saved["status"], seconds=saved["seconds"], replay=saved["replay"]
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
