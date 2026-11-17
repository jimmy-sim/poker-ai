"""Browse retained earlier-source elapsed costs; never run poker or a profiler."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from earlier_source_profile_support import direct_calls, saved_graph, write_report

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/earlier-source-profile.json"
CONFIG_SHA = "599a763e8f27e485ae8ba94ca99da1000fc2ab6874808bd296785399a7fe5d1e"


def contract(root: Path) -> dict[str, Any]:
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ArithmeticError("fixed saved-data analysis contract changed")
    config: dict[str, Any] = json.loads(raw)
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--function", type=int, choices=range(1, 6))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = contract(ROOT)
    if args.output is not None:
        result = write_report(ROOT, ROOT / args.output, config)
        print(
            f"Saved {result['frame_count']} original frames and "
            f"{result['edge_count']} edges; data-only report: {args.output}"
        )
        return 0
    stats, _ = saved_graph(ROOT, config)
    saved = direct_calls(stats)
    print(
        "Historical instrumented elapsed-stack seconds, including waits. "
        "Nested totals overlap; these are not current CPU or strength estimates."
    )
    for index, page in enumerate(saved["selected"], 1):
        row = page["frame"]
        print(
            f"{index}: {row['file']}:{row['line']} {row['qualname']}; "
            f"{row['total_calls']} calls; self {row['self_seconds']:.6f}s; "
            f"inclusive {row['cumulative_seconds']:.6f}s"
        )
    if args.function is not None:
        page = saved["selected"][args.function - 1]
        by_id = {row["id"]: row for row in saved["functions"]}
        for direction in ("incoming", "outgoing"):
            print(direction + " (all direct edges):")
            for edge in sorted(
                page[direction],
                key=lambda row: (
                    -row["cumulative_seconds"],
                    row["caller"],
                    row["callee"],
                ),
            ):
                peer = by_id[
                    edge["caller"] if direction == "incoming" else edge["callee"]
                ]
                print(
                    f"  {edge['cumulative_seconds']:.6f}s inclusive; "
                    f"{edge['total_calls']} calls; "
                    f"entry {peer['entry_index']}; "
                    f"{peer['file']}:{peer['line']} {peer['qualname']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
