"""Prospective whole-grid identities for own finer-opponent learning controls.

This module creates no learner or admission. Real labels never shrink to fit a
clock. Tiny software proofs have explicit fictional scope and separate labels.
"""

import itertools
from dataclasses import dataclass
from typing import Any

from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same

GAMES = (
    "configs/learning-spots/dev_low_oop.json",
    "configs/learning-spots/dev_medium_oop.json",
)
SEEDS = (20261301, 20261302, 20261303)
WORK = (100_000, 1_000_000, 10_000_000)
TOY_WORK = (80, 240, 720)
READOUTS = ("current", "uniform_average", "linear_average")
WEIGHTS = ("uniform", "linear")
PATHS = ("coarse0", "coarse1", "mixed0", "mixed1", "fine")
ARMS = ("coarse_self", "coarse_pair", "mixed_pair", "fine_self")
REAL = "KNOWN_HOLDEM_OWN_OPPONENT_INFORMATION_NOT_GLOBAL_ADMISSION"
TOY = "FICTIONAL_SIGNAL_GAMES_OWN_OPPONENT_SOFTWARE_NOT_HOLDEM"


@dataclass(frozen=True)
class Design:
    scope: str
    labels: tuple[int, int, int]

    def __post_init__(self) -> None:
        if (self.scope, self.labels) not in ((REAL, WORK), (TOY, TOY_WORK)):
            raise ValueError("use the complete fixed real or explicit toy design")

    def coordinate(self, index: int) -> dict[str, Any]:
        if type(index) is not int or not 0 <= index < 6:
            raise ValueError("game/seed coordinate outside complete six-cell grid")
        game, seed = divmod(index, 3)
        return dict(coordinate=index, spot_file=GAMES[game], seed=SEEDS[seed])

    def path(self, index: int) -> dict[str, Any]:
        if type(index) is not int or not 0 <= index < 30:
            raise ValueError("path outside complete thirty-path grid")
        coordinate, kind = divmod(index, 5)
        name = PATHS[kind]
        seed = self.coordinate(coordinate)["seed"]
        role = 1 if name in ("coarse1", "mixed1") else 0
        return dict(
            **self.coordinate(coordinate),
            path_index=index,
            path_kind=name,
            tree_kind="coarse" if name.startswith("coarse") else name,
            role=role,
            rng_entropy=seed if role == 0 else [seed, 1],
            batch_size=4,
            regret_rule="signed",
            regret_weight="linear",
            primary_average_weight="linear",
            scope=self.scope,
        )

    def boundaries(self, index: int) -> tuple[int, ...]:
        kind = self.path(index)["path_kind"]
        half = tuple(v // 2 for v in self.labels)
        if kind == "coarse0":
            return tuple(sorted((*self.labels, *half)))
        return self.labels if kind == "fine" else half

    def raw(self, index: int, work: int, readout: str) -> dict[str, Any]:
        if (
            type(work) is not int
            or work not in self.boundaries(index)
            or readout not in READOUTS
        ):
            raise ValueError("raw capture outside fixed work/readout inventory")
        return dict(
            **self.path(index),
            id=f"opponent-{self.scope}-{index:02d}-{work}-{readout}",
            work_label=work,
            readout=readout,
            origin="own_raw_trajectory",
        )

    def mass(self, index: int, work: int, weight: str) -> dict[str, Any]:
        if weight not in WEIGHTS:
            raise ValueError("unknown own average ledger")
        row = self.raw(index, work, weight + "_average")
        return dict(row, id=row["id"] + "-mass", readout=weight)

    def arm(self, coordinate: int, work: int, readout: str, arm: str) -> dict[str, Any]:
        self.coordinate(coordinate)
        if (
            type(work) is not int
            or work not in self.labels
            or readout not in READOUTS
            or arm not in ARMS
        ):
            raise ValueError("logical arm outside fixed full comparison grid")
        offset = 5 * coordinate
        components = {
            "coarse_self": ((offset, work),),
            "fine_self": ((offset + 4, work),),
            "coarse_pair": ((offset, work // 2), (offset + 1, work // 2)),
            "mixed_pair": ((offset + 2, work // 2), (offset + 3, work // 2)),
        }[arm]
        sources = [self.raw(i, w, readout)["id"] for i, w in components]
        identifier = (
            sources[0]
            if len(sources) == 1
            else f"opponent-{self.scope}-arm-{coordinate}-{work}-{readout}-{arm}"
        )
        return dict(
            **self.coordinate(coordinate),
            scope=self.scope,
            id=identifier,
            arm=arm,
            work_label=work,
            readout=readout,
            origin="raw_alias" if len(sources) == 1 else "own_seat_composition",
            components=sources,
            component_work_labels=[w for _, w in components],
            information="fine" if arm == "fine_self" else "coarse",
        )

    def manifest(self) -> dict[str, Any]:
        paths = [self.path(i) for i in range(30)]
        raw = [
            self.raw(i, w, r)
            for i in range(30)
            for w in self.boundaries(i)
            for r in READOUTS
        ]
        masses = [
            self.mass(i, w, r)
            for i in range(30)
            for w in self.boundaries(i)
            for r in WEIGHTS
        ]
        arms = [
            self.arm(i, w, r, a)
            for i, w, r, a in itertools.product(range(6), self.labels, READOUTS, ARMS)
        ]
        composed = [r for r in arms if r["origin"] == "own_seat_composition"]
        result = dict(
            scope=self.scope,
            work_labels=list(self.labels),
            paths=paths,
            captures=raw,
            masses=masses,
            arms=arms,
            profiles=[*raw, *composed],
            actual_last_work_labels=[self.boundaries(i)[-1] for i in range(30)],
            logical_arms_share_prefixes=True,
            counts=dict(
                actual_paths=30,
                raw_boundaries=108,
                raw_profiles=324,
                raw_ledgers=216,
                logical_profiles=216,
                composed_profiles=108,
                unique_profiles=432,
                final_fixed_conditions=1152,
                original_B4_work_boundaries=36 if self.scope == REAL else 0,
            ),
        )
        result["sha256"] = sha(result)
        return result

    def require_rows(self, name: str, rows: list[dict[str, Any]]) -> None:
        """Complete typed identity set; reject extras, duplicates and bool counters."""
        if name not in ("captures", "masses", "arms", "profiles"):
            raise ValueError("unknown complete design inventory")
        wanted = {r["id"]: r for r in self.manifest()[name]}
        actual = {r["id"]: r for r in rows}
        if len(actual) != len(rows) or set(actual) != set(wanted):
            raise ArithmeticError(
                "complete own-opponent inventory missing/extra/duplicate"
            )
        for key, row in wanted.items():
            if any(not same(actual[key].get(k), v) for k, v in row.items()):
                raise ArithmeticError("own-opponent typed design coordinate changed")


def paired_work(components: list[dict[str, Any]], logical_label: int) -> dict[str, Any]:
    """Add both warm starts/updates; one complete overshoot per component.

    Reused prefixes remain charged in this logical arm. They are charged only
    once in actual execution totals, which are reported separately by the runner.
    """
    if len(components) not in (1, 2) or type(logical_label) is not int:
        raise ValueError("one or two paths and integer logical work required")
    label = logical_label // len(components)
    if logical_label <= 0 or label * len(components) != logical_label:
        raise ValueError("paired work requires an exactly divisible positive label")
    fields = (
        "work_label",
        "previous_work",
        "total_work",
        "last_iteration_visits",
        "initialization_visits",
        "iteration",
    )
    for row in components:
        if any(type(row[k]) is not int for k in fields) or (
            row["work_label"] != label
            or not 0 <= row["previous_work"] < label <= row["total_work"]
            or row["total_work"] - row["previous_work"] != row["last_iteration_visits"]
            or not 0 < row["initialization_visits"] <= row["total_work"]
            or row["iteration"] < 1
        ):
            raise ArithmeticError("component is not a charged first whole crossing")
    total = sum(r["total_work"] for r in components)
    return dict(
        logical_work_label=logical_label,
        total_work=total,
        initialization_visits=sum(r["initialization_visits"] for r in components),
        overshoot=total - logical_label,
        overshoot_bound_exclusive=sum(r["last_iteration_visits"] for r in components),
        component_count=len(components),
        component_iterations=[r["iteration"] for r in components],
        component_total_work=[r["total_work"] for r in components],
        units="charged visited nodes, including both players and all warm starts",
    )
