"""Process-owned exact normalization, with truthful live and restored states."""

import functools
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from types import MethodType, ModuleType
from typing import Any

import grouped_depth_support as aliases
import suit_candidates_support as kernel

from poker_ai.abstraction import potential

SCOPE = "parent-only exact suit factorization; workers original; no adaptive hand cache"


class Normalization:
    def __init__(self, config: dict[str, Any], *, parent: bool) -> None:
        if type(parent) is not bool:
            raise TypeError("explicit boolean parent role required")
        if (
            type(config["maximum_parent_requests"]) is not int
            or config["maximum_parent_requests"] <= 0
        ):
            raise ValueError("positive normalization request bound required")
        self.config, self.parent = config, parent
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.requests = self.original_evaluations = self.reduced_evaluations = 0
        self.fallbacks = self.errors = 0
        self.active, self.restored = False, not parent
        self.remaining: int | None = 0 if not parent else None
        self.status = "complete" if not parent else "not_started"

    def summary(self) -> dict[str, Any]:
        return dict(
            scope=SCOPE,
            role="parent" if self.parent else "worker",
            enabled=self.parent,
            pid=self.pid,
            thread=self.thread,
            status=self.status,
            active=self.active,
            restored=self.restored,
            aliases_remaining=self.remaining,
            maximum=self.config["maximum_parent_requests"],
            requests=self.requests,
            original_evaluations=self.original_evaluations,
            reduced_evaluations=self.reduced_evaluations,
            fallbacks=self.fallbacks,
            errors=self.errors,
            table_sha256=self.config["lookup_table_sha256"],
            geometry_sha256=self.config["geometry_sha256"],
        )

    def call(self, *args: Any, **kwargs: Any) -> Any:
        if (
            not self.parent
            or not self.active
            or os.getpid() != self.pid
            or threading.get_ident() != self.thread
            or self.requests >= self.config["maximum_parent_requests"]
        ):
            self.errors += 1
            raise ArithmeticError("normalization process/thread/scope/cap changed")
        self.requests += 1
        eligible = (
            not kwargs
            and len(args) == 2
            and kernel.primitive(args[0])
            and kernel.primitive(args[1])
            and kernel.dependencies_unchanged()
        )
        if eligible:
            self.reduced_evaluations += 1
            call = kernel.reduced_cards
        else:
            self.original_evaluations += 1
            self.fallbacks += 1
            call = kernel.BASE
        try:
            return call(*args, **kwargs)
        except BaseException:
            self.errors += 1
            raise

    @contextmanager
    def installed(self) -> Iterator["Normalization"]:
        if self.active or self.status not in ("not_started", "complete"):
            raise ArithmeticError("normalization scope cannot be reused or nested")
        if not self.parent:
            if potential.canonical_cards is not kernel.BASE:
                raise ArithmeticError("worker must retain original normalization")
            primary = False
            try:
                yield self
            except BaseException:
                primary = True
                raise
            finally:
                self.restored = potential.canonical_cards is kernel.BASE
                self.status = (
                    "complete" if self.restored and not primary else "failed_retained"
                )
                if not self.restored:
                    self.errors += 1
                    if not primary:
                        raise ArithmeticError("worker original normalization changed")
            return
        if (
            self.status != "not_started"
            or potential.canonical_cards is not kernel.BASE
            or threading.current_thread() is not threading.main_thread()
        ):
            raise ArithmeticError(
                "parent normalization requires original main-thread owner"
            )
        kernel.check_geometry(
            self.config["lookup_table_sha256"], self.config["geometry_sha256"]
        )
        initial: list[tuple[ModuleType, str, Any]] = []
        primary = False

        @functools.wraps(kernel.BASE)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(*args, **kwargs)

        self.active, self.status = True, "running"
        try:
            aliases.aliases(kernel.BASE, wrapper, initial)
            if potential.canonical_cards is not wrapper:
                raise ArithmeticError("defining normalization alias not installed")
            yield self
        except BaseException:
            primary = True
            raise
        finally:
            try:
                if potential.canonical_cards is not wrapper:
                    self.errors += 1
                aliases.aliases(wrapper, kernel.BASE)
                for module, name, value in initial:
                    setattr(module, name, value)
                self.remaining = sum(
                    value is wrapper
                    or (isinstance(value, MethodType) and value.__func__ is wrapper)
                    for module in aliases.owned_modules()
                    for value in vars(module).values()
                )
                self.restored = (
                    potential.canonical_cards is kernel.BASE and self.remaining == 0
                )
                self.active = False
                self.status = (
                    "complete" if self.restored and not primary else "failed_retained"
                )
                if not self.restored and not primary:
                    raise ArithmeticError("normalization aliases not restored")
            except BaseException:
                self.active, self.status = False, "failed_retained"
                if not primary:
                    raise


def validate(
    row: dict[str, Any],
    config: dict[str, Any],
    *,
    parent: bool,
    expected_errors: int = 0,
    expected_failure: bool = False,
) -> None:
    """Final state only; fictional zero-card games can have zero requests."""
    expected = Normalization(config, parent=parent).summary()
    numeric = (
        "pid",
        "thread",
        "maximum",
        "requests",
        "original_evaluations",
        "reduced_evaluations",
        "fallbacks",
        "errors",
        "aliases_remaining",
    )
    if (
        set(row) != set(expected)
        or any(type(row[k]) is not int or row[k] < 0 for k in numeric)
        or row["pid"] <= 0
        or row["thread"] <= 0
        or row["scope"] != SCOPE
        or row["role"] != expected["role"]
        or row["enabled"] is not parent
        or row["active"] is not False
        or row["restored"] is not True
        or row["aliases_remaining"] != 0
        or type(expected_failure) is not bool
        or row["status"] != ("failed_retained" if expected_failure else "complete")
        or row["maximum"] != expected["maximum"]
        or row["table_sha256"] != expected["table_sha256"]
        or row["geometry_sha256"] != expected["geometry_sha256"]
        or not 0 <= row["requests"] <= row["maximum"]
        or row["requests"] != row["original_evaluations"] + row["reduced_evaluations"]
        or row["fallbacks"] != row["original_evaluations"]
        or type(expected_errors) is not int
        or expected_errors < 0
        or row["errors"] != expected_errors
        or (
            not parent
            and any(
                row[k]
                for k in (
                    "requests",
                    "original_evaluations",
                    "reduced_evaluations",
                    "fallbacks",
                    "errors",
                )
            )
        )
    ):
        raise ArithmeticError(
            "normalization counters, role or final restoration changed"
        )
