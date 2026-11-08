"""Fixed saved-policy substitutions; no training or native strategy inputs."""

import gzip
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_protocol import CONTROLS, build_representation_control
from poker_ai.postflop.range_reply import check_source, compare, load_inputs
from poker_ai.postflop.range_reply import replay as previous_replay
from poker_ai.postflop.range_reply_report import checked_audit
from poker_ai.postflop.reply_trace import response_profile
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-frozen-policy-swaps-v1"
DETAIL_FORMAT = "poker-ai-frozen-policy-swap-profiles-v1"
CELL = ("spot_file", "representation")
HYBRID = (*CELL, "seed", "combination")
CROSS = (*CELL, "first", "second")
ENTRYPOINTS = (
    "scripts/study_policy_swaps.py",
    "scripts/audit_policy_swaps.py",
    "scripts/report_policy_swaps.py",
    "scripts/inspect_policy_swap.py",
)


def labels(config: dict[str, Any]) -> list[str]:
    return ["full"] + [str(s) for s in config["seeds"]]


def validate_config(config: dict[str, Any]) -> None:
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != 1
        or config["representations"] != CONTROLS
        or config["street_combinations"] != ["FF", "SF", "FS", "SS"]
        or not config["spot_files"]
        or len(set(config["spot_files"])) != len(config["spot_files"])
        or not config["seeds"]
        or config["seeds"] != sorted(set(config["seeds"]))
        or any(type(s) is not int or s < 1 for s in config["seeds"])
        or len(config["inputs_sha256"]) != 4
        or not {
            config[k] for k in ("previous_config", "previous_report", "previous_audit")
        }.issubset(config["inputs_sha256"])
        or type(config["maximum_seconds"]) is not int
        or config["maximum_seconds"] < 1
        or type(config["tolerance_chips"]) not in (int, float)
        or not math.isfinite(config["tolerance_chips"])
        or not 0 < config["tolerance_chips"] <= 1e-9
        or config["tie_rule"]
        != "first legal maximizer, no approximate tie substitution"
    ):
        raise ValueError("invalid fixed policy-swap config")


def check_inputs(root: Path, config: dict[str, Any]) -> None:
    validate_config(config)
    if any(digest(root / name) != sha for name, sha in config["inputs_sha256"].items()):
        raise ArithmeticError("policy-swap prerequisite changed")


def load_previous(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    check_inputs(root, config)
    prior, _, _ = previous_replay(root, root / config["previous_report"])
    if json.loads((root / config["previous_config"]).read_text()) != prior["config"]:
        raise ArithmeticError("previous diagnosis config changed")
    bundle = str(Path(config["previous_report"]).parent / prior["details_file"])
    if config["inputs_sha256"].get(bundle) != prior["details_sha256"]:
        raise ArithmeticError("previous reply details not pinned")
    audit = json.loads((root / config["previous_audit"]).read_text())
    checked_audit(root / config["previous_report"], prior, audit)
    check_source(root, audit["source"])
    if (
        prior["config"]["representations"] != config["representations"]
        or prior["config"]["spot_files"] != config["spot_files"]
        or prior["config"]["sampled_seeds"] != config["seeds"]
    ):
        raise ArithmeticError("policy-swap selection changed")
    original, policies = load_inputs(root, prior["config"])
    return original, policies, prior["cases"]


def value(tree: MatrixTree, policy: FloatArray) -> float:
    tree.validate_policy(policy)
    return float(tree.values(tree.edges(policy))[0])


def street_mask(
    exact: MatrixTree, abstract: MatrixTree
) -> np.ndarray[Any, np.dtype[np.bool_]]:
    """Street is constant in each legal information group; never use hidden worlds."""
    names = []
    for node in exact.source.representatives:
        dealer = exact.source.states[node].dealer
        if dealer is None:
            raise ValueError("decision has no observation")
        names.append(dealer.street.name)
    if not set(names).issubset({"TURN", "RIVER"}):
        raise ValueError("requires turn-river game")
    turn = np.array([n == "TURN" for n in names])
    for group in range(len(abstract.keys)):
        if len(set(turn[abstract.exact_to_abstract == group])) != 1:
            raise ArithmeticError("street depends on hidden state inside a group")
    return turn


def project(exact: MatrixTree, abstract: MatrixTree, policy: FloatArray) -> FloatArray:
    exact.validate_policy(policy)
    first = np.unique(abstract.exact_to_abstract, return_index=True)[1]
    limited = policy[first]
    if not np.array_equal(exact.dense_exact(abstract.exact_policy(limited)), policy):
        raise ArithmeticError("policy substitution violates information groups")
    return limited


def hybrid_policy(
    exact: MatrixTree,
    abstract: MatrixTree,
    full: FloatArray,
    sampled: FloatArray,
    combination: str,
) -> FloatArray:
    if combination not in ("FF", "SF", "FS", "SS"):
        raise ValueError("invalid street substitution")
    project(exact, abstract, full)
    project(exact, abstract, sampled)
    turn = street_mask(exact, abstract)
    use_sampled = np.where(turn, combination[0] == "S", combination[1] == "S")
    mixed = np.where(use_sampled[:, None], sampled, full)
    project(exact, abstract, mixed)
    return mixed


def seat_policy(exact: MatrixTree, first: FloatArray, second: FloatArray) -> FloatArray:
    exact.validate_policy(first)
    exact.validate_policy(second)
    return np.where((exact.owners == 0)[:, None], first, second)


def response_roots(
    exact: MatrixTree, abstract: MatrixTree, baseline: FloatArray, tolerance: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    limited = project(exact, abstract, baseline)
    saved = value(exact, baseline)
    rows, profiles = [], []
    for target in (0, 1):
        exact_reply = response_profile(exact, baseline, target)
        restricted = exact.dense_exact(
            abstract.exact_policy(response_profile(abstract, limited, target))
        )
        sign = 1 if target == 0 else -1
        b = sign * value(exact, exact_reply)
        r = sign * value(exact, restricted)
        if b < r - tolerance or r < sign * saved - tolerance:
            raise ArithmeticError("invalid constrained response ordering")
        rows.append(
            {
                "target": target,
                "baseline_value_chips": sign * saved,
                "exact_reply_value_chips": b,
                "restricted_reply_value_chips": r,
                "within_partition_gain_chips": r - sign * saved,
                "extra_information_chips": b - r,
            }
        )
        profiles.append(
            {
                "target": target,
                "exact_reply_profile": exact.exact_policy(exact_reply),
                "restricted_reply_profile": exact.exact_policy(restricted),
            }
        )
    return rows, profiles


def effects(gaps: dict[str, float]) -> dict[str, float]:
    ff, sf, fs, ss = (gaps[k] for k in ("FF", "SF", "FS", "SS"))
    result = {
        "gap_change_chips": ss - ff,
        "turn_effect_chips": ((sf - ff) + (ss - fs)) / 2,
        "river_effect_chips": ((fs - ff) + (ss - sf)) / 2,
        "interaction_chips": ss - sf - fs + ff,
    }
    if (
        abs(
            result["gap_change_chips"]
            - result["turn_effect_chips"]
            - result["river_effect_chips"]
        )
        > 1e-9
    ):
        raise ArithmeticError("street attribution does not add")
    return result


def compute(
    root: Path, config: dict[str, Any], deadline: Deadline | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    original, records, previous = load_previous(root, config)
    model = CardAbstraction.load(root / original["config"]["model"])
    crossed, targets, hybrids, attribution, details = [], [], [], [], []
    tolerance = config["tolerance_chips"]
    for filename in config["spot_files"]:
        if deadline is not None:
            deadline.check()
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        for name in config["representations"]:
            abstract = build_representation_control(source, name, model)
            selected = [
                r
                for r in records
                if r["spot_file"] == filename and r["representation"] == name
            ]
            policies = {
                "full"
                if r["training"] == "full"
                else str(r["seed"]): exact.dense_exact(
                    tuple(tuple(v) for v in r["policy"])
                )
                for r in selected
            }
            if set(policies) != set(labels(config)):
                raise ArithmeticError("incomplete saved policy labels")
            contexts = {r["range_context_sha256"] for r in selected}
            if len(contexts) != 1:
                raise ArithmeticError("different representation contexts")
            identity = {
                "spot_file": filename,
                "representation": name,
                "range_context_sha256": contexts.pop(),
                "pot": source.spot.pot,
            }
            roots = {}
            for seed in config["seeds"]:
                for combination in config["street_combinations"]:
                    if deadline is not None:
                        deadline.check()
                    policy = hybrid_policy(
                        exact,
                        abstract,
                        policies["full"],
                        policies[str(seed)],
                        combination,
                    )
                    responses, profiles = response_roots(
                        exact, abstract, policy, tolerance
                    )
                    key = {**identity, "seed": seed, "combination": combination}
                    hybrids.append({**key, "responses": responses})
                    details.append(
                        {
                            **key,
                            "baseline_policy": exact.exact_policy(policy),
                            "responses": profiles,
                        }
                    )
                    roots[seed, combination] = responses
                    if combination in ("FF", "SS"):
                        old = next(
                            c
                            for c in previous
                            if c["spot_file"] == filename
                            and c["representation"] == name
                            and c["training"]
                            == ("full" if combination == "FF" else "sampled")
                            and c["seed"] == (None if combination == "FF" else seed)
                        )
                        for target, response in enumerate(responses):
                            for field in (
                                "exact_reply_value_chips",
                                "restricted_reply_value_chips",
                            ):
                                if (
                                    abs(
                                        response[field]
                                        - old["responses"][target][field]
                                    )
                                    > tolerance
                                ):
                                    raise ArithmeticError(
                                        "prior full/sampled response diagonal changed"
                                    )
                    if name == "exact" and any(
                        abs(r["extra_information_chips"]) > tolerance for r in responses
                    ):
                        raise ArithmeticError(
                            "exact partition acquired information premium"
                        )
                for target in (0, 1):
                    attribution.append(
                        {
                            **identity,
                            "seed": seed,
                            "target": target,
                            **effects(
                                {
                                    c: roots[seed, c][target]["extra_information_chips"]
                                    for c in config["street_combinations"]
                                }
                            ),
                        }
                    )
            lookup = {
                "full": roots[config["seeds"][0], "FF"],
                **{str(s): roots[s, "SS"] for s in config["seeds"]},
            }
            values = {
                (a, b): value(exact, seat_policy(exact, policies[a], policies[b]))
                for a in labels(config)
                for b in labels(config)
            }
            for first in labels(config):
                for second in labels(config):
                    if deadline is not None:
                        deadline.check()
                    ev = values[first, second]
                    epsilon = (
                        lookup[second][0]["exact_reply_value_chips"]
                        + lookup[first][1]["exact_reply_value_chips"]
                    ) / 2
                    crossed.append(
                        {
                            **identity,
                            "first": first,
                            "second": second,
                            "value_player_zero_chips": ev,
                            "seat_balanced_first_chips": (ev - values[second, first])
                            / 2,
                            "exploitability_chips": epsilon,
                        }
                    )
                    total_gain = 0.0
                    for target, opponent in ((0, second), (1, first)):
                        base = (1 if target == 0 else -1) * ev
                        r = lookup[opponent][target]
                        within = r["restricted_reply_value_chips"] - base
                        extra = r["extra_information_chips"]
                        if within < -tolerance:
                            raise ArithmeticError(
                                "crossed restricted improvement negative"
                            )
                        targets.append(
                            {
                                **identity,
                                "first": first,
                                "second": second,
                                "target": target,
                                "opponent": opponent,
                                "baseline_value_chips": base,
                                "within_partition_gain_chips": within,
                                "extra_information_chips": extra,
                                "exact_gain_chips": r["exact_reply_value_chips"] - base,
                            }
                        )
                        total_gain += within + extra
                    if abs(total_gain / 2 - epsilon) > tolerance:
                        raise ArithmeticError("crossed NashConv identity failed")
                    if first == second:
                        old = next(
                            c
                            for c in previous
                            if c["spot_file"] == filename
                            and c["representation"] == name
                            and c["training"]
                            == ("full" if first == "full" else "sampled")
                            and c["seed"] == (None if first == "full" else int(first))
                        )
                        if (
                            abs(epsilon - old["exact_exploitability_chips"]) > tolerance
                            or abs(ev - old["saved_value_player_zero_chips"])
                            > tolerance
                        ):
                            raise ArithmeticError("prior self-profile diagonal changed")
            print(f"policy swaps: {source.spot.name}/{name}", flush=True)
    return {
        "crossplay": crossed,
        "cross_targets": targets,
        "hybrids": hybrids,
        "effects": attribution,
    }, details


def run(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text())
    validate_config(config)
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    sidecar = output.with_name(output.stem + "-profiles.json.gz")
    if output.exists() or sidecar.exists():
        raise FileExistsError("retain prior policy-swap evidence")
    source = source_provenance(root, config_path, entrypoints=ENTRYPOINTS)
    if source["dirty"] is not False:
        raise ValueError("publish checked code first; use clean source")
    timestamp = datetime.now(UTC).isoformat()
    result, details = compute(root, config, deadline)
    deadline.check()
    check_source(root, source)
    check_inputs(root, config)
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(
        gzip.compress(
            json.dumps(
                {"format": DETAIL_FORMAT, "hybrids": details}, allow_nan=False
            ).encode(),
            mtime=0,
        )
    )
    elapsed = time.perf_counter() - started
    report = {
        "format": FORMAT,
        "status": "completed"
        if elapsed <= config["maximum_seconds"]
        else "over_budget",
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "started_at_utc": timestamp,
        "seconds": elapsed,
        "profiles_file": sidecar.name,
        "profiles_sha256": digest(sidecar),
        **result,
        "training_performed": False,
        "fresh_global_admission": False,
    }
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return report


def grids(config: dict[str, Any]) -> tuple[set[tuple[Any, ...]], set[tuple[Any, ...]]]:
    cells = [(p, e) for p in config["spot_files"] for e in config["representations"]]
    cross = {(*c, a, b) for c in cells for a in labels(config) for b in labels(config)}
    hybrid = {
        (*c, s, k)
        for c in cells
        for s in config["seeds"]
        for k in config["street_combinations"]
    }
    return cross, hybrid


def checked(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    validate_config(report["config"])
    json.dumps(report, allow_nan=False)
    if (
        report["format"] != FORMAT
        or report["status"] != "completed"
        or report["training_performed"] is not False
        or report["fresh_global_admission"] is not False
        or not 0 <= report["seconds"] <= report["config"]["maximum_seconds"]
    ):
        raise ArithmeticError("partial/changed policy-swap stage")
    sidecar = path.parent / report["profiles_file"]
    if digest(sidecar) != report["profiles_sha256"]:
        raise ArithmeticError("own hybrid profiles changed")
    payload = json.loads(gzip.decompress(sidecar.read_bytes()))
    json.dumps(payload, allow_nan=False)
    cross, hybrid = grids(report["config"])
    for rows, fields, expected in (
        (report["crossplay"], CROSS, cross),
        (report["hybrids"], HYBRID, hybrid),
        (payload["hybrids"], HYBRID, hybrid),
        (
            report["cross_targets"],
            (*CROSS, "target"),
            {(*c, t) for c in cross for t in (0, 1)},
        ),
        (
            report["effects"],
            (*CELL, "seed", "target"),
            {
                (p, e, s, t)
                for p in report["config"]["spot_files"]
                for e in report["config"]["representations"]
                for s in report["config"]["seeds"]
                for t in (0, 1)
            },
        ),
    ):
        ids = [tuple(r[k] for k in fields) for r in rows]
        if len(ids) != len(set(ids)) or set(ids) != expected:
            raise ArithmeticError("incomplete/duplicate policy-swap grid")
        if any(
            type(r[k]) is not int
            for r in rows
            for k in fields
            if k in ("seed", "target")
        ):
            raise ArithmeticError("invalid policy-swap numeric identity")
    if payload["format"] != DETAIL_FORMAT:
        raise ArithmeticError("wrong own hybrid profile format")
    return report, payload["hybrids"]


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report, details = checked(path)
    check_source(root, report["source"])
    result, profiles = compute(root, report["config"])
    maximum = max(
        compare(result, {k: report[k] for k in result}), compare(profiles, details)
    )
    if maximum > report["config"]["tolerance_chips"]:
        raise ArithmeticError("policy-swap numerical replay changed")
    check_source(root, report["source"])
    check_inputs(root, report["config"])
    return report, details, maximum
