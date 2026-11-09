"""Complete intervention identities and strict typed source/score receipts."""

from typing import Any

from poker_ai.evaluation.controlled_reply_inputs import modes
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs
from poker_ai.evaluation.window_fallback_math import LABELS, MASKS
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same

FORMAT = "poker-ai-window-fallback-v1"


def static_fields(
    index: int,
    order: int,
    data: FallbackInputs,
    binding: str,
) -> dict[str, Any]:
    source = data.history.base.policies[index // 2]
    variant = data.config["suffix_variants"][index % 2]
    peers = [
        r
        for r in data.saved["rows"]
        if r["index"] == index // 2 and r["variant"] == variant
    ]
    if len(peers) != 1:
        raise ArithmeticError("original window source missing or duplicated")
    peer = peers[0]
    return dict(
        id=f"window-{index:03d}-{LABELS[order]}",
        index=index,
        order=order,
        case=source.case,
        source_case_index=index // 2,
        source_profile_id=source.identifier,
        source_window_id=peer["id"],
        window_variant=variant,
        source_window_policy_sha256=peer["receipt"]["policy_sha256"],
        whole_policy_sha256=source.row["receipt"]["policy_sha256"],
        window_mass_sha256=peer["window"]["increment_mass_sha256"],
        window_definition=peer["window"],
        upstream_iteration=peer["iteration"],
        upstream_work=peer["total_work"],
        source_sha256=binding,
        fill_label=LABELS[order],
        fill_targets=list(MASKS[order]),
    )


def support(row: dict[str, Any], data: FallbackInputs) -> None:
    reports = row["support"]
    if len(reports) != 2 or not same([r["target"] for r in reports], [0, 1]):
        raise ArithmeticError("fallback support target inventory changed")
    tree = data.history.base.context(row["case"]).partition
    for target, r in enumerate(reports):
        counts = (
            "owned_rows",
            "eligible_rows",
            "eligible_river_rows",
            "changed_rows",
            "changed_river_rows",
        )
        if (
            any(type(r[k]) is not int or r[k] < 0 for k in counts)
            or r["owned_rows"] != int((tree.owners == target).sum())
            or not 0 <= r["changed_rows"] <= r["eligible_rows"] <= r["owned_rows"]
            or not 0
            <= r["changed_river_rows"]
            <= min(r["changed_rows"], r["eligible_river_rows"])
            or r["eligible_river_rows"] > r["eligible_rows"]
            or r["selected"] is not (target in row["fill_targets"])
            or (not r["selected"] and r["changed_rows"] != 0)
        ):
            raise ArithmeticError("fallback support counts or ownership changed")
        for key in (
            "eligible_uniform_reach_fraction",
            "maximum_own_reach_at_eligible_histories",
            "eligible_river_uniform_reach_fraction",
            "maximum_own_reach_at_eligible_river_histories",
        ):
            if key.endswith("uniform_reach_fraction") and r[key] is None:
                continue
            if (
                not number(r[key], nonnegative=True)
                or r[key] > 1 + data.config["tolerance_unitless"]
            ):
                raise ArithmeticError("nonfinite/out-of-range fallback reach")


def grid(saved: dict[str, Any], data: FallbackInputs) -> None:
    rows, panels, matches = saved["rows"], saved["panels"], saved["fixed_matches"]
    if len(rows) != 512 or len(panels) != 128 or len(matches) != 2048:
        raise ArithmeticError("incomplete fallback profile/panel/fixed grid")
    binding = saved["source_sha256"]
    for position, row in enumerate(rows):
        i, j = divmod(position, 4)
        expected = static_fields(i, j, data, binding)
        if any(not same(row[k], v) for k, v in expected.items()):
            raise ArithmeticError("fallback profile source/mask/order binding changed")
        if row["file"] != f"snapshots/{row['id']}.json.gz":
            raise ArithmeticError("fallback relative snapshot path changed")
        hashes = [
            row[k] for k in ("metadata_sha256", "eligible_sha256", "changed_sha256")
        ]
        hashes.extend(row["receipt"][k] for k in ("sha256", "policy_sha256"))
        if (
            any(
                not isinstance(v, str)
                or len(v) != 64
                or any(c not in "0123456789abcdef" for c in v)
                for v in hashes
            )
            or type(row["receipt"]["bytes"]) is not int
            or row["receipt"]["bytes"] <= 0
            or (
                j == 0
                and row["receipt"]["policy_sha256"]
                != expected["source_window_policy_sha256"]
            )
        ):
            raise ArithmeticError("invalid fallback byte/policy/mask receipt")
        metrics = row["metrics"]
        if (
            set(metrics)
            != {
                "exact_exploitability_chips",
                "within_partition_gain_chips",
                "extra_information_gap_chips",
                "river_only_gain_exact_prefix_chips",
                "value_player_zero_chips",
            }
            or any(not number(v) for v in metrics.values())
            or len(row["responses"]) != 2
            or not same([r["target"] for r in row["responses"]], [0, 1])
            or len(row["reply_sha256"]) != 2
            or not number(row["maximum_accounting_error"], nonnegative=True)
            or row["maximum_accounting_error"] > data.config["tolerance_chips"]
        ):
            raise ArithmeticError("invalid fallback score/response inventory")
        support(row, data)
        value = row["maximum_realization_change"]
        if (
            not number(value, nonnegative=True)
            or value > 1 + data.config["tolerance_unitless"]
        ):
            raise ArithmeticError("invalid fallback realization change")
        if (
            row["case"]["traversal"] == "full"
            and value > data.config["tolerance_unitless"]
        ):
            raise ArithmeticError("full fallback realization gate failed")
    for index, panel in enumerate(panels):
        raw = rows[4 * index]
        if any(
            not same(panel[k], raw[k])
            for k in (
                "index",
                "case",
                "source_profile_id",
                "source_window_id",
                "window_variant",
            )
        ):
            raise ArithmeticError("fallback accounting panel source/order changed")
        for key in ("maximum_error_chips", "raw_control_error_chips"):
            if (
                not number(panel[key], nonnegative=True)
                or panel[key] > data.config["tolerance_chips"]
            ):
                raise ArithmeticError("fallback accounting/control error")
        if not number(panel["baseline_ev_interaction_chips"]):
            raise ArithmeticError("invalid fallback EV interaction")
        full = raw["case"]["traversal"] == "full"
        error = panel["full_control_error_chips"]
        if (not full and error is not None) or (
            full
            and (
                not number(error, nonnegative=True)
                or error > data.config["tolerance_chips"]
            )
        ):
            raise ArithmeticError("fallback full-control panel missing/changed")
        if not same(
            panel["maximum_realization_change"],
            max(
                r["maximum_realization_change"] for r in rows[4 * index : 4 * index + 4]
            ),
        ):
            raise ArithmeticError("fallback panel realization summary changed")
    fixed_grid(matches, rows, data)


def fixed_grid(
    matches: list[dict[str, Any]], rows: list[dict[str, Any]], data: FallbackInputs
) -> None:
    mode_order = {m: i for i, m in enumerate(modes(data.config))}
    position = 0
    for index in range(128):
        source = data.history.base.policies[index // 2]
        opponents = sorted(
            (p for p in data.history.base.policies if p.group == source.group),
            key=lambda p: mode_order[p.mode],
        )
        if len(opponents) != 4:
            raise ArithmeticError("fallback fixed opponent inventory changed")
        baseline = {}
        for order in (0, 3):
            own = rows[4 * index + order]
            for opponent in opponents:
                for target in (0, 1):
                    row = matches[position]
                    position += 1
                    expected = dict(
                        index=index,
                        case=source.case,
                        source_window_id=own["source_window_id"],
                        window_variant=own["window_variant"],
                        fill_label=own["fill_label"],
                        own_snapshot_id=own["id"],
                        own_source_profile_id=source.identifier,
                        own_variant=own["window_variant"] + "/" + own["fill_label"],
                        own_policy_sha256=own["receipt"]["policy_sha256"],
                        opponent_profile_id=opponent.identifier,
                        opponent_case=opponent.case,
                        opponent_policy_sha256=opponent.row["receipt"]["policy_sha256"],
                        reply_sha256=opponent.row["reply_sha256"][target]["restricted"],
                        target=target,
                    )
                    if any(not same(row[k], v) for k, v in expected.items()):
                        raise ArithmeticError(
                            "fallback fixed target/source/reply changed"
                        )
                    values = (
                        "baseline_value_chips",
                        "restricted_reply_value_chips",
                        "achieved_reply_value_chips",
                        "gain_chips",
                        "gain_difference_chips",
                        "ev_difference_chips",
                    )
                    if any(not number(row[k]) for k in values):
                        raise ArithmeticError("nonfinite fallback fixed value")
                    key = opponent.identifier, target
                    if order == 0:
                        baseline[key] = row
                    raw = baseline[key]
                    errors = [
                        abs(
                            row["restricted_reply_value_chips"]
                            - row["achieved_reply_value_chips"]
                        ),
                        abs(
                            row["gain_chips"]
                            - row["restricted_reply_value_chips"]
                            + row["baseline_value_chips"]
                        ),
                        abs(
                            row["restricted_reply_value_chips"]
                            - raw["restricted_reply_value_chips"]
                        ),
                        abs(
                            row["gain_difference_chips"]
                            - (row["gain_chips"] - raw["gain_chips"])
                        ),
                        abs(
                            row["ev_difference_chips"]
                            - (
                                row["baseline_value_chips"]
                                - raw["baseline_value_chips"]
                            )
                        ),
                        abs(row["gain_difference_chips"] + row["ev_difference_chips"]),
                    ]
                    if source.case["traversal"] == "full":
                        errors.extend(
                            abs(row[k])
                            for k in ("gain_difference_chips", "ev_difference_chips")
                        )
                    if (
                        row["gain_chips"] < -data.config["tolerance_chips"]
                        or max(errors) > data.config["tolerance_chips"]
                    ):
                        raise ArithmeticError(
                            "fallback fixed root/gain/EV identity failed"
                        )


def validate_replay(proof: dict[str, Any], config: dict[str, Any]) -> None:
    if not isinstance(proof, dict):
        raise ArithmeticError("missing fallback replay proof")
    fixed = dict(
        status="all_window_fallback_profiles_and_targets_replayed",
        new_postflop_training_performed=False,
        source_windows=128,
        profiles=512,
        raw_window_controls=128,
        full_windows=32,
        additivity_panels=128,
        fixed_target_conditions=2048,
    )
    if any(not same(proof[k], v) for k, v in fixed.items()) or not number(
        proof["seconds"], nonnegative=True
    ):
        raise ArithmeticError("incomplete/changed fallback replay proof")
    for key, limit in dict(
        maximum_error_chips=config["tolerance_chips"],
        maximum_error_unitless=config["tolerance_unitless"],
        maximum_full_control_error_chips=config["tolerance_chips"],
        maximum_full_realization_change=config["tolerance_unitless"],
    ).items():
        if not number(proof[key], nonnegative=True) or proof[key] > limit:
            raise ArithmeticError("fallback replay numerical gate failed")
