"""Actual per-process hook scope and mandatory serialized execution evidence."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from recall_cache_support import RecallProofs, hooks

from compact_suit.contract import CONFIG_SHA, variant
from compact_suit.normalization import Normalization, validate
from poker_ai.evaluation.opponent_learning_design import COST, REAL, TOY
from poker_ai.postflop.parallel_profile import same


class Execution:
    """Keep historical recall counters separate from normalization evidence."""

    def __init__(self, recall: RecallProofs, normalization: Normalization) -> None:
        self.recall, self.normalization = recall, normalization
        self.last_receipt: tuple[Path, str] | None = None

    def summary(self) -> dict[str, Any]:
        return self.recall.summary()


@contextmanager
def cached(root: Path, *, parent: bool = True) -> Iterator[Execution]:
    c = variant(root)
    config = json.loads((root / c["cache_config"]).read_text())
    normalization = Normalization(c["normalization"], parent=parent)
    with normalization.installed(), hooks(config, enabled=True) as cache:
        yield Execution(cache, normalization)


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
    if not same(saved.get("implementation_config"), variant(root)):
        raise ArithmeticError("effective cached implementation contract required")
    if (
        saved.get("status") == "completed_own_native_pending"
        and saved.get("scope") == TOY
    ):
        parity = saved.get("software_vector_parity")
        if (
            not isinstance(parity, dict)
            or parity.get("status")
            != "all324policies216books30warms_exact_with_original_own_toy"
        ):
            raise ArithmeticError("formal own toy vector parity evidence required")
        card = saved.get("normalization_contract")
        if (
            not isinstance(card, dict)
            or set(card) != {"folder", "sha256", "source_sha256"}
            or card["folder"] != "own-card-contract"
            or card["source_sha256"] != saved["source_sha256"]
            or type(card["sha256"]) is not str
            or len(card["sha256"]) != 64
        ):
            raise ArithmeticError("fresh complete own production-card proof required")
    try:
        check_counters(saved["validation_cache"])
        validate(saved["normalization"], variant(root)["normalization"], parent=True)
        if (
            saved.get("scope") in (COST, REAL)
            and saved.get("operation") in ("cost-own", "cost-audit", "study", "audit")
            and saved["normalization"]["reduced_evaluations"] <= 0
        ):
            raise ArithmeticError(
                "positive actual parent normalization coverage required"
            )
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
                normalization = done[0]["summary"]["normalization"]
                validate(normalization, variant(root)["normalization"], parent=False)
                if (
                    type(worker["pid"]) is not int
                    or normalization["pid"] != worker["pid"]
                ):
                    raise ArithmeticError("worker normalization process changed")
    except (KeyError, TypeError) as exc:
        raise ArithmeticError("missing effective execution/counter evidence") from exc
