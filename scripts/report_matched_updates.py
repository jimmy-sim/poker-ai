"""Replay real matched-update archives and optionally regenerate paired tables."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.matched_update_replay import replay_real
from poker_ai.evaluation.matched_update_report import write_report
from poker_ai.evaluation.matched_update_run import read_saved
from poker_ai.postflop.river_study import Deadline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--own", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    own, sources = read_saved(root, root / args.own)
    proof = replay_real(root / args.own, own, sources, Deadline(900))
    if args.output is not None:
        write_report(own, root / args.output)
    print(json.dumps(proof, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
