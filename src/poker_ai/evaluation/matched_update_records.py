"""Complete identities, immutable capture lineage and paired own score accounting."""

from typing import Any

from poker_ai.evaluation.matched_update_capture import barrier
from poker_ai.postflop.parallel_profile import same

OUTER = {"file", "receipt", "metadata_sha256", "seconds", "cpu_seconds"}


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k not in OUTER}


def inventory(
    saved: dict[str, Any], manifest: dict[str, Any], expected: list[dict[str, Any]]
) -> None:
    """Validate the complete prospective shape; a toy shape is never admission."""
    barrier(saved["checkpoints"], expected)
    targets = {t["id"]: t for t in manifest["iteration_targets"]}
    pairs = {p["planned_prefix_id"]: p for p in manifest["self_pairs"]}
    if len(targets) != 48 or len(pairs) != 144:
        raise ArithmeticError("complete matched-update manifest required")
    for name, wanted in (
        ("captures", set(pairs)),
        ("masses", {t + "-" + w for t in targets for w in ("uniform", "linear")}),
    ):
        rows = saved[name]
        if len(rows) != len(wanted) or {r["id"] for r in rows} != wanted:
            raise ArithmeticError("incomplete/duplicate matched capture inventory")
        for row in rows:
            target = targets[row["target_id"]]
            if any(
                type(row[k]) is not int
                for k in (
                    "iteration",
                    "path_index",
                    "comparison_batch_size",
                    "total_work",
                    "previous_work",
                    "last_iteration_visits",
                    "initialization_visits",
                    "sampled_traversals",
                )
            ) or any(
                not same(row[k], v)
                for k, v in dict(
                    iteration=target["target_iteration"],
                    path_index=target["baseline_path_index"],
                    comparison_batch_size=target["comparison_batch_size"],
                    batch_size=1,
                    source_sha256=saved["source_sha256"],
                    scope=saved["scope"],
                ).items()
            ):
                raise ArithmeticError("capture target/source/coordinate changed")
            if row["total_work"] < row["initialization_visits"] or (
                row["last_iteration_visits"] != row["total_work"] - row["previous_work"]
            ):
                raise ArithmeticError("capture work accounting changed")
            readout = row["readout"]
            if row["id"] != row["target_id"] + "-" + readout:
                raise ArithmeticError("capture readout identity changed")
            if name == "captures" and readout != pairs[row["id"]]["readout"]:
                raise ArithmeticError("capture readout changed")
            if name == "masses" and readout not in ("uniform", "linear"):
                raise ArithmeticError("mass readout changed")


def lineage(row: dict[str, Any], captured: dict[str, Any]) -> None:
    """Scoring adds own metrics but cannot change a policy or its capture source."""
    if any(not same(row.get(k), v) for k, v in metadata(captured).items()) or (
        row["receipt"]["policy_sha256"] != captured["receipt"]["policy_sha256"]
        or row["capture_sha256"] != captured["receipt"]["sha256"]
        or row["capture_metadata_sha256"] != captured["metadata_sha256"]
    ):
        raise ArithmeticError("scored policy changed its immutable capture lineage")


def paired_self(
    manifest: dict[str, Any], left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    a, b = {r["id"]: r for r in left}, {r["id"]: r for r in right}
    if len(a) != 144 or len(b) != 144 or len(left) != 144 or len(right) != 144:
        raise ArithmeticError("all matched self profiles required")
    result = []
    for pair in manifest["self_pairs"]:
        x, y = a[pair["planned_prefix_id"]], b[pair["reused_profile_id"]]
        if (
            x["iteration"] != y["iteration"]
            or x["iteration"] != pair["target_iteration"]
            or (y["receipt"]["policy_sha256"] != pair["reused_policy_sha256"])
            or any(
                not same(x["case"][k], y["case"][k])
                for k in (
                    "spot_file",
                    "representation",
                    "regret_rule",
                    "seed",
                )
            )
            or set(x["metrics"]) != set(y["metrics"])
        ):
            raise ArithmeticError("matched profile coordinate/case/hash changed")
        result.append(
            dict(
                **pair,
                prefix_total_work=x["total_work"],
                batched_total_work=y["total_work"],
                difference_prefix_minus_batched_chips={
                    k: x["metrics"][k] - y["metrics"][k] for k in x["metrics"]
                },
            )
        )
    return result


def paired_fixed(
    manifest: dict[str, Any], left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Same opponent, seat and best-reply root; EV and gain contrasts sum to zero."""

    def index(rows: list[dict[str, Any]]) -> dict[Any, Any]:
        result = {
            (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
            for r in rows
        }
        if (
            len(result) != 1152
            or len(rows) != 1152
            or any(
                type(r["target"]) is not int or r["target"] not in (0, 1) for r in rows
            )
        ):
            raise ArithmeticError("complete unique fixed target inventory required")
        return result

    a, b = index(left), index(right)
    result = []
    used_a, used_b = set(), set()
    for pair in manifest["self_pairs"]:
        prefix, batched = pair["planned_prefix_id"], pair["reused_profile_id"]
        keys = [
            (opponent, seat) for identifier, opponent, seat in a if identifier == prefix
        ]
        if len(keys) != 8 or len({p for p, _ in keys}) != 4:
            raise ArithmeticError(
                "each matched policy needs four own opponents/two seats"
            )
        for opponent, seat in sorted(keys):
            ka, kb = (prefix, opponent, seat), (batched, opponent, seat)
            x, y = a[ka], b[kb]
            if any(
                not same(x[k], y[k])
                for k in (
                    "opponent_policy_sha256",
                    "reply_sha256",
                    "restricted_reply_value_chips",
                    "achieved_reply_value_chips",
                )
            ):
                raise ArithmeticError("matched fixed opponent/reply/root changed")
            ev = x["baseline_value_chips"] - y["baseline_value_chips"]
            gain = x["gain_chips"] - y["gain_chips"]
            if abs(ev + gain) > 1e-9:
                raise ArithmeticError("fixed EV/gain contrast accounting failed")
            result.append(
                dict(
                    target_id=pair["target_id"],
                    readout=pair["readout"],
                    opponent_profile_id=opponent,
                    target=seat,
                    difference_prefix_minus_batched_ev_chips=ev,
                    difference_prefix_minus_batched_gain_chips=gain,
                )
            )
            used_a.add(ka)
            used_b.add(kb)
    if used_a != set(a) or used_b != set(b):
        raise ArithmeticError("unpaired fixed target")
    return result
