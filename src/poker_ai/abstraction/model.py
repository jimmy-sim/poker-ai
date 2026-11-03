"""Own card quantizers and public-observation keys with abstract perfect recall."""

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from numpy.random import Generator

from poker_ai.abstraction.clustering import (
    Metric,
    distances,
    fit_clusters,
    validate_histograms,
)
from poker_ai.abstraction.potential import (
    FeatureConfig,
    Potential,
    canonical_cards,
    deterministic_potential,
)
from poker_ai.engine import Observation
from poker_ai.toy.tree import FloatArray

Kind = Literal["strength", "distribution", "potential"]
FORMAT = "poker-ai-own-card-abstraction-v1"


@dataclass(frozen=True)
class Quantizer:
    kind: Kind
    centers: FloatArray
    reconstruction: FloatArray
    equities: FloatArray
    occupied: int
    iterations: int

    def assign(self, feature: Potential) -> int:
        if self.kind == "strength":
            return min(len(self.centers) - 1, int(feature.equity * len(self.centers)))
        values = (
            feature.histograms[-1:]
            if self.kind == "distribution"
            else feature.histograms
        )
        metric: Metric = "euclidean" if self.kind == "distribution" else "earth_mover"
        return int(distances(values[None, :], self.centers, metric).argmin(axis=1)[0])


def fit_quantizer(
    features: Sequence[Potential], *, kind: Kind, buckets: int, rng: Generator
) -> Quantizer:
    if not features or kind not in ("strength", "distribution", "potential"):
        raise ValueError("need features and a known card quantizer")
    full = np.stack([f.histograms for f in features])
    validate_histograms(full)
    if any(f.board_lengths != features[0].board_lengths for f in features):
        raise ValueError("fit each board length separately")
    if type(buckets) is not int or not 1 <= buckets <= len(features):
        raise ValueError("invalid card bucket count")
    equities = np.array([f.equity for f in features])
    if (
        not np.all(np.isfinite(equities))
        or np.any(equities < 0)
        or np.any(equities > 1)
    ):
        raise ValueError("invalid equity feature")
    if kind == "strength":
        labels = np.minimum(buckets - 1, (equities * buckets).astype(np.int64))
        centers = np.zeros((buckets, 1, full.shape[-1]))
        representative_equity = (np.arange(buckets) + 0.5) / buckets
        iterations = 0
    else:
        selected = full[:, -1:] if kind == "distribution" else full
        model = fit_clusters(
            selected,
            equities,
            clusters=buckets,
            metric="euclidean" if kind == "distribution" else "earth_mover",
            rng=rng,
        )
        centers, representative_equity = model.centers, model.equity_centers.copy()
        labels, iterations = model.assign(selected), model.iterations
    reconstruction = np.zeros((buckets,) + full.shape[1:])
    for bucket in range(buckets):
        members = labels == bucket
        if np.any(members):
            representative_equity[bucket] = equities[members].mean()
            reconstruction[bucket] = (
                centers[bucket] if kind == "potential" else full[members].mean(axis=0)
            )
        else:
            fallback = int(np.abs(equities - representative_equity[bucket]).argmin())
            reconstruction[bucket] = full[fallback]
        if kind == "strength":
            centers[bucket] = reconstruction[bucket, :1]
    return Quantizer(
        kind,
        centers,
        reconstruction,
        representative_equity,
        len(set(labels.tolist())),
        iterations,
    )


class CardAbstraction:
    """Deterministic observed-card mapping; cache size is bounded and explicit.

    Keys preserve the entire sequence of own abstract buckets and own/public
    actions. Exact public boards and private cards are projected into buckets;
    their loss is part of this abstraction, not hidden from the error report.
    Opponent private cards and dealer future cards are never accepted inputs.
    """

    def __init__(
        self,
        models: dict[int, Quantizer],
        config: FeatureConfig,
        *,
        cache_size: int = 8192,
    ) -> None:
        if set(models) != {0, 3, 4, 5} or type(cache_size) is not int or cache_size < 1:
            raise ValueError("need a model per street and a positive cache size")
        if len({model.kind for model in models.values()}) != 1:
            raise ValueError("all streets need the same quantizer kind")
        for length, model in models.items():
            expected = 1 + sum(t > length for t in (3, 4, 5))
            if (
                model.reconstruction.shape
                != (len(model.centers), expected, config.bins)
                or model.equities.shape != (len(model.centers),)
                or np.any(model.equities < 0)
                or np.any(model.equities > 1)
                or not np.all(np.isfinite(model.equities))
            ):
                raise ValueError("invalid street model shape/equity")
            expected_center_blocks = expected if model.kind == "potential" else 1
            if model.centers.shape[1:] != (expected_center_blocks, config.bins):
                raise ValueError("invalid card cluster center shape")
            validate_histograms(model.centers)
            validate_histograms(model.reconstruction)
        self.models = models
        self.config = config
        self.cached_bucket = lru_cache(maxsize=cache_size)(self._bucket)

    def _bucket(self, hole: tuple[int, ...], board: tuple[int, ...]) -> int:
        feature = deterministic_potential(hole, board, self.config)
        return self.models[len(board)].assign(feature)

    def bucket(self, hole: tuple[int, ...], board: tuple[int, ...]) -> int:
        canonical_hole, canonical_board = canonical_cards(hole, board)
        return self.cached_bucket(canonical_hole, canonical_board)

    def information(self, observation: Observation) -> str:
        buckets = [
            self.bucket(observation.hole_cards, observation.board[:length])
            for length in (0, 3, 4, 5)
            if length <= len(observation.board)
        ]
        return json.dumps(
            {
                "seat": observation.seat,
                "button": observation.button,
                "street": int(observation.street),
                "buckets": buckets,
                "stacks": observation.stacks,
                "paid": observation.total_commitments,
                "history": [
                    (r.seat, int(r.street), r.action.kind.value, r.action.amount)
                    for r in observation.history
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def save(self, path: Path, *, provenance: dict[str, Any]) -> None:
        payload = {
            "format": FORMAT,
            "features": asdict(self.config),
            "source": provenance,
            "models": {
                str(length): {
                    "kind": model.kind,
                    "centers": model.centers.tolist(),
                    "reconstruction": model.reconstruction.tolist(),
                    "equities": model.equities.tolist(),
                    "occupied": model.occupied,
                    "iterations": model.iterations,
                }
                for length, model in self.models.items()
            },
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")

    @classmethod
    def load(cls, path: Path, *, cache_size: int = 8192) -> "CardAbstraction":
        payload = json.loads(path.read_text())
        if (
            not isinstance(payload, dict)
            or set(payload) != {"format", "features", "source", "models"}
            or payload["format"] != FORMAT
        ):
            raise ValueError("invalid own card-abstraction artifact")
        config = FeatureConfig(**payload["features"])
        models = {}
        for length, row in payload["models"].items():
            if set(row) != {
                "kind",
                "centers",
                "reconstruction",
                "equities",
                "occupied",
                "iterations",
            } or row["kind"] not in ("strength", "distribution", "potential"):
                raise ValueError("invalid card-abstraction model")
            models[int(length)] = Quantizer(
                cast(Kind, row["kind"]),
                np.asarray(row["centers"], dtype=np.float64),
                np.asarray(row["reconstruction"], dtype=np.float64),
                np.asarray(row["equities"], dtype=np.float64),
                row["occupied"],
                row["iterations"],
            )
        return cls(models, config, cache_size=cache_size)
