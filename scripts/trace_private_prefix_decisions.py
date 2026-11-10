"""Inspect own saved decisions; never construct learners or reference solvers."""

import argparse
import gzip
import itertools
import json
import math
import time
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.matched_update_lifecycle import measured
from poker_ai.evaluation.private_prefix_admission import native_journal
from poker_ai.evaluation.private_prefix_read import read
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import canonical, decode, read_archive, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.reply_diagnosis import analyse
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.private_prefix import validate
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/private-prefix-decisions.json"
CONFIG_SHA = "c8c6aadc3e16ec7e5bc6ad0bae1176d317de9ea63336dc81b4cc217451411589"
FOLDER = "results/private-prefix/decisions"


def panel(config: dict[str, Any], own: dict[str, Any]) -> list[dict[str, Any]]:
    selected = {}
    for row in own["rows"]:
        case = row["case"]
        if (
            Path(case["spot_file"]).stem != config["game"]
            or any(case[k] != config[k] for k in ("representation", "regret_rule"))
            or any(row[k] != config[k] for k in ("batch_size", "work_label", "readout"))
        ):
            continue
        seed = case["seed"]
        if type(seed) is not int or seed not in config["seeds"] or seed in selected:
            raise ArithmeticError("changed/duplicate decision seed")
        selected[seed] = row
    if sorted(selected) != config["seeds"]:
        raise ArithmeticError("all three decision seeds required")
    baselines = {r["id"]: r for r in own["baseline_rows"]}
    pairs = {(r["candidate_id"], r["baseline_kind"]): r for r in own["self_pairs"]}
    if len(baselines) != len(own["baseline_rows"]) or len(pairs) != len(
        own["self_pairs"]
    ):
        raise ArithmeticError("duplicate decision source identity")
    result = []
    for seed, role in itertools.product(config["seeds"], config["roles"]):
        row = selected[seed]
        if role != "stratified":
            row = baselines[pairs[row["id"], role]["baseline_id"]]
        result.append(dict(role=role, seed=seed, row=row))
    if len(result) != config["expected_profiles"]:
        raise ArithmeticError("complete nine-profile decision panel required")
    return result


def verify(summary: dict[str, Any], row: dict[str, Any], tolerance: float) -> None:
    """Check own trace roots and total-row accounting against audited source."""
    json.dumps(summary, allow_nan=False)
    if [r["target"] for r in summary["responses"]] != [0, 1]:
        raise ArithmeticError("both ordered responding seats required")
    roots = {
        "exact_exploitability_chips": "exact_exploitability_chips",
        "restricted_exploitability_chips": "within_partition_gain_chips",
        "extra_information_chips": "extra_information_gap_chips",
        "saved_value_player_zero_chips": "value_player_zero_chips",
    }
    errors = [abs(summary[a] - row["metrics"][b]) for a, b in roots.items()]
    for response, previous in zip(summary["responses"], row["responses"], strict=True):
        errors.extend(
            abs(response[a] - previous[b])
            for a, b in (
                ("baseline_value_chips", "baseline_value_chips"),
                ("exact_reply_value_chips", "exact_reply_value_chips"),
                ("restricted_reply_value_chips", "restricted_reply_value_chips"),
                ("within_partition_gain_chips", "within_partition_gain_chips"),
                ("extra_information_value_chips", "extra_information_gap_chips"),
            )
        )
        street = response["street_losses_chips"]
        if set(street) - {"TURN", "RIVER"}:
            raise ArithmeticError("unexpected decision street")
        errors += [
            abs(
                response["exact_gain_chips"]
                - response["exact_reply_value_chips"]
                + response["baseline_value_chips"]
            ),
            abs(
                response["within_partition_gain_chips"]
                - response["restricted_reply_value_chips"]
                + response["baseline_value_chips"]
            ),
            abs(
                response["extra_information_value_chips"]
                - response["exact_reply_value_chips"]
                + response["restricted_reply_value_chips"]
            ),
            abs(math.fsum(street.values()) - response["exact_gain_chips"]),
            abs(response["loss_sum_chips"] - response["exact_gain_chips"]),
            abs(response["accounting_error_chips"]),
        ]
        if any(v < -tolerance for v in street.values()):
            raise ArithmeticError("negative street loss")
    errors.append(
        abs(
            math.fsum(r["exact_gain_chips"] for r in summary["responses"]) / 2
            - summary["exact_exploitability_chips"]
        )
    )
    if any(not math.isfinite(e) or e > tolerance for e in errors):
        raise ArithmeticError("decision trace differs from audited roots/accounting")


def verify_details(
    summary: dict[str, Any],
    detail: dict[str, Any],
    owners: list[int],
    menus: list[int],
    tolerance: float,
) -> None:
    """Require every owned row exactly once, not just the displayed examples."""
    json.dumps(detail, allow_nan=False)
    if [r["target"] for r in detail["responses"]] != [0, 1]:
        raise ArithmeticError("complete ordered decision detail seats required")
    for response, scalar in zip(detail["responses"], summary["responses"], strict=True):
        target = response["target"]
        rows = response["infos"]
        if [r["exact_info"] for r in rows] != [
            i for i, owner in enumerate(owners) if owner == target
        ]:
            raise ArithmeticError("complete owned exact-row inventory required")
        if any(
            r["loss_chips"] < -tolerance
            or r["counterfactual_mass"] < 0
            or r["saved_reach_mass"] < 0
            or len(r["conditional_values_chips"]) != menus[r["exact_info"]]
            for r in rows
        ):
            raise ArithmeticError("invalid decision row values/support/menu")
        if (
            abs(math.fsum(r["loss_chips"] for r in rows) - scalar["exact_gain_chips"])
            > tolerance
        ):
            raise ArithmeticError("all owned decision rows differ from root gain")


def retain_partial(
    output: Path,
    summaries: list[dict[str, Any]],
    detail: dict[str, Any],
) -> None:
    """Commit each completed profile's finite details before advancing."""
    data = canonical(detail)
    path = output / f"partial-{len(summaries):02d}-details.json.gz"
    with path.open("xb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped:
            zipped.write(data)
    persist(output / "partial.json", dict(status="partial", profiles=summaries))


def policies(
    root: Path,
    path: Path,
    own: dict[str, Any],
    sources: Any,
    selected: list[dict[str, Any]],
) -> dict[str, FloatArray]:
    identifiers = {p["row"]["id"] for p in selected}
    found = {}
    old = sources.parent.archived
    archives: tuple[
        tuple[Path, dict[str, Any], Callable[[dict[str, Any]], ScoringContext]], ...
    ] = (
        (path, own, lambda r: sources.context(r["path_index"])),
        (old.own_path, old.own, lambda r: old.data.base.context(r["case"])),
    )
    for source_path, saved, context in archives:
        for row, blob in read_archive(
            source_path.parent / saved["details_file"],
            saved["details_sha256"],
            saved["rows"],
        ):
            if row["id"] not in identifiers:
                continue
            if row["id"] in found:
                raise ArithmeticError("duplicate saved decision policy")
            scoring = context(row)
            found[row["id"]] = unpack_policy(
                scoring.partition, decode(blob, scoring, row)["policy"]
            )
    if set(found) != identifiers:
        raise ArithmeticError("complete saved decision policy archive required")
    return found


def run(root: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain complete/partial decision output")
    started = time.perf_counter()
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("fixed decision protocol changed")
    config = json.loads((root / CONFIG).read_text())
    path = root / config["own"]
    if digest(path) != config["own_sha256"]:
        raise ArithmeticError("published own decision input changed")

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("decision diagnosis constructed learner/reference")

    print(
        "Replaying saved evidence; learner/reference constructors blocked...",
        flush=True,
    )
    with ExitStack() as stack:
        for name in (
            "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
            "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            "poker_ai.solver_validation.reference.Reference.__init__",
        ):
            stack.enter_context(patch(name, forbidden))
        own, sources = read(root, path, Deadline(900))
        native_path = root / config["native"]
        native = json.loads(native_path.read_text())
        check_source(root, native["source"])
        native_journal(native_path, native)
        measured(root, native_path, "real_native")
        validate(native, own, path)
        if own["source_sha256"] != config["model_source_sha256"]:
            raise ArithmeticError("frozen decision model source changed")
        provenance = source_provenance(
            root,
            root / CONFIG,
            entrypoints=("scripts/trace_private_prefix_decisions.py",),
        )
        selected = panel(config, own)
        saved = policies(root, path, own, sources, selected)
        output.mkdir(parents=True, exist_ok=False)
        summaries, details = [], []
        for record in selected:
            row = record["row"]
            scoring = sources.context(
                next(
                    r["path_index"]
                    for r in own["rows"]
                    if r["case"]["seed"] == record["seed"]
                    and r["case"]["representation"] == config["representation"]
                    and Path(r["case"]["spot_file"]).stem == config["game"]
                    and r["case"]["regret_rule"] == config["regret_rule"]
                    and r["batch_size"] == config["batch_size"]
                )
            )
            policy = saved[row["id"]]
            fingerprint = array_sha(policy)
            if fingerprint != row["receipt"]["policy_sha256"]:
                raise ArithmeticError("saved decision policy fingerprint changed")
            expanded = scoring.expand(policy)
            before = array_sha(expanded)
            summary, detail = analyse(
                scoring.exact,
                scoring.partition,
                expanded,
                top=config["top_groups"],
                examples=config["examples_per_group"],
                tolerance=config["tolerance_chips"],
            )
            verify(summary, row, config["tolerance_chips"])
            verify_details(
                summary,
                detail,
                [int(o) for o in scoring.exact.owners],
                [len(a) for a in scoring.exact.actions],
                config["tolerance_chips"],
            )
            if array_sha(policy) != fingerprint or array_sha(expanded) != before:
                raise ArithmeticError("decision analysis mutated saved policy")
            identity = dict(
                seed=record["seed"],
                role=record["role"],
                source_id=row["id"],
                policy_sha256=fingerprint,
            )
            summaries.append(dict(**identity, **summary))
            details.append(dict(**identity, **detail))
            retain_partial(output, summaries, details[-1])
            print(f"traced {record['seed']}/{record['role']}", flush=True)
    if len(summaries) != 9 or sum(len(s["responses"]) for s in summaries) != 18:
        raise ArithmeticError("complete nine/eighteen decision inventory required")
    with (output / "details.json.gz").open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped:
            zipped.write(canonical(dict(profiles=details)))
    persist(output / "summary.json", dict(profiles=summaries))
    persist(
        output / "manifest.json",
        dict(
            status="complete_saved_decision_diagnosis",
            config_sha256=CONFIG_SHA,
            source=provenance,
            source_sha256=sha(provenance["sha256"]),
            own_sha256=digest(path),
            native_sha256=digest(native_path),
            model_source_sha256=config["model_source_sha256"],
            outputs={p.name: digest(p) for p in sorted(output.iterdir())},
            environment=runtime_environment(),
            seconds=time.perf_counter() - started,
            profiles=9,
            responses=18,
            owned_exact_rows=sum(
                len(r["infos"]) for p in details for r in p["responses"]
            ),
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            new_agent_default=False,
            fresh_global_admission=False,
            limits=config["limits"],
        ),
    )
    print("Completed nine profiles/eighteen responses; no training.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run(root, root / args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
