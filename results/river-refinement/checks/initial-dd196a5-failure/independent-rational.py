"""Independent exact-rational local score from retained binary64 Qs/weights."""

import gzip
import json
import math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

root = Path.cwd()
folder = root / "results/river-refinement"
summary = json.loads((folder / "summary.json").read_text())["profiles"]
details = json.loads(gzip.decompress((folder / "rows.json.gz").read_bytes()))[
    "profiles"
]
checks = []
for scalar, detail in zip(summary, details, strict=True):
    for response, inventory in zip(
        scalar["responses"], detail["responses"], strict=True
    ):
        rows = inventory["rows"]
        total = math.fsum(r["counterfactual_mass"] for r in rows)
        groups = defaultdict(list)
        for r in rows:
            groups[r["parent"]].append(r)
        for suffix in ("exact", "restricted"):
            cost = Fraction()
            for members in groups.values():
                weighted = [
                    (
                        Fraction.from_float(r["counterfactual_mass"] / total),
                        [Fraction.from_float(float(q)) for q in r["q"][suffix]],
                    )
                    for r in members
                ]
                separate = sum((w * max(q) for w, q in weighted), Fraction())
                common = max(
                    sum((w * q[a] for w, q in weighted), Fraction())
                    for a in range(len(weighted[0][1]))
                )
                assert separate >= common
                cost += separate - common
            expected = float(cost)
            saved = response["probes"][0]["panels"][suffix][
                "local_sharing_cost_chips_per_cf_decision"
            ]
            checks.append(
                dict(
                    seed=scalar["seed"],
                    role=scalar["role"],
                    target=response["target"],
                    suffix=suffix,
                    exact_rational_cost_rounded=expected,
                    saved_cost=saved,
                    absolute_error=abs(expected - saved),
                )
            )
result = dict(
    status="all36saved_costs_match_exact_rational_reference_within_1e-12",
    checks=checks,
    maximum_error=max(r["absolute_error"] for r in checks),
    basis=(
        "exact Fraction arithmetic on retained binary64 normalized weights "
        "and Q inputs; not training or Linux measurement"
    ),
)
assert result["maximum_error"] <= 1e-12
print(json.dumps(result, indent=2))
