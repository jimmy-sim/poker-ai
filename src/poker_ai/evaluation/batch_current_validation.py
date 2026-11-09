"""Complete source-bound216 current profiles and1728 original fixed targets."""

from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same

CURRENT_KEYS = set(
    (
        "id",
        "path_index",
        "case",
        "batch_size",
        "work_label",
        "variant",
        "origin",
        "source_current_id",
        "source_current_policy_sha256",
        "source_guard_sha256",
        "source_study_sha256",
        "source_sha256",
        "iteration",
        "total_work",
        "metrics",
        "responses",
        "reply_sha256",
        "maximum_accounting_error",
        "file",
        "receipt",
        "metadata_sha256",
        "seconds",
        "cpu_seconds",
    )
)
FIXED_KEYS = set(
    (
        "target",
        "baseline_value_chips",
        "restricted_reply_value_chips",
        "achieved_reply_value_chips",
        "gain_chips",
        "path_index",
        "case",
        "batch_size",
        "work_label",
        "own_snapshot_id",
        "own_source_profile_id",
        "own_variant",
        "opponent_profile_id",
        "own_policy_sha256",
        "opponent_policy_sha256",
        "reply_sha256",
        "source_sha256",
    )
)


def grid(
    rows: list[dict[str, Any]],
    fixed: list[dict[str, Any]],
    sources: inputs.Sources,
    binding: str,
) -> None:
    source = {r["id"]: r for r in sources.own["currents"]}
    if (
        len(rows) != 216
        or len(source) != 216
        or [r["id"] for r in rows] != list(source)
    ):
        raise ArithmeticError("current profile grid/order incomplete")
    work = {
        (r["path_index"], r["work_label"]): r
        for r in sources.own["rows"]
        if r["path_index"] < 72 and r["case"]["average_weight"] == "linear"
    }
    for row in rows:
        peer = source[row["id"]]
        checkpoint = work[peer["path_index"], peer["work_label"]]
        if (
            set(row) != CURRENT_KEYS
            or row["file"] != "snapshots/" + row["id"] + ".json.gz"
            or any(
                not number(row[k], nonnegative=True)
                for k in ("seconds", "cpu_seconds", "maximum_accounting_error")
            )
            or any(not same(row[k], checkpoint[k]) for k in ("iteration", "total_work"))
        ):
            raise ArithmeticError("current schema/work/elapsed changed")
        if (
            any(
                not same(row[k], peer[k])
                for k in ("id", "path_index", "case", "batch_size", "work_label")
            )
            or row["variant"] != "current"
            or row["origin"] != "saved_current_rescored_no_training"
            or row["source_current_id"] != peer["id"]
            or row["source_guard_sha256"] != peer["guard_sha256"]
            or row["source_study_sha256"] != sources.own["source_sha256"]
            or row["source_sha256"] != binding
            or row["receipt"]["policy_sha256"] != peer["receipt"]["policy_sha256"]
            or row["source_current_policy_sha256"] != peer["receipt"]["policy_sha256"]
            or any(not number(v) for v in row["metrics"].values())
        ):
            raise ArithmeticError("rescored current source/policy binding changed")
    final = inputs.candidates(sources)
    candidate = {r["id"]: r for r in final}
    opponents = {p.identifier: p for p in full_sources(sources.data)}
    expected = {
        (r["id"], p.identifier, t)
        for r in final
        for p in opponents.values()
        if all(p.case[k] == r["case"][k] for k in ("spot_file", "representation"))
        for t in (0, 1)
    }
    found = []
    for row in fixed:
        if set(row) != FIXED_KEYS:
            raise ArithmeticError("fixed target fields changed")
        key = row["own_snapshot_id"], row["opponent_profile_id"], row["target"]
        if key not in expected or type(row["target"]) is not int:
            raise ArithmeticError("fixed target identity changed")
        c = candidate[key[0]]
        o = opponents[key[1]]
        tree = sources.data.base.context(c["case"]).partition
        reply = sources.data.replies[o.identifier, key[2]]
        if (
            any(
                not same(row[k], c[k])
                for k in ("path_index", "case", "work_label", "batch_size")
            )
            or row["own_variant"] != c["variant"]
            or row["own_policy_sha256"] != c["policy_sha256"]
            or row["own_source_profile_id"] != c["id"]
            or row["opponent_policy_sha256"] != o.row["receipt"]["policy_sha256"]
            or row["reply_sha256"] != array_sha(reply.apply(tree, o.policy))
            or row["source_sha256"] != binding
            or any(
                not number(row[k])
                for k in (
                    "baseline_value_chips",
                    "restricted_reply_value_chips",
                    "achieved_reply_value_chips",
                    "gain_chips",
                )
            )
            or row["gain_chips"] < -1e-9
            or abs(
                row["restricted_reply_value_chips"]
                - row["baseline_value_chips"]
                - row["gain_chips"]
            )
            > 1e-9
            or abs(row["restricted_reply_value_chips"] - reply.root) > 1e-9
            or abs(row["achieved_reply_value_chips"] - reply.root) > 1e-9
        ):
            raise ArithmeticError("fixed target source/root/value binding changed")
        found.append(key)
    if (
        len(found) != 1728
        or len(set(found)) != 1728
        or set(found) != expected
        or found != sorted(found)
    ):
        raise ArithmeticError("fixed target grid incomplete/duplicate/order changed")


def gather(
    batch: dict[str, Any], sources: inputs.Sources, binding: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(72, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("incomplete saved-current worker batch")
    rows = []
    fixed = []
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("saved-current worker failed")
        local_self = local_fixed = 0
        for e in worker["messages"]:
            if e["kind"] == "cell":
                if (
                    type(e["index"]) is not int
                    or e["index"] not in assigned
                    or not same(e["index"], e["row"]["path_index"])
                ):
                    raise ArithmeticError("saved-current row assigned incorrectly")
                if e["phase"] == "profile":
                    rows.append(e["row"])
                    local_self += 1
                elif e["phase"] == "fixed":
                    fixed.append(e["row"])
                    local_fixed += 1
                else:
                    raise ArithmeticError("unknown saved-current worker row")
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            local_self != 72
            or local_fixed != 576
            or len(done) != 1
            or not same(
                done[0]["summary"],
                dict(
                    paths=24, self_profiles=72, fixed_targets=576, final_candidates=72
                ),
            )
        ):
            raise ArithmeticError("saved-current completion inventory changed")
    rows.sort(key=lambda r: (r["path_index"], r["work_label"]))
    fixed.sort(
        key=lambda r: (r["own_snapshot_id"], r["opponent_profile_id"], r["target"])
    )
    grid(rows, fixed, sources, binding)
    return rows, fixed
