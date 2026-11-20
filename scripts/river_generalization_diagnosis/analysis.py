"""Bounded saved-policy best-response attribution, without new learning."""

import gzip
import hashlib
import json
import math
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from river_generalization.gate import require_archive, source_fingerprint
from river_generalization.learning import context

from poker_ai.cards import format_card
from poker_ai.postflop.collision_diagnosis import conditional_actions
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.postflop.river_study import Deadline
from poker_ai.training.no_limit import NoLimitState

PLAN = Path("configs/river-generalization-diagnosis.json")
PLAN_COMMIT = "e832cb8fd0ac28815f69286a8a5ebf794002fee5"
PLAN_SHA256 = "65af83cffbce098b98acca0ac6e7c0bbc529da47c009ff3d524651da57b9d418"
PARENT_FINGERPRINT = "152b357b6942d065e402c84abc14ca3631b29d54551ead71bb668729ccbc81d3"
SOURCE = Path("results/river-generalization/source-checks")
OWN = Path("results/river-generalization/own")
NATIVE = Path("results/river-generalization/native")
REPORT = Path("results/river-generalization/report")
FINAL = Path("results/river-generalization/final-checks")
LABELS = (100_000, 1_000_000, 10_000_000)
SEEDS = (20261371, 20261372, 20261373)
TOLERANCE = 1e-9
FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class Case:
    index: int
    arm: str
    seed: int
    work: int
    path_index: int


def cases() -> tuple[Case, ...]:
    """All declared checkpoints, then the three matched final controls."""
    items: list[Case] = []
    for arm, works, offset in (
        ("q8_turn_exact_river", LABELS, 1),
        ("texture_range_q8_b8", (LABELS[-1],), 0),
    ):
        for seed_index, seed in enumerate(SEEDS):
            for work in works:
                items.append(
                    Case(len(items), arm, seed, work, 6 + 2 * seed_index + offset)
                )
    return tuple(items)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fingerprint_diagnosis(root: Path) -> str:
    """Bind only the isolated diagnostic adapter, plan and parent source ID."""
    paths = sorted((root / "scripts/river_generalization_diagnosis").glob("*.py"))
    paths += [root / "scripts/diagnose_river_generalization.py", root / PLAN]
    paths.append(root / "scripts/inspect_river_generalization_diagnosis.py")
    if len(paths) != 5 or any(path.is_symlink() for path in paths):
        raise ArithmeticError("closed diagnostic source set changed")
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in paths}
    hashes["parent_source_fingerprint"] = PARENT_FINGERPRINT
    return hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify_inputs(root: Path) -> tuple[dict[str, Any], str]:
    """Require a clean normal clone, published plan and immutable old archives."""
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1"], text=True
    )
    if status:
        raise RuntimeError("diagnosis requires a clean published source checkout")
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", PLAN_COMMIT, head],
        check=False,
    ).returncode:
        raise RuntimeError("prospective diagnostic plan absent from history")
    raw = (root / PLAN).read_bytes()
    if (
        hashlib.sha256(raw).hexdigest() != PLAN_SHA256
        or subprocess.check_output(
            ["git", "-C", str(root), "show", f"{PLAN_COMMIT}:{PLAN}"]
        )
        != raw
    ):
        raise ArithmeticError("published diagnostic plan changed")
    plan: dict[str, Any] = json.loads(raw)
    if (
        plan["spot"] != "new_medium_dry_oop"
        or plan["seeds"] != list(SEEDS)
        or plan["policy_grid"]["candidate_linear_average_work"] != list(LABELS)
        or plan["policy_grid"]["control_linear_average_work"] != [LABELS[-1]]
        or plan["policy_grid"]["expected_saved_policies"] != 12
        or plan["policy_grid"]["expected_seat_traces"] != 24
        or plan["wall_cap_seconds_including_startup_and_report"] != 900
        or plan["ranking"]["top_aggregate_exact_rows"] != 10
        or plan["ranking"]["top_per_seed_and_seat"] != 5
    ):
        raise ArithmeticError("prospective diagnostic grid or budget changed")
    for name, expected in plan["input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned diagnostic input changed: {name}")
    if source_fingerprint(root) != PARENT_FINGERPRINT:
        raise ArithmeticError("parent experimental source changed")
    for folder, expected in (
        (SOURCE, "source_qualified"),
        (OWN, "own_published"),
        (NATIVE, "native_audited"),
        (REPORT, "report_negative"),
        (FINAL, "failed_final_local_gate_retained"),
    ):
        require_archive(root, root / folder, expected, PARENT_FINGERPRINT)
    parent = json.loads((root / REPORT / "report.json").read_bytes())
    final = json.loads((root / FINAL / "result.json").read_bytes())
    if (
        parent["classification"] != "negative"
        or final["status"] != "failed_final_local_gate_retained"
        or final["report_sha256"] != digest(root / REPORT / "report.json")
    ):
        raise ArithmeticError("failed parent gates no longer bound")
    return plan, head


def ordered_top(values: FloatArray, support: FloatArray, count: int) -> list[int]:
    """Rank positive supported additive contributions, exact-row tie break."""
    if (
        values.ndim != 1
        or support.shape != values.shape
        or not np.all(np.isfinite(values))
        or not np.all(np.isfinite(support))
        or np.any(support < 0)
        or type(count) is not int
        or count < 1
    ):
        raise ValueError("invalid ranked loss/support arrays")
    return sorted(
        (int(i) for i in np.flatnonzero((values > 0) & (support > 0))),
        key=lambda i: (-float(values[i]), i),
    )[:count]


def write_json(path: Path, data: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError("retain existing diagnostic evidence")
    path.write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n")


def write_gzip(path: Path, data: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError("retain existing diagnostic trace")
    raw = json.dumps(
        data, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    with path.open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as zipped:
            zipped.write(raw)


def event(path: Path, data: dict[str, Any]) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(data, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def row_identity(tree: MatrixTree, info: int) -> dict[str, Any]:
    state = tree.source.states[tree.source.representatives[info]]
    if state.dealer is None:
        raise ArithmeticError("exact decision lacks dealer state")
    observation = state.dealer.observe(state.actor)
    decoder = NoLimitState(state.dealer, tree.source.spot.rules)
    actions = []
    for action in tree.actions[info]:
        move = decoder.decode(action)
        actions.append(
            move.kind.value + ("" if move.amount is None else f" {move.amount}")
        )
    return dict(
        exact_info=info,
        seat=observation.seat,
        street="TURN" if len(observation.board) == 4 else "RIVER",
        hole=[format_card(card) for card in observation.hole_cards],
        board=[format_card(card) for card in observation.board],
        pot_chips=observation.pot,
        legal_actions=actions,
    )


def trace_case(
    root: Path,
    spec: Case,
    scoring: Any,
    native_rows: dict[tuple[int, int, str], dict[str, Any]],
    report_rows: dict[tuple[str, int, int, str], dict[str, Any]],
    deadline: Deadline,
) -> dict[str, Any]:
    folder = root / OWN / "study" / f"path{spec.path_index:02d}"
    summary: dict[str, Any] = json.loads((folder / "summary.json").read_bytes())
    if (
        summary["path"]
        != dict(
            index=spec.path_index,
            game="new_medium_dry_oop",
            seed=spec.seed,
            arm=spec.arm,
        )
        or summary["recall_violations"] != 0
    ):
        raise ArithmeticError("saved path identity or recall changed")
    matches = [
        row
        for row in summary["captures"]
        if row["metadata"]["work_label"] == spec.work
        and row["metadata"]["readout"] == "linear_average"
    ]
    if len(matches) != 1:
        raise ArithmeticError("fixed policy checkpoint missing or duplicated")
    saved = matches[0]
    native = native_rows[(spec.path_index, spec.work, "linear_average")]
    if (
        native["own_policy_sha256"] != saved["receipt"]["policy_sha256"]
        or native["native"]["maximum_error_chips"] > TOLERANCE
    ):
        raise ArithmeticError("published native scalar binding failed")
    parent = report_rows[(spec.arm, spec.seed, spec.work, "linear_average")]
    if parent["policy_sha256"] != saved["receipt"]["policy_sha256"]:
        raise ArithmeticError("published report/policy binding failed")
    policy = read_snapshot(
        folder / saved["file"], scoring.partition, saved["receipt"], saved["metadata"]
    )
    exact = scoring.expand(policy)
    tree = scoring.exact
    if not isinstance(tree, MatrixTree) or recall_violations(tree):
        raise ArithmeticError("exact game or recall changed")
    local_q, local_support = conditional_actions(tree, exact)
    traces = []
    for target in (0, 1):
        deadline.check()
        result = trace_losses(tree, exact, target, tolerance=TOLERANCE)
        response = saved["score"]["responses"][target]
        baseline = response["baseline_value_chips"]
        if (
            response["target"] != target
            or abs(result.value - response["exact_reply_value_chips"]) > TOLERANCE
            or abs(result.gain - (result.value - baseline)) > TOLERANCE
            or result.accounting_error > TOLERANCE
            or float(result.losses.min(initial=0.0)) < -TOLERANCE
        ):
            raise ArithmeticError("saved response or additive accounting changed")
        traces.append(
            dict(
                target=target,
                gain_chips=result.gain,
                accounting_error_chips=result.accounting_error,
                contribution_chips=(result.losses / 2).tolist(),
                counterfactual_reach=result.counterfactual_mass.tolist(),
                saved_prefix_reach=result.saved_reach_mass.tolist(),
                best_reply_suffix_action_values_chips=result.conditional_values.tolist(),
                saved_continuation_action_values_chips=local_q.tolist(),
                local_counterfactual_reach=local_support.tolist(),
            )
        )
    exact_exploitability = math.fsum(t["gain_chips"] for t in traces) / 2
    if (
        abs(
            exact_exploitability
            - saved["score"]["metrics"]["exact_exploitability_chips"]
        )
        > TOLERANCE
        or abs(exact_exploitability - parent["exploitability_chips"]) > TOLERANCE
    ):
        raise ArithmeticError("two-seat trace/exploitability identity failed")
    return dict(
        case_index=spec.index,
        arm=spec.arm,
        seed=spec.seed,
        work_label=spec.work,
        path_index=spec.path_index,
        policy_sha256=saved["receipt"]["policy_sha256"],
        actual_work=saved["metadata"]["total_work"],
        exploitability_chips=exact_exploitability,
        exploitability_fraction_initial_pot=parent[
            "exploitability_fraction_initial_pot"
        ],
        native_maximum_error_chips=native["native"]["maximum_error_chips"],
        traces=traces,
    )


def contribution(case: dict[str, Any]) -> FloatArray:
    return np.asarray(
        [
            math.fsum(t["contribution_chips"][i] for t in case["traces"])
            for i in range(len(case["traces"][0]["contribution_chips"]))
        ],
        dtype=np.float64,
    )


def summarise(
    cases_data: list[dict[str, Any]], exact: MatrixTree, candidate: MatrixTree
) -> dict[str, Any]:
    if len(cases_data) != 12 or [row["case_index"] for row in cases_data] != list(
        range(12)
    ):
        raise ArithmeticError("complete fixed diagnostic grid required")
    identities = [row_identity(exact, i) for i in range(len(exact.keys))]
    streets = np.array([row["street"] for row in identities])
    final = [
        row
        for row in cases_data
        if row["arm"] == "q8_turn_exact_river" and row["work_label"] == LABELS[-1]
    ]
    if [row["seed"] for row in final] != list(SEEDS):
        raise ArithmeticError("candidate final seeds changed")
    support = np.asarray(
        [
            math.fsum(
                t["saved_prefix_reach"][i] for row in final for t in row["traces"]
            )
            for i in range(len(exact.keys))
        ],
        dtype=np.float64,
    )
    mean = np.mean(np.stack([contribution(row) for row in final]), axis=0)
    ranked = ordered_top(mean, support, 10)
    per_seed_seat = []
    for row in final:
        for trace in row["traces"]:
            values = np.asarray(trace["contribution_chips"], dtype=np.float64)
            mass = np.asarray(trace["saved_prefix_reach"], dtype=np.float64)
            per_seed_seat.append(
                dict(
                    seed=row["seed"],
                    target=trace["target"],
                    top_exact_infos=ordered_top(values, mass, 5),
                    zero_saved_prefix_rows=int(
                        np.count_nonzero(
                            (exact.owners == trace["target"]) & (mass == 0)
                        )
                    ),
                )
            )
    detailed = []
    for info in ranked:
        owner = identities[info]["seat"]
        observations = []
        for row in final:
            trace = row["traces"][owner]
            n = len(exact.actions[info])
            observations.append(
                dict(
                    seed=row["seed"],
                    saved_probabilities=row["exact_policy_row_lookup"][info][:n],
                    counterfactual_reach=trace["counterfactual_reach"][info],
                    saved_prefix_reach=trace["saved_prefix_reach"][info],
                    best_reply_suffix_action_values_chips=trace[
                        "best_reply_suffix_action_values_chips"
                    ][info][:n],
                    saved_continuation_action_values_chips=trace[
                        "saved_continuation_action_values_chips"
                    ][info][:n],
                    additive_exploitability_contribution_chips=trace[
                        "contribution_chips"
                    ][info],
                )
            )
        trajectory = [
            dict(
                seed=seed,
                work_label=work,
                contribution_chips=float(
                    contribution(
                        next(
                            row
                            for row in cases_data
                            if row["arm"] == "q8_turn_exact_river"
                            and row["seed"] == seed
                            and row["work_label"] == work
                        )
                    )[info]
                ),
            )
            for seed in SEEDS
            for work in LABELS
        ]
        detailed.append(
            dict(
                **identities[info],
                candidate_abstract_info=int(candidate.exact_to_abstract[info]),
                mean_additive_exploitability_contribution_chips=float(mean[info]),
                per_seed=observations,
                candidate_checkpoint_trajectory=trajectory,
            )
        )
    case_summaries = []
    mapping = candidate.exact_to_abstract
    group_sizes = np.bincount(mapping, minlength=len(candidate.keys))
    collided = group_sizes[mapping] > 1
    for row in cases_data:
        values = contribution(row)
        if abs(float(values.sum()) - row["exploitability_chips"]) > TOLERANCE:
            raise ArithmeticError("street contribution does not sum to exploitability")
        case_summaries.append(
            dict(
                case_index=row["case_index"],
                arm=row["arm"],
                seed=row["seed"],
                work_label=row["work_label"],
                exploitability_chips=row["exploitability_chips"],
                exploitability_fraction_initial_pot=row[
                    "exploitability_fraction_initial_pot"
                ],
                turn_contribution_chips=float(values[streets == "TURN"].sum()),
                river_contribution_chips=float(values[streets == "RIVER"].sum()),
                candidate_collided_turn_contribution_chips=float(
                    values[(streets == "TURN") & collided].sum()
                ),
                candidate_collided_river_contribution_chips=float(
                    values[(streets == "RIVER") & collided].sum()
                ),
                maximum_accounting_error_chips=max(
                    t["accounting_error_chips"] for t in row["traces"]
                ),
                native_maximum_error_chips=row["native_maximum_error_chips"],
            )
        )
    mean_exploitability = math.fsum(row["exploitability_chips"] for row in final) / 3
    return dict(
        status="complete_read_only_diagnosis",
        parent_classification="negative",
        final_local_qualification="failed_retained",
        cases=case_summaries,
        top_final_candidate_exact_rows=detailed,
        top_per_seed_and_seat=per_seed_seat,
        top_ten_mean_contribution_chips=float(mean[ranked].sum()),
        final_candidate_mean_exploitability_chips=mean_exploitability,
        top_ten_share_of_final_candidate_mean_exploitability=float(
            mean[ranked].sum() / mean_exploitability
        ),
        candidate_collision_inventory=dict(
            turn_collided_exact_infos=int(
                np.count_nonzero((streets == "TURN") & collided)
            ),
            river_collided_exact_infos=int(
                np.count_nonzero((streets == "RIVER") & collided)
            ),
            turn_collided_abstract_groups=int(
                len(
                    set(
                        int(mapping[i])
                        for i in np.flatnonzero((streets == "TURN") & collided)
                    )
                )
            ),
            river_collided_abstract_groups=int(
                len(
                    set(
                        int(mapping[i])
                        for i in np.flatnonzero((streets == "RIVER") & collided)
                    )
                )
            ),
        ),
        exact_infos=len(exact.keys),
        candidate_infos=len(candidate.keys),
        maximum_accounting_error_chips=max(
            t["accounting_error_chips"] for row in cases_data for t in row["traces"]
        ),
        maximum_native_error_chips=max(
            row["native_maximum_error_chips"] for row in cases_data
        ),
    )


def run(root: Path, output: Path) -> None:
    started = time.perf_counter()
    plan, head = verify_inputs(root)
    fingerprint = source_fingerprint_diagnosis(root)
    deadline = Deadline(900)
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "started.json",
        dict(
            head=head,
            diagnostic_source_fingerprint=fingerprint,
            parent_source_fingerprint=PARENT_FINGERPRINT,
            plan_sha256=PLAN_SHA256,
            wall_cap_seconds=900,
        ),
    )
    events = output / "events.jsonl"
    data: list[dict[str, Any]] = []
    try:
        native: dict[str, Any] = json.loads(
            (root / NATIVE / "result.json").read_bytes()
        )
        parent: dict[str, Any] = json.loads(
            (root / REPORT / "report.json").read_bytes()
        )
        native_rows = {
            (row["path_index"], row["work_label"], row["readout"]): row
            for row in native["rows"]
        }
        report_rows = {
            (row["arm"], row["seed"], row["work_label"], row["readout"]): row
            for row in parent["rows"]
            if row["game"] == plan["spot"]
        }
        contexts = {
            arm: context(root, plan["spot"], arm)
            for arm in (plan["candidate"], plan["control"])
        }
        for spec in cases():
            deadline.check()
            record = trace_case(
                root, spec, contexts[spec.arm], native_rows, report_rows, deadline
            )
            # Exact policy rows are transient for selected examples; all underlying
            # bytes remain in the published snapshots and are hash checked above.
            folder = root / OWN / "study" / f"path{spec.path_index:02d}"
            summary = json.loads((folder / "summary.json").read_bytes())
            saved = next(
                row
                for row in summary["captures"]
                if row["metadata"]["work_label"] == spec.work
                and row["metadata"]["readout"] == "linear_average"
            )
            policy = read_snapshot(
                folder / saved["file"],
                contexts[spec.arm].partition,
                saved["receipt"],
                saved["metadata"],
            )
            record["exact_policy_row_lookup"] = (
                contexts[spec.arm].expand(policy).tolist()
            )
            data.append(record)
            durable = {
                k: v for k, v in record.items() if k != "exact_policy_row_lookup"
            }
            name = f"case{spec.index:02d}.json.gz"
            write_gzip(output / name, durable)
            event(
                events,
                dict(
                    kind="case_complete",
                    case_index=spec.index,
                    file=name,
                    sha256=digest(output / name),
                ),
            )
        deadline.check()
        exact = contexts[plan["candidate"]].exact
        candidate = contexts[plan["candidate"]].partition
        if not isinstance(exact, MatrixTree) or not isinstance(candidate, MatrixTree):
            raise ArithmeticError("expected frozen matrix contexts")
        result = summarise(data, exact, candidate)
        result.update(
            source_commit=head,
            diagnostic_source_fingerprint=fingerprint,
            parent_source_fingerprint=PARENT_FINGERPRINT,
            plan_sha256=PLAN_SHA256,
            elapsed_seconds=time.perf_counter() - started,
        )
        if result["elapsed_seconds"] >= 900:
            raise TimeoutError("whole diagnostic cap exceeded")
        write_json(output / "report.json", result)
        event(
            events, dict(kind="completed", report_sha256=digest(output / "report.json"))
        )
    except BaseException as error:
        write_json(
            output / "failure.json",
            dict(
                status="failed_retained",
                completed_cases=len(data),
                type=type(error).__name__,
                reason=str(error),
                elapsed_seconds=time.perf_counter() - started,
            ),
        )
        event(
            events,
            dict(kind="failed_retained", type=type(error).__name__, reason=str(error)),
        )
        raise
