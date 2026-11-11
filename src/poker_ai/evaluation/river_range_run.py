"""Complete fixed-suffix local range-weight command; never learn or deploy."""

import argparse
import csv
import gzip
import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_decision_inputs import checked, profiles
from poker_ai.evaluation.opponent_decision_inputs import contract as old_contract
from poker_ai.evaluation.opponent_decision_run import BLOCKED, forbidden
from poker_ai.evaluation.opponent_learning_clock import atomic
from poker_ai.evaluation.river_range_case import Inventory, analyse_profile
from poker_ai.evaluation.river_range_io import (
    CONFIG,
    CONFIG_SHA,
    ENTRIES,
    FOLDER,
    contract,
    prior,
    validate_profiles,
    validate_suffix,
)
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance


def csv_rows(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for p in profiles:
        for r in p["responses"]:
            for s in r["suffixes"]:
                for panel in s["panels"]:
                    for control, metrics in panel["group_controls"].items():
                        rows.append(
                            dict(
                                coordinate=p["coordinate"],
                                game=p["game"],
                                seed=p["seed"],
                                arm=p["arm"],
                                target=r["target"],
                                suffix=s["suffix"],
                                range_weights=panel["range_weights"],
                                group_control=control,
                                **metrics,
                            )
                        )
    if len(rows) != 384:
        raise ArithmeticError(
            "192local panels times2group controls must give384CSV rows"
        )
    return rows


def run(root: Path, output: Path, started: float) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing complete/partial local range output")
    config = contract(root)
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    provenance = source_provenance(root, root / CONFIG, entrypoints=ENTRIES)
    if provenance["dirty"] is not False:
        raise ValueError("publish clean local range source before reproduction")
    output.mkdir(parents=True)
    summaries: list[dict[str, Any]] = []
    cache: dict[tuple[str, int], Inventory] = {}
    try:
        with ExitStack() as stack:
            for name in BLOCKED:
                stack.enter_context(patch(name, forbidden))
            print(
                "Replaying bound archives; learner/reference constructors blocked...",
                flush=True,
            )
            previous = prior(root, config)
            old_config = old_contract(root)
            own = checked(root, old_config, deadline)
            selected = profiles(root, old_config, own, deadline)
            old_by_id = {r["source_id"]: r for r in previous}
            (output / "details").mkdir()
            for profile in selected:
                deadline.check()
                before = (
                    tree_digest(profile.contexts.fine),
                    tree_digest(profile.contexts.coarse),
                    array_sha(profile.policy),
                    array_sha(profile.fine_policy),
                )
                old = old_by_id[profile.row["id"]]
                with gzip.open(
                    root / config["decision_folder"] / old["details_file"], "rt"
                ) as stream:
                    old_detail = json.load(stream)
                summary, detail = analyse_profile(
                    profile, old, old_detail, config, cache
                )
                for response, full in zip(
                    summary["responses"], detail["responses"], strict=True
                ):
                    if response["target"] != full["target"]:
                        raise ArithmeticError("changed local target")
                    for s, d in zip(
                        response["suffixes"], full["suffixes"], strict=True
                    ):
                        validate_suffix(s, d, len(full["declared_opponent_range"]))
                if before != (
                    tree_digest(profile.contexts.fine),
                    tree_digest(profile.contexts.coarse),
                    array_sha(profile.policy),
                    array_sha(profile.fine_policy),
                ):
                    raise ArithmeticError(
                        "local range calculation mutated source game/policy"
                    )
                filename = f"details/{profile.coordinate:02d}-{profile.arm}.json.gz"
                with (output / filename).open("xb") as raw:
                    with gzip.GzipFile(
                        fileobj=raw, mode="wb", filename="", mtime=0
                    ) as stream:
                        stream.write(canonical(dict(**profile.identity(), **detail)))
                summaries.append(
                    dict(**profile.identity(), **summary, details_file=filename)
                )
                atomic(
                    output / "partial.json",
                    dict(
                        status="partial",
                        profiles=summaries,
                        training_performed=False,
                        reference_constructed=False,
                    ),
                )
                print(
                    f"reweighted {profile.game}/{profile.seed}/{profile.arm} "
                    f"({len(summaries)}/24)",
                    flush=True,
                )
            validate_profiles(summaries, config)
            prior(root, config)
        if (
            source_provenance(root, root / CONFIG, entrypoints=ENTRIES)["sha256"]
            != provenance["sha256"]
        ):
            raise ArithmeticError("range diagnostic source changed during reproduction")
        atomic(output / "summary.json", dict(profiles=summaries))
        rows = csv_rows(summaries)
        with (output / "panels.csv").open("x", newline="") as stream:
            writer = csv.DictWriter(stream, sorted(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        deadline.check()
        suffixes = [s for p in summaries for r in p["responses"] for s in r["suffixes"]]
        manifest = dict(
            status="complete_local_river_range_reweighting",
            config_sha256=CONFIG_SHA,
            source=provenance,
            source_sha256=sha(provenance["sha256"]),
            continuation_manifest_sha256=config["continuation_manifest_sha256"],
            profiles=24,
            responses=48,
            suffix_conditions=96,
            local_panels=192,
            group_control_csv_rows=len(rows),
            profile_river_rows=sum(
                len(r["suffixes"][0]["river_info_ids"])
                for p in summaries
                for r in p["responses"]
            ),
            suffix_river_rows=sum(len(s["river_info_ids"]) for s in suffixes),
            maximum_source_chip_error=max(
                s["maximum_source_chip_error"] for s in suffixes
            ),
            maximum_unitless_error=max(s["maximum_unitless_error"] for s in suffixes),
            maximum_seconds=config["maximum_seconds"],
            clock_scope=config["clock_scope"],
            seconds=time.perf_counter() - started,
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            new_independent_audit=False,
            feature_deployed=False,
            new_agent_default=False,
            fresh_global_admission=False,
            environment=runtime_environment(),
            limits=(
                "Local reweighting of fixed own continuations against saved opponents; "
                "not a global strategy/root EV/retraining gain/new native audit. "
                "Dependent known-game records, not independent samples."
            ),
            outputs={
                str(p.relative_to(output)): digest(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        )
        atomic(output / "manifest.json", manifest)
        deadline.check()
        return manifest
    except BaseException as exc:
        atomic(
            output / "failure.json",
            dict(
                status="failed_retained",
                failure=dict(type=type(exc).__name__, message=str(exc)),
                completed_profiles=len(summaries),
                seconds=time.perf_counter() - started,
                training_performed=False,
                reference_constructed=False,
                feature_deployed=False,
                new_agent_default=False,
                fresh_global_admission=False,
            ),
        )
        raise


def main(root: Path, started: float) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    result = run(root, root / args.output, started)
    print(f"{result['status']}:24profiles/48responses/96suffixes/192LOCALpanels")
    return 0
