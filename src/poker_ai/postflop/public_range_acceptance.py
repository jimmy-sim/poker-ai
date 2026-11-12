"""Pure future metric rules, NOT source authentication or experiment admission."""

import math
import statistics
from typing import Any

from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.public_range_definition import CANDIDATE, validate


def number(row: dict[str, Any], key: str, maximum: float = math.inf) -> float:
    x = row[key]
    if type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= maximum:
        raise ValueError("invalid nonnegative finite metric: " + key)
    return float(x)


def integer(row: dict[str, Any], key: str, minimum: int = 0) -> int:
    x = row[key]
    if type(x) is not int or x < minimum:
        raise ValueError("invalid integer metric: " + key)
    return x


def grid(
    rows: list[dict[str, Any]], fields: tuple[str, ...], expected: set[tuple[Any, ...]]
) -> bool:
    for row in rows:
        for k in fields:
            if k in ("iteration", "seed", "work_checkpoint"):
                integer(row, k, 1)
            elif type(row[k]) is not str or not row[k]:
                raise ValueError("invalid identity: " + k)
    ids = [tuple(r[k] for k in fields) for r in rows]
    return len(ids) == len(set(ids)) and set(ids) == expected


def binding(rows: list[dict[str, Any]], c: dict[str, Any]) -> bool:
    return all(
        r.get("context_sha256") == c["contexts"].get(r["spot_file"]) for r in rows
    )


def result(
    stage: str, checks: dict[str, bool], config: dict[str, Any], **extra: Any
) -> dict[str, Any]:
    return dict(
        stage=stage,
        contract_sha256=sha(config),
        thresholds_passed=all(checks.values()),
        checks=checks,
        actual_admission=False,
        fresh_global_admission=False,
        scope=(
            "metric arithmetic only; authenticated source/policy/work/audit "
            "and published admission remain required"
        ),
        **extra,
    )


def assess_full(
    rows: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    audit: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    elapsed_seconds: float,
    audit_seconds: float,
) -> dict[str, Any]:
    """Check ALL72 hypothetical policies and12 layouts; never train/load strategies."""
    validate(config)
    f, reps, spots = config["full"], config["representations"], config["spot_files"]
    expected = {(s, r, t) for s in spots for r in reps for t in f["checkpoints"]}
    fields = ("spot_file", "representation", "iteration")
    complete = (
        grid(rows, fields, expected)
        and grid(audit, fields, expected)
        and grid(partitions, fields[:2], {(s, r) for s in spots for r in reps})
    )
    layouts = {(d["spot_file"], d["representation"]): d for d in partitions}
    recall = menus = work = True
    for d in partitions:
        integer(d, "information_sets", 1)
        nodes = integer(d, "tree_nodes", 1)
        if nodes > f["maximum_tree_nodes"]:
            raise ValueError("tree exceeds frozen node cap")
        recall = recall and integer(d, "recall_violations") == 0
        if type(d["menus_compatible"]) is not bool:
            raise ValueError("menu compatibility must be boolean")
        menus = menus and d["menus_compatible"]
    for row in rows:
        number(row, "exploitability_pot")
        number(row, "coverage", 1)
        layout = layouts.get((row["spot_file"], row["representation"]))
        work = work and integer(row, "total_node_work") == (
            2 * row["iteration"] * layout["tree_nodes"] if layout else -1
        )
    tol = f["limits"]["independent_tolerance_chips"]
    audit_ok = all(
        number(a, k) <= tol
        for a in audit
        for k in ("value_error_chips", "exploitability_error_chips")
    )
    by = {
        (r["spot_file"], r["representation"]): r
        for r in rows
        if r["iteration"] == f["checkpoints"][-1]
    }
    accuracy = compression = coverage = True
    for spot in spots:
        if any((spot, r) not in by or (spot, r) not in layouts for r in reps):
            accuracy = compression = coverage = False
            continue
        lim = f["limits"]
        exact = by[spot, "exact"]["exploitability_pot"]
        candidate = by[spot, CANDIDATE]["exploitability_pot"]
        accuracy = (
            accuracy
            and exact <= lim["exact_full_exploitability_pot"]
            and candidate - exact <= lim["candidate_full_excess_pot"]
        )
        compression = (
            compression
            and layouts[spot, CANDIDATE]["information_sets"]
            <= lim["candidate_information_sets_relative_to_public_b8"]
            * layouts[spot, "public_b8"]["information_sets"]
        )
        coverage = coverage and all(
            by[spot, r]["coverage"] >= lim["minimum_uniform_reach_average_coverage"]
            for r in reps
        )
    checks = dict(
        complete=complete,
        context_binding=binding(rows + partitions + audit, config),
        work=work,
        recall=recall,
        menus=menus,
        accuracy=accuracy,
        compression=compression,
        coverage=coverage,
        audit=audit_ok,
        own_clock=number(dict(seconds=elapsed_seconds), "seconds")
        <= f["maximum_seconds"],
        audit_clock=number(dict(seconds=audit_seconds), "seconds")
        <= f["maximum_audit_seconds"],
    )
    return result("full", checks, config, partitions=partitions)


def assess_sampled(
    rows: list[dict[str, Any]],
    audit: list[dict[str, Any]],
    full: dict[str, Any],
    config: dict[str, Any],
    *,
    elapsed_seconds: float,
    audit_seconds: float,
) -> dict[str, Any]:
    """Check all324 hypothetical readouts; primary accuracy is LINEAR only."""
    validate(config)
    s, reps, spots = config["sampled"], config["representations"], config["spot_files"]
    expected = {
        (p, r, seed, w, b)
        for p in spots
        for r in reps
        for seed in s["seeds"]
        for w in s["node_work_checkpoints"]
        for b in s["readouts"]
    }
    fields = ("spot_file", "representation", "seed", "work_checkpoint", "readout")
    complete = grid(rows, fields, expected) and grid(audit, fields, expected)
    layouts = {
        (d["spot_file"], d["representation"]): d for d in full.get("partitions", [])
    }
    prior = (
        full.get("stage") == "full"
        and full.get("contract_sha256") == sha(config)
        and full.get("thresholds_passed") is True
    )
    methods = work = recall = geometry = consistent = True
    origins: dict[tuple[Any, ...], tuple[int, ...]] = {}
    for row in rows:
        number(row, "exploitability_pot")
        number(row, "coverage", 1)
        total, before, last, warm, nodes = (
            integer(row, k, 1)
            for k in (
                "total_node_work",
                "previous_node_work",
                "last_iteration_work",
                "initialization_work",
                "tree_nodes",
            )
        )
        d = layouts.get((row["spot_file"], row["representation"]))
        geometry = (
            geometry
            and d is not None
            and nodes == d["tree_nodes"]
            and integer(row, "information_sets", 1) == d["information_sets"]
        )
        work = (
            work
            and warm == 2 * nodes
            and warm <= before < row["work_checkpoint"] <= total
            and total - before == last
        )
        recall = recall and integer(row, "recall_violations") == 0
        if type(row["menus_compatible"]) is not bool:
            raise ValueError("menu compatibility must be boolean")
        methods = (
            methods
            and row["menus_compatible"]
            and all(
                type(row.get(k)) is type(s[k]) and row[k] == s[k]
                for k in (
                    "sampling",
                    "batch_size",
                    "regret_mode",
                    "regret_weighting",
                    "average_weighting",
                    "initial_exact_expectation",
                )
            )
        )
        key = tuple(row[k] for k in fields[:-1])
        signature = (total, before, last, warm, nodes)
        consistent = consistent and origins.setdefault(key, signature) == signature
    tol = s["independent_tolerance_chips"]
    audit_ok = all(
        number(a, k) <= tol
        for a in audit
        for k in ("value_error_chips", "exploitability_error_chips")
    )
    accuracy = coverage = True
    final = [r for r in rows if r["work_checkpoint"] == s["node_work_checkpoints"][-1]]
    for p in spots:
        for rep in ("exact", CANDIDATE):
            selected = [
                r
                for r in final
                if r["spot_file"] == p
                and r["representation"] == rep
                and r["readout"] == "linear"
            ]
            values = [r["exploitability_pot"] for r in selected]
            accuracy = (
                accuracy
                and len(values) == len(s["seeds"])
                and statistics.median(values) <= s["median_exploitability_pot_limit"]
                and max(values) <= s["worst_exploitability_pot_limit"]
            )
    coverage = all(
        r["coverage"] >= s["minimum_uniform_reach_average_coverage"]
        for r in final
        if r["readout"] in ("uniform", "linear")
    )
    checks = dict(
        complete=complete,
        prior_full_contract=prior,
        context_binding=binding(rows + audit, config),
        geometry=geometry,
        work=work,
        identical_readout_work=consistent,
        method=methods,
        recall=recall,
        accuracy=accuracy,
        coverage=coverage,
        audit=audit_ok,
        own_clock=number(dict(seconds=elapsed_seconds), "seconds")
        <= s["maximum_seconds"],
        audit_clock=number(dict(seconds=audit_seconds), "seconds")
        <= s["maximum_audit_seconds"],
    )
    return result("sampled", checks, config)
