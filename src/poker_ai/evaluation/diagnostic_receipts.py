"""Sealed historical dependencies and exact-source diagnostic check receipts.

Historical compatibility authenticates every originally named file/Git blob,
not a replacement implementation. Old aggregate checkers remain unchanged.
"""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.compact_fixed_inputs import bound as bound
from poker_ai.evaluation.compact_fixed_inputs import checked
from poker_ai.evaluation.compact_fixed_inputs import historical as historical
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance


def config(root: Path, filename: str, expected: str) -> dict[str, Any]:
    path = root / filename
    if digest(path) != expected:
        raise ArithmeticError("prospective diagnostic contract changed")
    result: dict[str, Any] = json.loads(path.read_text())
    for name, checksum in result["input_sha256"].items():
        checked(root, dict(file=name, sha256=checksum))
    return result


def source(
    root: Path, filename: str, entry: str, *, clean: bool = True
) -> dict[str, Any]:
    if not Path(__file__).resolve().is_relative_to(root / "src"):
        raise ArithmeticError("diagnostic modules outside stated checkout")
    saved = source_provenance(root, root / filename, entrypoints=(entry,))
    saved["fingerprint"] = sha(saved["sha256"])
    if clean and saved["dirty"] is not False:
        raise ArithmeticError("publish clean diagnostic source first")
    return saved


def check_source(root: Path, saved: dict[str, Any], filename: str, entry: str) -> None:
    historical(root, saved, saved["fingerprint"])
    if (
        source(root, filename, entry, clean=False)["fingerprint"]
        != saved["fingerprint"]
    ):
        raise ArithmeticError("diagnostic execution source/config changed")


def checks(root: Path, path: Path, current: dict[str, Any]) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    rows = saved["checks"]
    keys = [(r["role"], r["minor"]) for r in rows]
    if (
        len(keys) != 6
        or set(keys)
        != {(r, v) for r in ("base", "optional", "hosted") for v in ("311", "312")}
        or saved["source_fingerprint"] != current["fingerprint"]
        or len({r["checked_commit"] for r in rows}) != 1
    ):
        raise ArithmeticError("six exact-source check roles required")
    files.commit_sources(root, rows[0]["checked_commit"], current["sha256"])
    for row in rows:
        log = checked(root, row["log"]).read_text(encoding="utf-8-sig")
        if (
            row["status"] != "passed"
            or row["source_fingerprint"] != current["fingerprint"]
            or row["checked_commit"] not in log
            or "passed" not in log
            or row["python"] != ("3.11.17" if row["minor"] == "311" else "3.12.15")
        ):
            raise ArithmeticError("diagnostic execution/runtime/log mismatch")
        if row["role"] == "hosted" and (
            row["conclusion"] != "success"
            or row["head_sha"] != row["checked_commit"]
            or type(row["job_id"]) is not int
            or type(row["run_id"]) is not int
        ):
            raise ArithmeticError("both exact-head hosted passes required")
    return bound(root, path)
