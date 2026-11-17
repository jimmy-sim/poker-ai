"""Compare exact root-local context reuse with original complete validation.

No saved policy, score or reference answer is cached. Published own software
proof precedes the fresh fixed diagnostic; all partial/failing outputs remain.
"""

import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import profile_checkpoint_cpu as previous
import profile_parent_archive as predecessor

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/context-reuse.json"
CONFIG_SHA = "59208fb4cba0e6cbaf40efe9968550f554459ac7963fcee2fb86be79e30da11c"
ENTRY = "scripts/compare_context_reuse.py"
SUPPORT = "scripts/context_reuse_support.py"
FOLDER = "results/context-reuse"


def canonical(value: Any) -> bytes:
    return previous.canonical(value)


def digest(path: Path) -> str:
    return previous.digest(path)


def atomic(path: Path, value: Any) -> None:
    previous.atomic(path, value)


def retain_failure(path: Path, value: Any) -> None:
    """A secondary receipt-write error cannot replace the original failure."""
    try:
        atomic(path, value)
    except BaseException as error:
        try:
            print(
                "Failure receipt write failed: " + type(error).__name__, file=sys.stderr
            )
        except BaseException:
            pass


def contract(root: Path) -> dict[str, Any]:
    from poker_ai.evaluation.diagnostic_receipts import config

    c = config(root, CONFIG, CONFIG_SHA)
    prior = c["previous_summary"]
    if digest(root / prior["file"]) != prior["sha256"]:
        raise ArithmeticError("preserve the published previous numerical summary")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    _, old = predecessor.binding(root, clean=clean)
    if (
        old["fingerprint"] != c["base_source_sha256"]
        or len(old["sha256"]) != c["base_source_files"]
    ):
        raise ArithmeticError("preserve all447 preceding scientific source bytes")
    saved: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    saved["sha256"].update(old["sha256"])
    saved["fingerprint"] = sha(saved["sha256"])
    if (
        len(saved["sha256"]) != c["source_files"]
        or clean
        and saved["dirty"] is not False
    ):
        raise ArithmeticError("publish clean complete450-file archive source")
    if clean:
        commit_sources(root, saved["git_commit"], saved["sha256"])
    return c, saved


def checked(root: Path, source: dict[str, Any]) -> None:
    import trace_card_audit as original
    from compact_suit.admission import published

    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    checks(root, path, source)
    published(root, path)
    for row in json.loads(path.read_text())["checks"]:
        path = root / row["log"]["file"]
        published(root, path)
        text = path.read_text(encoding="utf-8-sig")
        py, np = ("3.11.17", "2.4.6") if row["minor"] == "311" else ("3.12.15", "2.5.4")
        if row["numpy"] != np:
            raise ArithmeticError("actual qualified NumPy required")
        if row["role"] == "hosted":
            original.actual_host_runtime(text, py, np)
        elif set(re.findall(r"ACTUAL_PYTHON=([0-9.]+)", text)) != {py} or set(
            re.findall(r"ACTUAL_NUMPY=([0-9.]+)", text)
        ) != {np}:
            raise ArithmeticError("actual qualified local runtime required")


@contextmanager
def observe_reader(
    output: Path, *, enabled: bool
) -> Iterator[tuple[Any, dict[str, Any]]]:
    import context_reuse_support as support
    from compact_suit import cli
    from profile_coarse_reader import clock

    underlying = cli.read
    replays: list[dict[str, Any]] = []
    reads: list[dict[str, Any]] = []
    observed: dict[str, Any] = dict(replays=replays, reads=reads)
    with ExitStack() as stack:
        streams = [
            stack.enter_context((output / f"read-{i}-events.jsonl").open("xb"))
            for i in range(3)
        ]
        index = 0

        def emit(event: dict[str, Any]) -> None:
            streams[index].write(canonical(event) + b"\n")
            streams[index].flush()

        session = support.Session(enabled=enabled, sink=emit)

        def read(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal index
            if len(args) != 3 or kwargs or len(reads) >= 3:
                raise ArithmeticError(
                    "unchanged complete three-read call shape required"
                )
            index = len(reads)
            row: dict[str, Any] = dict(index=index, status="running", before=clock())
            start_rows, start_events = len(session.rows), len(session.events)
            reads.append(row)
            computed: list[dict[str, Any]] = []
            primary: BaseException | None = None
            try:
                saved = underlying(*args, observed=computed)
                if len(computed) != 1:
                    raise ArithmeticError("one complete mathematical replay required")
                replays.append(dict(scope=saved["scope"], computed=computed[0]))
                row["status"] = "complete"
                return saved
            except BaseException as error:
                primary = error
                row.update(status="failed", failure_kind=type(error).__name__)
                raise
            finally:
                row.update(
                    after=clock(),
                    row_indices=list(range(start_rows, len(session.rows))),
                    events=session.events[start_events:],
                )
                try:
                    atomic(output / f"read-{index}.json", row)
                except BaseException:
                    if primary is None:
                        raise

        primary = False
        try:
            with session.hooks(), patch.object(cli, "read", read):
                yield session, observed
        except BaseException:
            primary = True
            raise
        finally:
            observed["state"] = session.state()
            try:
                atomic(output / "observer.json", observed)
            except BaseException:
                if not primary:
                    raise


def validate_observed(
    observed: Any,
    *,
    enabled: bool,
    pid: int,
    thread: int,
    config: dict[str, Any],
    proof: bool = False,
) -> list[dict[str, Any]]:
    import context_reuse_support as support
    from checkpoint_cpu_support import check_clock

    if type(observed) is not dict or set(observed) != {"state", "reads", "replays"}:
        raise ArithmeticError("explicit complete context observation required")
    summaries = support.validate_session(
        observed["state"],
        enabled=enabled,
        pid=pid,
        thread=thread,
        keys=config["expected_context_keys"],
        roots=0 if proof else 2,
    )
    reads, replays = observed["reads"], observed["replays"]
    count = 1 if proof else 3
    if (
        type(reads) is not list
        or len(reads) != count
        or type(replays) is not list
        or len(replays) != count
        or [x["scope"] for x in replays] != config["expected"]["read_scopes"][:count]
    ):
        raise ArithmeticError("complete original read inventory required")
    for i, row in enumerate(reads):
        if (
            type(row) is not dict
            or set(row)
            != {"index", "status", "before", "after", "row_indices", "events"}
            or type(row["index"]) is not int
            or row["index"] != i
            or row["status"] != "complete"
        ):
            raise ArithmeticError("complete ordered context read required")
        for stamp in (row["before"], row["after"]):
            check_clock(stamp)
            if stamp["pid"] != pid or stamp["thread"] != thread:
                raise ArithmeticError("context read producer changed")
        indices = [] if i == 0 else list(range(4 * (i - 1), 4 * i))
        events = [e for e in observed["state"]["events"] if e["index"] in indices]
        if (
            row["row_indices"] != indices
            or row["events"] != events
            or any(row["after"][k] < row["before"][k] for k in ("cpu", "wall"))
        ):
            raise ArithmeticError("read boundary/events/inventory changed")
        if i and any(
            reads[i - 1]["after"][k] > row["before"][k] for k in ("cpu", "wall")
        ):
            raise ArithmeticError("read clocks overlap")
        for event in events:
            if any(
                not row["before"][k] <= event["clock"][k] <= row["after"][k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("context event outside whole read")
        for j in indices:
            boundary = observed["state"]["rows"][j]
            if any(
                not row["before"][k]
                <= boundary["before"][k]
                <= boundary["after"][k]
                <= row["after"][k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("context boundary outside whole read")
    return summaries


def tiny_math() -> dict[str, Any]:
    """Independent terminal recursion and exhaustive pure replies on own Kuhn.

    No tree values/edges/reaches helper is used by the scalar enumerator. This
    checks the software graph, not real Hold'em strength or a native solver.
    """
    import itertools

    import context_reuse_support as support

    from poker_ai.toy.analysis import evaluate
    from poker_ai.toy.tree import Tree

    tree = Tree.build("kuhn")
    policy = tree.normalize(tree.legal)

    def terminal(node: int, response: dict[int, int]) -> float:
        player = int(tree.player[node])
        if player == -2:
            return float(tree.terminal_values[node])
        total = 0.0
        for slot, valid in enumerate(tree.valid[node]):
            if not valid:
                continue
            info = int(tree.information[node])
            probability = (
                float(tree.chance_edges[node, slot])
                if player == -1
                else float(slot == response[info])
                if info in response
                else float(policy[info, slot])
            )
            total += probability * terminal(int(tree.children[node, slot]), response)
        return total

    direct = terminal(0, {})
    best = []
    for player in (0, 1):
        owned = [i for i, owner in enumerate(tree.owners) if owner == player]
        menus = [
            list(map(int, __import__("numpy").flatnonzero(tree.legal[i])))
            for i in owned
        ]
        values = [
            terminal(0, dict(zip(owned, actions, strict=True)))
            for actions in itertools.product(*menus)
        ]
        best.append(max(values) if player == 0 else -min(values))
    scalar = evaluate(tree, policy)
    actual = [
        scalar.value_player_zero,
        scalar.best_response_zero,
        scalar.best_response_one,
    ]
    expected = [direct, *best]
    error = max(abs(a - b) for a, b in zip(actual, expected, strict=True))
    cloned = support.isolated_clone(tree)
    second = evaluate(cloned, cloned.normalize(cloned.legal))
    if error > 1e-12 or second != scalar:
        raise ArithmeticError("own independent tiny terminal/pure-reply values differ")
    return dict(
        game="kuhn",
        policy="uniform",
        direct=expected,
        helper=actual,
        maximum_error_chips=error,
        independent_terminal_and_pure_response=True,
        reference_constructed=False,
    )


def own_math(root: Path, output: Path) -> dict[str, Any]:
    import context_reuse_support as support
    from compact_suit import cli

    from poker_ai.postflop.game import load_spot
    from poker_ai.postflop.matrix import MatrixTree
    from poker_ai.postflop.river_study import Deadline
    from poker_ai.postflop.tree import SpotTree

    path = root / "results/compact-suit-learning/software/own.json"
    input_digest = digest(path)
    plain: list[dict[str, Any]] = []
    expected = cli.read(root, path, Deadline(180), observed=plain)
    with observe_reader(output, enabled=True) as (_, observed):
        actual = cli.read(root, path, Deadline(180))
    if (
        actual != expected
        or [x["computed"] for x in observed["replays"]] != plain
        or digest(path) != input_digest
    ):
        raise ArithmeticError("actual saved software replay/input changed")
    c = contract(root)
    validate_observed(
        observed,
        enabled=True,
        pid=os.getpid(),
        thread=threading.get_ident(),
        config=c,
        proof=True,
    )
    with (output / "fixture-events.jsonl").open("xb") as stream:

        def emit(event: dict[str, Any]) -> None:
            stream.write(canonical(event) + b"\n")
            stream.flush()

        fixture = support.Session(enabled=True, sink=emit)
        with fixture.hooks():
            for _ in range(2):
                with fixture.root(root, True):
                    a = fixture.dictionary("sampled_dictionary", root, "software")
                    checksum = support.witness(a)
                    first = next(iter(a.values()))
                    first.diagnostics.clear()
                    first.scoring.exact.terminal_values[:] = 123
                    b = fixture.dictionary("full_dictionary", root, "software")
                    d = {
                        (x.spot_file, x.representation): x
                        for x in fixture.iterator(root, software=True)
                    }
                    if support.witness(b) != checksum or support.witness(d) != checksum:
                        raise ArithmeticError(
                            "caller mutation contaminated later returns"
                        )
        fixture_state = fixture.state()
        summaries = support.validate_session(
            fixture_state,
            enabled=True,
            pid=os.getpid(),
            thread=threading.get_ident(),
            keys=c["expected_software_keys"],
            software=True,
        )
    matrix = MatrixTree.build(
        SpotTree.build(load_spot(root / "configs/learning-spots/dev_low_oop.json"))
    )
    copied = support.isolated_clone(matrix)
    checksum = support.witness(matrix)
    if checksum != support.witness(copied):
        raise ArithmeticError("nested source clone differs")
    dealer = next(x.dealer for x in copied.source.states if x.dealer is not None)
    object.__setattr__(dealer.deck, "cards", ())
    if support.witness(matrix) != checksum or support.witness(copied) == checksum:
        raise ArithmeticError("nested source mutation was shared or not witnessed")
    return dict(
        status="actual_software_replay_and_separate_isolated_factory_proof",
        input=dict(file=str(path.relative_to(root)), sha256=input_digest),
        observed=observed,
        plain_computed_replays=plain,
        fixture_state=fixture_state,
        fixture_summaries=summaries,
        nested_source=dict(
            nodes=len(matrix.player),
            original_sha256=checksum,
            caller_mutation_isolated=True,
        ),
        tiny_math=tiny_math(),
        real_cost_loader_coverage=False,
        new_holdem_training_performed=False,
        reference_constructed=False,
    )


def proof(root: Path, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="running",
        admission_evidence=False,
        reference_constructed=False,
        poker_training_performed=False,
        pid=os.getpid(),
        thread=threading.get_ident(),
        executable=sys.executable,
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        started_perf_counter=origin,
    )
    atomic(output / "child.json", saved)
    try:
        c, source = binding(root)
        checked(root, source)
        previous.runtime(c)
        from poker_ai.evaluation.compact_opponent_guard import isolated

        with isolated(worker=False):
            result = own_math(root, output)
        atomic(output / "proof.json", result)
        after_c, after = binding(root, clean=False)
        if after_c != c or after["sha256"] != source["sha256"]:
            raise ArithmeticError("own phase proof source changed")
        saved.update(
            status="complete_own_only_context_reuse_proof",
            source=source,
            config_sha256=CONFIG_SHA,
            proof_sha256=digest(output / "proof.json"),
            seconds=time.perf_counter() - origin,
        )
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(status="failed_retained", failure_kind=type(error).__name__)
        retain_failure(output / "child.json", saved)
        raise


def own_published(root: Path, source: dict[str, Any]) -> dict[str, Any]:
    """Authenticate the published complete own proof without executing its math."""
    import context_reuse_support as support
    from compact_suit.admission import published
    from profile_compact_replay import authenticate_source

    folder = root / FOLDER / "software"
    files = {
        "child.json",
        "proof.json",
        "measurement.json",
        "command.log",
        "observer.json",
        "read-0.json",
        "fixture-events.jsonl",
    } | {f"read-{i}-events.jsonl" for i in range(3)}
    if (
        any(p.is_symlink() for p in folder.rglob("*"))
        or {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()}
        != files
    ):
        raise ArithmeticError("complete explicit own-reuse proof inventory required")
    child = json.loads((folder / "child.json").read_text())
    proof_data = json.loads((folder / "proof.json").read_text())
    measurement = json.loads((folder / "measurement.json").read_text())
    c = contract(root)
    if (
        child["status"] != "complete_own_only_context_reuse_proof"
        or child["source"]["sha256"] != source["sha256"]
        or child["config_sha256"] != CONFIG_SHA
        or child["proof_sha256"] != digest(folder / "proof.json")
        or child["reference_constructed"] is not False
        or child["poker_training_performed"] is not False
        or child["admission_evidence"] is not False
        or type(measurement["returncode"]) is not int
        or measurement["returncode"] != 0
        or measurement["interrupted"] is not None
        or type(measurement["cap_seconds"]) not in (int, float)
        or not math.isfinite(measurement["cap_seconds"])
        or not 0 < measurement["cap_seconds"] <= 180
        or type(measurement["seconds"]) not in (int, float)
        or not math.isfinite(measurement["seconds"])
        or not 0 < measurement["seconds"] < measurement["cap_seconds"]
        or measurement["child_sha256"] != digest(folder / "child.json")
        or type(measurement["child_pid"]) is not int
        or measurement["child_pid"] != child["pid"]
        or proof_data["status"]
        != "actual_software_replay_and_separate_isolated_factory_proof"
        or any(
            proof_data[k] is not False
            for k in (
                "real_cost_loader_coverage",
                "new_holdem_training_performed",
                "reference_constructed",
            )
        )
    ):
        raise ArithmeticError("publish complete source-bound own-reuse proof first")
    authenticate_source(root, child["source"])
    observed = json.loads((folder / "observer.json").read_text())
    if observed != proof_data["observed"]:
        raise ArithmeticError("separately saved software observation changed")
    validate_observed(
        observed,
        enabled=True,
        pid=child["pid"],
        thread=child["thread"],
        config=c,
        proof=True,
    )
    actual = [r["computed"] for r in observed["replays"]]
    if actual != proof_data["plain_computed_replays"]:
        raise ArithmeticError("original software calculation changed")
    path = root / "results/compact-suit-learning/software/own.json"
    if proof_data["input"] != dict(
        file=str(path.relative_to(root)), sha256=digest(path)
    ):
        raise ArithmeticError("original archived software proof input changed")
    expected = json.loads(path.read_text())["own_replay"]
    errors = {"maximum_error": 1e-9, "maximum_unitless_error": 1e-12}
    if (
        set(actual[0]) != set(expected)
        or canonical({k: v for k, v in actual[0].items() if k not in errors})
        != canonical({k: v for k, v in expected.items() if k not in errors})
        or any(
            type(actual[0][k]) not in (int, float)
            or not math.isfinite(actual[0][k])
            or not 0 <= actual[0][k] <= cap
            for k, cap in errors.items()
        )
    ):
        raise ArithmeticError("original software inventory/replay limits required")
    summaries = support.validate_session(
        proof_data["fixture_state"],
        enabled=True,
        pid=child["pid"],
        thread=child["thread"],
        keys=c["expected_software_keys"],
        software=True,
    )
    if (
        summaries != proof_data["fixture_summaries"]
        or [
            json.loads(line)
            for line in (folder / "fixture-events.jsonl").read_bytes().splitlines()
        ]
        != proof_data["fixture_state"]["events"]
    ):
        raise ArithmeticError("complete separate synthetic-factory proof changed")
    nested, tiny = proof_data["nested_source"], proof_data["tiny_math"]
    if (
        type(nested["nodes"]) is not int
        or nested["nodes"] <= 0
        or re.fullmatch("[0-9a-f]{64}", nested["original_sha256"]) is None
        or nested["caller_mutation_isolated"] is not True
    ):
        raise ArithmeticError("nested actual matrix-source proof required")
    if (
        tiny["game"] != "kuhn"
        or tiny["policy"] != "uniform"
        or tiny["independent_terminal_and_pure_response"] is not True
        or tiny["reference_constructed"] is not False
        or len(tiny["direct"]) != 3
        or len(tiny["helper"]) != 3
        or any(
            type(v) not in (int, float) or not math.isfinite(v)
            for v in [*tiny["direct"], *tiny["helper"]]
        )
        or type(tiny["maximum_error_chips"]) not in (int, float)
        or not 0 <= tiny["maximum_error_chips"] <= 1e-12
        or max(abs(a - b) for a, b in zip(tiny["direct"], tiny["helper"], strict=True))
        != tiny["maximum_error_chips"]
    ):
        raise ArithmeticError("independent own tiny terminal/reply proof required")
    expected_command = [
        child["executable"],
        str(Path(child["execution_root"]) / ENTRY),
        "--child",
        "proof",
        "--output",
        child["execution_output"],
    ]
    if (
        measurement["command"] != expected_command
        or type(child["started_perf_counter"]) not in (int, float)
        or not math.isfinite(child["started_perf_counter"])
        or child["started_perf_counter"] != measurement["started_perf_counter"]
        or type(child["seconds"]) not in (int, float)
        or not 0 < child["seconds"] <= measurement["seconds"]
        or not Path(child["execution_output"]).is_relative_to(
            Path(child["execution_root"]) / "results/runs"
        )
    ):
        raise ArithmeticError("complete actual own command/startup allowance required")
    upper = measurement["started_perf_counter"] + measurement["seconds"]
    intervals = observed["reads"] + proof_data["fixture_state"]["rows"]
    if any(
        not measurement["started_perf_counter"]
        <= row["before"]["wall"]
        <= row["after"]["wall"]
        <= upper
        for row in intervals
    ):
        raise ArithmeticError("own proof work outside complete clock")
    if json.loads((folder / "read-0.json").read_text()) != observed["reads"][0] or any(
        (folder / f"read-{i}-events.jsonl").read_bytes() for i in range(3)
    ):
        raise ArithmeticError("actual software read must have zero context roots")
    for name in sorted(files):
        published(root, folder / name)
    return dict(
        file=str((folder / "child.json").relative_to(root)),
        sha256=digest(folder / "child.json"),
    )


def execute_child(
    root: Path, output: Path, c: dict[str, Any], *, enabled: bool
) -> dict[str, Any]:
    from compact_suit import cli
    from compact_suit.cache import check_execution

    raw = output / "native.json"
    primary = False
    native: dict[str, Any] | None = None
    try:
        with observe_reader(output, enabled=enabled) as (_, observed):
            code = cli.child_main(
                root,
                [
                    "cost-audit",
                    "--repetition",
                    "0",
                    "--own",
                    c["base_own"],
                    "--output",
                    str(raw),
                ],
            )
        if code != 0:
            raise ArithmeticError("complete original cost-audit child failed")
        native = json.loads(raw.read_text())
        check_execution(root, native)
        identity = previous.numerical_identity(native, observed["replays"])
    except BaseException:
        primary = True
        raise
    finally:
        # Even a failed receipt is diagnostic. Cleanup errors preserve the
        # underlying audit error; they cannot accidentally promote its output.
        if raw.is_file():
            try:
                retained = json.loads(raw.read_text())
                retained["base_implementation_config"] = retained[
                    "implementation_config"
                ]
                retained["implementation_config"] = dict(
                    instrumentation_config=CONFIG,
                    instrumentation_sha256=CONFIG_SHA,
                    admission_evidence=False,
                )
                retained["instrumentation_scope"] = c["scope"]
                atomic(raw, retained)
            except BaseException as error:
                if not primary:
                    raise
                try:
                    atomic(
                        output / "invalidation-failure.json",
                        dict(failure_kind=type(error).__name__),
                    )
                except BaseException:
                    pass
    assert native is not None
    try:
        check_execution(root, json.loads(raw.read_text()))
    except ArithmeticError:
        return dict(
            identity=identity,
            base_admission_rejected=True,
            observer=observed,
            worker_body_clocks=[
                dict(
                    slot=w["slot"],
                    wall_seconds=m["seconds"],
                    cpu_seconds=m["cpu_seconds"],
                )
                for w in native["native_batch"]["workers"]
                for m in w["messages"]
                if m.get("kind") == "done"
            ],
        )
    raise ArithmeticError("diagnostic receipt must reject base admission")


def child(root: Path, mode: str, output: Path, origin: float) -> int:

    saved: dict[str, Any] = dict(
        status="running",
        mode=mode,
        pid=os.getpid(),
        thread=threading.get_ident(),
        admission_evidence=False,
        poker_training_performed=False,
        reference_output_used_in_training=False,
        executable=sys.executable,
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
    )
    atomic(output / "child.json", saved)
    try:
        if mode not in ("ordinary", "reuse"):
            raise ArithmeticError("fixed reader phase observation mode required")
        c, source = binding(root)
        previous.runtime(c)
        checked(root, source)
        saved.update(
            source=source,
            config_sha256=CONFIG_SHA,
            own_proof=own_published(root, source),
        )
        atomic(output / "child.json", saved)
        # Both arms have identical imports before the original parent adapters.
        from compact_suit import cli  # noqa: F401
        from profile_coarse_reader import clock

        from poker_ai.reproducibility import runtime_environment

        saved["environment"] = runtime_environment()
        os.environ["POKER_COMPACT_OPPONENT_STARTED"] = repr(origin)
        saved["body_before"] = clock()
        result = execute_child(root, output, c, enabled=mode == "reuse")
        saved["body_after"] = clock()
        saved["complete_body_parent_cpu_seconds"] = (
            saved["body_after"]["cpu"] - saved["body_before"]["cpu"]
        )
        observed = result.pop("observer")
        summaries = validate_observed(
            observed,
            enabled=mode == "reuse",
            pid=saved["pid"],
            thread=saved["thread"],
            config=c,
        )
        if [r["scope"] for r in observed["replays"]] != c["expected"]["read_scopes"]:
            raise ArithmeticError("fixed complete read scope inventory changed")
        after_c, after = binding(root, clean=False)
        if after_c != c or after["sha256"] != source["sha256"]:
            raise ArithmeticError("phase source or sealed inputs changed")
        saved.update(
            result,
            status="complete_context_reuse_diagnostic",
            summaries=summaries,
            read_clocks=observed["reads"],
            context_identity_sha256=observed["state"]["rows"][1]["collection_sha256"],
            reference_constructed=True,
            seconds=time.perf_counter() - origin,
        )
        saved["raw_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
            and p.name not in ("child.json", "command.log", "measurement.json")
        }
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
            seconds=time.perf_counter() - origin,
        )
        retain_failure(output / "child.json", saved)
        raise


def pair_identity(children: list[dict[str, Any]]) -> dict[str, Any]:
    if (
        len(children) != 2
        or [r["mode"] for r in children] != ["ordinary", "reuse"]
        or any(
            r["status"] != "complete_context_reuse_diagnostic"
            or r["base_admission_rejected"] is not True
            or r["admission_evidence"] is not False
            or r["config_sha256"] != CONFIG_SHA
            for r in children
        )
        or type(children[0]["pid"]) is not int
        or type(children[1]["pid"]) is not int
        or children[0]["pid"] == children[1]["pid"]
        or children[0]["source"]["sha256"] != children[1]["source"]["sha256"]
        or canonical(children[0]["identity"]) != canonical(children[1]["identity"])
        or children[0]["context_identity_sha256"]
        != children[1]["context_identity_sha256"]
    ):
        raise ArithmeticError(
            "complete separate ordinary/reuse phase identity required"
        )
    identity_sha = hashlib.sha256(canonical(children[0]["identity"])).hexdigest()
    if (
        identity_sha
        != "ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185"
    ):
        raise ArithmeticError("unchanged previous complete numerical identity required")
    return dict(
        status="exact_complete_scalar_and_computed_replay_identity",
        identity_sha256=identity_sha,
    )


def pair(root: Path, output: Path) -> int:
    started = time.perf_counter()
    if (
        output.exists()
        or output.is_symlink()
        or not output.resolve().is_relative_to(root.resolve() / "results/runs")
    ):
        raise FileExistsError(
            "fresh ignored pair destination required; retain every attempt"
        )
    output.mkdir(parents=True)
    saved: dict[str, Any] = dict(
        status="running",
        order=["ordinary", "reuse"],
        measurements=[],
        admission_evidence=False,
    )
    atomic(output / "pair.json", saved)
    try:
        c, source = binding(root)
        checked(root, source)
        own_published(root, source)
        for mode in c["order"]:
            remaining = c["caps"]["shared_seconds"] - (time.perf_counter() - started)
            if remaining <= 0:
                raise TimeoutError("shared1800-second phase pair cap exhausted")
            measurement = previous.supervise(
                [
                    sys.executable,
                    str(root / ENTRY),
                    "--child",
                    mode,
                    "--output",
                    str(output / mode),
                ],
                output / mode,
                min(c["caps"]["child_seconds"], remaining),
            )
            saved["measurements"].append(measurement)
            atomic(output / "pair.json", saved)
            if measurement["returncode"] != 0:
                raise ArithmeticError("retained failed phase child; no favorable retry")
        saved.update(
            pair_identity(
                [
                    json.loads((output / mode / "child.json").read_text())
                    for mode in c["order"]
                ]
            )
        )
        saved["seconds"] = time.perf_counter() - started
        if saved["seconds"] >= c["caps"]["shared_seconds"]:
            raise TimeoutError("complete phase pair exceeded shared1800seconds")
        atomic(output / "pair.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        retain_failure(output / "pair.json", saved)
        raise


def saved_pair(root: Path, output: Path) -> dict[str, Any]:
    """Authenticate complete saved evidence without a replay or reference call."""
    from checkpoint_cpu_support import check_clock
    from compact_suit.cache import check_execution
    from profile_compact_replay import authenticate_source

    from poker_ai.evaluation.opponent_learning_workers import gather_independent
    from poker_ai.evaluation.private_prefix_journal import validate as validate_journal
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.solver_validation.opponent_learning import validate_rows

    c = contract(root)
    pair_data = json.loads((output / "pair.json").read_text())
    if (
        pair_data["admission_evidence"] is not False
        or pair_data["order"] != c["order"]
        or len(pair_data["measurements"]) != 2
        or pair_data["status"] != "exact_complete_scalar_and_computed_replay_identity"
    ):
        raise ArithmeticError("complete fixed ordered pair required")
    children, ledgers = [], []
    for mode, measurement in zip(c["order"], pair_data["measurements"], strict=True):
        folder = output / mode
        child_data = json.loads((folder / "child.json").read_text())
        if (
            measurement != json.loads((folder / "measurement.json").read_text())
            or child_data["admission_evidence"] is not False
            or child_data["reference_constructed"] is not True
            or child_data["poker_training_performed"] is not False
            or child_data["reference_output_used_in_training"] is not False
            or measurement["returncode"] != 0
            or type(measurement["returncode"]) is not int
            or measurement["interrupted"] is not None
            or type(measurement["seconds"]) not in (int, float)
            or type(measurement["cap_seconds"]) not in (int, float)
            or not math.isfinite(measurement["seconds"])
            or not math.isfinite(measurement["cap_seconds"])
            or not 0 < measurement["cap_seconds"] <= 900
            or not 0 < measurement["seconds"] < min(900, measurement["cap_seconds"])
            or measurement["child_sha256"] != digest(folder / "child.json")
            or type(measurement["child_pid"]) is not int
            or measurement["child_pid"] != child_data["pid"]
            or child_data["mode"] != mode
            or child_data["source"]["fingerprint"]
            != sha(child_data["source"]["sha256"])
        ):
            raise ArithmeticError("saved complete producer measurement changed")
        for stamp in (child_data["body_before"], child_data["body_after"]):
            check_clock(stamp)
            if (
                stamp["pid"] != measurement["child_pid"]
                or stamp["thread"] != child_data["thread"]
            ):
                raise ArithmeticError("complete body producer changed")
        start, end = child_data["body_before"], child_data["body_after"]
        if (
            not measurement["started_perf_counter"]
            <= start["wall"]
            <= end["wall"]
            <= measurement["started_perf_counter"] + measurement["seconds"]
            or child_data["complete_body_parent_cpu_seconds"]
            != end["cpu"] - start["cpu"]
            or end["cpu"] < start["cpu"]
        ):
            raise ArithmeticError("complete body and supervisor clocks changed")
        expected_command = [
            child_data["executable"],
            str(Path(child_data["execution_root"]) / ENTRY),
            "--child",
            mode,
            "--output",
            child_data["execution_output"],
        ]
        if measurement["command"] != expected_command or not Path(
            child_data["execution_output"]
        ).is_relative_to(Path(child_data["execution_root"]) / "results/runs"):
            raise ArithmeticError("actual complete child command/output changed")
        authenticate_source(root, child_data["source"])
        expected_raw = {"observer.json", "native.json", "native-events.jsonl"} | {
            f"read-{i}{suffix}"
            for i in range(3)
            for suffix in (".json", "-events.jsonl")
        }
        if set(child_data["raw_sha256"]) != expected_raw or any(
            p.is_symlink() for p in folder.rglob("*")
        ):
            raise ArithmeticError(
                "complete explicit raw observation inventory required"
            )
        actual_raw = {
            str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()
        }
        if actual_raw != expected_raw | {
            "child.json",
            "command.log",
            "measurement.json",
        }:
            raise ArithmeticError("unexpected or missing raw diagnostic member")
        for name, checksum in child_data["raw_sha256"].items():
            path = folder / name
            if (
                path.is_symlink()
                or not path.resolve().is_relative_to(folder.resolve())
                or digest(path) != checksum
            ):
                raise ArithmeticError("saved raw observation changed")
        observed = json.loads((folder / "observer.json").read_text())
        results = validate_observed(
            observed,
            enabled=mode == "reuse",
            pid=measurement["child_pid"],
            thread=child_data["thread"],
            config=c,
        )
        if (
            results != child_data["summaries"]
            or observed["reads"] != child_data["read_clocks"]
            or observed["state"]["rows"][1]["collection_sha256"]
            != child_data["context_identity_sha256"]
            or observed["replays"] != child_data["identity"]["computed_replays"]
        ):
            raise ArithmeticError("saved computed summary changed")
        for row in observed["reads"]:
            if any(
                not start[k] <= row["before"][k] <= row["after"][k] <= end[k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("complete read outside actual parent body")
        for index, row in enumerate(observed["reads"]):
            stream = folder / f"read-{index}-events.jsonl"
            if [json.loads(line) for line in stream.read_bytes().splitlines()] != row[
                "events"
            ] or json.loads((folder / f"read-{index}.json").read_text()) != row:
                raise ArithmeticError(
                    "independently retained boundary/event stream changed"
                )
        native = json.loads((folder / "native.json").read_text())
        if native["implementation_config"] != dict(
            instrumentation_config=CONFIG,
            instrumentation_sha256=CONFIG_SHA,
            admission_evidence=False,
        ):
            raise ArithmeticError("saved instrumentation must reject base admission")
        native["implementation_config"] = native["base_implementation_config"]
        check_execution(root, native)
        if (
            native["normalization"]["pid"] != measurement["child_pid"]
            or native["normalization"]["thread"] != child_data["thread"]
        ):
            raise ArithmeticError("base parent and observer producer differ")
        own = json.loads((root / c["base_own"]).read_text())
        if validate_rows(native, own) != native["verification"]:
            raise ArithmeticError("saved scalar comparison verification changed")
        gathered = gather_independent(native["native_batch"], own)
        if any(native[k] != v for k, v in gathered.items()):
            raise ArithmeticError("complete native workers and scalar rows differ")
        validate_journal(
            folder / native["journal"]["file"],
            native["journal"],
            native["source_sha256"],
            {
                3: native["events"],
                **{w["slot"]: w["messages"] for w in native["native_batch"]["workers"]},
            },
        )
        clocks = [
            dict(
                slot=w["slot"], wall_seconds=m["seconds"], cpu_seconds=m["cpu_seconds"]
            )
            for w in native["native_batch"]["workers"]
            for m in w["messages"]
            if m.get("kind") == "done"
        ]
        if clocks != child_data["worker_body_clocks"] or any(
            type(x[k]) not in (int, float) or not math.isfinite(x[k]) or x[k] < 0
            for x in clocks
            for k in ("wall_seconds", "cpu_seconds")
        ):
            raise ArithmeticError("saved separate worker clocks changed")
        if any(w["wall_seconds"] > end["wall"] - start["wall"] for w in clocks):
            raise ArithmeticError(
                "individual worker body exceeds enclosing parent body"
            )
        if (
            previous.numerical_identity(native, observed["replays"])
            != child_data["identity"]
        ):
            raise ArithmeticError("complete raw numerical identity changed")
        children.append(child_data)
        ledgers.append(results)
    identity = pair_identity(children)
    if (
        any(pair_data[k] != v for k, v in identity.items())
        or type(pair_data["seconds"]) not in (int, float)
        or not 0 < pair_data["seconds"] < 1800
    ):
        raise ArithmeticError("saved pair identity/shared clock changed")
    if (
        pair_data["measurements"][0]["started_perf_counter"]
        + pair_data["measurements"][0]["seconds"]
        > pair_data["measurements"][1]["started_perf_counter"]
    ):
        raise ArithmeticError("pair child clocks overlap")
    span = (
        pair_data["measurements"][-1]["started_perf_counter"]
        + pair_data["measurements"][-1]["seconds"]
        - pair_data["measurements"][0]["started_perf_counter"]
    )
    if pair_data["seconds"] < span:
        raise ArithmeticError("shared pair clock omits child execution")
    return dict(pair=pair_data, children=children, ledgers=ledgers)


def exports(saved: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Use saved complete clocks; iterator time includes consumer work at yields."""
    reads, commands = [], []
    for mode, child_data, measurement, stages in zip(
        ("ordinary", "reuse"),
        saved["children"],
        saved["pair"]["measurements"],
        saved["ledgers"],
        strict=True,
    ):
        for index, row in enumerate(child_data["read_clocks"]):
            selected = [] if index == 0 else stages[4 * (index - 1) : 4 * index]
            request_cpu = math.fsum(x["cpu_seconds"] for x in selected[1:])
            archive_cpu = selected[0]["cpu_seconds"] if selected else 0.0
            read_cpu = row["after"]["cpu"] - row["before"]["cpu"]
            if request_cpu > archive_cpu + 1e-9 or archive_cpu > read_cpu + 1e-9:
                raise ArithmeticError("saved context CPU accounting does not close")
            reads.append(
                dict(
                    mode=mode,
                    read=index,
                    scope=child_data["identity"]["computed_replays"][index]["scope"],
                    read_cpu_seconds=read_cpu,
                    read_wall_seconds=row["after"]["wall"] - row["before"]["wall"],
                    archive_cpu_seconds=archive_cpu,
                    sampled_dictionary_cpu_seconds=selected[1]["cpu_seconds"]
                    if selected
                    else 0.0,
                    full_dictionary_cpu_seconds=selected[2]["cpu_seconds"]
                    if selected
                    else 0.0,
                    prior_iterator_inclusive_cpu_seconds=selected[3]["cpu_seconds"]
                    if selected
                    else 0.0,
                    other_archive_cpu_seconds=archive_cpu - request_cpu,
                    outside_archive_cpu_seconds=read_cpu - archive_cpu,
                )
            )
        workers = child_data["worker_body_clocks"]
        commands.append(
            dict(
                mode=mode,
                complete_wall_seconds=measurement["seconds"],
                parent_body_cpu_seconds=child_data["complete_body_parent_cpu_seconds"],
                sum_worker_body_cpu_seconds=math.fsum(
                    w["cpu_seconds"] for w in workers
                ),
                maximum_worker_body_wall_seconds=max(
                    w["wall_seconds"] for w in workers
                ),
                worker_count=len(workers),
            )
        )
    return reads, commands


def report(root: Path, output: Path, destination: Path | None = None) -> None:
    """Saved-data-only authentication/rendering; no construction or reference."""
    import csv
    import importlib

    from compact_suit.admission import published

    saved = saved_pair(root, output)
    for path in sorted(output.rglob("*")):
        if path.is_file() and "report" not in path.relative_to(output).parts:
            published(root, path)
    folder = destination if destination is not None else output / "report"
    if folder.exists() or folder.is_symlink():
        raise FileExistsError("retain existing report; choose a fresh destination")
    if destination is not None and folder.resolve().is_relative_to(output.resolve()):
        raise ValueError(
            "separate report destination must be outside saved raw evidence"
        )
    folder.mkdir(parents=True)
    reads, commands = exports(saved)
    for name, rows in (("reads.csv", reads), ("commands.csv", commands)):
        with (folder / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    atomic(
        folder / "summary.json",
        dict(
            reads=reads,
            commands=commands,
            identity_sha256=saved["pair"]["identity_sha256"],
            admission_evidence=False,
            limitations=(
                "One ordered pair, not stable causal speedup or production/strength "
                "admission. Ordinary has the same root/request observation. "
                "Dictionary clocks include validation/witness/copy work; prior "
                "iterator includes consumer decoding while yields are suspended. "
                "Add disjoint request CPU and archive residual only; never add "
                "inclusive root twice. Worker CPU sums parallel work and is not "
                "elapsed time. No new training/default/forecast admission."
            ),
        ),
    )
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors = ("#0072B2", "#E69F00", "#009E73", "#CC79A7")
    for index, axis in enumerate(axes, 1):
        chosen = [r for r in reads if r["read"] == index]
        bottom = [0.0, 0.0]
        for color, key, label in zip(
            colors,
            (
                "sampled_dictionary_cpu_seconds",
                "full_dictionary_cpu_seconds",
                "prior_iterator_inclusive_cpu_seconds",
                "other_archive_cpu_seconds",
            ),
            (
                "First dictionary",
                "Second dictionary",
                "Prior iterator + consumer",
                "Other archive work",
            ),
            strict=True,
        ):
            values = [r[key] for r in chosen]
            axis.bar(
                [r["mode"] for r in chosen],
                values,
                bottom=bottom,
                color=color,
                label=label,
            )
            bottom = [a + b for a, b in zip(bottom, values, strict=True)]
        axis.set_title(
            "Cost before reference" if index == 1 else "Cost after reference"
        )
        axis.set_ylabel("Parent CPU seconds inside archive check")
    axes[1].legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    figure.suptitle("Exact context reuse: complete root and disjoint request work")
    figure.tight_layout()
    figure.savefig(folder / "context-work.png", dpi=150)
    plt.close(figure)
    figure, axes = plt.subplots(1, 3, figsize=(11, 4))
    for axis, key, title in zip(
        axes,
        (
            "complete_wall_seconds",
            "parent_body_cpu_seconds",
            "sum_worker_body_cpu_seconds",
        ),
        ("Complete elapsed time", "Parent body CPU", "Sum of worker body CPU"),
        strict=True,
    ):
        axis.bar([r["mode"] for r in commands], [r[key] for r in commands])
        axis.set_title(title)
        axis.set_ylabel("Seconds")
    figure.suptitle("Separate clocks; parallel worker CPU is not elapsed time")
    figure.tight_layout()
    figure.savefig(folder / "complete-clocks.png", dpi=150)
    plt.close(figure)


def main() -> int:
    import argparse

    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=("proof", "pair", "report"))
    parser.add_argument("--child", choices=("proof", "ordinary", "reuse"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--report-output",
        type=Path,
        help="Fresh report destination outside saved raw evidence",
    )
    args = parser.parse_args()
    output = ROOT / args.output
    if args.report_output is not None and args.operation != "report":
        parser.error("--report-output is only for saved-data reports")
    if args.child and args.operation:
        parser.error("child mode and parent operation are separate")
    if args.child:
        origin = float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"])
        return (
            proof(ROOT, output, origin)
            if args.child == "proof"
            else child(ROOT, args.child, output, origin)
        )
    if args.operation == "report":
        report(
            ROOT,
            output,
            ROOT / args.report_output if args.report_output is not None else None,
        )
        return 0
    if args.operation == "pair":
        return pair(ROOT, output)
    if args.operation != "proof":
        parser.error("choose proof or pair")
    if not output.resolve().is_relative_to(ROOT / "results/runs"):
        raise ValueError("fresh ignored own-proof destination required")
    remaining = 180 - (time.perf_counter() - started)
    if remaining <= 0:
        raise TimeoutError("complete own-proof startup exhausted180-second cap")
    measurement = previous.supervise(
        [
            sys.executable,
            str(ROOT / ENTRY),
            "--child",
            "proof",
            "--output",
            str(output),
        ],
        output,
        remaining,
    )
    return 0 if measurement["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
