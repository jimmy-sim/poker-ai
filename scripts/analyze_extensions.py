"""Reproduce both selected extensions in ignored staging, then publish reviewed data."""

import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from poker_ai.validation.five_card import source_provenance


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    source = source_provenance(
        root,
        root / "configs/opponent-modeling.json",
        entrypoints=(
            "scripts/analyze_extensions.py",
            "scripts/analyze_opponents.py",
            "scripts/analyze_bankroll.py",
            "scripts/audit_opponent_records.py",
            "scripts/render_extensions.py",
        ),
    )
    directory = root / "results/extensions"
    stage = directory / "runs" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    stage.mkdir(parents=True)
    steps = [
        ["analyze_opponents.py", "--output", str(stage / "opponents.json")],
        [
            "analyze_bankroll.py",
            "--own-profiles",
            str(stage / "own-risk-profiles.json.gz"),
            "--output",
            str(stage / "bankroll.json"),
        ],
        ["audit_opponent_records.py", "--report", str(stage / "opponents.json")],
        ["render_extensions.py", "--directory", str(stage)],
    ]
    for script, *args in steps:
        subprocess.run(
            [sys.executable, str(root / "scripts" / script), *args],
            cwd=root,
            check=True,
        )
    (stage / "manifest.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "source": source,
                "total_seconds": time.perf_counter() - started,
                "stages": [s[0] for s in steps],
                "scope": (
                    "own toy learning and conditional risk only; "
                    "no external outputs trained on"
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    for path in stage.iterdir():
        shutil.copy2(path, directory / path.name)
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/render_extensions.py"),
            "--directory",
            str(directory),
            "--update-docs-only",
        ],
        cwd=root,
        check=True,
    )
    print(f"passed: both extensions reproduced in {time.perf_counter() - started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
