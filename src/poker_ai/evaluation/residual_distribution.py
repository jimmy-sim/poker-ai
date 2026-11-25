"""Read-only additive accounting of already published best-response row gains.

Each row is half a unilateral exact best-response gain in acting-seat chips.
The control and candidate gains use their own saved opponents and optimized
continuations; their difference is an accounting identity, not a causal swap.
"""

import math
from typing import Any


def _sum(values: list[float]) -> float:
    return math.fsum(values)


def _share(part: float, total: float) -> float | None:
    return None if total == 0 else part / total


def _classify(share: float | None, threshold: float) -> str:
    if share is None:
        return "none"
    return "concentrated" if share >= threshold else "distributed"


def summarize_street(
    control: list[float],
    candidate: list[float],
    known_indices: list[int],
    *,
    top_k: int,
    concentration_share: float,
    nonnegative_slack: float,
) -> dict[str, Any]:
    """Rank fixed exact indices and partition signed candidate-control gain.

    All values and totals are chips of NashConv/2. A positive delta worsens
    the candidate; a negative delta offsets that worsening. Positive sums use
    ``math.fsum`` to make the all-row reconciliation numerically stable.
    """
    count = len(control)
    if (
        not count
        or len(candidate) != count
        or not 0 < top_k <= count
        or not 0 < concentration_share <= 1
        or nonnegative_slack < 0
        or len(known_indices) != len(set(known_indices))
        or any(i < 0 or i >= count for i in known_indices)
        or any(not math.isfinite(x) or x < -nonnegative_slack for x in control)
        or any(not math.isfinite(x) or x < -nonnegative_slack for x in candidate)
    ):
        raise ArithmeticError("invalid aligned row contributions")
    delta = [candidate[i] - control[i] for i in range(count)]
    positive = [max(x, 0.0) for x in delta]
    improvement = [max(-x, 0.0) for x in delta]
    candidate_positive = [max(x, 0.0) for x in candidate]
    control_positive = [max(x, 0.0) for x in control]
    candidate_total = _sum(candidate_positive)
    control_total = _sum(control_positive)
    worsening_total = _sum(positive)
    improvement_total = _sum(improvement)
    candidate_rank = sorted(range(count), key=lambda i: (-candidate[i], i))
    worsening_rank = sorted(range(count), key=lambda i: (-delta[i], i))
    improvement_rank = sorted(range(count), key=lambda i: (delta[i], i))
    candidate_top = candidate_rank[:top_k]
    worsening_top = worsening_rank[:top_k]
    improvement_top = improvement_rank[:top_k]
    candidate_one_share = _share(candidate_positive[candidate_rank[0]], candidate_total)
    candidate_ten_share = _share(
        _sum([candidate_positive[i] for i in candidate_top]), candidate_total
    )
    worsening_one_share = _share(positive[worsening_rank[0]], worsening_total)
    worsening_ten_share = _share(
        _sum([positive[i] for i in worsening_top]), worsening_total
    )
    improvement_ten_share = _share(
        _sum([improvement[i] for i in improvement_top]), improvement_total
    )
    return {
        "row_count": count,
        "control_total_chips": control_total,
        "candidate_total_chips": candidate_total,
        "positive_worsening_chips": worsening_total,
        "negative_offset_chips": improvement_total,
        "net_change_chips": _sum(delta),
        "candidate_top_one_share": candidate_one_share,
        "candidate_top_ten_share": candidate_ten_share,
        "worsening_top_one_share": worsening_one_share,
        "worsening_top_ten_share": worsening_ten_share,
        "improvement_top_ten_share": improvement_ten_share,
        "known_candidate_share": _share(
            _sum([candidate_positive[i] for i in known_indices]), candidate_total
        ),
        "known_worsening_share": _share(
            _sum([positive[i] for i in known_indices]), worsening_total
        ),
        "known_improvement_share": _share(
            _sum([improvement[i] for i in known_indices]), improvement_total
        ),
        "candidate_location": _classify(candidate_ten_share, concentration_share),
        "worsening_location": _classify(worsening_ten_share, concentration_share),
        "improvement_location": _classify(improvement_ten_share, concentration_share),
        "candidate_top_indices": candidate_top,
        "worsening_top_indices": worsening_top,
        "improvement_top_indices": improvement_top,
        "known_indices": known_indices,
        "control_vector_chips": control,
        "candidate_vector_chips": candidate,
        "delta_vector_chips": delta,
    }


def analyze_report(report: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """Guard the fixed eight-case grid before deriving any row distribution."""
    games: list[str] = contract["games"]
    arms = (contract["control"], contract["candidate"])
    if (
        report["head"] != contract["report_head"]
        or report["source_fingerprint"] != contract["source_fingerprint"]
        or report["primary"]["classification"] != contract["prior_result"]
        or len(report["cases"]) != 48
        or len(report["diagnostics"]) != 32
        or len(games) != 4
        or len(set(games)) != 4
    ):
        raise ArithmeticError("published report identity changed")
    selected = [
        case
        for case in report["cases"]
        if case["work_label"] == contract["work_label"]
        and case["readout"] == contract["readout"]
    ]
    identities = [(case["game"], case["arm"]) for case in selected]
    if (
        len(selected) != contract["cases"]
        or len(set(identities)) != len(identities)
        or set(identities) != {(game, arm) for game in games for arm in arms}
    ):
        raise ArithmeticError("fixed final case grid changed")
    cases = dict(zip(identities, selected, strict=True))
    known: dict[tuple[str, str], list[int]] = {}
    for game in games:
        for street in ("TURN", "RIVER"):
            indices = [
                int(row["exact_info"])
                for row in report["diagnostics"]
                if row["game"] == game and row["street"] == street
            ]
            if len(indices) != len(set(indices)):
                raise ArithmeticError("duplicate published diagnostic row")
            known[(game, street)] = indices
    tolerance = float(contract["arithmetic_tolerance_chips"])
    paired: list[tuple[str, float]] = []
    all_absolute_pass = True
    for game in games:
        control = cases[(game, arms[0])]
        candidate = cases[(game, arms[1])]
        for case in (control, candidate):
            if (
                case["seed"] != contract["seed_metadata"]
                or case["actual_node_work"] != contract["actual_work"]
                or case["recall_violations"] != 0
                or case["whole_coverage"] is None
                or len(case["policy_sha256"]) != 64
                or case["native_maximum_error_chips"] > tolerance
                or abs(
                    case["exploitability_chips"]
                    - case["exploitability_fraction_initial_pot"]
                    * contract["initial_pot_chips"]
                )
                > tolerance
            ):
                raise ArithmeticError("published case metadata changed")
            street_total = 0.0
            for street in ("turn", "river"):
                vector = case[f"{street}_row_contributions_chips"]
                if (
                    len(vector) != contract["exact_rows_per_street_vector"]
                    or any(not math.isfinite(x) for x in vector)
                    or abs(_sum(vector) - case[f"{street}_contribution_chips"])
                    > tolerance
                ):
                    raise ArithmeticError("published street vector changed")
                street_total += case[f"{street}_contribution_chips"]
            if abs(street_total - case["exploitability_chips"]) > tolerance:
                raise ArithmeticError("published whole score changed")
        if abs(control["actual_node_work"] - candidate["actual_node_work"]) > 0:
            raise ArithmeticError("paired charged work changed")
        prior = report["primary"]["by_game"][game]
        if (
            abs(prior["control"] - control["exploitability_fraction_initial_pot"])
            > tolerance
            or abs(
                prior["candidate"] - candidate["exploitability_fraction_initial_pot"]
            )
            > tolerance
            or abs(
                prior["candidate_minus_control"]
                - (candidate["exploitability_chips"] - control["exploitability_chips"])
                / contract["initial_pot_chips"]
            )
            > tolerance
        ):
            raise ArithmeticError("published paired result changed")
        candidate_fraction = candidate["exploitability_fraction_initial_pot"]
        candidate_pass = (
            candidate_fraction <= contract["absolute_fraction_max"]
            and candidate_fraction <= contract["worst_fraction_max"]
            and candidate["whole_coverage"] >= contract["whole_coverage_min"]
            and candidate["recall_violations"] <= contract["recall_violations_max"]
        )
        if (
            prior["candidate_absolute_pass"]
            != (candidate_fraction <= contract["absolute_fraction_max"])
            or abs(prior["candidate_worst_fraction_initial_pot"] - candidate_fraction)
            > tolerance
        ):
            raise ArithmeticError("published absolute decision changed")
        all_absolute_pass &= candidate_pass
        paired.append((game, prior["candidate_minus_control"]))
    improvements = [
        game
        for game, delta in paired
        if delta <= contract["paired_improvement_fraction_max"]
    ]
    positive = (
        all_absolute_pass
        and len(improvements) >= 3
        and any("dry" in game for game in improvements)
        and any("wet" in game for game in improvements)
        and all(
            delta <= contract["paired_remaining_fraction_max"] for _, delta in paired
        )
    )
    negative = not all_absolute_pass or any(
        delta > contract["paired_remaining_fraction_max"] for _, delta in paired
    )
    classification = (
        "positive" if positive else "negative" if negative else "inconclusive"
    )
    if classification != report["primary"]["classification"]:
        raise ArithmeticError("published strength decision changed")
    output: list[dict[str, Any]] = []
    for game in games:
        control = cases[(game, arms[0])]
        candidate = cases[(game, arms[1])]
        for street in ("turn", "river"):
            summary = summarize_street(
                control[f"{street}_row_contributions_chips"],
                candidate[f"{street}_row_contributions_chips"],
                known[(game, street.upper())],
                top_k=contract["top_k"],
                concentration_share=contract["concentration_share"],
                nonnegative_slack=contract["nonnegative_slack_chips"],
            )
            if (
                abs(
                    summary["control_total_chips"]
                    - control[f"{street}_contribution_chips"]
                )
                > tolerance
                or abs(
                    summary["candidate_total_chips"]
                    - candidate[f"{street}_contribution_chips"]
                )
                > tolerance
                or abs(
                    summary["net_change_chips"]
                    - (
                        candidate[f"{street}_contribution_chips"]
                        - control[f"{street}_contribution_chips"]
                    )
                )
                > tolerance
            ):
                raise ArithmeticError("paired street accounting changed")
            output.append({"game": game, "street": street.upper(), **summary})
    return {
        "status": "analyzed_known_rows",
        "prior_strength_classification": "negative",
        "cases": output,
    }
