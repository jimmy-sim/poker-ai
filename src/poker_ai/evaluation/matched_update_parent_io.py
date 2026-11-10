"""Versioned parent IO service for unchanged matched-update numerical workers.

Publication changes Git HEAD/status. Those are provenance, not a corpus identity.
The original reader and all its code/hash/schema/numerical checks stay frozen.
This explicit process-scoped adapter supplies a validated manifest view to that
reader; it changes no policy, target, counter, tolerance or training operation.
Use this module as the CLI entry point. It is not a concurrent threaded API.
"""

import json
import runpy
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any

from poker_ai.evaluation import matched_update_overhead as legacy
from poker_ai.evaluation.matched_update_inputs import Sources
from poker_ai.evaluation.matched_update_timing_corpus import corpus as _BASE_CORPUS
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest

CONFIG = "configs/matched-update-parent-io.json"
CONFIG_SHA = "f4cda544a0e0999a8deb16f234f219c8816f760fe0b8633dc071c09fd01c53b2"
_BASE_READ = legacy.read
_LOCK = RLock()


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("parent IO adapter contract changed")
    saved: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if digest(root / saved["parent_config"]) != saved["parent_sha256"]:
        raise ArithmeticError("parent scientific protocol changed")
    return saved


def manifest_view(
    root: Path, original: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    """Keep the saved view only after all stable identities and original bytes pass."""
    if set(original) != set(current) or not same(
        {k: v for k, v in original.items() if k != "source"},
        {k: v for k, v in current.items() if k != "source"},
    ):
        raise ArithmeticError("stable old-policy corpus identity changed")
    # The containing own receipt already requires originally clean source. The
    # nested grid was observed during output creation and can legitimately be
    # dirty with new DATA. Still verify every original grid source/config byte.
    provenance = original["source"]
    if (
        not isinstance(provenance, dict)
        or not provenance["sha256"]
        or any(
            digest(root / path) != expected
            for path, expected in provenance["sha256"].items()
        )
    ):
        raise ArithmeticError("original nested grid source/config bytes changed")
    return original


def read(root: Path, path: Path, deadline: Deadline) -> tuple[dict[str, Any], Sources]:
    """Delegate EVERY frozen receipt/worker/archive/math check with a stable view."""
    saved: dict[str, Any] = json.loads(path.read_text())

    def stable_corpus(
        sources: Sources,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        actual, right, fixed = _BASE_CORPUS(sources)
        view = manifest_view(root, saved["manifest"], actual)
        return view, right, fixed

    with _LOCK:
        previous = vars(legacy)["corpus"]
        if previous is not _BASE_CORPUS:
            raise RuntimeError("another parent corpus service is active")
        vars(legacy)["corpus"] = stable_corpus
        try:
            return _BASE_READ(root, path, deadline)
        finally:
            vars(legacy)["corpus"] = previous


@contextmanager
def activate(root: Path) -> Iterator[None]:
    """Explicit parent service boundary; restore even on failure/SystemExit.

    Spawned numerical workers use the unchanged source factories and algorithms;
    they do not call this parent reader. The service is serialized in its process.
    """
    contract(root)
    with _LOCK:
        previous = legacy.read
        if previous not in (_BASE_READ, read):
            raise RuntimeError("another parent IO service is active")
        legacy.read = read
        try:
            yield
        finally:
            legacy.read = previous


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    operations = {
        name: root / "scripts" / (name + "_matched_updates.py")
        for name in ("check", "profile", "study", "audit", "report")
    }
    if len(sys.argv) < 2 or sys.argv[1] not in operations:
        print(
            "usage: python -m poker_ai.evaluation.matched_update_parent_io "
            "{check,profile,study,audit,report} [original command arguments]"
        )
        return 0 if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help") else 2
    previous = sys.argv
    script = operations[sys.argv[1]]
    sys.argv = [str(script), *sys.argv[2:]]
    try:
        with activate(root):
            runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = previous
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
