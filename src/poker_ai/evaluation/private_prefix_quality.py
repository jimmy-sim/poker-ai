"""Report the original known-game limits without selecting a new default."""

import itertools
import statistics
from typing import Any


def summarize(rows: list[dict[str, Any]], pots: dict[str, float]) -> dict[str, Any]:
    games = sorted({r["case"]["spot_file"] for r in rows})
    result = []
    for game, representation in itertools.product(
        games, ("exact", "texture_range_q8_b8")
    ):
        selected = [
            r
            for r in rows
            if r["case"]["spot_file"] == game
            and r["case"]["representation"] == representation
            and r["case"]["regret_rule"] == "signed"
            and r["batch_size"] == 4
            and r["readout"] == "linear_average"
            and r["work_label"] == 10000000
        ]
        if sorted(r["case"]["seed"] for r in selected) != [
            20261301,
            20261302,
            20261303,
        ]:
            raise ArithmeticError("all primary fixed-work seeds required")
        values = [
            100 * r["metrics"]["exact_exploitability_chips"] / pots[game]
            for r in selected
        ]
        result.append(
            dict(
                spot_file=game,
                representation=representation,
                primary=representation == "texture_range_q8_b8",
                seeds=[20261301, 20261302, 20261303],
                exact_exploitability_pct_initial_pot=values,
                median_pct=statistics.median(values),
                worst_pct=max(values),
                historical_accuracy_limits_pass=statistics.median(values) <= 1.0
                and max(values) <= 2.5,
                whole_row_coverage=[
                    r["coverage"]["whole"]["all"]["row_fraction"] for r in selected
                ],
                post_warm_row_coverage=[
                    r["coverage"]["post_warm"]["all"]["row_fraction"] for r in selected
                ],
                whole_river_reach_coverage=[
                    r["coverage"]["whole"]["river"]["uniform_reach_fraction"]
                    for r in selected
                ],
                post_warm_river_reach_coverage=[
                    r["coverage"]["post_warm"]["river"]["uniform_reach_fraction"]
                    for r in selected
                ],
            )
        )
    return dict(
        scope="original_known_case_diagnostic_limits_not_policy_selection",
        median_limit_pct=1.0,
        worst_limit_pct=2.5,
        coverage_limit_fraction=0.95,
        warm_coverage_is_not_learned_support=True,
        groups=result,
        new_agent_default=False,
        fresh_global_admission=False,
    )
