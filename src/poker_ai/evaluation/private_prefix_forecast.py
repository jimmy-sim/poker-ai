"""Complete worst-repeat, fixed-partition forecast; fixed allowances, no tuning."""

import math
from typing import Any

from poker_ai.evaluation.private_prefix_design import Design
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.parallel_profile import finite, same


def forecast(
    rows: list[dict[str, Any]], config: dict[str, Any], binding: str
) -> dict[str, Any]:
    design = Design.build(config, mode="real")
    expected = {(rep, index) for rep in range(3) for index in range(48)}
    actual = {}
    for row in rows:
        key = row["repeat"], row["index"]
        if (
            any(type(x) is not int for x in key)
            or key not in expected
            or key in actual
            or not same(row["global_index"], key[0] * 48 + key[1])
            or not same(row["path"], design.paths[key[1]])
            or row["source_sha256"] != binding
            or row["backend"] != "StratifiedBatchTrainer"
            or row["reference_constructed"] is not False
        ):
            raise ArithmeticError(
                "complete unchanged profiling case/seed/backend required"
            )
        ints = (
            "initialization_visits",
            "incremental_visits",
            "total_work",
            "previous_work",
            "iteration",
            "last_iteration_visits",
            "sampled_traversals",
        )
        if any(type(row[k]) is not int or row[k] < 0 for k in ints):
            raise ArithmeticError("invalid prefix timing work counters")
        target = row["initialization_visits"] + 100000
        if (
            row["initialization_visits"] <= 0
            or row["iteration"] <= 1
            or row["incremental_visits"]
            != row["total_work"] - row["initialization_visits"]
            or not row["previous_work"] < target <= row["total_work"]
            or row["last_iteration_visits"] != row["total_work"] - row["previous_work"]
            or row["sampled_traversals"]
            != 2 * row["path"]["batch_size"] * (row["iteration"] - 1)
            or not finite(row["setup_seconds"])
            or not finite(row["incremental_seconds"], positive=True)
            or not finite(row["seconds"], positive=True)
            or row["setup_seconds"] + row["incremental_seconds"] > row["seconds"] + 1e-6
        ):
            raise ArithmeticError(
                "prefix timing must include warm setup "
                "and exact additional-work crossing"
            )
        value = (
            row["setup_seconds"]
            + row["incremental_seconds"]
            * (10000000 - row["initialization_visits"])
            / row["incremental_visits"]
        )
        if not math.isfinite(value) or value <= 0:
            raise ArithmeticError("nonfinite prefix cost extrapolation")
        actual[key] = row, value
    if set(actual) != expected:
        raise ArithmeticError("all144 timing rows required")
    state_fields = (
        "initialization_visits",
        "incremental_visits",
        "total_work",
        "previous_work",
        "iteration",
        "last_iteration_visits",
        "sampled_traversals",
        "guard_sha256",
    )
    costs = []
    for index in range(48):
        peers = [actual[rep, index][0] for rep in range(3)]
        if any(not same(r[k], peers[0][k]) for r in peers for k in state_fields):
            raise ArithmeticError("repeated same-seed prefix state/work changed")
        costs.append(max(actual[rep, index][1] for rep in range(3)))
    assignments = partition(48, 3)
    worker_totals = [math.fsum(costs[i] for i in indices) for indices in assignments]
    training = max(worker_totals)
    guarded = 2 * (2 * training + 600)
    return dict(
        paths=48,
        timing_rows=144,
        per_path_max_seconds=costs,
        assignments=assignments,
        partition_totals_seconds=worker_totals,
        training_forecast_seconds=training,
        observation_allowance_multiplier=2.0,
        fixed_overhead_allowance_seconds=600.0,
        guard_multiplier=2.0,
        formula="2*(2*T+600)",
        guarded_seconds=guarded,
        own_cap_seconds=7200,
        passes=guarded < 7200,
        long_run_admitted=False,
    )
