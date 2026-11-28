"""Fixed interpretation of published own row vectors and parent records."""

import json
from pathlib import Path
from typing import Any

from known_turn_half_policy_mixture.plan import ARMS, GAMES

from known_mixture_residual_map.gate import (
    OWN,
    clean_head,
    require_own,
    source_fingerprint,
)
from known_mixture_residual_map.own import save
from known_mixture_residual_map.plan import contract


def report(root: Path, output: Path) -> None:
    """Describe all four games once, without new scoring or row selection."""
    data = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_own(root, fingerprint)
    own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
    parent: dict[str, Any] = json.loads(
        (
            root / "results/known-turn-collision-medium-transfer/report/report.json"
        ).read_bytes()
    )
    mixed: dict[str, Any] = json.loads(
        (
            root / "results/known-turn-half-policy-mixture/report/report.json"
        ).read_bytes()
    )
    if (
        own["status"] != "completed"
        or own["games"] != list(GAMES)
        or parent["status"] != "completed"
        or mixed["classification"] != "negative"
    ):
        raise ArithmeticError("fixed published input grid incomplete")
    parent_cases = {
        (row["game"], row["arm"]): row
        for row in parent["cases"]
        if row["work_label"] == 40_000_000 and row["readout"] == "linear_average"
    }
    if set(parent_cases) != {(game, arm) for game in GAMES for arm in ARMS}:
        raise ArithmeticError("eight final parent cases changed")
    rows: list[dict[str, Any]] = []
    for index, game in enumerate(GAMES):
        traced: dict[str, Any] = json.loads(
            (root / OWN / f"game{index:02d}.json").read_bytes()
        )
        if traced["game"] != game or traced["index"] != index:
            raise ArithmeticError("mixed trace order changed")
        result = traced["summary"]
        parent_streets = {}
        for arm in ARMS:
            row = parent_cases[(game, arm)]
            turn = row["turn_contribution_chips"]
            river = row["river_contribution_chips"]
            if (
                abs(turn + river - row["exploitability_chips"])
                > data["arithmetic_tolerance_chips"]
            ):
                raise ArithmeticError("published parent street accounting changed")
            parent_streets[arm] = {"turn_chips": turn, "river_chips": river}
        mixed_turn = result["streets"]["TURN"]["gain_chips"]
        mixed_river = result["streets"]["RIVER"]["gain_chips"]
        rows.append(
            {
                "game": game,
                "mixed_exploitability_chips": result["total_chips"],
                "mixed_turn_chips": mixed_turn,
                "mixed_river_chips": mixed_river,
                "street_label": result["street_label"],
                "turn_top_ten_share": result["streets"]["TURN"][
                    "top_ten_positive_share"
                ],
                "river_top_ten_share": result["streets"]["RIVER"][
                    "top_ten_positive_share"
                ],
                "turn_concentration": result["streets"]["TURN"]["concentration"],
                "river_concentration": result["streets"]["RIVER"]["concentration"],
                "parents": parent_streets,
                "mixed_minus_q8_turn_chips": mixed_turn
                - parent_streets[ARMS[0]]["turn_chips"],
                "mixed_minus_q8_river_chips": mixed_river
                - parent_streets[ARMS[0]]["river_chips"],
                "mixed_minus_exact_turn_chips": mixed_turn
                - parent_streets[ARMS[1]]["turn_chips"],
                "mixed_minus_exact_river_chips": mixed_river
                - parent_streets[ARMS[1]]["river_chips"],
                "selected_decisions": traced["decisions"],
                "peak_rss_bytes": traced["peak_rss_bytes"],
            }
        )
    if output.exists():
        raise FileExistsError("retain prior residual-map report")
    output.mkdir(parents=True)
    save(
        output / "report.json",
        {
            "status": "informative",
            "head": head,
            "source_fingerprint": fingerprint,
            "cases": rows,
            "scope": "four known dependent restricted games; no new policy or training",
            "interpretation": (
                "each arm has its own saved opponent, reach and optimized best-reply "
                "continuation; street differences are descriptive, not causal swaps"
            ),
            "maximum_scalar_error_chips": max(
                abs(
                    row["mixed_exploitability_chips"]
                    - row["mixed_turn_chips"]
                    - row["mixed_river_chips"]
                )
                for row in rows
            ),
        },
    )
