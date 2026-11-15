"""Sparse nested input-loader CPU boundaries; never a training admission."""

import argparse
import hashlib
import inspect
import json
import os
import re
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

import collect_complete_reader_helpers as helpers
import profile_coarse_reader as coarse
import trace_card_audit as original
from profile_compact_replay import atomic, canonical, digest, supervise

original_result = coarse.original_result
ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/profile_reader_loads.py"
CONFIG = "configs/reader-load-cpu.json"
CONFIG_SHA = "ddc766c5357cfabc831113d158f6a3e25df161a9f5bfacc3b3408848a15f44a3"
FOLDER = "results/reader-load-cpu"
BASE_CATEGORIES = coarse.CATEGORIES
BASE_TARGETS = coarse.targets
BASE_MODULES = coarse.modules
CATEGORIES = (
    *BASE_CATEGORIES,
    "comparison_inputs",
    "legacy_inputs",
    "sampled_source_replay",
)


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective loader CPU contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, checksum in c["input_sha256"].items():
        p = root / name
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != checksum
        ):
            raise ArithmeticError("loader CPU retained input changed")
    if c["regions"] != list(CATEGORIES):
        raise ArithmeticError("six declared loader boundaries required")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    if (
        Path(__file__).resolve() != root.resolve() / ENTRY
        or Path(coarse.__file__).resolve()
        != root.resolve() / "scripts/profile_coarse_reader.py"
    ):
        raise ArithmeticError("prior collector outside stated checkout")
    c = contract(root)
    _, prior = coarse.binding(root, clean=clean)
    anchor = json.loads((root / c["preserved_source_anchor"]).read_text())["source"][
        "sha256"
    ]
    if len(anchor) != 404 or prior["sha256"] != anchor:
        raise ArithmeticError("preserve all404 prior source files")
    s: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    s["sha256"].update(anchor)
    s["fingerprint"] = sha(s["sha256"])
    if len(s["sha256"]) != 406 or (clean and s["dirty"] is not False):
        raise ArithmeticError("publish clean406-file loader CPU source")
    commit_sources(root, s["git_commit"], s["sha256"])
    return c, s


def modules() -> Iterator[ModuleType]:
    """Owned aliases only, including the private command's earlier imports."""
    seen: set[int] = set()
    for name, mod in list(sys.modules.items()):
        owned = (
            name.startswith("poker_ai.")
            or name == "compact_cached"
            or name.startswith("compact_cached.")
        )
        if owned and isinstance(mod, ModuleType) and id(mod) not in seen:
            seen.add(id(mod))
            yield mod


def targets() -> tuple[tuple[str, Any, str], ...]:
    from compact_cached import cli

    import poker_ai.evaluation.compact_fixed_inputs as sampled
    import poker_ai.evaluation.compact_opponent_sources as comparison
    import poker_ai.evaluation.opponent_learning_sources as legacy

    if vars(cli).get("load") is not comparison.load:
        raise ArithmeticError("actual private reader input alias changed")
    selected = (
        *BASE_TARGETS(),
        ("comparison_inputs", comparison, "load"),
        ("legacy_inputs", legacy, "load"),
        ("sampled_source_replay", sampled, "replay_sources"),
    )
    for _, owner, name in selected:
        value = vars(owner)[name]
        function = value.__func__ if isinstance(value, classmethod) else value
        if (
            not callable(function)
            or inspect.isgeneratorfunction(function)
            or inspect.isasyncgenfunction(function)
            or inspect.iscoroutinefunction(function)
        ):
            raise ArithmeticError("ordinary synchronous target body required")
    return selected


@contextmanager
def extension() -> Iterator[None]:
    """Explicit new capture registry, with original collector globals restored."""
    if (
        coarse.CATEGORIES is not BASE_CATEGORIES
        or coarse.targets is not BASE_TARGETS
        or coarse.modules is not BASE_MODULES
    ):
        raise ArithmeticError("changed or nested collector extension")
    with (
        patch.object(coarse, "CATEGORIES", CATEGORIES),
        patch.object(coarse, "targets", targets),
        patch.object(coarse, "modules", modules),
    ):
        yield


@contextmanager
def reader_observer(root: Path, c: dict[str, Any], output: Path) -> Iterator[None]:
    with extension(), coarse.reader_observer(root, c, output):
        yield


def phase_ledgers(
    output: Path,
    child: dict[str, Any],
    old: dict[str, Any],
    c: dict[str, Any],
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    with extension():
        data = coarse.phase_ledgers(output, child, old, c)
    baseline = json.loads((root / c["baseline_capture"]).read_text())
    expected = [
        dict(
            read=x["read"],
            counts={k: v["calls"] for k, v in x["selected"]["groups"].items()},
        )
        for x in baseline["rows"]
        if x["mode"] == "profiled"
    ]
    if expected != c["baseline_selected_read_counts"] or len(expected) != 3:
        raise ArithmeticError("pinned original per-read selected inventory changed")
    for i, (actual, wanted) in enumerate(zip(data, expected, strict=True)):
        counts = {k: actual["summary"]["groups"][k]["calls"] for k in BASE_CATEGORIES}
        if (
            wanted["read"] != i
            or set(wanted["counts"]) != set(BASE_CATEGORIES)
            or counts != wanted["counts"]
        ):
            raise ArithmeticError("original selected capture lost or gained calls")
    return data


def checked(root: Path, source: dict[str, Any]) -> None:
    from compact_cached.admission import published

    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    checks(root, path, source)
    published(root, path)
    for row in json.loads(path.read_text())["checks"]:
        p = root / row["log"]["file"]
        published(root, p)
        log = p.read_text(encoding="utf-8-sig")
        py, np = ("3.11.17", "2.4.6") if row["minor"] == "311" else ("3.12.15", "2.5.4")
        if row["numpy"] != np:
            raise ArithmeticError("actual qualified NumPy required")
        if row["role"] == "hosted":
            original.actual_host_runtime(log, py, np)
        elif set(re.findall(r"ACTUAL_PYTHON=([0-9.]+)", log)) != {py} or set(
            re.findall(r"ACTUAL_NUMPY=([0-9.]+)", log)
        ) != {np}:
            raise ArithmeticError("actual qualified local runtime required")


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="starting",
        mode=mode,
        pid=os.getpid(),
        thread=threading.get_ident(),
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        admission_evidence=False,
        poker_training_performed=False,
        reference_output_used_in_training=False,
    )
    atomic(output / "child.json", saved)
    try:
        if mode not in ("control", "profiled"):
            raise ValueError("unknown observation mode")
        c, source = binding(root)
        checked(root, source)
        saved["runtime_requirements"] = helpers.runtime_requirements(c)
        import numpy

        # Both arms import the same original entry alias before original card hooks.
        from compact_cached import cli  # noqa: F401

        from poker_ai.reproducibility import runtime_environment

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or numpy.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError("original real-archive runtime required")
        saved.update(
            source=source,
            config_sha256=CONFIG_SHA,
            qualification_sha256=digest(root / FOLDER / "checks.json"),
            environment=runtime_environment(),
            idle_control=original.control(c),
        )
        atomic(output / "child.json", saved)
        targets()  # Common preloading in both halves, before original card hooks.
        (output / "old").mkdir()
        if mode == "profiled":
            with reader_observer(root, c, output):
                code = original.child(root, "uncached", output / "old", origin)
        else:
            code = original.child(root, "uncached", output / "old", origin)
        if code != 0:
            raise ArithmeticError("original audit child did not complete")
        old = original_result(root, output, c)
        if mode == "profiled":
            phase_ledgers(output, saved, old, c, root=root)
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or saved["qualification_sha256"] != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("measurement source/input/qualification changed")
        saved.update(
            status="complete",
            original_identity_sha256=hashlib.sha256(
                canonical(old["identity"])
            ).hexdigest(),
            reference_constructed=True,
            seconds=time.perf_counter() - origin,
        )
        saved["raw_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
            and (
                p.parent != output
                or p.name not in ("child.json", "measurement.json", "command.log")
            )
        }
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - origin,
        )
        atomic(output / "child.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def verify_pair(root: Path, output: Path) -> dict[str, Any]:
    c, current = binding(root, clean=False)
    pair = json.loads((output / "pair.json").read_text())
    if (
        pair["status"] != "complete"
        or pair["admission_evidence"] is not False
        or type(pair["seconds"]) not in (int, float)
        or not 0 < pair["seconds"] < c["maximum_pair_seconds"]
        or len(pair["measurements"]) != 2
    ):
        raise ArithmeticError("complete capped original-context pair required")
    children, olds, data = [], [], []
    expected_files = {"pair.json"}
    for mode, m in zip(c["order"], pair["measurements"], strict=True):
        folder = output / mode
        row = json.loads((folder / "child.json").read_text())
        if (
            m != json.loads((folder / "measurement.json").read_text())
            or m["returncode"] != 0
            or m["interrupted"] is not None
            or type(m["seconds"]) not in (int, float)
            or not 0 < m["seconds"] < c["maximum_child_seconds"]
            or m["child_sha256"] != digest(folder / "child.json")
            or digest(folder / "command.log") != pair["command_log_sha256"][mode]
        ):
            raise ArithmeticError(
                "complete supervised measurement/raw binding required"
            )
        command = [
            c["idle_control"]["path"],
            *c["idle_control"]["arguments"],
            row["executable"],
            str(Path(row["execution_root"]) / ENTRY),
            "--child",
            mode,
            "--output",
            row["execution_output"],
        ]
        if (
            m["command"] != command
            or not Path(row["execution_output"]).is_relative_to(
                Path(row["execution_root"]) / "results/runs"
            )
            or row["mode"] != mode
            or row["status"] != "complete"
            or row["config_sha256"] != CONFIG_SHA
            or row["source"]["sha256"] != current["sha256"]
            or row["qualification_sha256"] != digest(root / FOLDER / "checks.json")
            or any(
                row[k] is not False
                for k in (
                    "admission_evidence",
                    "poker_training_performed",
                    "reference_output_used_in_training",
                )
            )
            or row["reference_constructed"] is not True
        ):
            raise ArithmeticError("measurement scope/source/command changed")
        if (
            row["runtime_requirements"]
            != dict(
                distributions=c["required_distributions"],
                metadata_probe=c["metadata_probe"],
            )
            or any(row["environment"][k] != v for k, v in c["runtime"].items())
            or row["idle_control"]
            != dict(
                c["idle_control"],
                requested=True,
                assertion_state_independently_audited=False,
            )
        ):
            raise ArithmeticError("actual runtime/metadata/control context changed")
        for name, sha in row["raw_sha256"].items():
            p = folder / name
            if (
                p.is_symlink()
                or not p.resolve().is_relative_to(folder.resolve())
                or digest(p) != sha
            ):
                raise ArithmeticError("retained raw original-context file changed")
            expected_files.add(f"{mode}/{name}")
        expected_files.update(
            f"{mode}/{n}" for n in ("child.json", "measurement.json", "command.log")
        )
        old = original_result(root, folder, c)
        if (
            row["pid"] != old["child_before"]["pid"]
            or row["original_identity_sha256"]
            != hashlib.sha256(canonical(old["identity"])).hexdigest()
        ):
            raise ArithmeticError("original child process or identity changed")
        if mode == "profiled":
            data = phase_ledgers(folder, row, old, c, root=root)
        elif (folder / "inner-reads.json").exists() or (folder / "reads").exists():
            raise ArithmeticError("control must not install the added read observer")
        children.append(row)
        olds.append(old)
    if expected_files != {
        str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()
    } or any(p.is_symlink() for p in output.rglob("*")):
        raise ArithmeticError("raw file inventory changed")
    if (
        children[0]["pid"] == children[1]["pid"]
        or children[0]["source"] != children[1]["source"]
        or olds[0]["identity"] != olds[1]["identity"]
        or olds[0]["card_cache"] != olds[1]["card_cache"]
    ):
        raise ArithmeticError(
            "separate children with exact original audit identity required"
        )
    checked(root, children[0]["source"])
    return dict(pair=pair, children=children, originals=olds, ledgers=data)


def pair(root: Path, output: Path) -> int:
    started = time.perf_counter()
    output = output.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(root.resolve() / "results/runs")
    ):
        raise ValueError("fresh ignored destination required; retain every attempt")
    output.mkdir(parents=True)
    saved: dict[str, Any] = dict(
        status="running", measurements=[], admission_evidence=False
    )
    atomic(output / "pair.json", saved)
    try:
        c = contract(root)
        original.control(c)
        for mode in c["order"]:
            cap = min(
                c["maximum_child_seconds"],
                started + c["maximum_pair_seconds"] - time.perf_counter(),
            )
            if cap <= 0:
                raise TimeoutError("shared complete diagnostic cap")
            m = supervise(
                [
                    c["idle_control"]["path"],
                    *c["idle_control"]["arguments"],
                    sys.executable,
                    str(root / ENTRY),
                    "--child",
                    mode,
                    "--output",
                    str(output / mode),
                ],
                output / mode,
                cap,
            )
            saved["measurements"].append(m)
            log = output / mode / "command.log"
            saved.setdefault("command_log_sha256", {})[mode] = (
                digest(log) if log.is_file() else None
            )
            atomic(output / "pair.json", saved)
            if m["returncode"] != 0:
                raise ArithmeticError("child failed; partial evidence retained")
        saved.update(status="complete", seconds=time.perf_counter() - started)
        atomic(output / "pair.json", saved)
        verify_pair(root, output)
        saved["seconds"] = time.perf_counter() - started
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("final verification exceeds shared cap")
        atomic(output / "pair.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        atomic(output / "pair.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--output", type=Path, default=Path("results/runs/reader-load-cpu/pair")
    )
    p.add_argument("--child", choices=("control", "profiled"), help=argparse.SUPPRESS)
    p.add_argument("--show", action="store_true")
    args = p.parse_args()
    if args.show:
        print(json.dumps(report(ROOT, ROOT / args.output), sort_keys=True, indent=2))
        return 0
    if args.child:
        return child(
            ROOT,
            args.child,
            ROOT / args.output,
            float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"]),
        )
    return pair(ROOT, ROOT / args.output)


def report(root: Path, output: Path) -> dict[str, Any]:
    verified = verify_pair(root, output)
    rows = []
    for mode in ("control", "profiled"):
        outer = json.loads(
            (output / mode / "old/parent-resource-reads.json").read_text()
        )["reads"]
        for i, row in enumerate(outer):
            v: dict[str, Any] = dict(
                mode=mode,
                read=i,
                scope=row["scope"],
                outer=row["observation"]["interval"],
                selected=None,
            )
            if mode == "profiled":
                x = verified["ledgers"][i]["summary"]
                inner = json.loads((output / mode / "inner-reads.json").read_text())[
                    "reads"
                ][i]["observation"]["interval"]
                v.update(
                    selected=x,
                    inner=inner,
                    outside_selected_cpu=inner["clocks"]["process_cpu_seconds"]
                    - x["selected_union_cpu"],
                )
            rows.append(v)
    return dict(
        scope="ONE_ORDERED_NESTED_LOADER_PROCESS_CPU_NOT_INSTRUCTION_SAMPLES_OR_ADMISSION",
        rows=rows,
        measurements=verified["pair"]["measurements"],
        original_identity_exact=True,
        poker_training_performed=False,
        long_run_admitted=False,
        input_sha256={
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
