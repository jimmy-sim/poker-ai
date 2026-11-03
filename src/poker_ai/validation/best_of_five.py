"""Seeded six/seven-card comparisons using a calibrated five-card reference map.

Reference scores and the calibration map exist only in this validation module;
the production evaluator never imports them.
"""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import combinations_with_replacement
from pathlib import Path
from typing import Literal

from numpy.random import PCG64, Generator

from poker_ai.cards import DECK_SIZE, format_card, make_card
from poker_ai.evaluator import HandCategory, HandRank, evaluate_best, evaluate_five
from poker_ai.validation.five_card import (
    RankAgreement,
    expected_distinct_ranks,
    source_provenance,
)

ReferenceScore = Callable[[tuple[int, ...]], int]


def representative_hands() -> Iterable[tuple[int, ...]]:
    """Generate one physical representative of every five-card rank class.

    Iterate rank multisets, excluding impossible five-of-a-kind. A repeated rank
    uses distinct suits. A five-distinct-rank multiset needs both a nonflush
    representative (cyclic suits) and a flush representative (all clubs).
    """
    for ranks in combinations_with_replacement(range(2, 15), 5):
        counts = Counter(ranks)
        if max(counts.values()) > 4:
            continue
        if len(counts) == 5:
            yield tuple(make_card(rank, index % 4) for index, rank in enumerate(ranks))
            yield tuple(make_card(rank, 0) for rank in ranks)
        else:
            cards: list[int] = []
            for rank, count in counts.items():
                cards.extend(make_card(rank, suit) for suit in range(count))
            yield tuple(cards)


def calibrate_reference(reference_score: ReferenceScore) -> dict[int, HandRank]:
    """Map all Treys scores to already-validated five-card comparison keys.

    Checking every class and its order calibrates the score conventions. A sampled
    six/seven-card result can then be compared for exact category and tie-breaker
    equality, rather than only relative ordering among the sampled hands.
    """
    agreement = RankAgreement()
    for cards in representative_hands():
        agreement.observe(evaluate_five(cards), reference_score(cards))
    agreement.check_order()
    if len(agreement.own_to_reference) != expected_distinct_ranks() or set(
        agreement.reference_to_own
    ) != set(range(1, expected_distinct_ranks() + 1)):
        raise ValueError("reference calibration does not cover all five-card ranks")
    return agreement.reference_to_own


@dataclass(frozen=True)
class SampleConfig:
    """A uniform random hand sample with an explicit independently owned RNG."""

    hand_size: int
    hands: int
    seed: int

    def __post_init__(self) -> None:
        if type(self.hand_size) is not int or self.hand_size not in (6, 7):
            raise ValueError("hand_size must be 6 or 7")
        if type(self.hands) is not int or self.hands < 1:
            raise ValueError("hands must be a positive integer")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")


def load_configs(path: Path) -> tuple[SampleConfig, ...]:
    """Load versioned runs, rejecting unknown keys and repeated hand sizes."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or set(data) != {"runs"}:
        raise ValueError("config must contain exactly runs")
    runs = data["runs"]
    if not isinstance(runs, list) or not runs:
        raise ValueError("runs must be a nonempty list")
    configs = []
    for run in runs:
        if not isinstance(run, dict) or set(run) != {"hand_size", "hands", "seed"}:
            raise ValueError("each run must contain exactly hand_size, hands, and seed")
        configs.append(SampleConfig(run["hand_size"], run["hands"], run["seed"]))
    if len({config.hand_size for config in configs}) != len(configs):
        raise ValueError("hand sizes must not repeat")
    return tuple(configs)


def iter_samples(config: SampleConfig) -> Iterable[tuple[int, ...]]:
    """Sample without replacement within a hand, independently between hands."""
    rng = Generator(PCG64(config.seed))
    for _ in range(config.hands):
        yield tuple(
            int(card) for card in rng.choice(DECK_SIZE, config.hand_size, replace=False)
        )


@dataclass(frozen=True)
class SampleResult:
    """Raw comparison evidence for one configured hand size."""

    config: SampleConfig
    status: Literal["passed", "failed"]
    hands_checked: int
    observed_rank_classes: int
    category_counts: dict[str, int]
    failures: list[dict[str, object]]
    input_sha256: str
    validation_seconds: float


def compare_samples(
    config: SampleConfig,
    reference_score: ReferenceScore,
    reference_ranks: dict[int, HandRank],
) -> SampleResult:
    """Compare exact ranks; keep a concrete first failure and stop on mismatch."""
    categories: Counter[HandCategory] = Counter()
    observed = set()
    digest = hashlib.sha256()
    failures: list[dict[str, object]] = []
    checked = 0
    started = time.perf_counter()
    for cards in iter_samples(config):
        own = evaluate_best(cards)
        score = reference_score(cards)
        expected = reference_ranks.get(score)
        checked += 1
        digest.update(bytes(cards))
        observed.add(own)
        categories[own.category] += 1
        if own != expected:
            failures.append(
                {
                    "cards": [format_card(card) for card in cards],
                    "actual": {
                        "category": own.category.name,
                        "tiebreakers": own.tiebreakers,
                    },
                    "expected": None
                    if expected is None
                    else {
                        "category": expected.category.name,
                        "tiebreakers": expected.tiebreakers,
                    },
                    "reference_score": score,
                    "reason": "best-five rank differs from calibrated reference",
                }
            )
            break
        if checked % 100_000 == 0:
            print(
                f"{config.hand_size}-card: checked {checked:,}/{config.hands:,}",
                file=sys.stderr,
                flush=True,
            )
    return SampleResult(
        config=config,
        status="passed" if not failures and checked == config.hands else "failed",
        hands_checked=checked,
        observed_rank_classes=len(observed),
        category_counts={
            category.name: categories[category] for category in HandCategory
        },
        failures=failures,
        input_sha256=digest.hexdigest(),
        validation_seconds=time.perf_counter() - started,
    )


def run_validation(
    configs: tuple[SampleConfig, ...], provenance: dict[str, object]
) -> dict[str, object]:
    """Use optional Treys for comparisons only and record full run provenance."""
    if not configs:
        raise ValueError("at least one sample run is required")
    try:
        treys = importlib.import_module("treys")
    except ImportError as error:
        raise RuntimeError(
            "Install validation extras: uv sync --locked --extra validation"
        ) from error
    oracle = treys.Evaluator()
    encoded = [int(treys.Card.new(format_card(card))) for card in range(DECK_SIZE)]

    def reference_score(cards: tuple[int, ...]) -> int:
        return int(oracle.evaluate([], [encoded[card] for card in cards]))

    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    calibration = calibrate_reference(reference_score)
    results = []
    for config in configs:
        result = compare_samples(config, reference_score, calibration)
        results.append(result)
        if result.status == "failed":
            break
    return {
        "schema_version": 1,
        "status": "passed"
        if all(result.status == "passed" for result in results)
        else "failed",
        "started_at_utc": started_at,
        "validation_seconds": time.perf_counter() - started,
        "calibration_rank_classes": len(calibration),
        "planned_runs": [asdict(config) for config in configs],
        "total_hands_checked": sum(result.hands_checked for result in results),
        "runs": [asdict(result) for result in results],
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
    """Write an auditable report atomically; failed comparisons exit nonzero."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    configs = load_configs(args.config)
    provenance = source_provenance(
        root, args.config, entrypoints=("scripts/validate_best.py",)
    )
    report = run_validation(configs, provenance)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(
        f"{report['status']}: {report['total_hands_checked']:,} sampled hands; "
        f"report: {args.output}"
    )
    return 0 if report["status"] == "passed" else 1
