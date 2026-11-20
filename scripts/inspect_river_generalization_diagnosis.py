"""Print a ranked saved-policy medium/dry decision from the published diagnosis."""

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rank", type=int, default=1, help="one-based rank, 1 to 10")
    args = parser.parse_args()
    path = (
        Path(__file__).resolve().parents[1]
        / "results/river-generalization/diagnosis/report.json"
    )
    report: dict[str, Any] = json.loads(path.read_text())
    rows: list[dict[str, Any]] = report["top_final_candidate_exact_rows"]
    if report["status"] != "complete_read_only_diagnosis" or not 1 <= args.rank <= len(
        rows
    ):
        parser.error("rank outside the completed published diagnosis")
    print(json.dumps(rows[args.rank - 1], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
