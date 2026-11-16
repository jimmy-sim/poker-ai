"""Source-bound software/cost proofs and gated known-game learning commands.

Real study entry requires the complete checked and published forecast permit.
Cost stand-ins cannot enter a learner or claim original work-crossing evidence.
"""

import json
import os
import socket
import time
from pathlib import Path
from typing import Any

from compact_suit import admission as gates
from compact_suit.cache import Execution, cached, check_execution
from compact_suit.clock import (
    CAPS,
    arguments,
    atomic,
    measurement,
    output_path,
    preserve_temporary,
)
from compact_suit.contract import contract, input_pins, require_prefix_runtime, variant
from compact_suit.native import independent
from compact_suit.parity import vectors
from compact_suit.publication import publication
from compact_suit.source import check_source, source
from compact_suit.workers import training
from poker_ai.evaluation import opponent_learning_cost as cost
from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.evaluation.compact_opponent_sources import load
from poker_ai.evaluation.compact_opponent_sources import standins as load_standins
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import (
    COST,
    GAMES,
    REAL,
    TOY,
    TOY_WORK,
    WORK,
    Design,
)
from poker_ai.evaluation.opponent_learning_own import finish_own, fixture, replay
from poker_ai.evaluation.opponent_learning_replay import ContextFor
from poker_ai.evaluation.opponent_learning_report import write as write_report
from poker_ai.evaluation.opponent_learning_sources import Opponent
from poker_ai.evaluation.opponent_learning_workers import (
    gather,
    gather_independent,
)
from poker_ai.evaluation.private_prefix_journal import (
    Batch,
    Journal,
)
from poker_ai.evaluation.private_prefix_journal import (
    validate as validate_journal,
)
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment


def read(
    root: Path,
    path: Path,
    deadline: Deadline,
    observed: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    with isolated(worker=False):
        return _read(root, path, deadline, observed)


def _read(
    root: Path,
    path: Path,
    deadline: Deadline,
    observed: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    check_execution(root, saved)
    scope = saved["scope"]
    if scope != TOY:
        require_prefix_runtime(root)
    if scope == TOY:
        from compact_suit.card_contract import member

        member(root, path, saved)
    operation = {TOY: "software-own", COST: "cost-own", REAL: "study"}.get(scope)
    if operation is None:
        raise ArithmeticError("unknown own learning/cost scope")
    measurement(path, operation)
    check_source(root, saved["source"])
    if (
        saved["study_id"] != contract(root)["study_id"]
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or not same(saved["config"], contract(root))
        or not same(saved["input_sha256"], input_pins(root))
    ):
        raise ArithmeticError("complete same-source own evidence required")
    design = Design(scope, TOY_WORK if scope == TOY else WORK)
    groups = {3: saved["events"]}
    if "training_batch" in saved:
        gather(saved["training_batch"], design)
        groups.update(
            {w["slot"]: w["messages"] for w in saved["training_batch"]["workers"]}
        )
    validate_journal(
        path.with_name(saved["journal"]["file"]),
        saved["journal"],
        saved["source_sha256"],
        groups,
    )
    standins = None
    if scope == TOY:
        context_for, opponents = software_inputs()
    else:
        sources = load(root, deadline)
        context_for, opponents = sources.context, sources.opponents
        if scope == REAL and not same(
            saved["original_B4_boundaries"], list(sources.original_boundaries)
        ):
            raise ArithmeticError(
                "saved original barriers differ from pinned compact archive"
            )
        if scope == COST:
            standins = load_standins(root, sources, deadline)
    actual = replay(
        path.parent,
        saved,
        design,
        context_for,
        opponents,
        saved["source_sha256"],
        deadline,
        standins=standins,
    )
    if (
        compare(actual, saved["own_replay"]) > 1e-9
        or abs(
            actual["maximum_unitless_error"]
            - saved["own_replay"]["maximum_unitless_error"]
        )
        > 1e-12
    ):
        raise ArithmeticError("own whole-grid replay receipt changed")
    for name, expected in saved["report"].items():
        if digest(path.parent / "report" / name) != expected:
            raise ArithmeticError("own report file changed")
    if scope == TOY and not same(
        vectors(root, path.parent, saved, deadline), saved["software_vector_parity"]
    ):
        raise ArithmeticError("formal cached toy vector parity changed")
    deadline.check()
    if observed is not None:
        observed.append(actual)
    return saved


def _child_main(root: Path, argv: list[str], cache: Execution) -> int:
    args = arguments(argv)
    if args.operation in (
        "cost-own",
        "cost-audit",
        "forecast",
        "admit",
        "study",
        "audit",
    ):
        require_prefix_runtime(root)
    origin = float(os.environ["POKER_COMPACT_OPPONENT_STARTED"])
    deadline = Deadline(CAPS[args.operation])
    deadline.started = origin
    output = output_path(root, args)
    receipt = (
        output
        if args.operation != "report"
        else output.with_name(output.name + "-receipt.json")
    )
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError("retain existing own-opponent command receipt")
    default_own = (
        f"results/compact-suit-learning/cost/{args.repetition}/own.json"
        if args.operation == "cost-audit"
        else "results/compact-suit-learning/own.json"
        if args.operation == "audit"
        else "results/compact-suit-learning/software/own.json"
    )
    own_path = root / (args.own or default_own)
    current = source(root)
    binding = sha(current["sha256"])
    saved: dict[str, Any] = dict(
        status="running",
        implementation_config=variant(root),
        validation_cache=cache.summary(),
        study_id=contract(root)["study_id"],
        failure=None,
        operation=args.operation,
        scope=COST
        if args.operation.startswith("cost-")
        else REAL
        if args.operation in ("study", "audit")
        else TOY,
        source=current,
        source_sha256=binding,
        config=contract(root),
        events=[],
        poker_training_performed=False,
        toy_learning_performed=False,
        reference_constructed=False,
        training_start_attempted=False,
        reference_construction_attempted=False,
        compute_permit_checked=False,
        observed_training_work_lower_bound=0,
        observed_work_units="reported visited nodes; lower bound, not completed total",
        reference_output_used_in_training=False,
        long_run_admitted=False,
        new_agent_default=False,
        fresh_global_admission=False,
    )
    receipt.parent.mkdir(parents=True, exist_ok=True)
    prepared_own: dict[str, Any] | None = None
    witness: dict[str, Any] | None = None
    if args.operation in (
        "software-audit",
        "cost-own",
        "cost-audit",
        "checks",
        "forecast",
        "admit",
        "study",
        "audit",
    ):
        # Publication must be checked while the checkout is still clean, before
        # creating this new native receipt/journal. Retain preflight failures.
        try:
            if current["dirty"] is not False:
                raise ValueError("publish the exact clean source before this stage")
            if args.operation == "checks":
                saved.update(
                    status="complete_source_check_verification",
                    checked=gates.require_checks(root),
                )
            elif args.operation == "forecast":
                saved.update(prepare_forecast(root, deadline))
            elif args.operation == "admit":
                saved.update(
                    gates.permit(
                        root,
                        json.loads(
                            (
                                root / "results/compact-suit-learning/forecast.json"
                            ).read_text()
                        ),
                    )
                )
            elif args.operation in ("study", "audit"):
                saved["admission"] = gates.require_admission(root, binding)
                saved["compute_permit_checked"] = True
                if args.operation == "study":
                    saved["long_run_admitted"] = True
                if args.operation == "audit":
                    prepared_own = read(root, own_path, deadline)
                    if prepared_own["scope"] != REAL:
                        raise ArithmeticError(
                            "real audit requires a real own trajectory"
                        )
                    witness = publication(root, own_path, prepared_own)
            else:
                gates.require_checks(root)
                if args.operation == "software-audit":
                    own_clock = measurement(own_path, "software-own")
                    age = time.perf_counter() - own_clock["started_perf_counter"]
                    if (
                        own_clock["hostname"] != socket.gethostname()
                        or not own_clock["seconds"] <= age < 180
                    ):
                        raise ArithmeticError(
                            "invalid or expired shared software clock"
                        )
                    deadline.started = own_clock["started_perf_counter"]
                else:
                    proof_path = (
                        root / "results/compact-suit-learning/software/own.json"
                    )
                    proof = read(root, proof_path, deadline)
                    publication(root, proof_path, proof)
                    saved["software_gate"] = gates.software(root, proof)
                if args.operation == "cost-audit":
                    saved["all_own_cost_publications_before_native"] = (
                        gates.all_own_costs_published(root)
                    )
                if args.operation in ("software-audit", "cost-audit"):
                    prepared_own = read(root, own_path, deadline)
                    if prepared_own["scope"] != saved["scope"]:
                        raise ArithmeticError("independent comparison scope changed")
                    witness = publication(root, own_path, prepared_own)
        except BaseException as exc:
            saved.update(
                status="failed_preflight_retained",
                failure=dict(type=type(exc).__name__, message=str(exc)),
                seconds=time.perf_counter() - origin,
            )
            record(receipt, saved, cache)
            raise
    record(receipt, saved, cache)
    journal = Journal(
        receipt.with_name(receipt.stem + "-events.jsonl"), binding, args.operation
    )

    def send(event: dict[str, Any]) -> None:
        journal.append(3, event)
        saved["events"].append(event)

    try:
        if (
            args.operation
            in ("software-own", "software-audit", "cost-own", "cost-audit")
            and current["dirty"] is not False
        ):
            raise ValueError("publish the exact clean source before the software stage")
        saved["input_sha256"] = input_pins(root)
        if args.operation == "software-own":
            gates.require_checks(root)
        if args.operation in ("checks", "forecast", "admit"):
            pass
        elif args.operation in ("software-own", "cost-own", "study"):
            scratch = root / (
                args.scratch
                or f"results/runs/own-opponent-{receipt.parent.name}-scratch"
            )
            if scratch.exists() or scratch.is_symlink():
                raise FileExistsError("retain complete/partial own-opponent scratch")

            with isolated(worker=False):
                standins = None
                context_for: ContextFor
                originals: tuple[dict[str, Any], ...] = ()
                design = Design(
                    saved["scope"],
                    TOY_WORK if args.operation == "software-own" else WORK,
                )
                if args.operation == "cost-own":
                    sources = load(root, deadline)
                    standins = load_standins(root, sources, deadline)
                    context_for, opponents = sources.context, sources.opponents
                    paths = [
                        cost.collect(
                            standins, scratch, design, i, binding, send, deadline
                        )
                        for i in range(30)
                    ]
                    saved["repetition"] = args.repetition
                else:
                    if args.operation == "software-own":
                        context_for, opponents = software_inputs()
                        contexts = (context_for(0), context_for(3))
                    else:
                        sources = load(root, deadline)
                        context_for, opponents = sources.context, sources.opponents
                        contexts = sources.games
                        originals = sources.original_boundaries
                    batch = Batch(journal)
                    saved["training_batch"] = batch
                    saved["training_start_attempted"] = True
                    training_key = (
                        "poker_training_performed"
                        if design.scope == REAL
                        else "toy_learning_performed"
                    )
                    work_key = (
                        "actual_poker_training_work"
                        if design.scope == REAL
                        else "actual_toy_training_work"
                    )
                    saved[training_key] = None
                    saved[work_key] = None
                    # A hard kill can bypass except/finally. Persist uncertainty
                    # BEFORE any worker can initialize rather than claiming False.
                    record(receipt, saved, cache)
                    run_batch(
                        30,
                        3,
                        training,
                        dict(
                            root=str(root),
                            source_sha256=binding,
                            scope=design.scope,
                            admission_sha256=digest(root / gates.ADMISSION)
                            if args.operation == "study"
                            else None,
                            scratch=str(scratch),
                            deadline_started=deadline.started,
                            context_sha256=[
                                {
                                    k: tree_digest(c.tree(k))
                                    for k in ("coarse", "mixed0", "mixed1", "fine")
                                }
                                for c in contexts
                            ],
                        ),
                        deadline,
                        batch,
                    )
                    paths = gather(batch, design)
                    saved.update(partial_evidence(saved))
                    record(receipt, saved, cache)
                data = finish_own(
                    receipt.parent,
                    scratch,
                    design,
                    paths,
                    context_for,
                    opponents,
                    binding,
                    send,
                    deadline,
                    standins=standins,
                    originals=originals if args.operation != "cost-own" else (),
                )
            saved.update(data)
            if args.operation == "software-own":
                saved["software_vector_parity"] = vectors(
                    root, receipt.parent, saved, deadline
                )
            saved["report"] = write_report(
                receipt.parent / "report", saved, design, pots(root, saved["scope"])
            )
            saved["scratch"] = str(scratch)
        elif args.operation in ("software-audit", "cost-audit", "audit"):
            assert prepared_own is not None and witness is not None
            own = prepared_own
            # These imports/constructors occur only after full own replay and
            # actual publication. Native outputs remain scalar comparisons.
            from poker_ai.solver_validation.controlled_pipeline import license_record
            from poker_ai.solver_validation.opponent_learning import (
                FORMAT,
                validate_rows,
            )

            saved["license"] = license_record(saved["config"])
            design = Design(
                saved["scope"], TOY_WORK if args.operation == "software-audit" else WORK
            )
            if args.operation == "cost-audit":
                saved["repetition"] = args.repetition
            batch = Batch(journal)
            saved["native_batch"] = batch
            saved["reference_construction_attempted"] = True
            saved["reference_constructed"] = None
            record(receipt, saved, cache)
            run_batch(
                6,
                3,
                independent,
                dict(
                    root=str(root),
                    own=str(own_path),
                    own_sha256=digest(own_path),
                    source_sha256=binding,
                    publication=witness,
                    deadline_started=deadline.started,
                ),
                deadline,
                batch,
            )
            result = gather_independent(batch, own)
            verified = validate_rows(result, own)
            saved.update(
                result,
                format=FORMAT,
                status="completed_scalar_comparison",
                own_sha256=digest(own_path),
                publication=witness,
                verification=verified,
                reference_constructed=True,
                shared_seconds=time.perf_counter() - deadline.started,
            )
            # A final own replay is included in the same shared proof clock.
            read(root, own_path, deadline)
            if digest(own_path) != witness["own_sha256"]:
                raise ArithmeticError("published own receipt changed during comparison")
        else:
            observed: list[dict[str, Any]] = []
            own = read(root, own_path, deadline, observed)
            saved["scope"] = own["scope"]
            if len(observed) != 1:
                raise ArithmeticError("exactly one computed replay summary required")
            if args.operation == "replay":
                saved.update(
                    status="complete_read_only_replay",
                    own_sha256=digest(own_path),
                    replay=observed[0],
                    stored_replay=own["own_replay"],
                    reference_constructed=False,
                )
            else:
                scope = own["scope"]
                hashes = write_report(
                    output,
                    own,
                    Design(scope, TOY_WORK if scope == TOY else WORK),
                    pots(root, scope),
                )
                saved.update(
                    status="complete_read_only_report",
                    report=hashes,
                    own_sha256=digest(own_path),
                    reference_constructed=False,
                )
        deadline.check()
        if (
            source(root)["sha256"] != current["sha256"]
            or input_pins(root) != saved["input_sha256"]
        ):
            raise ArithmeticError("source or used input changed during command")
        saved["environment"] = runtime_environment()
        saved["seconds"] = time.perf_counter() - origin
        saved["journal"] = journal.close()
        record(receipt, saved, cache)
        deadline.check()
    except BaseException as exc:
        saved.update(partial_evidence(saved))
        saved.update(
            status="failed_retained",
            failure=dict(type=type(exc).__name__, message=str(exc)),
            seconds=time.perf_counter() - origin,
            journal=journal.close(),
            retained_temporary=preserve_temporary(receipt),
        )
        record(receipt, saved, cache)
        raise
    print(saved["status"] + "; agent default unchanged")
    return 0


def partial_evidence(saved: dict[str, Any]) -> dict[str, Any]:
    """Raw acknowledgments give lower bounds; missing messages mean unknown.

    This is failure reporting only, never an inventory/math acceptance gate.
    Complete work counters remain the independently replayed own result's job.
    """
    result: dict[str, Any] = {}
    if saved.get("training_start_attempted") is True:
        known: dict[int, int] = {}
        for worker in saved["training_batch"].get("workers", []):
            for event in worker["messages"]:
                if event.get("kind") != "cell":
                    continue
                index = event.get("index")
                if type(index) is not int or not 0 <= index < 30:
                    continue
                phase = event.get("phase")
                row = event.get("row", {})
                value = (
                    row.get("initialization_visits")
                    if phase == "warm"
                    else row.get("total_work")
                    if phase in ("capture", "mass")
                    else event.get("result", {}).get("final_total_work")
                    if phase == "path_finished"
                    else None
                )
                if type(value) is int and value > 0:
                    known[index] = max(known.get(index, 0), value)
        key = (
            "poker_training_performed"
            if saved["scope"] == REAL
            else "toy_learning_performed"
        )
        result[key] = True if known else None
        result["observed_training_work_lower_bound"] = sum(known.values())
    if saved.get("reference_construction_attempted") is True:
        witnessed = any(
            e.get("kind") == "cell" and e.get("phase") in ("self", "fixed")
            for w in saved["native_batch"].get("workers", [])
            for e in w["messages"]
        )
        result["reference_constructed"] = True if witnessed else None
    return result


def pots(root: Path, scope: str) -> tuple[float, float]:
    if scope == TOY:
        return (1.0, 1.0)
    spots = [load_spot(root / name) for name in GAMES]
    return float(spots[0].pot), float(spots[1].pot)


def software_inputs() -> tuple[ContextFor, tuple[Opponent, ...]]:
    contexts, opponents = fixture()

    def context_for(coordinate: int) -> Contexts:
        Design(TOY, TOY_WORK).coordinate(coordinate)
        return contexts[coordinate // 3]

    return context_for, opponents


def prepare_forecast(root: Path, deadline: Deadline) -> dict[str, Any]:
    """Recheck the entire fixed corpus; failure retains all previous evidence."""
    gates.require_checks(root)
    proof_path = root / "results/compact-suit-learning/software/own.json"
    proof = read(root, proof_path, deadline)
    publication(root, proof_path, proof)
    software_gate = gates.software(root, proof)
    for index in (0, 1, 2):
        path = root / f"results/compact-suit-learning/cost/{index}/own.json"
        own = read(root, path, deadline)
        if own["scope"] != COST or not same(own["repetition"], index):
            raise ArithmeticError(
                "cost forecast needs all fixed old-source repetitions"
            )
        publication(root, path, own)
        deadline.check()
    forecast, hashes = gates.sealed_costs(root)
    deadline.check()
    return dict(
        status="complete_fixed_cost_forecast",
        software_gate=software_gate,
        verified_input_sha256=hashes,
        forecast=forecast,
        reference_constructed=False,
        long_run_admitted=False,
    )


def record(path: Path, saved: dict[str, Any], cache: Execution) -> None:
    saved["validation_cache"] = cache.summary()
    saved["normalization"] = cache.normalization.summary()
    atomic(path, saved)
    cache.last_receipt = (path.resolve(), digest(path))


def child_main(root: Path, argv: list[str]) -> int:
    args = arguments(argv)
    path = output_path(root, args)
    receipt = (
        path
        if args.operation != "report"
        else path.with_name(path.name + "-receipt.json")
    )
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError("retain the existing command receipt")
    execution: Execution | None = None
    card_proof: dict[str, Any] | None = None
    if args.operation == "software-own":
        import math

        from compact_suit.card_contract import NAME, collect

        gates.require_checks(root)
        current = source(root, clean=True)
        origin = float(os.environ["POKER_COMPACT_OPPONENT_STARTED"])
        if not math.isfinite(origin) or not 0 < origin <= time.perf_counter():
            raise ArithmeticError("complete original software command clock required")
        deadline = Deadline(180)
        deadline.started = origin
        deadline.check()
        with isolated(worker=False):
            card_proof = collect(
                root, receipt.parent / NAME, current["fingerprint"], deadline
            )
    try:
        with cached(root) as execution:
            return _child_main(root, argv, execution)
    finally:
        # The live snapshots above cannot establish restoration. The complete
        # child clock includes this post-scope final write before parent capture.
        import sys

        primary = sys.exception()
        try:
            if execution is not None and execution.last_receipt is not None:
                if execution.last_receipt[
                    0
                ] != receipt.resolve() or execution.last_receipt[1] != digest(receipt):
                    raise ArithmeticError(
                        "command receipt changed before final restoration write"
                    )
                saved = json.loads(receipt.read_text())
                saved["normalization"] = execution.normalization.summary()
                if card_proof is not None:
                    saved["normalization_contract"] = card_proof
                atomic(receipt, saved)
        except BaseException:
            if primary is None:
                raise
