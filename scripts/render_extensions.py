"""Render audited Bayesian/risk tables and scientific figures from retained JSON."""

import argparse
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.risk.bankroll import ReturnLaw, binary_law, finite_ruin
from poker_ai.validation.five_card import source_provenance


def update(path: Path, body: str) -> None:
    begin, end = "<!-- EXTENSIONS_BEGIN -->", "<!-- EXTENSIONS_END -->"
    text = path.read_text()
    block = begin + "\n" + body.strip() + "\n" + end
    if begin in text:
        first, rest = text.split(begin, 1)
        _, last = rest.split(end, 1)
        text = first + block + last
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text)


def csv_file(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def check_risk(report: dict[str, Any], opponents: dict[str, Any]) -> None:
    if (
        report["status"] != "completed"
        or report["own_profile_sha256"]
        != opponents["artifacts_sha256"]["own-risk-profiles.json.gz"]
    ):
        raise ValueError(
            "requires completed risk experiment from this own Bayesian run"
        )
    config = report["config"]
    expected = (
        len(config["binary_true_win_probabilities"]) * len(config["binary_persistence"])
        + 2 * len(config["toy_policies"]) * len(config["pot_rake_rates"])
    ) * len(config["kelly_multipliers"])
    if len(report["rows"]) != expected:
        raise ArithmeticError("missing risk cells")
    for row in report["rows"]:
        law = (
            binary_law(row["true_p"])
            if row["domain"] == "synthetic_binary"
            else ReturnLaw(
                np.array(row["law_outcomes"]), np.array(row["law_probabilities"])
            )
        )
        growth = law.log_growth(row["fraction"])
        if abs(growth - row["expected_log_growth_per_step"]) > 1e-13:
            raise ArithmeticError("risk analytic growth changed")
        simulation = row["simulation"]
        expected_log = config["horizon"] * growth
        if abs(simulation["mean_terminal_log_wealth"] - expected_log) > (
            config["horizon"]
            * float(np.ptp(np.log1p(row["fraction"] * law.outcomes)))
            * math.sqrt(
                math.log(2 * len(report["rows"]) / 0.001) / (2 * config["paths"])
            )
            + 1e-10
        ):
            raise ArithmeticError(
                "simulated mean growth disagrees with analytic marginal law"
            )
        for event in ("threshold_crossing", "drawdown_exceedance", "terminal_loss"):
            result = simulation[event]
            if (
                result["paths"] != config["paths"]
                or result["probability"] != result["count"] / result["paths"]
                or not 0 <= result["count"] <= result["paths"]
            ):
                raise ArithmeticError("risk event count/denominator inconsistent")
    ruin = config["ruin_control"]
    for row in report["ruin_controls"]:
        value = finite_ruin(ruin["start"], ruin["target"], row["p"], ruin["horizon"])
        if abs(value - row["exact_finite_horizon_ruin"]) > 1e-13:
            raise ArithmeticError("finite-horizon ruin control changed")


def render(directory: Path, root: Path) -> None:
    opponents = json.loads((directory / "opponents.json").read_text())
    risk = json.loads((directory / "bankroll.json").read_text())
    audit = json.loads((directory / "opponent-audit.json").read_text())
    if (
        audit["status"] != "passed"
        or audit["input_sha256"]
        != hashlib.sha256((directory / "opponents.json").read_bytes()).hexdigest()
    ):
        raise ValueError("requires current exact-metric/posterior audit")
    check_risk(risk, opponents)
    source = source_provenance(
        root,
        root / "configs/opponent-modeling.json",
        entrypoints=("scripts/render_extensions.py", "scripts/analyze_extensions.py"),
    )
    rows = opponents["rows"]
    flattened = []
    for r in rows:
        row = {
            k: r[k]
            for k in (
                "game",
                "seat",
                "scenario",
                "seed",
                "hands_observed",
                "predictive_nll_nats",
                "prior_nll_nats",
                "guarded_fraction",
                "certified_lower_bound",
            )
        }
        row.update(
            {
                f"posterior_{name}": p
                for name, p in zip(
                    opponents["config"]["hypotheses"], r["posterior"], strict=True
                )
            }
        )
        row.update(
            {
                f"{policy}_{metric}": value
                for policy, metrics in r["policies"].items()
                for metric, value in metrics.items()
            }
        )
        flattened.append(row)
    csv_file(directory / "opponent-checkpoints.csv", flattened)
    summaries = []
    for game in opponents["config"]["games"]:
        for scenario in opponents["config"]["scenarios"]:
            selected = [
                r
                for r in rows
                if r["game"] == game
                and r["scenario"] == scenario
                and r["hands_observed"] == opponents["config"]["checkpoints"][-1]
            ]
            summaries.append(
                {
                    "game": game,
                    "scenario": scenario,
                    "mean_predictive_nll_improvement_nats": float(
                        np.mean(
                            [
                                r["prior_nll_nats"] - r["predictive_nll_nats"]
                                for r in selected
                            ]
                        )
                    ),
                    "mean_guarded_ev_gain_chips": float(
                        np.mean(
                            [
                                r["policies"]["guarded"]["ev_ante_chips"]
                                - r["policies"]["blueprint"]["ev_ante_chips"]
                                for r in selected
                            ]
                        )
                    ),
                    "mean_unrestricted_ev_gain_chips": float(
                        np.mean(
                            [
                                r["policies"]["unrestricted"]["ev_ante_chips"]
                                - r["policies"]["blueprint"]["ev_ante_chips"]
                                for r in selected
                            ]
                        )
                    ),
                    "worst_guarded_security_degradation_chips": max(
                        r["policies"]["blueprint"]["security_ante_chips"]
                        - r["policies"]["guarded"]["security_ante_chips"]
                        for r in selected
                    ),
                }
            )
    csv_file(directory / "opponent-summary.csv", summaries)
    risk_flat = []
    for r in risk["rows"]:
        sim = r["simulation"]
        risk_flat.append(
            {
                "domain": r["domain"],
                "game": r.get("game"),
                "policy": r.get("policy"),
                "true_p": r.get("true_p"),
                "persistence": r["persistence"],
                "pot_rake_rate": r.get("pot_rake_rate"),
                "kelly_multiplier": r["kelly_multiplier"],
                "fraction": r["fraction"],
                "expected_log_growth_per_step": r["expected_log_growth_per_step"],
                "mean_terminal_log_wealth": sim["mean_terminal_log_wealth"],
                "se_terminal_log_wealth": sim["se_terminal_log_wealth"],
                **{
                    f"{event}_{key}": sim[event][key]
                    for event in (
                        "threshold_crossing",
                        "drawdown_exceedance",
                        "terminal_loss",
                    )
                    for key in ("count", "paths", "probability")
                },
            }
        )
    csv_file(directory / "bankroll-cells.csv", risk_flat)
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    matplotlib.rcParams.update({"font.size": 9, "svg.hashsalt": "poker-ai-extensions"})
    figures: list[Path] = []
    for game in opponents["config"]["games"]:
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), constrained_layout=True)
        for scenario in opponents["config"]["scenarios"]:
            points = []
            for cp in opponents["config"]["checkpoints"]:
                subset = [
                    r
                    for r in rows
                    if r["game"] == game
                    and r["scenario"] == scenario
                    and r["hands_observed"] == cp
                ]
                points.append(
                    [
                        np.mean(
                            [
                                r["prior_nll_nats"] - r["predictive_nll_nats"]
                                for r in subset
                            ]
                        ),
                        np.mean(
                            [
                                r["policies"]["guarded"]["ev_ante_chips"]
                                - r["policies"]["blueprint"]["ev_ante_chips"]
                                for r in subset
                            ]
                        ),
                        max(
                            r["policies"]["blueprint"]["security_ante_chips"]
                            - r["policies"]["guarded"]["security_ante_chips"]
                            for r in subset
                        ),
                    ]
                )
            for i, axis in enumerate(axes):
                axis.plot(
                    opponents["config"]["checkpoints"],
                    np.array(points)[:, i],
                    marker="o",
                    linestyle="--"
                    if scenario in ("misspecified", "switching")
                    else "-",
                    label=scenario,
                )
        for axis, title in zip(
            axes,
            (
                "Predictive NLL improvement (nats)",
                "Guarded EV gain (ante chips/hand)",
                "Worst security degradation (chips)",
            ),
            strict=True,
        ):
            axis.set_title(title)
            axis.set_xlabel("Censored hands observed")
            axis.grid(alpha=0.2)
            axis.axhline(0, color="black", linewidth=0.6)
        axes[2].axhline(
            opponents["config"]["security_degradation_budget_ante_chips"],
            color="red",
            linestyle=":",
            label="budget",
        )
        axes[2].legend(fontsize=7)
        fig.suptitle(
            f"{game.title()}: exact metrics, fixed own opponents; means over 2 seats "
            f"× 3 histories"
        )
        for suffix in ("png", "svg"):
            path = directory / f"bayesian-{game}.{suffix}"
            fig.savefig(
                path, dpi=160, metadata={"Date": None} if suffix == "svg" else {}
            )
            figures.append(path)
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for p in risk["config"]["binary_true_win_probabilities"]:
        subset = [
            r
            for r in risk["rows"]
            if r["domain"] == "synthetic_binary"
            and r["true_p"] == p
            and r["persistence"] == 0
        ]
        axes[0, 0].plot(
            [r["kelly_multiplier"] for r in subset],
            [r["expected_log_growth_per_step"] for r in subset],
            marker="o",
            label=f"true p={p:g}",
        )
    for rho in risk["config"]["binary_persistence"]:
        subset = [
            r
            for r in risk["rows"]
            if r["domain"] == "synthetic_binary"
            and r["true_p"] == risk["config"]["binary_estimated_win_probability"]
            and r["persistence"] == rho
        ]
        for axis, event in (
            (axes[0, 1], "threshold_crossing"),
            (axes[1, 0], "drawdown_exceedance"),
        ):
            probs = [r["simulation"][event]["probability"] for r in subset]
            intervals = [r["simulation"][event]["wilson_95"] for r in subset]
            axis.errorbar(
                [r["kelly_multiplier"] for r in subset],
                probs,
                yerr=np.array(
                    [
                        [p - ci[0], ci[1] - p]
                        for p, ci in zip(probs, intervals, strict=True)
                    ]
                ).T,
                marker="o",
                label=f"persistence={rho:g}",
            )
    for game in ("kuhn", "leduc"):
        for policy in risk["config"]["toy_policies"]:
            subset = [
                r
                for r in risk["rows"]
                if r["domain"] == "own_toy"
                and r["game"] == game
                and r["policy"] == policy
                and r["kelly_multiplier"] == 1
            ]
            axes[1, 1].plot(
                [r["pot_rake_rate"] for r in subset],
                [r["conditional_optimal_fraction"] for r in subset],
                marker="o",
                label=f"{game}/{policy}",
            )
    for axis, title in zip(
        axes.flat,
        (
            "Assumed p=.55 sizing: exact log growth",
            "P(wealth crosses 20% of initial)",
            "P(maximum drawdown ≥50%)",
            "Own toy conditional optimum vs pot rake",
        ),
        strict=True,
    ):
        axis.set_title(title)
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7)
        axis.set_xlabel(
            "Multiplier of assumed binary Kelly"
            if axis is not axes[1, 1]
            else "Toy pot-rake fraction"
        )
    axes[0, 0].axhline(0, color="black", linewidth=0.6)
    fig.suptitle(
        f"Conditional models only: {risk['config']['paths']:,} independent paths/cell "
        f"× {risk['config']['horizon']:,} steps; Wilson 95% event intervals"
    )
    for suffix in ("png", "svg"):
        path = directory / f"bankroll-risk.{suffix}"
        fig.savefig(path, dpi=160, metadata={"Date": None} if suffix == "svg" else {})
        figures.append(path)
    plt.close(fig)
    table = (
        "| Game | Opponent scenario | NLL improvement (nats) | "
        "Guarded EV gain | Unrestricted EV gain |\n"
        "| --- | --- | ---: | ---: | ---: |\n"
    )
    for r in summaries:
        table += (
            f"| {r['game']} | {r['scenario']} | "
            f"{r['mean_predictive_nll_improvement_nats']:+.4f} | "
            f"{r['mean_guarded_ev_gain_chips']:+.4f} | "
            f"{r['mean_unrestricted_ev_gain_chips']:+.4f} |\n"
        )
    binary_primary = [
        r
        for r in risk["rows"]
        if r["domain"] == "synthetic_binary"
        and r["true_p"] == risk["config"]["binary_estimated_win_probability"]
        and r["kelly_multiplier"] == 1
    ]
    dependence = "; ".join(
        f"persistence {r['persistence']:g}: threshold crossing "
        f"{r['simulation']['threshold_crossing']['probability']:.1%}"
        for r in binary_primary
    )
    body = (
        "### Selected quantitative extensions\n\n"
        f"Own finite-type Bayesian models: **{audit['observed_hands']:,} censored toy "
        f"hands**, "
        f"**{audit['checkpoint_rows']} exact checkpoint profiles**. Each table cell "
        f"is the "
        "final-checkpoint mean over both seats and three training histories. Positive "
        "NLL "
        "improvement means better held-out public-transcript prediction under a fixed "
        "blueprint logging policy. EV gains are exact **ante chips/hand versus the "
        "same "
        "own scripted opponent**, relative to the own CFR+ blueprint. "
        "Those gains include exploitation already available from the prior; "
        "they do not isolate the benefit of learning.\n\n" + table + "\n"
        "The model improves predictions on included stationary types but can worsen "
        "them "
        "under misspecification or drift. A root-level exploitation mixture is "
        "certified "
        f"to lose at most "
        f"**{opponents['config']['security_degradation_budget_ante_chips']:g} "
        "chip/hand** of blueprint worst-case security in these exact games. "
        "This permits "
        "some degradation; it is not a Hold'em guarantee or a game-value safety "
        "claim.\n\n"
        "![Bayesian learning and security](results/extensions/bayesian-leduc.png)\n\n"
        f"Conditional bankroll study: **{len(risk['rows'])} cells**, "
        f"{risk['config']['paths']:,} independent paths per cell, "
        f"{risk['config']['horizon']:,} steps/path. In the synthetic binary p=.55 "
        f"model "
        "with sizing chosen at that assumed edge, " + dependence + ". "
        f"The specified uncertainty set gives a robust fraction of "
        f"**{risk['robust_binary_fraction']:g}**. "
        "All fixed-stake Monte Carlo controls match finite-horizon exact ruin "
        "probabilities "
        "within the predeclared reported tolerance. Fractional threshold crossing is "
        "not "
        "literal bankruptcy. Return laws, fees, stationarity and stake scaling are "
        "model "
        "assumptions; no positive real-world edge or bankroll recommendation "
        "follows.\n\n"
        "![Conditional bankroll sensitivity](results/extensions/bankroll-risk.png)\n\n"
        "`make analyze-extensions` reproduces both studies, posterior audit, tables "
        "and "
        "figures offline. No external solver or public benchmark outputs enter "
        "learning. "
        "See [methods, limitations and interview answers](docs/phase5-extensions.md)."
    )
    (directory / "summary-body.md").write_text(body + "\n")
    (directory / "verified-claims.md").write_text(
        "# Verified extension claim drafts\n\n"
        f"- Implemented hidden-card-marginalized Bayesian opponent learning and "
        f"audited "
        f"{audit['observed_hands']:,} own simulated Kuhn/Leduc observations across "
        f"{audit['checkpoint_rows']} exact response profiles, with a declared "
        "0.1-chip blueprint-security degradation budget. This is a finite-type "
        "toy-game "
        "result; misspecification and switching failures are retained.\n"
        f"- Built conditional bankroll simulations over {len(risk['rows'])} fixed "
        "return/sizing/dependence/fee cells, with analytic Kelly controls, exact "
        "finite-"
        "horizon ruin checks and path-level event intervals. No empirical real-world "
        "poker edge or financial recommendation is claimed.\n"
    )
    artifacts = [
        directory / name
        for name in (
            "opponent-checkpoints.csv",
            "opponent-summary.csv",
            "bankroll-cells.csv",
            "summary-body.md",
            "verified-claims.md",
        )
    ] + figures
    (directory / "render-manifest.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "source": source,
                "inputs_sha256": {
                    n: hashlib.sha256((directory / n).read_bytes()).hexdigest()
                    for n in ("opponents.json", "bankroll.json", "opponent-audit.json")
                },
                "artifacts_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in artifacts
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print("passed: posterior/risk controls, all tables and figures rendered")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("results/extensions"))
    parser.add_argument("--update-docs-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.update_docs_only:
        body = (args.directory / "summary-body.md").read_text()
        update(root / "README.md", body)
        update(
            root / "docs/phase5-extensions.md",
            body.replace("(results/", "(../results/").replace(
                "(docs/phase5-extensions.md)", "(phase5-extensions.md)"
            ),
        )
    else:
        render(args.directory, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
