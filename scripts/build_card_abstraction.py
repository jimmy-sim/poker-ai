"""Fit own equity/potential card buckets and reproduce empirical loss plots."""

import argparse
import csv
import hashlib
import importlib
import json
import os
import platform
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.clustering import earth_mover
from poker_ai.abstraction.model import CardAbstraction, Kind, Quantizer, fit_quantizer
from poker_ai.abstraction.potential import (
    FeatureConfig,
    Potential,
    canonical_cards,
    deterministic_potential,
)
from poker_ai.cards import Deck
from poker_ai.validation.five_card import source_provenance

KINDS: tuple[Kind, ...] = ("strength", "distribution", "potential")


def plot(
    rows: list[dict[str, Any]], noise: dict[str, dict[str, float]], output: Path
) -> list[Path]:
    os.environ.setdefault("MPLCONFIGDIR", str(output.parent / "runs" / "mpl-cache"))
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "poker-ai-card-abstraction"
    pyplot = importlib.import_module("matplotlib.pyplot")
    fig, axes = pyplot.subplots(2, 2, figsize=(10, 7), layout="constrained")
    for axis, length, name in zip(
        axes.flat, (0, 3, 4, 5), ("Preflop", "Flop", "Turn", "River"), strict=True
    ):
        for kind in KINDS:
            selected = [
                r for r in rows if r["board_length"] == length and r["kind"] == kind
            ]
            axis.plot(
                [r["buckets"] for r in selected],
                [r["histogram_w1"] for r in selected],
                marker="o",
                label=kind,
            )
        axis.axhline(
            noise[str(length)]["histogram_w1"],
            color="gray",
            linestyle="--",
            label="Input MC discrepancy",
        )
        axis.set(
            title=name,
            xlabel="Requested buckets",
            ylabel="Mean grid-W1 reconstruction error",
        )
        axis.set_xticks(sorted({r["buckets"] for r in rows}))
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7)
    paths = [
        output.with_name("card-abstraction-loss.png"),
        output.with_name("card-abstraction-loss.svg"),
    ]
    fig.savefig(paths[0], dpi=160)
    fig.savefig(paths[1], metadata={"Date": None})
    pyplot.close(fig)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    fields = {
        "train_states_per_street",
        "test_states_per_street",
        "buckets",
        "kinds",
        "dataset_seed",
        "clustering_seed",
        "features",
        "reference_features",
        "sampling",
        "limitations",
    }
    if set(config) != fields or config["kinds"] != list(KINDS):
        raise ValueError("invalid card abstraction config")
    for key in (
        "train_states_per_street",
        "test_states_per_street",
        "dataset_seed",
        "clustering_seed",
    ):
        if type(config[key]) is not int or config[key] < (
            0 if key.endswith("seed") else 1
        ):
            raise ValueError("invalid state budget or seed")
    train_count, test_count = (
        config["train_states_per_street"],
        config["test_states_per_street"],
    )
    if train_count + test_count > 169:
        raise ValueError("disjoint canonical preflop states cannot exceed 169")
    if (
        not config["buckets"]
        or any(
            type(b) is not int or not 1 <= b <= train_count for b in config["buckets"]
        )
        or config["buckets"] != sorted(set(config["buckets"]))
    ):
        raise ValueError("invalid bucket list")
    feature_config = FeatureConfig(**config["features"])
    reference_config = FeatureConfig(**config["reference_features"])
    if (
        feature_config.bins != reference_config.bins
        or feature_config.seed == reference_config.seed
    ):
        raise ValueError("reference features need matched grids and independent seed")
    root = Path(__file__).resolve().parents[1]
    source = source_provenance(
        root, args.config, entrypoints=("scripts/build_card_abstraction.py",)
    )
    started = time.perf_counter()
    rng = Generator(PCG64(config["dataset_seed"]))
    datasets: dict[int, dict[str, list[Potential]]] = {}
    dataset_rows = []
    noise: dict[str, dict[str, float]] = {}
    for length in (0, 3, 4, 5):
        positions: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
        seen = set()
        while len(positions) < train_count + test_count:
            deck = Deck.shuffled(rng)
            canonical = canonical_cards(deck.cards[:2], deck.cards[2 : 2 + length])
            if canonical not in seen:
                seen.add(canonical)
                positions.append(canonical)
        train, test, reference = [], [], []
        for index, (hole, board) in enumerate(positions):
            feature = deterministic_potential(hole, board, feature_config)
            higher = None
            if index < train_count:
                train.append(feature)
            else:
                test.append(feature)
                higher = deterministic_potential(hole, board, reference_config)
                reference.append(higher)
            dataset_rows.append(
                {
                    "board_length": length,
                    "split": "train" if index < train_count else "test",
                    "hole": hole,
                    "board": board,
                    "equity": feature.equity,
                    "board_lengths": feature.board_lengths,
                    "histograms": feature.histograms.tolist(),
                    "reference_equity": None if higher is None else higher.equity,
                    "reference_histograms": None
                    if higher is None
                    else higher.histograms.tolist(),
                }
            )
        datasets[length] = {"train": train, "test": test, "reference": reference}
        noise[str(length)] = {
            "equity_mse": float(
                np.mean(
                    [
                        (a.equity - b.equity) ** 2
                        for a, b in zip(test, reference, strict=True)
                    ]
                )
            ),
            "histogram_w1": float(
                np.mean(
                    [
                        earth_mover(a.histograms, b.histograms).mean()
                        for a, b in zip(test, reference, strict=True)
                    ]
                )
            ),
        }
        print(
            f"board length {length}: {train_count} train / {test_count} test; "
            "features complete",
            flush=True,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset_path = args.output.with_name("card-abstraction-dataset.json")
    dataset_path.write_text(
        json.dumps(
            {"config": config, "source": source, "positions": dataset_rows},
            sort_keys=True,
        )
        + "\n"
    )
    rows: list[dict[str, Any]] = []
    models: dict[tuple[Kind, int], dict[int, Quantizer]] = {}
    for kind_index, kind in enumerate(KINDS):
        for count in config["buckets"]:
            street_models = {}
            for length, data in datasets.items():
                fit_seed = (
                    config["clustering_seed"]
                    + 10000 * kind_index
                    + 100 * count
                    + length
                )
                quantizer = fit_quantizer(
                    data["train"],
                    kind=kind,
                    buckets=count,
                    rng=Generator(PCG64(fit_seed)),
                )
                street_models[length] = quantizer
                predictions = [quantizer.assign(f) for f in data["test"]]
                mse = float(
                    np.mean(
                        [
                            (quantizer.equities[label] - actual.equity) ** 2
                            for label, actual in zip(
                                predictions, data["reference"], strict=True
                            )
                        ]
                    )
                )
                w1 = float(
                    np.mean(
                        [
                            earth_mover(
                                quantizer.reconstruction[label], actual.histograms
                            ).mean()
                            for label, actual in zip(
                                predictions, data["reference"], strict=True
                            )
                        ]
                    )
                )
                rows.append(
                    {
                        "kind": kind,
                        "board_length": length,
                        "buckets": count,
                        "occupied_training_buckets": quantizer.occupied,
                        "fit_iterations": quantizer.iterations,
                        "fit_seed": fit_seed,
                        "equity_mse": mse,
                        "histogram_w1": w1,
                        "input_mc_equity_mse": noise[str(length)]["equity_mse"],
                        "input_mc_histogram_w1": noise[str(length)]["histogram_w1"],
                    }
                )
            models[kind, count] = street_models
    artifacts = [dataset_path]
    for (kind, count), street_models in models.items():
        path = args.output.parent / "card-models" / f"{kind}-{count}.json"
        CardAbstraction(street_models, feature_config).save(path, provenance=source)
        artifacts.append(path)
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    artifacts += [csv_path] + plot(rows, noise, args.output)
    report = {
        "schema_version": 1,
        "status": "passed",
        "config": config,
        "source": source,
        "rows": rows,
        "input_mc_discrepancy": noise,
        "features": asdict(feature_config),
        "reference_features": asdict(reference_config),
        "seconds": time.perf_counter() - started,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "artifacts_sha256": {
            str(p.relative_to(args.output.parent)): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in artifacts
        },
        "interpretation": (
            "empirical noisy feature reconstruction; "
            "no equilibrium or win-rate certificate"
        ),
    }
    if any(
        not np.isfinite(r["equity_mse"]) or not np.isfinite(r["histogram_w1"])
        for r in rows
    ):
        report["status"] = "failed"
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], args.output)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
