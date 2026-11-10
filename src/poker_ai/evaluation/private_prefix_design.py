"""Complete fixed identities for the new candidate; no metric-based selection."""

import itertools
from dataclasses import dataclass
from typing import Any, Literal

from poker_ai.evaluation.frozen_batch_inputs import case
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import finite, same

READOUTS = ("current", "uniform_average", "linear_average")
WEIGHTS = ("uniform", "linear")
REAL = "KNOWN_HOLDEM_PRIVATE_PREFIX_DIAGNOSTIC_NOT_GLOBAL_ADMISSION"
TOY = "EXPLICIT_NONUNIFORM_KUHN_PRIVATE_PREFIX_SOFTWARE_NOT_POKER_RESULTS"
OLD = "OLD_OWN_PRIVATE_PREFIX_COST_CALIBRATION_NO_NEW_TRAJECTORIES"


@dataclass(frozen=True)
class Design:
    """Logical context labels are the fixed config grid, even in a toy proof.

    A toy proof substitutes one declared nonuniform-Kuhn context for all logical
    spot/representation labels. Those labels are not independent poker games.
    Scope and actual fixture work labels are always bound to every archive row.
    """

    paths: tuple[dict[str, Any], ...]
    labels: tuple[int, int, int]
    scope: str

    @classmethod
    def build(
        cls,
        config: dict[str, Any],
        *,
        mode: Literal["real", "toy", "old"],
        toy_labels: tuple[int, int, int] | None = None,
    ) -> "Design":
        if any(
            not same(config[k], v)
            for k, v in {
                "new_batch_sizes": [4, 16],
                "spot_files": [
                    "configs/learning-spots/dev_low_oop.json",
                    "configs/learning-spots/dev_medium_oop.json",
                ],
                "representations": ["exact", "texture_range_q8_b8"],
                "regret_rules": ["signed", "clipped"],
                "seeds": [20261301, 20261302, 20261303],
                "work_labels": [100000, 1000000, 10000000],
            }.items()
        ):
            raise ValueError("private-prefix prospective case grid changed")
        paths = tuple(
            dict(batch_size=b, spot_file=g, representation=r, regret_rule=c, seed=s)
            for b, g, r, c, s in itertools.product(
                config["new_batch_sizes"],
                config["spot_files"],
                config["representations"],
                config["regret_rules"],
                config["seeds"],
            )
        )
        if len(paths) != 48 or config["new_batch_sizes"] != [4, 16]:
            raise ValueError("complete private-prefix48-path design required")
        if mode not in ("real", "toy", "old") or (mode == "toy") != (
            toy_labels is not None
        ):
            raise ValueError("explicit toy scope and actual labels must agree")
        labels = toy_labels if mode == "toy" else tuple(config["work_labels"])
        if (
            labels is None
            or len(labels) != 3
            or list(labels) != sorted(set(labels))
            or any(type(t) is not int or t <= 0 for t in labels)
        ):
            raise ValueError("three distinct positive work labels required")
        return cls(
            paths,
            (labels[0], labels[1], labels[2]),
            {"real": REAL, "toy": TOY, "old": OLD}[mode],
        )

    def common(self, index: int, label: int) -> dict[str, Any]:
        if (
            type(index) is not int
            or not 0 <= index < 48
            or type(label) is not int
            or label not in self.labels
        ):
            raise ValueError("private-prefix coordinate outside full design")
        path = self.paths[index]
        return dict(
            path_index=index,
            context_index=index % 24,
            original_iid_path_index=index + 24,
            case=case(path, "linear"),
            batch_size=path["batch_size"],
            scope=self.scope,
            work_label=label,
        )

    def prefix(self) -> str:
        return (
            "old-iid"
            if self.scope == OLD
            else "toy-stratified"
            if self.scope == TOY
            else "stratified"
        )

    def profile(self, index: int, label: int, readout: str) -> dict[str, Any]:
        if readout not in READOUTS:
            raise ValueError("unknown private-prefix readout")
        result = self.common(index, label)
        result.update(
            id=f"{self.prefix()}-{index:03d}-{label}-{readout}",
            readout=readout,
            variant=readout,
        )
        result["case"] = case(
            self.paths[index], "uniform" if readout == "uniform_average" else "linear"
        )
        return result

    def mass(self, index: int, label: int, weight: str) -> dict[str, Any]:
        if weight not in WEIGHTS:
            raise ValueError("unknown private-prefix ledger")
        result = self.common(index, label)
        result.update(
            id=f"{self.prefix()}-{index:03d}-{label}-mass-{weight}", readout=weight
        )
        result["case"] = case(self.paths[index], weight)  # type: ignore[arg-type]
        return result

    def manifest(self) -> dict[str, Any]:
        result = dict(
            paths=list(self.paths),
            work_labels=list(self.labels),
            scope=self.scope,
            captures=[
                self.profile(i, t, r)
                for i in range(48)
                for t in self.labels
                for r in READOUTS
            ],
            masses=[
                self.mass(i, t, w)
                for i in range(48)
                for t in self.labels
                for w in WEIGHTS
            ],
        )
        result["sha256"] = sha(result)
        return result


def index_rows(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[Any, Any]:
    result = {tuple(row[k] for k in fields): row for row in rows}
    if len(result) != len(rows):
        raise ArithmeticError("duplicate private-prefix record identity")
    return result


def inventory(design: Design, saved: dict[str, Any], *, scored: bool) -> None:
    """Require the entire grid and exact typed coordinates, not just counts."""
    manifest = design.manifest()
    if not same(saved["manifest"], manifest) or saved["scope"] != design.scope:
        raise ArithmeticError("private-prefix design/scope changed")
    captures = index_rows(saved["captures"], ("id",))
    for name in ("captures", "masses"):
        actual = index_rows(saved[name], ("id",))
        wanted = index_rows(manifest[name], ("id",))
        if set(actual) != set(wanted):
            raise ArithmeticError("private-prefix complete grid missing/extra")
        for key, row in actual.items():
            if any(not same(row.get(k), v) for k, v in wanted[key].items()):
                raise ArithmeticError("private-prefix typed coordinate/case changed")
            if row["source_sha256"] != saved["source_sha256"]:
                raise ArithmeticError("private-prefix row source changed")
            integers = (
                "iteration",
                "previous_work",
                "total_work",
                "last_iteration_visits",
                "initialization_visits",
                "sampled_traversals",
                "overshoot",
            )
            if any(type(row[k]) is not int for k in integers):
                raise ArithmeticError("private-prefix counters require exact integers")
            if (
                row["iteration"] < 1
                or row["initialization_visits"] <= 0
                or not row["previous_work"] < row["work_label"] <= row["total_work"]
                or row["last_iteration_visits"]
                != row["total_work"] - row["previous_work"]
                or row["sampled_traversals"]
                != 2 * row["batch_size"] * (row["iteration"] - 1)
                or row["overshoot"] != row["total_work"] - row["work_label"]
                or row["total_work"] < row["initialization_visits"]
                or row["total_work"]
                < row["initialization_visits"] + 3 * row["sampled_traversals"]
                or (
                    row["iteration"] > 1
                    and (
                        row["previous_work"] < row["initialization_visits"]
                        or row["last_iteration_visits"] < 6 * row["batch_size"]
                    )
                )
                or (
                    row["iteration"] == 1
                    and (
                        row["previous_work"] != 0
                        or row["total_work"] != row["initialization_visits"]
                    )
                )
            ):
                raise ArithmeticError("private-prefix work/update accounting changed")
            if any(
                not finite(row[k])
                for k in ("prefix_setup_seconds", "initialization_seconds")
            ):
                raise ArithmeticError("nonfinite/negative private-prefix setup time")
            for h in ("guard_sha256", "current_sha256", "prefix_plan_sha256"):
                value = row[h]
                if (
                    not isinstance(value, str)
                    or len(value) != 64
                    or any(c not in "0123456789abcdef" for c in value)
                ):
                    raise ArithmeticError("invalid private-prefix state hash")
    # All three readouts and both books share a single trajectory/crossing.
    common = (
        "guard_sha256",
        "current_sha256",
        "prefix_plan_sha256",
        "previous_capture_guard_sha256",
        "current_movement",
        "iteration",
        "previous_work",
        "total_work",
        "last_iteration_visits",
        "initialization_visits",
        "sampled_traversals",
        "overshoot",
    )
    for i in range(48):
        previous = None
        for label in design.labels:
            rows = [
                r
                for r in saved["captures"] + saved["masses"]
                if r["path_index"] == i and r["work_label"] == label
            ]
            if len(rows) != 5 or any(
                not same(r[k], rows[0][k]) for r in rows for k in common
            ):
                raise ArithmeticError(
                    "private-prefix dependent readouts split trajectories"
                )
            now = rows[0]
            if previous is not None and (
                now["iteration"] < previous["iteration"]
                or now["total_work"] < previous["total_work"]
                or (
                    now["iteration"] == previous["iteration"]
                    and any(
                        not same(now[k], previous[k])
                        for k in common
                        if k != "overshoot"
                    )
                )
            ):
                raise ArithmeticError("private-prefix work crossings out of order")
            previous = now
    if scored:
        actual = index_rows(saved["rows"], ("id",))
        if set(actual) != set(captures):
            raise ArithmeticError("private-prefix scored policies missing/extra")
        outer = {"receipt", "file", "metadata_sha256", "seconds", "cpu_seconds"}
        for key, row in actual.items():
            captured = captures[key]
            if (
                any(
                    not same(row.get(k), v)
                    for k, v in captured.items()
                    if k not in outer
                )
                or row["receipt"]["policy_sha256"]
                != captured["receipt"]["policy_sha256"]
                or row["capture_sha256"] != captured["receipt"]["sha256"]
                or row["capture_metadata_sha256"] != captured["metadata_sha256"]
            ):
                raise ArithmeticError(
                    "private-prefix scored policy changed immutable lineage"
                )
