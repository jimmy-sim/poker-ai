"""Actual per-process hook scope and mandatory serialized execution evidence."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from recall_cache_support import RecallProofs, hooks

from compact_cached.contract import CONFIG_SHA, variant


@contextmanager
def cached(root: Path) -> Iterator[RecallProofs]:
    c = variant(root)
    config = json.loads((root / c["cache_config"]).read_text())
    with hooks(config, enabled=True) as cache:
        yield cache


def check_counters(row: dict[str, Any]) -> None:
    fields = {
        "requests",
        "original_traversals",
        "hits",
        "rejections",
        "fallbacks",
        "successful_proofs",
        "enabled",
    }
    if set(row) != fields or row["enabled"] is not True:
        raise ArithmeticError("complete enabled validation-cache counters required")
    if any(type(row[k]) is not int or row[k] < 0 for k in fields - {"enabled"}):
        raise ArithmeticError("cache counters must be nonnegative integers")
    if (
        row["requests"] != row["original_traversals"] + row["hits"]
        or row["rejections"] != 0
        or row["fallbacks"] > row["original_traversals"]
        or row["successful_proofs"] != row["original_traversals"] - row["fallbacks"]
    ):
        raise ArithmeticError("effective cache request/proof accounting changed")


def check_execution(root: Path, saved: dict[str, Any]) -> None:
    if saved.get("implementation_config") != variant(root):
        raise ArithmeticError("effective cached implementation contract required")
    try:
        check_counters(saved["validation_cache"])
        for name in ("training_batch", "native_batch"):
            if name not in saved:
                continue
            workers = saved[name]["workers"]
            if len(workers) != 3:
                raise ArithmeticError("all three effective worker records required")
            for worker in workers:
                done = [e for e in worker["messages"] if e.get("kind") == "done"]
                if (
                    len(done) != 1
                    or done[0]["summary"]["implementation_sha256"] != CONFIG_SHA
                ):
                    raise ArithmeticError("worker effective implementation changed")
                check_counters(done[0]["summary"]["validation_cache"])
    except (KeyError, TypeError) as exc:
        raise ArithmeticError("missing effective execution/counter evidence") from exc
