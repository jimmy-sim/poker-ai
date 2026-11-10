"""Real, pinned own-source factories for the complete matched-update design.

No reference is constructed, and no strength statistic selects a target. Toy
fixtures use the lower-level capture API; this factory always requires the
published poker receipts and their complete independent audits.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as old
from poker_ai.evaluation import matched_update_grid as grid
from poker_ai.evaluation import reduced_study_inputs as study
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest

CONFIG = "configs/matched-update-pipeline.json"
CONFIG_SHA = "39fa5606d1338a6e8e97c568b3ebcdc91189f95e821f95fa57790600d67c71bb"


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective complete pipeline config changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for key in ("parent_config", "component_config"):
        if digest(root / result[key]) != result[key + "_sha256"]:
            raise ArithmeticError("pipeline parent/component contract changed")
    return result


def unique(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[Any, Any]:
    """Reject duplicate source identities rather than allowing last-write wins."""
    result = {}
    for row in rows:
        key = tuple(row[k] for k in fields)
        if key in result:
            raise ArithmeticError("duplicate matched-update source identity")
        result[key] = row
    return result


@dataclass(frozen=True)
class Sources:
    archived: old.Sources
    manifest: dict[str, Any]
    paths: list[dict[str, Any]]
    averages: dict[Any, Any]
    currents: dict[Any, Any]
    masses: dict[Any, Any]
    scored_currents: dict[Any, Any]
    fixed: list[dict[str, Any]]

    def context(self, index: int) -> ScoringContext:
        if type(index) is not int or not 0 <= index < 24:
            raise ValueError("real matched-update context index outside complete grid")
        return self.archived.data.base.context(study.case(self.paths[index], "linear"))

    def targets(self, index: int) -> list[dict[str, Any]]:
        self.context(index)
        return [
            t
            for t in self.manifest["iteration_targets"]
            if t["baseline_path_index"] == index
        ]

    def original(self, index: int, label: int) -> dict[str, Any]:
        """Expected bits from reduced B1; earlier independent prefixes stay bound."""
        self.context(index)
        average = self.averages[index, "linear", label]
        other = self.averages[index, "uniform", label]
        current = self.currents[index, label]
        fields = (
            "iteration",
            "previous_work",
            "total_work",
            "last_iteration_visits",
            "initialization_visits",
            "sampled_traversals",
            "guard_sha256",
            "current_sha256",
        )
        if any(not same(average[k], other[k]) for k in fields) or (
            average["guard_sha256"] != current["guard_sha256"]
            or average["current_sha256"] != current["receipt"]["policy_sha256"]
        ):
            raise ArithmeticError("original B1 current/readout guards disagree")
        masses = {w: self.masses[index, w, label] for w in study.WEIGHTS}
        if any(m["guard_sha256"] != average["guard_sha256"] for m in masses.values()):
            raise ArithmeticError("original B1 ledger guard changed")
        originals = study.prefix_map(self.archived.data, self.paths[index])
        for weight in study.WEIGHTS:
            peer = originals[weight][label]
            row = self.averages[index, weight, label]
            if (
                any(
                    not same(peer[k], row[k])
                    for k in (
                        "iteration",
                        "previous_work",
                        "total_work",
                        "last_iteration_visits",
                        "initialization_visits",
                        "state_sha256",
                    )
                )
                or peer["receipt"]["policy_sha256"] != row["receipt"]["policy_sha256"]
            ):
                raise ArithmeticError("original pre-batch B1 readout changed")
        return dict(
            path_index=index,
            work_label=label,
            **{k: average[k] for k in fields},
            readouts={
                w: dict(
                    source_id=self.averages[index, w, label]["id"],
                    original_id=originals[w][label]["id"],
                    policy_sha256=self.averages[index, w, label]["receipt"][
                        "policy_sha256"
                    ],
                    state_sha256=self.averages[index, w, label]["state_sha256"],
                    mass_sha256=masses[w]["receipt"]["mass_sha256"],
                )
                for w in study.WEIGHTS
            },
        )


def load(root: Path) -> Sources:
    """Validate all source receipts before providing a real scoring context."""
    config_inputs(root)
    manifest = grid.manifest(root)
    archived = old.load(root)
    parent = grid.config_inputs(root)
    current: dict[str, Any] = json.loads((root / parent["source_currents"]).read_text())
    paths = study.paths(study.config_inputs(root))[:24]
    averages = [r for r in archived.own["rows"] if r["path_index"] < 24]
    masses = [r for r in archived.own["masses"] if r["path_index"] < 24]
    currents = [r for r in archived.own["currents"] if r["path_index"] < 24]
    result = Sources(
        archived,
        manifest,
        paths,
        unique(
            [dict(r, weight=r["case"]["average_weight"]) for r in averages],
            ("path_index", "weight", "work_label"),
        ),
        unique(currents, ("path_index", "work_label")),
        unique(
            [dict(r, weight=r["case"]["average_weight"]) for r in masses],
            ("path_index", "weight", "work_label"),
        ),
        unique(current["rows"], ("id",)),
        current["fixed_matches"],
    )
    if (
        len(result.paths),
        len(result.averages),
        len(result.currents),
        len(result.masses),
    ) != (24, 144, 72, 144):
        raise ArithmeticError("real matched-update baseline inventory incomplete")
    for index in range(24):
        for label in parent["original_work_labels"]:
            result.original(index, label)
        if len(result.targets(index)) != 2:
            raise ArithmeticError("both original B4/B16 targets required")
    # Pin every upstream file before the factory escapes. This also catches a
    # concurrent local edit between the first manifest read and the heavy load.
    if any(digest(root / p) != h for p, h in manifest["input_sha256"].items()):
        raise ArithmeticError("source evidence changed while loading contexts")
    return result
