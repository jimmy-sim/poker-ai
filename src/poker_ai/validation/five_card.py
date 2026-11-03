"""Reproducible five-card rank validation against optional Treys.

The production evaluator never imports this module or the reference library.
Treys is loaded only when run_validation is explicitly invoked.
"""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from itertools import combinations, pairwise
from math import comb
from pathlib import Path
from typing import Literal

from numpy.random import PCG64, Generator

from poker_ai.cards import DECK_SIZE, format_card
from poker_ai.evaluator import HandCategory, HandRank, evaluate_five


def expected_category_counts() -> dict[HandCategory, int]:
    """Derive physical-hand counts independently from evaluator logic.

    For example, a pair chooses its rank, two suits, three other ranks, and one
    suit per kicker. Distinct-rank hands exclude ten straight rank sets and four
    same-suit assignments when computing the high-card count.
    """
    return {
        HandCategory.HIGH_CARD: (comb(13, 5) - 10) * (4**5 - 4),
        HandCategory.ONE_PAIR: 13 * comb(4, 2) * comb(12, 3) * 4**3,
        HandCategory.TWO_PAIR: comb(13, 2) * comb(4, 2) ** 2 * 11 * 4,
        HandCategory.THREE_OF_A_KIND: 13 * comb(4, 3) * comb(12, 2) * 4**2,
        HandCategory.STRAIGHT: 10 * (4**5 - 4),
        HandCategory.FLUSH: 4 * (comb(13, 5) - 10),
        HandCategory.FULL_HOUSE: 13 * comb(4, 3) * 12 * comb(4, 2),
        HandCategory.FOUR_OF_A_KIND: 13 * 12 * 4,
        HandCategory.STRAIGHT_FLUSH: 10 * 4,
    }


def expected_distinct_ranks() -> int:
    """Count equivalence classes after removing suit-based distinctions."""
    distinct_rank_sets = comb(13, 5) - 10
    return (
        2 * distinct_rank_sets  # High card and flush
        + 13 * comb(12, 3)  # Pair
        + comb(13, 2) * 11  # Two pair
        + 13 * comb(12, 2)  # Trips
        + 20  # Straight and straight flush
        + 2 * 13 * 12  # Full house and quads
    )


@dataclass
class RankAgreement:
    """Check equality classes and ordering despite opposite scoring directions.

    Our HandRank increases with strength; Treys integers decrease with strength.
    A bijection checks ties in both directions. Its strict descending reference
    scores under ascending own ranks then check the full observed ordering.
    """

    own_to_reference: dict[HandRank, int] = field(default_factory=dict)
    reference_to_own: dict[int, HandRank] = field(default_factory=dict)

    def observe(self, own: HandRank, reference: int) -> None:
        """Record one observation, raising if either equality relation differs."""
        if (
            type(reference) is not int
            or not 1 <= reference <= expected_distinct_ranks()
        ):
            raise ValueError("invalid Treys reference score")
        if own in self.own_to_reference and self.own_to_reference[own] != reference:
            raise ValueError("own evaluator ties hands that Treys distinguishes")
        if (
            reference in self.reference_to_own
            and self.reference_to_own[reference] != own
        ):
            raise ValueError("own evaluator distinguishes hands that Treys ties")
        self.own_to_reference[own] = reference
        self.reference_to_own[reference] = own

    def check_order(self) -> None:
        """Raise if any observed adjacent classes disagree on strength order."""
        for weaker, stronger in pairwise(sorted(self.own_to_reference)):
            if self.own_to_reference[weaker] <= self.own_to_reference[stronger]:
                raise ValueError(
                    f"ordering disagrees with Treys: {weaker!r} vs {stronger!r}"
                )


@dataclass(frozen=True)
class ValidationConfig:
    """Exactly specified traversal; exhaustive enumeration uses no random seed."""

    mode: Literal["exhaustive", "random"]
    hands: int
    seed: int | None

    def __post_init__(self) -> None:
        if type(self.hands) is not int or self.hands < 1:
            raise ValueError("hands must be a positive built-in int")
        if self.mode == "exhaustive":
            if self.hands != comb(DECK_SIZE, 5) or self.seed is not None:
                raise ValueError(
                    "exhaustive mode requires all combinations and seed=null"
                )
        elif self.mode == "random":
            if type(self.seed) is not int or self.seed < 0:
                raise ValueError("random mode requires a nonnegative integer seed")
        else:
            raise ValueError("mode must be exhaustive or random")


def load_config(path: Path) -> ValidationConfig:
    """Reject misspelled settings, booleans-as-counts, and ambiguous seed usage."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or set(data) != {"mode", "hands", "seed"}:
        raise ValueError("config must contain exactly mode, hands, and seed")
    hands, seed = data["hands"], data["seed"]
    if data["mode"] == "exhaustive":
        return ValidationConfig("exhaustive", hands, seed)
    if data["mode"] == "random":
        return ValidationConfig("random", hands, seed)
    raise ValueError("mode must be exhaustive or random")


def iter_hands(config: ValidationConfig) -> Iterable[tuple[int, ...]]:
    """Enumerate lexicographically or sample independently with an explicit RNG."""
    if config.mode == "exhaustive":
        yield from combinations(range(DECK_SIZE), 5)
    else:
        rng = Generator(PCG64(config.seed))
        for _ in range(config.hands):
            yield tuple(int(card) for card in rng.choice(DECK_SIZE, 5, replace=False))


def source_provenance(root: Path, config_path: Path) -> dict[str, object]:
    """Capture revision, dirty state, and exact validation/source/config hashes."""
    paths = sorted((root / "src").rglob("*.py"))
    paths += [
        root / "scripts/validate_five.py",
        root / "pyproject.toml",
        root / "uv.lock",
    ]
    paths.append(config_path.resolve())
    hashes = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }

    def git_output(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return None
        return result.stdout.rstrip("\n") if result.returncode == 0 else None

    status = git_output("status", "--porcelain=v1")
    return {
        "git_commit": git_output("rev-parse", "HEAD"),
        "dirty": bool(status) if status is not None else None,
        "git_status": status.splitlines() if status is not None else None,
        "sha256": hashes,
    }


def run_validation(
    config: ValidationConfig, provenance: dict[str, object]
) -> dict[str, object]:
    """Compare actual reference scores and save enough evidence to audit a run.

    A zero-error exhaustive pass requires agreement for every hand, the exact
    physical-category census, all expected rank classes, and their total order.
    Random runs verify only the sampled hands and observed classes.
    """
    try:
        treys = importlib.import_module("treys")
    except ImportError as error:
        raise RuntimeError(
            "Install validation extras: uv sync --locked --extra validation"
        ) from error
    oracle = treys.Evaluator()
    reference_cards = [
        int(treys.Card.new(format_card(card))) for card in range(DECK_SIZE)
    ]
    agreement = RankAgreement()
    categories: Counter[HandCategory] = Counter()
    digest = hashlib.sha256()
    failures: list[dict[str, object]] = []
    checked = 0
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    for cards in iter_hands(config):
        own = evaluate_five(cards)
        reference = int(oracle.evaluate([], [reference_cards[card] for card in cards]))
        checked += 1
        digest.update(bytes(cards))
        categories[own.category] += 1
        try:
            agreement.observe(own, reference)
        except ValueError as error:
            failures.append(
                {
                    "cards": [format_card(card) for card in cards],
                    "own_rank": {
                        "category": own.category.name,
                        "tiebreakers": list(own.tiebreakers),
                    },
                    "reference_score": reference,
                    "reason": str(error),
                }
            )
            break
        if checked % 100_000 == 0:
            print(
                f"Checked {checked:,}/{config.hands:,} hands",
                file=sys.stderr,
                flush=True,
            )

    try:
        agreement.check_order()
    except ValueError as error:
        failures.append({"reason": str(error)})
    census_matches = (
        categories == expected_category_counts()
        if config.mode == "exhaustive"
        else None
    )
    classes_match = (
        len(agreement.own_to_reference) == expected_distinct_ranks()
        if config.mode == "exhaustive"
        else None
    )
    if census_matches is False:
        failures.append({"reason": "category census differs from combinatorial counts"})
    if classes_match is False:
        failures.append({"reason": "distinct rank-class count is wrong"})
    if checked != config.hands:
        failures.append({"reason": "run did not check the configured number of hands"})
    elapsed = time.perf_counter() - started
    return {
        "schema_version": 1,
        "status": "failed" if failures else "passed",
        "config": asdict(config),
        "started_at_utc": started_at,
        "validation_seconds": elapsed,
        "hands_checked": checked,
        "observed_rank_classes": len(agreement.own_to_reference),
        "expected_rank_classes": expected_distinct_ranks(),
        "exhaustive_census_matches": census_matches,
        "exhaustive_rank_classes_match": classes_match,
        "category_counts": {
            category.name: categories[category] for category in HandCategory
        },
        "expected_category_counts": {
            category.name: count
            for category, count in expected_category_counts().items()
        },
        "failures": failures,
        "input_sha256": digest.hexdigest(),
        "source": provenance,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "numpy": importlib.metadata.version("numpy"),
            "treys": importlib.metadata.version("treys"),
        },
        "reference": {
            "package": "treys",
            "license": "MIT",
            "lower_score_is_stronger": True,
        },
    }


def main() -> int:
    """CLI entry point; a failed validation writes evidence and exits nonzero."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    config = load_config(args.config)
    report = run_validation(config, source_provenance(root, args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(
        f"{report['status']}: {report['hands_checked']:,} hands; report: {args.output}"
    )
    return 0 if report["status"] == "passed" else 1
