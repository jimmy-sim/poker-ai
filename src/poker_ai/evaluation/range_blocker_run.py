"""Checked cached-data command with complete partial/failure retention."""

import argparse
import csv
import gzip
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

from poker_ai.evaluation.opponent_decision_run import BLOCKED, forbidden
from poker_ai.evaluation.opponent_learning_clock import atomic
from poker_ai.evaluation.range_blocker_io import (
    CONFIG,
    CONFIG_SHA,
    ENTRIES,
    FLAGS,
    FOLDER,
    IDENTITY,
    contract,
    csv_rows,
    parents,
    source_detail,
    validate_profiles,
)
from poker_ai.evaluation.range_blocker_probe import FeatureBook, analyse
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance


def run(root: Path, output: Path, started: float) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing complete/partial blocker output")
    config = contract(root)
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    source = source_provenance(root, root / CONFIG, entrypoints=ENTRIES)
    if source["dirty"] is not False:
        raise ValueError("publish clean blocker source before measurement")
    output.mkdir(parents=True)
    summaries: list[dict[str, Any]] = []
    book = FeatureBook()
    try:
        with ExitStack() as stack:
            for name in BLOCKED:
                stack.enter_context(patch(name, forbidden))
            print(
                "Validating complete parent cache; "
                "learner/reference constructors blocked...",
                flush=True,
            )
            previous = parents(root, config)
            (output / "details").mkdir()
            for parent in previous:
                deadline.check()
                detail = source_detail(root, parent)
                summary, full = analyse(parent, detail, book)
                identity = {k: parent[k] for k in IDENTITY}
                filename = f"details/{parent['coordinate']:02d}-{parent['arm']}.json.gz"
                with (output / filename).open("xb") as stream:
                    with gzip.GzipFile(
                        fileobj=stream, mode="wb", filename="", mtime=0
                    ) as archive:
                        archive.write(canonical(identity | full))
                summaries.append(
                    identity
                    | summary
                    | dict(
                        details_file=filename,
                        source_details_file=parent["details_file"],
                        source_details_sha256=parent["_detail_sha256"],
                    )
                )
                atomic(output / "catalog.json", book.record())
                atomic(
                    output / "partial.json",
                    dict(
                        status="partial",
                        profiles=summaries,
                        **{k: False for k in FLAGS},
                    ),
                )
                print(
                    f"regrouped {parent['game']}/{parent['seed']}/{parent['arm']} "
                    f"({len(summaries)}/24)",
                    flush=True,
                )
            validate_profiles(summaries, previous, config)
            parents(root, config)
        if (
            source_provenance(root, root / CONFIG, entrypoints=ENTRIES)["sha256"]
            != source["sha256"]
        ):
            raise ArithmeticError("scientific source changed during reproduction")
        atomic(output / "summary.json", dict(profiles=summaries))
        rows = csv_rows(summaries)
        with (output / "panels.csv").open("x", newline="") as stream:
            writer = csv.DictWriter(stream, sorted(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        deadline.check()
        panels = [
            w
            for p in summaries
            for r in p["responses"]
            for s in r["suffixes"]
            for w in s["panels"]
        ]
        result = dict(
            status="complete_cached_two_sided_blockers",
            config_sha256=CONFIG_SHA,
            source=source,
            source_sha256=sha(source["sha256"]),
            source_manifest_sha256=config["source_manifest_sha256"],
            profiles=24,
            responses=48,
            suffix_conditions=96,
            range_panels=192,
            group_panels=len(rows),
            profile_river_rows=config["expected_profile_river_rows"],
            suffix_river_rows=config["expected_suffix_river_rows"],
            public_boards=len(book.entries),
            maximum_source_chip_error=max(
                w["maximum_source_chip_error"] for w in panels
            ),
            maximum_unitless_error=max(w["maximum_unitless_error"] for w in panels),
            constructors_blocked=True,
            maximum_seconds=config["maximum_seconds"],
            clock_scope=config["clock_scope"],
            seconds=time.perf_counter() - started,
            environment=runtime_environment(),
            limits=(
                "Cached grouping association, not causal policy attribution, "
                "root EV, exploitability or learned improvement; "
                "dependent known games."
            ),
            outputs={
                str(p.relative_to(output)): digest(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
            **{k: False for k in FLAGS},
        )
        atomic(output / "manifest.json", result)
        deadline.check()
        return result
    except BaseException as exc:
        atomic(
            output / "failure.json",
            dict(
                status="failed_retained",
                failure=dict(type=type(exc).__name__, message=str(exc)),
                completed_profiles=len(summaries),
                seconds=time.perf_counter() - started,
                **{k: False for k in FLAGS},
            ),
        )
        raise


def main(root: Path, started: float) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    result = run(root, root / args.output, started)
    print(
        f"{result['status']}:24profiles/48responses/96suffixes/192range/960group panels"
    )
    return 0
