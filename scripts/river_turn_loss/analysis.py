"""Bounded additive reply traces on immutable, already evaluated policies."""

import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path
from statistics import median
from typing import Any, cast

import numpy as np
from medium_dry_full.capture import replay_path as full_replay
from river_full_broader.control_capture import replay_path as control_replay
from river_full_broader.gate import source_fingerprint as parent_fingerprint
from river_full_broader.learning import (
    CANDIDATE,
    CONTROL,
    LABELS,
    SEEDS,
    context,
    paths,
)
from river_generalization.gate import require_archive
from river_generalization_diagnosis.analysis import row_identity, write_gzip, write_json

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.postflop.river_study import Deadline

PLAN = Path("configs/river-turn-loss-diagnosis.json")
PLAN_COMMIT = "237e820bc4afd1315ceb05e8d18b9c14523addaa"
PLAN_SHA256 = "a562247097d255ccecad93d76b8c1b1384451c2a85b3925f8bf903c8867ee356"
PARENT = "5aafb939fdc4ac75b06480dbd8203efddbd0e1f1b02170ab086ff8bf61668ac6"
INPUT = "full_new_medium_dry_oop"
BASE = Path("results/river-full-broader")
TOLERANCE = 1e-9
CAP = 900


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(root: Path) -> str:
    """Bind the new isolated source plus inherited analysis helpers."""
    names = (
        "scripts/diagnose_river_turn_loss.py",
        "scripts/river_turn_loss/__init__.py",
        "scripts/river_turn_loss/analysis.py",
        "scripts/river_generalization_diagnosis/analysis.py",
        PLAN.as_posix(),
    )
    files = [root / name for name in names]
    if any(not file.is_file() or file.is_symlink() for file in files):
        raise ArithmeticError("closed diagnostic source set changed")
    hashes = {name: digest(root / name) for name in names}
    hashes["parent_source_fingerprint"] = PARENT
    return hashlib.sha256(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify(root: Path) -> tuple[dict[str, Any], str]:
    """Require published prospective bytes and exact prior scientific evidence."""
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root):
        raise RuntimeError("diagnosis requires clean published source")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PLAN_COMMIT, head],
        cwd=root,
        check=False,
    ).returncode:
        raise ArithmeticError("prospective plan absent from history")
    raw = (root / PLAN).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PLAN_SHA256 or raw != subprocess.check_output(
        ["git", "show", f"{PLAN_COMMIT}:{PLAN.as_posix()}"], cwd=root
    ):
        raise ArithmeticError("prospective plan changed")
    plan: dict[str, Any] = json.loads(raw)
    if (
        plan["parent_merge"] != "c84302b58c8ee18220d39a2d8130abae803a779a"
        or plan["input"] != INPUT
        or plan["candidate"] != {"arm": CANDIDATE, "seed": 0}
        or plan["controls"] != {"arm": CONTROL, "seeds": list(SEEDS)}
        or plan["charged_work_labels"] != list(LABELS)
        or plan["readout"] != "linear_average"
        or plan["saved_policies"] != 12
        or plan["responding_seat_traces"] != 24
        or plan["ranking"]["turn_top"] != 10
        or plan["ranking"]["river_top"] != 5
        or plan["numeric_tolerance_chips"] != TOLERANCE
        or plan["whole_process_cap_seconds"] != CAP
        or plan["new_training"]
        or plan["new_reference_comparison"]
    ):
        raise ArithmeticError("diagnostic grid or gates changed")
    for name, expected in plan["archive_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError(f"pinned prior evidence changed: {name}")
    if parent_fingerprint(root) != PARENT:
        raise ArithmeticError("parent source changed")
    for stage, status in (
        ("own", "own_published"),
        ("native", "native_audited"),
        ("report", "report_negative"),
    ):
        require_archive(root, root / BASE / stage, status, PARENT)
    return plan, head


def rank(
    values: np.ndarray[Any, Any], streets: np.ndarray[Any, Any], street: str, count: int
) -> list[int]:
    """Keep every row including zero reach; exact index resolves ties."""
    if (
        values.ndim != 1
        or streets.shape != values.shape
        or count < 1
        or not np.all(np.isfinite(values))
    ):
        raise ValueError("invalid fixed rank inputs")
    return sorted(
        (int(i) for i in np.flatnonzero(streets == street)),
        key=lambda i: (-float(values[i]), i),
    )[:count]


def collision_sizes(
    mapping: np.ndarray[Any, Any], abstract_count: int
) -> np.ndarray[Any, Any]:
    """The exact row is collided when its abstract group has size above one."""
    if (
        mapping.ndim != 1
        or abstract_count < 1
        or np.any(mapping < 0)
        or np.any(mapping >= abstract_count)
    ):
        raise ValueError("invalid exact-to-abstract mapping")
    return cast(
        np.ndarray[Any, Any], np.bincount(mapping, minlength=abstract_count)[mapping]
    )


def event(path: Path, row: dict[str, Any]) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def proof(root: Path, output: Path, head: str, source: str, deadline: Deadline) -> None:
    """Use only a fictional signal game to verify additive traces and grouping."""
    scoring = software_context(0).scoring["coarse"]
    policy = scoring.partition.normalize(scoring.partition.legal.copy())
    exact = scoring.expand(policy)
    tree = scoring.exact
    traces = [trace_losses(tree, exact, seat, tolerance=TOLERANCE) for seat in (0, 1)]
    chips = math.fsum(trace.gain for trace in traces) / 2
    own = scoring.score(policy).metrics["exact_exploitability_chips"]
    sizes = collision_sizes(scoring.exact_to_partition, len(scoring.partition.keys))
    if abs(chips - own) > TOLERANCE or any(
        t.accounting_error > TOLERANCE for t in traces
    ):
        raise ArithmeticError("fictional trace identity failed")
    deadline.check()
    write_json(
        output / "proof.json",
        dict(
            status="passed",
            head=head,
            source_fingerprint=source,
            exact_rows=len(tree.keys),
            collided_rows=int(np.count_nonzero(sizes > 1)),
            exploitability_chips=chips,
            maximum_accounting_error_chips=max(t.accounting_error for t in traces),
        ),
    )


def trace_case(
    scoring: Any,
    spec: Any,
    work: int,
    native: dict[tuple[int, int, str], dict[str, Any]],
    parent: dict[tuple[int, int, str], dict[str, Any]],
    root: Path,
    deadline: Deadline,
) -> tuple[dict[str, Any], np.ndarray[Any, Any]]:
    folder = root / BASE / "own" / "study" / f"path{spec.index:02d}"
    replay = full_replay if spec.arm == CANDIDATE else control_replay
    summary = replay(scoring, folder)
    expected = dict(index=spec.index, game=INPUT, arm=spec.arm)
    if spec.arm == CONTROL:
        expected["seed"] = spec.seed
    if summary["path"] != expected or summary["recall_violations"] != 0:
        raise ArithmeticError("saved path or recall changed")
    matches = [
        row
        for row in summary["captures"]
        if row["metadata"]["work_label"] == work
        and row["metadata"]["readout"] == "linear_average"
    ]
    if len(matches) != 1:
        raise ArithmeticError("fixed checkpoint absent or duplicated")
    saved = matches[0]
    audited = native[(spec.index, work, "linear_average")]
    reported = parent[(spec.index, work, "linear_average")]
    if (
        audited["own_policy_sha256"] != saved["receipt"]["policy_sha256"]
        or audited["native"]["maximum_error_chips"] > TOLERANCE
        or reported["policy_sha256"] != saved["receipt"]["policy_sha256"]
    ):
        raise ArithmeticError("native/report policy binding failed")
    policy = read_snapshot(
        folder / saved["file"], scoring.partition, saved["receipt"], saved["metadata"]
    )
    exact = scoring.expand(policy)
    tree = scoring.exact
    if not isinstance(tree, MatrixTree) or recall_violations(tree):
        raise ArithmeticError("exact game recall changed")
    traces = []
    for seat in (0, 1):
        deadline.check()
        trace = trace_losses(tree, exact, seat, tolerance=TOLERANCE)
        if (
            trace.accounting_error > TOLERANCE
            or float(trace.losses.min(initial=0)) < -TOLERANCE
        ):
            raise ArithmeticError("additive trace accounting failed")
        traces.append(trace)
    contribution = (traces[0].losses + traces[1].losses) / 2
    chips = math.fsum(trace.gain for trace in traces) / 2
    if (
        abs(chips - saved["score"]["metrics"]["exact_exploitability_chips"]) > TOLERANCE
        or abs(chips - reported["exploitability_chips"]) > TOLERANCE
        or abs(float(contribution.sum()) - chips) > TOLERANCE
    ):
        raise ArithmeticError("trace and published score differ")
    data = dict(
        index=spec.index,
        arm=spec.arm,
        seed=spec.seed,
        work_label=work,
        actual_node_work=saved["metadata"]["total_work"],
        policy_sha256=saved["receipt"]["policy_sha256"],
        exploitability_chips=chips,
        whole_coverage=reported["whole_coverage"],
        native_maximum_error_chips=audited["native"]["maximum_error_chips"],
        contribution_chips=contribution.tolist(),
        traces=[
            dict(
                target=seat,
                counterfactual_reach=t.counterfactual_mass.tolist(),
                saved_prefix_reach=t.saved_reach_mass.tolist(),
                alternative_action_values_chips=t.conditional_values.tolist(),
                accounting_error_chips=t.accounting_error,
            )
            for seat, t in enumerate(traces)
        ],
    )
    return data, exact


def summarise(
    rows: list[dict[str, Any]],
    policies: list[np.ndarray[Any, Any]],
    exact: MatrixTree,
    partition: MatrixTree,
) -> dict[str, Any]:
    if len(rows) != 12 or len(policies) != 12:
        raise ArithmeticError("incomplete fixed policy grid")
    identities = [row_identity(exact, i) for i in range(len(exact.keys))]
    streets = np.asarray([row["street"] for row in identities])
    mapping = partition.exact_to_abstract
    sizes = collision_sizes(mapping, len(partition.keys))
    collided = sizes > 1
    final = next(
        row
        for row in rows
        if row["arm"] == CANDIDATE and row["work_label"] == LABELS[-1]
    )
    final_values = np.asarray(final["contribution_chips"], dtype=np.float64)
    selected = rank(final_values, streets, "TURN", 10) + rank(
        final_values, streets, "RIVER", 5
    )
    case_summaries = []
    for row in rows:
        values = np.asarray(row["contribution_chips"], dtype=np.float64)
        support = np.asarray(
            [
                math.fsum(trace["saved_prefix_reach"][i] for trace in row["traces"])
                for i in range(len(exact.keys))
            ]
        )
        turn = float(values[streets == "TURN"].sum())
        river = float(values[streets == "RIVER"].sum())
        if abs(turn + river - row["exploitability_chips"]) > TOLERANCE:
            raise ArithmeticError("street gains do not reconcile")
        case_summaries.append(
            dict(
                index=row["index"],
                arm=row["arm"],
                seed=row["seed"],
                work_label=row["work_label"],
                actual_node_work=row["actual_node_work"],
                exploitability_chips=row["exploitability_chips"],
                turn_contribution_chips=turn,
                river_contribution_chips=river,
                positive_reach_rows=int(np.count_nonzero(support > 0)),
                whole_coverage=row["whole_coverage"],
                top_ten_turn_share=float(values[selected[:10]].sum() / turn)
                if turn > 0
                else None,
            )
        )
    details = []
    for info in selected:
        identity = identities[info]
        seat = identity["seat"]
        count = len(exact.actions[info])
        observations = []
        for row, policy in zip(rows, policies, strict=True):
            trace = row["traces"][seat]
            observations.append(
                dict(
                    arm=row["arm"],
                    seed=row["seed"],
                    work_label=row["work_label"],
                    saved_probabilities=policy[info, :count].tolist(),
                    counterfactual_reach=trace["counterfactual_reach"][info],
                    saved_prefix_reach=trace["saved_prefix_reach"][info],
                    alternative_action_values_chips=trace[
                        "alternative_action_values_chips"
                    ][info][:count],
                    additive_contribution_chips=row["contribution_chips"][info],
                )
            )
        details.append(
            dict(
                **identity,
                abstract_info=int(mapping[info]),
                collided=bool(collided[info]),
                rank_within_street=selected[:10].index(info) + 1
                if info in selected[:10]
                else selected[10:].index(info) + 1,
                final_candidate_contribution_chips=float(final_values[info]),
                observations=observations,
            )
        )
    turn_mask = streets == "TURN"
    river_mask = streets == "RIVER"
    turn_gain = float(final_values[turn_mask].sum())
    collided_gain = float(final_values[turn_mask & collided].sum())
    inventory = dict(
        turn_collided_exact_rows=int(np.count_nonzero(turn_mask & collided)),
        river_collided_exact_rows=int(np.count_nonzero(river_mask & collided)),
        turn_collided_abstract_groups=int(
            len(set(int(mapping[i]) for i in np.flatnonzero(turn_mask & collided)))
        ),
        river_collided_abstract_groups=int(
            len(set(int(mapping[i]) for i in np.flatnonzero(river_mask & collided)))
        ),
        final_candidate_collided_turn_gain_chips=collided_gain,
        final_candidate_collided_turn_gain_share=collided_gain / turn_gain
        if turn_gain > 0
        else None,
    )
    signal = (
        "no_turn_collisions"
        if inventory["turn_collided_exact_rows"] == 0
        else "grouping_test_candidate"
        if inventory["final_candidate_collided_turn_gain_share"] is not None
        and inventory["final_candidate_collided_turn_gain_share"] >= 0.5
        and any(collided[i] for i in selected[:10])
        else "collision_present_below_signal"
    )
    contrasts = []
    for work in LABELS:
        selected_cases = [r for r in case_summaries if r["work_label"] == work]
        candidate = next(r for r in selected_cases if r["arm"] == CANDIDATE)
        controls = [r for r in selected_cases if r["arm"] == CONTROL]
        if [r["seed"] for r in controls] != list(SEEDS):
            raise ArithmeticError("control seed grid changed")
        contrasts.append(
            dict(
                work_label=work,
                turn_candidate_minus_each_control=[
                    candidate["turn_contribution_chips"] - r["turn_contribution_chips"]
                    for r in controls
                ],
                turn_median_difference=median(
                    candidate["turn_contribution_chips"] - r["turn_contribution_chips"]
                    for r in controls
                ),
                river_candidate_minus_each_control=[
                    candidate["river_contribution_chips"]
                    - r["river_contribution_chips"]
                    for r in controls
                ],
                river_median_difference=median(
                    candidate["river_contribution_chips"]
                    - r["river_contribution_chips"]
                    for r in controls
                ),
            )
        )
    return dict(
        status="complete_read_only_diagnosis",
        parent_classification="negative",
        input=INPUT,
        cases=case_summaries,
        candidate_ranked_decisions=details,
        collision_inventory=inventory,
        interpretation_signal=signal,
        checkpoint_contrasts=contrasts,
        selected_exact_infos=selected,
        exact_information_rows=len(exact.keys),
        abstract_information_rows=len(partition.keys),
        decision_assumptions=(
            "saved opponent policy and optimal reply continuation; "
            "values are not universal poker advice"
        ),
    )


def run(root: Path, output: Path, stage: str) -> None:
    """Preserve one complete or partial bounded run without replacement."""
    if stage not in ("proof", "diagnose") or output.exists() or output.is_symlink():
        raise ValueError("invalid or duplicate diagnostic stage")
    started = time.perf_counter()
    deadline = Deadline(180 if stage == "proof" else CAP)
    output.mkdir(parents=True, exist_ok=False)
    events = output / "events.jsonl"
    done: list[dict[str, Any]] = []
    try:
        plan, head = verify(root)
        source = fingerprint(root)
        deadline.check()
        write_json(
            output / "started.json",
            dict(
                stage=stage,
                head=head,
                source_fingerprint=source,
                plan_sha256=PLAN_SHA256,
            ),
        )
        if stage == "proof":
            proof(root, output, head, source, deadline)
        else:
            native: dict[str, Any] = json.loads(
                (root / BASE / "native/result.json").read_bytes()
            )
            parent: dict[str, Any] = json.loads(
                (root / BASE / "report/report.json").read_bytes()
            )
            audits = {
                (r["path_index"], r["work_label"], r["readout"]): r
                for r in native["rows"]
            }
            published = {
                (r["path_index"], r["work_label"], r["readout"]): r
                for r in parent["cases"]
                if r["game"] == INPUT
            }
            if len(audits) != 48 or len(published) != 24:
                raise ArithmeticError("parent fixed readout grid changed")
            scoring = context(root, INPUT)
            exact_policies = []
            for spec in paths()[:4]:
                for work in LABELS:
                    deadline.check()
                    row, exact_policy = trace_case(
                        scoring, spec, work, audits, published, root, deadline
                    )
                    index = len(done)
                    done.append(row)
                    exact_policies.append(exact_policy)
                    file = f"case{index:02d}.json.gz"
                    write_gzip(output / file, row)
                    event(
                        events,
                        dict(
                            kind="case_complete",
                            index=index,
                            file=file,
                            sha256=digest(output / file),
                        ),
                    )
            if not isinstance(scoring.exact, MatrixTree) or not isinstance(
                scoring.partition, MatrixTree
            ):
                raise ArithmeticError("frozen matrix contexts changed")
            report = summarise(done, exact_policies, scoring.exact, scoring.partition)
            report.update(
                head=head,
                source_fingerprint=source,
                plan_sha256=PLAN_SHA256,
                elapsed_seconds=time.perf_counter() - started,
            )
            deadline.check()
            write_json(output / "report.json", report)
        event(
            events,
            dict(
                kind="completed",
                stage=stage,
                elapsed_seconds=time.perf_counter() - started,
            ),
        )
    except BaseException as error:
        write_json(
            output / "failure.json",
            dict(
                status="failed_retained",
                stage=stage,
                completed_cases=len(done),
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
