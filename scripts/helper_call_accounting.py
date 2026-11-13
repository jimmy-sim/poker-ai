"""Software-only transparent helper-call accounting; no collection runner.

Resource changes span the synchronous call; they are not exclusive PID CPU.
Unknown calls retain execution behavior but make coverage incomplete. Contents,
raw arguments, environment and input are never retained in the ledger.
"""

import copy
import hashlib
import json
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

from card_clock_support import check_record, record, snapshot

READ_ONLY = frozenset(
    (
        "status",
        "rev-parse",
        "ls-tree",
        "show",
        "diff",
        "merge-base",
        "ls-files",
        "log",
        "cat-file",
    )
)


def fingerprint(value: Any) -> dict[str, Any]:
    if value is None:
        return dict(kind="none", encoded_bytes=0, sha256=None)
    if type(value) is bytes:
        encoded, kind = value, "bytes"
    elif type(value) is str:
        encoded, kind = (
            value.encode("utf-8", "surrogatepass"),
            "text_utf8_surrogatepass",
        )
    else:
        return dict(kind="unsupported_not_retained", encoded_bytes=None, sha256=None)
    return dict(
        kind=kind,
        encoded_bytes=len(encoded),
        sha256=hashlib.sha256(encoded).hexdigest(),
    )


class Recorder:
    def __init__(
        self,
        root: Path,
        commands: tuple[str, ...],
        *,
        original: Callable[..., Any] | None = None,
        emit: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if (
            not commands
            or any(type(c) is not str or c not in READ_ONLY for c in commands)
            or len(set(commands)) != len(commands)
        ):
            raise ValueError(
                "unique declared read-only Git command categories required"
            )
        self.root = root.resolve()
        self.commands = frozenset(commands)
        self.original = original if original is not None else subprocess.run
        self.emit = emit
        self.rows: list[dict[str, Any]] = []
        self.retention_errors = 0
        self.observer_errors = 0

    def classify(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> dict[str, Any] | None:
        argv: Any = (
            args[0]
            if len(args) == 1 and "args" not in kwargs
            else kwargs.get("args")
            if not args
            else None
        )
        if (
            kwargs.get("shell", False) is not False
            or type(argv) not in (list, tuple)
            or len(argv) < 4
            or any(type(a) is not str for a in argv)
        ):
            return None
        # Relative -C paths use the child's cwd, which may differ from ours.
        # Keep recognition narrow; the future collector uses absolute roots.
        if not Path(argv[2]).is_absolute():
            return None
        try:
            known_root = Path(argv[2]).resolve() == self.root
        except (OSError, ValueError, RuntimeError):
            return None
        if (
            Path(argv[0]).name != "git"
            or argv[1] != "-C"
            or not known_root
            or argv[3] not in self.commands
        ):
            return None
        return dict(
            category="git " + argv[3],
            argv_sha256=hashlib.sha256(
                json.dumps(
                    list(argv), ensure_ascii=True, separators=(",", ":")
                ).encode()
            ).hexdigest(),
        )

    def publish(self, row: dict[str, Any]) -> None:
        if self.emit is not None:
            try:
                self.emit(copy.deepcopy(row))
            except BaseException:
                self.retention_errors += 1
                raise

    def finish(self, row: dict[str, Any], before: dict[str, Any] | None) -> None:
        if before is not None:
            row["observation"] = record(before, snapshot())
        self.publish(row)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        classification = self.classify(args, kwargs)
        row: dict[str, Any] = dict(
            ordinal=len(self.rows),
            recognized=classification is not None,
            status="running",
        )
        before = None
        if classification is not None:
            row.update(
                classification,
                attribution=(
                    "parent reaped-child increment over call; not exclusive PID "
                    "CPU; concurrent children would confound"
                ),
            )
        else:
            row["coverage"] = (
                "unsupported call; arguments/input/environment/output not retained"
            )
        # Count the attempt even if its first resource reading fails. Otherwise
        # earlier completed calls could incorrectly look like full coverage.
        self.rows.append(row)
        try:
            before = snapshot() if classification is not None else None
            if classification is not None:
                row["before"] = before
            self.publish(row)
        except BaseException:
            self.observer_errors += 1
            row["status"] = "observer_failed_before_execution"
            raise
        try:
            result = self.original(*args, **kwargs)
        except BaseException as error:
            row.update(status="failed", exception_kind=type(error).__name__)
            code = getattr(error, "returncode", None)
            if type(code) is int:
                row["returncode"] = code
            try:
                self.finish(row, before)
            except BaseException:
                self.observer_errors += 1
                row["status"] = "primary_failure_with_observer_failure"
            raise
        row.update(status="complete")
        if classification is not None:
            row.update(
                returncode=result.returncode,
                stdout=fingerprint(result.stdout),
                stderr=fingerprint(result.stderr),
            )
        try:
            self.finish(row, before)
        except BaseException:
            self.observer_errors += 1
            row["status"] = "observer_failed_after_execution"
            raise
        return result

    def summary(self) -> dict[str, Any]:
        return dict(
            requests=len(self.rows),
            recognized=sum(r["recognized"] for r in self.rows),
            unsupported=sum(not r["recognized"] for r in self.rows),
            completed=sum(r["status"] == "complete" for r in self.rows),
            retention_errors=self.retention_errors,
            observer_errors=self.observer_errors,
            exclusive_pid_attribution=False,
            collection_scope_not_inferred=True,
        )

    def require_complete_coverage(self) -> None:
        s = self.summary()
        if (
            not s["requests"]
            or s["unsupported"]
            or s["completed"] != s["requests"]
            or s["retention_errors"]
            or s["observer_errors"]
        ):
            raise ArithmeticError(
                "incomplete, failed or unsupported helper-call coverage"
            )
        for index, row in enumerate(self.rows):
            if (
                row["ordinal"] != index
                or row.get("before") != row["observation"]["before"]
            ):
                raise ArithmeticError("raw helper start or ordinal changed")
            check_record(row["observation"])


@contextmanager
def hooks(recorder: Recorder) -> Iterator[Recorder]:
    if isinstance(subprocess.run, Recorder):
        raise RuntimeError("nested helper accounting is unsupported")
    with patch.object(subprocess, "run", recorder):
        yield recorder
