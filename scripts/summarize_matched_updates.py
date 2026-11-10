"""Reproduce all two-axis tables/heatmaps from verified published own archives."""

import argparse
import json
import time
from pathlib import Path

from poker_ai.evaluation.matched_update_data import CONFIG, load
from poker_ai.evaluation.matched_update_presentation import write
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/matched-update-summary")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if (root / args.output).exists() or (root / args.output).is_symlink():
        parser.error("retain existing report destination; choose a new --output")
    started = time.perf_counter()
    source = source_provenance(
        root,
        root / CONFIG,
        entrypoints=(
            "scripts/summarize_matched_updates.py",
            "scripts/inspect_matched_updates.py",
        ),
    )
    data = load(root, lambda line: print(line, flush=True))
    files = write(data, root / args.output, no_plots=args.no_plots)
    manifest = dict(
        status="read_only_matched_update_presentation",
        source=source,
        source_sha256=sha(source["sha256"]),
        outputs=files,
        environment=runtime_environment(),
        seconds=time.perf_counter() - started,
        training_performed=False,
        reference_constructed=False,
    )
    (root / args.output / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    print(
        json.dumps(
            dict(
                status=manifest["status"], files=len(files), seconds=manifest["seconds"]
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
