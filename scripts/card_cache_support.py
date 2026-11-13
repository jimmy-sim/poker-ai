"""Bounded reuse of original immutable card-only results; diagnostic scope.

Keys preserve input order and exact primitive types. Unsupported inputs and
changed kernel dependencies execute the original function; exceptions never enter
the cache. Hooks live only in this process and restore late aliases on exit.
"""

import sys
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import ModuleType
from typing import Any


class Store:
    """Exact input memoization with observable accounting and bounded entries."""

    def __init__(
        self,
        original: Callable[..., Any],
        supported: Callable[[tuple[Any, ...], dict[str, Any]], bool],
        dependencies: Callable[[], bool],
        maximum: int,
        enabled: bool,
    ) -> None:
        if type(maximum) is not int or maximum <= 0 or type(enabled) is not bool:
            raise ValueError("positive integer capacity and boolean enabled required")
        self.original = original
        self.supported = supported
        self.dependencies = dependencies
        self.maximum = maximum
        self.enabled = enabled
        self.entries: OrderedDict[tuple[Any, ...], Any] = OrderedDict()
        self.requests = self.original_calls = self.hits = self.fallbacks = 0
        self.insertions = self.evictions = self.errors = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.requests += 1
        eligible = self.supported(args, kwargs) and self.dependencies()
        if self.enabled and eligible:
            try:
                value = self.entries.pop(args)
            except KeyError:
                pass
            else:
                self.entries[args] = value
                self.hits += 1
                return value
        if not eligible:
            self.fallbacks += 1
        self.original_calls += 1
        try:
            value = self.original(*args, **kwargs)
        except BaseException:
            self.errors += 1
            raise
        if self.enabled and eligible:
            self.entries[args] = value
            self.insertions += 1
            if len(self.entries) > self.maximum:
                self.entries.popitem(last=False)
                self.evictions += 1
        return value

    def summary(self) -> dict[str, Any]:
        return dict(
            enabled=self.enabled,
            maximum=self.maximum,
            requests=self.requests,
            original_calls=self.original_calls,
            hits=self.hits,
            fallbacks=self.fallbacks,
            insertions=self.insertions,
            evictions=self.evictions,
            errors=self.errors,
            size=len(self.entries),
        )


def primitive(cards: Any) -> bool:
    return type(cards) is tuple and all(type(card) is int for card in cards)


def dependencies(module: ModuleType, names: tuple[str, ...]) -> Callable[[], bool]:
    frozen = tuple((name, getattr(module, name)) for name in names)
    return lambda: all(getattr(module, name) is value for name, value in frozen)


def modules() -> Iterator[ModuleType]:
    for name, module in list(sys.modules.items()):
        if name.startswith("poker_ai.") and isinstance(module, ModuleType):
            yield module


def replace(original: Any, replacement: Any) -> None:
    for module in modules():
        for name, value in list(vars(module).items()):
            if value is original:
                setattr(module, name, replacement)


@contextmanager
def hooks(config: dict[str, Any], *, enabled: bool) -> Iterator[dict[str, Store]]:
    from poker_ai import cards, evaluator
    from poker_ai.abstraction import potential

    originals = (potential.canonical_cards, evaluator.evaluate_best)
    if any(isinstance(x, Store) for x in originals):
        raise RuntimeError("nested card-cache hooks are not supported")
    card_dependencies = dependencies(
        cards, ("card_bit", "_require_int_in_range", "DECK_SIZE", "format_card")
    )
    canonical_dependencies = dependencies(
        potential, ("cards_to_mask", "SUIT_PERMUTATIONS")
    )
    rank_dependencies = dependencies(
        evaluator,
        (
            "cards_to_mask",
            "evaluate_five",
            "_highest_ranks",
            "_straight_high",
            "_WHEEL_RANK_MASK",
            "HandRank",
            "HandCategory",
            "Counter",
        ),
    )
    canonical = Store(
        originals[0],
        lambda a, k: not k and len(a) == 2 and primitive(a[0]) and primitive(a[1]),
        lambda: card_dependencies() and canonical_dependencies(),
        config["canonical_maxsize"],
        enabled,
    )
    rank = Store(
        originals[1],
        lambda a, k: not k and len(a) == 1 and primitive(a[0]),
        lambda: card_dependencies() and rank_dependencies(),
        config["rank_maxsize"],
        enabled,
    )
    stores = dict(canonical=canonical, rank=rank)
    wrappers = (canonical, rank)
    try:
        for original, wrapper in zip(originals, wrappers, strict=True):
            replace(original, wrapper)
        yield stores
    finally:
        # Includes aliases imported after entry; unrelated later replacements
        # remain untouched. Spawned workers never install these parent hooks.
        for original, wrapper in zip(originals, wrappers, strict=True):
            replace(wrapper, original)


def check_summary(saved: dict[str, Any], config: dict[str, Any], enabled: bool) -> None:
    if set(saved) != {"canonical", "rank"}:
        raise ArithmeticError("both card-cache summaries required")
    fields = {
        "enabled",
        "maximum",
        "requests",
        "original_calls",
        "hits",
        "fallbacks",
        "insertions",
        "evictions",
        "errors",
        "size",
    }
    for name, maximum in (
        ("canonical", config["canonical_maxsize"]),
        ("rank", config["rank_maxsize"]),
    ):
        row = saved[name]
        if (
            set(row) != fields
            or row["enabled"] is not enabled
            or row["maximum"] != maximum
            or any(type(row[k]) is not int or row[k] < 0 for k in fields - {"enabled"})
            or row["requests"] != row["original_calls"] + row["hits"]
            or row["fallbacks"] > row["original_calls"]
            or row["errors"] > row["original_calls"]
            or row["insertions"] > row["original_calls"] - row["errors"]
            or row["size"] != row["insertions"] - row["evictions"]
            or row["size"] > maximum
            or (
                not enabled
                and any(row[k] for k in ("hits", "insertions", "evictions", "size"))
            )
        ):
            raise ArithmeticError("card-cache accounting, bounds or mode changed")
