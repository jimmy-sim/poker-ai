"""Complete grids and typed work/case/source contracts for own batch evidence."""

from pathlib import PurePosixPath
from typing import Any

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.controlled_reply_inputs import identity
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same


def full_sources(data: HistoryInputs) -> list[Any]:
    return [p for p in data.base.policies if p.case["traversal"] == "full"]


def validate_row(
    row: dict[str, Any], data: HistoryInputs, config: dict[str, Any], binding: str
) -> None:
    index, label = row["path_index"], row["work_label"]
    if (
        not isinstance(row["file"], str)
        or PurePosixPath(row["file"]).is_absolute()
        or ".." in PurePosixPath(row["file"]).parts
    ):
        raise ArithmeticError("unsafe batch snapshot path")
    if (
        type(index) is not int
        or not 0 <= index < 88
        or type(label) is not int
        or label not in config["work_labels"]
    ):
        raise ArithmeticError("batch profile identity changed")
    case = row["case"]
    if index < 72:
        path = inputs.paths(config)[index]
        weight = case["average_weight"]
        if weight not in ("uniform", "linear"):
            raise ArithmeticError("invalid batch readout weight")
        expected = dict(
            case=inputs.case(path, weight),
            batch_size=path["batch_size"],
            origin="fresh_B1_replay" if path["batch_size"] == 1 else "fresh_batch",
            id=f"path-{index:03d}-{weight}-{label}",
            source_original_id=data.prefixes[
                identity(inputs.case(path, weight)), label
            ]["id"]
            if path["batch_size"] == 1
            else None,
        )
        if (
            type(row["sampled_traversals"]) is not int
            or row["sampled_traversals"]
            != 2 * path["batch_size"] * (row["iteration"] - 1)
            or not isinstance(row["coverage"], dict)
            or set(row["coverage"]) != {"whole", "post_warm"}
            or (row["current_movement"] is None) != (label == config["work_labels"][0])
        ):
            raise ArithmeticError("batch traversal/coverage/movement changed")
        context = data.base.context(case)
        if row["initialization_visits"] != 2 * len(context.partition.player):
            raise ArithmeticError("batch warm initialization work changed")
        if path["batch_size"] == 1:
            peer = data.prefixes[identity(inputs.case(path, weight)), label]
            if row["receipt"]["policy_sha256"] != peer["receipt"][
                "policy_sha256"
            ] or any(
                not same(row[k], peer[k])
                for k in (
                    "iteration",
                    "previous_work",
                    "total_work",
                    "last_iteration_visits",
                    "initialization_visits",
                    "state_sha256",
                )
            ):
                raise ArithmeticError("B1 profile no longer matches original prefix")
    else:
        source = full_sources(data)[index - 72]
        peer = data.prefixes[source.identifier, label]
        expected = dict(
            case=source.case,
            batch_size=None,
            origin="reused_full",
            id=f"full-{index - 72:02d}-{label}",
            source_original_id=peer["id"],
            coverage=None,
            current_movement=None,
            current_sha256=None,
            guard_sha256=None,
            sampled_traversals=0,
        )
        if any(
            not same(row[k], peer[k])
            for k in (
                "iteration",
                "previous_work",
                "total_work",
                "last_iteration_visits",
                "initialization_visits",
                "state_sha256",
            )
        ):
            raise ArithmeticError("reused full source prefix changed")
        if row["receipt"]["policy_sha256"] != peer["receipt"]["policy_sha256"]:
            raise ArithmeticError("reused full source policy changed")
    if (
        any(not same(row[k], v) for k, v in expected.items())
        or row["source_sha256"] != binding
    ):
        raise ArithmeticError("batch profile case/origin/source binding changed")
    for k in (
        "iteration",
        "previous_work",
        "total_work",
        "last_iteration_visits",
        "initialization_visits",
        "overshoot",
    ):
        if type(row[k]) is not int or row[k] < 0:
            raise ArithmeticError("batch work counters must be typed integers")
    if (
        row["iteration"] < 1
        or row["initialization_visits"] <= 0
        or not row["previous_work"] < label <= row["total_work"]
        or row["total_work"] - row["previous_work"] != row["last_iteration_visits"]
        or row["overshoot"] != row["total_work"] - label
    ):
        raise ArithmeticError("batch did not retain first whole-iteration crossing")
    if set(row["metrics"]) != {*data.base.policies[0].row["metrics"]} or any(
        not number(v) for v in row["metrics"].values()
    ):
        raise ArithmeticError("invalid own batch metric grid")
    if (
        not number(row["maximum_accounting_error"], nonnegative=True)
        or row["maximum_accounting_error"] > 1e-9
        or len(row["responses"]) != 2
        or len(row["reply_sha256"]) != 2
        or not same([x["target"] for x in row["responses"]], [0, 1])
    ):
        raise ArithmeticError("batch response/accounting inventory changed")
    for k in ("state_sha256",):
        h = row[k]
        if (
            not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdef" for c in h)
        ):
            raise ArithmeticError("invalid own batch state fingerprint")


def grid(
    rows: list[dict[str, Any]],
    data: HistoryInputs,
    config: dict[str, Any],
    binding: str,
) -> None:
    expected = {
        (i, w, t)
        for i in range(72)
        for w in ("uniform", "linear")
        for t in config["work_labels"]
    }
    expected |= {
        (72 + i, p.case["average_weight"], t)
        for i, p in enumerate(full_sources(data))
        for t in config["work_labels"]
    }
    found = []
    for row in rows:
        validate_row(row, data, config, binding)
        found.append(
            (row["path_index"], row["case"]["average_weight"], row["work_label"])
        )
    if len(rows) != 480 or len(set(found)) != 480 or set(found) != expected:
        raise ArithmeticError("missing/duplicate batch profile grid")
    if found != sorted(found):
        raise ArithmeticError("batch profile order must be canonical")


def gather(
    batch: dict[str, Any], selected: list[int]
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or len(batch["workers"]) != 3
        or not same(batch["assignments"], partition(len(selected), 3))
    ):
        raise ArithmeticError("incomplete batch learning phase")
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    masses: list[dict[str, Any]] = []
    currents: list[dict[str, Any]] = []
    trained = []
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("batch learning worker failed")
        global_indices = [selected[i] for i in assigned]
        for event in worker["messages"]:
            if event["kind"] != "cell":
                continue
            if type(event["index"]) is not int or event["index"] not in global_indices:
                raise ArithmeticError("learning path assigned incorrectly")
            if event["phase"] == "profile":
                if event["row"]["path_index"] != event["index"]:
                    raise ArithmeticError("learning event path mismatch")
                rows.append(event["row"])
            elif event["phase"] == "prefix":
                checks.append(dict(index=event["index"], **event["check"]))
            elif event["phase"] in ("current", "mass"):
                if event["row"]["path_index"] != event["index"]:
                    raise ArithmeticError("observation event path mismatch")
                (currents if event["phase"] == "current" else masses).append(
                    event["row"]
                )
            elif event["phase"] == "trained":
                trained.append(event["index"])
                if event["profiles"] != 6 or event["prefix_checks"] != (
                    6 if event["index"] < 24 else 0
                ):
                    raise ArithmeticError("path completion inventory changed")
            else:
                raise ArithmeticError("unknown batch learning event phase")
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if len(done) != 1 or not same(
            done[0]["summary"],
            dict(
                paths=len(assigned),
                profiles=6 * len(assigned),
                masses=6 * len(assigned),
                currents=3 * len(assigned),
                prefix_checks=6 * len(assigned) if selected == list(range(24)) else 0,
            ),
        ):
            raise ArithmeticError("learning worker completion incomplete")
    if (
        sorted(trained) != selected
        or len(rows) != 6 * len(selected)
        or len(masses) != 6 * len(selected)
        or len(currents) != 3 * len(selected)
        or len(checks) != (144 if selected == list(range(24)) else 0)
    ):
        raise ArithmeticError("phase rows/prefixes incomplete")
    return rows, checks, masses, currents
