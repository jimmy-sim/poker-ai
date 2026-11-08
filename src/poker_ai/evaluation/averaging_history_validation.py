"""Exact complete-grid and original-prefix contracts for diagnostic trajectory IO."""

from typing import Any

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.controlled_reply_inputs import KEY, identity
from poker_ai.postflop.cell_process import THREAD_ENV, partition
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same


def common(row: dict[str, Any], data: HistoryInputs, binding: str) -> None:
    index = row["index"]
    if type(index) is not int or not 0 <= index < 64:
        raise ArithmeticError("history source index changed")
    source = data.base.policies[index]
    fixed = dict(
        case=source.case,
        source_profile_id=source.identifier,
        source_snapshot_id=source.row["id"],
        original_index=source.row["index"],
        original_policy_sha256=source.row["receipt"]["policy_sha256"],
        source_sha256=binding,
        initialization_visits=source.row["initialization_visits"],
    )
    if any(not same(row[k], v) for k, v in fixed.items()):
        raise ArithmeticError("history source/case binding changed")
    for key in ("work_label", "iteration", "total_work", "last_iteration_visits"):
        if type(row[key]) is not int or row[key] <= 0:
            raise ArithmeticError("history work/iteration must be positive integers")
    if (
        type(row["previous_work"]) is not int
        or not 0 <= row["previous_work"] < row["work_label"] <= row["total_work"]
        or row["last_iteration_visits"] != row["total_work"] - row["previous_work"]
    ):
        raise ArithmeticError("history did not retain a first complete work crossing")
    for key in ("state_sha256", "learning_path_sha256"):
        value = row[key]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ArithmeticError("invalid history state fingerprint")
    path = row["file"]
    from pathlib import PurePosixPath

    if (
        not isinstance(path, str)
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
    ):
        raise ArithmeticError("invalid own snapshot relative path")


def profile(row: dict[str, Any], data: HistoryInputs, binding: str) -> None:
    common(row, data, binding)
    order = row["order"]
    if type(order) is not int or not 0 <= order < 8:
        raise ArithmeticError("history profile order changed")
    labels = data.config["current_work_labels"]
    if order < 5:
        kind, variant, label = "current", f"current-{labels[order]}", labels[order]
        if row["coverage"] is not None or row["window"] is not None:
            raise ArithmeticError("current profile cannot claim average/window support")
        if (row["current_movement"] is None) != (order == 0):
            raise ArithmeticError("current movement sequence incomplete")
    else:
        kind = "whole_average" if order == 5 else "suffix"
        variant = ("whole_average", "suffix_5m_10m", "suffix_9m_10m")[order - 5]
        label = data.config["source_target"]
        if row["coverage"] is None or row["current_movement"] is not None:
            raise ArithmeticError("average profile support/movement changed")
        if (row["window"] is None) != (order == 5):
            raise ArithmeticError("suffix window missing or assigned to whole average")
    if (
        not same(row["work_label"], label)
        or row["kind"] != kind
        or row["variant"] != variant
        or row["id"] != f"case-{row['index']:03d}-{variant}"
    ):
        raise ArithmeticError("history profile identity/kind/work changed")
    if set(row["metrics"]) != {
        "exact_exploitability_chips",
        "within_partition_gain_chips",
        "extra_information_gap_chips",
        "river_only_gain_exact_prefix_chips",
        "value_player_zero_chips",
    } or any(not number(v) for v in row["metrics"].values()):
        raise ArithmeticError("invalid history own score inventory/values")
    if (
        len(row["responses"]) != 2
        or not same([r["target"] for r in row["responses"]], [0, 1])
        or len(row["reply_sha256"]) != 2
        or not number(row["maximum_accounting_error"], nonnegative=True)
        or row["maximum_accounting_error"] > data.config["tolerance_chips"]
    ):
        raise ArithmeticError("history target/reply/accounting inventory changed")


def mass(row: dict[str, Any], data: HistoryInputs, binding: str) -> None:
    common(row, data, binding)
    order = row["order"]
    if type(order) is not int or not 0 <= order < 3:
        raise ArithmeticError("history mass boundary order changed")
    label = data.config["cumulative_mass_work_labels"][order]
    if (
        row["kind"] != "cumulative_mass"
        or not same(row["work_label"], label)
        or row["id"] != f"case-{row['index']:03d}-mass-{label}"
    ):
        raise ArithmeticError("history mass boundary identity changed")


def grid(
    rows: list[dict[str, Any]],
    masses: list[dict[str, Any]],
    data: HistoryInputs,
    binding: str,
) -> None:
    if (
        len(rows) != 512
        or len(masses) != 192
        or [(r["index"], r["order"]) for r in rows]
        != [(i, j) for i in range(64) for j in range(8)]
        or [(r["index"], r["order"]) for r in masses]
        != [(i, j) for i in range(64) for j in range(3)]
    ):
        raise ArithmeticError("history policy/mass grid incomplete or misordered")
    for row in rows:
        profile(row, data, binding)
    for row in masses:
        mass(row, data, binding)
    # Different averaging readouts must preserve the entire raw path at every label.
    pairs: dict[tuple[str, int], list[dict[str, Any]]] = {}
    fields = tuple(k for k in KEY if k != "average_weight")
    for row in rows:
        if row["kind"] == "current":
            key = identity(row["case"], fields), row["work_label"]
            pairs.setdefault(key, []).append(row)
    if len(pairs) != 160:
        raise ArithmeticError("history current-pair inventory changed")
    for chosen in pairs.values():
        if len(chosen) != 2 or {r["case"]["average_weight"] for r in chosen} != {
            "uniform",
            "linear",
        }:
            raise ArithmeticError("current average-weight pair missing")
        a, b = chosen
        if (
            any(
                not same(a[k], b[k])
                for k in (
                    "learning_path_sha256",
                    "iteration",
                    "total_work",
                    "previous_work",
                    "last_iteration_visits",
                )
            )
            or a["receipt"]["policy_sha256"] != b["receipt"]["policy_sha256"]
        ):
            raise ArithmeticError("average weights changed raw learning/current path")


def gather(
    batch: dict[str, Any], data: HistoryInputs, binding: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(64, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("history worker batch incomplete/changed")
    rows: list[dict[str, Any]] = []
    masses: list[dict[str, Any]] = []
    seen_prefixes, trained = set(), set()
    for worker, indices in zip(batch["workers"], partition(64, 3), strict=True):
        started = [e for e in worker["messages"] if e["kind"] == "started"]
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            worker["exitcode"] != 0
            or len(started) != 1
            or len(done) != 1
            or not same(started[0]["thread_environment"], THREAD_ENV)
            or not same(
                done[0]["summary"],
                dict(
                    cells=len(indices),
                    profiles=8 * len(indices),
                    masses=3 * len(indices),
                    prefixes=3 * len(indices),
                ),
            )
        ):
            raise ArithmeticError("history worker environment/completion changed")
        for event in worker["messages"]:
            if event["kind"] != "cell":
                continue
            index = event["index"]
            if type(index) is not int or index not in indices:
                raise ArithmeticError("history event assigned to wrong worker")
            source = data.base.policies[index]
            if event["phase"] in ("profile", "mass"):
                if not same(event["row"]["index"], index):
                    raise ArithmeticError("history row source index changed")
                (rows if event["phase"] == "profile" else masses).append(event["row"])
            elif event["phase"] == "prefix":
                threshold = event["work_label"]
                if type(threshold) is not int or (index, threshold) in seen_prefixes:
                    raise ArithmeticError("history original prefix duplicate/invalid")
                peer = data.prefixes[source.identifier, threshold]
                if any(
                    not same(event[k], peer[old])
                    for k, old in {
                        "source_snapshot_id": "id",
                        "state_sha256": "state_sha256",
                        "iteration": "iteration",
                        "total_work": "total_work",
                    }.items()
                ):
                    raise ArithmeticError("history original prefix binding changed")
                seen_prefixes.add((index, threshold))
            elif event["phase"] == "trained":
                if (
                    index in trained
                    or not same(
                        [event[k] for k in ("prefixes", "profiles", "masses")],
                        [3, 8, 3],
                    )
                    or not same(event["work"], source.row["total_work"])
                    or not same(event["iteration"], source.row["iteration"])
                ):
                    raise ArithmeticError(
                        "history case did not complete source trajectory"
                    )
                trained.add(index)
            else:
                raise ArithmeticError("unexpected history worker phase")
    if seen_prefixes != {
        (i, t) for i in range(64) for t in data.config["original_average_replay_labels"]
    } or trained != set(range(64)):
        raise ArithmeticError("history case/prefix grid incomplete")
    rows.sort(key=lambda r: (r["index"], r["order"]))
    masses.sort(key=lambda r: (r["index"], r["order"]))
    grid(rows, masses, data, binding)
    return rows, masses
