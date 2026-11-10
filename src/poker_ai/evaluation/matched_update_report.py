"""Complete paired tables and a static known-game diagnostic; no policy selection."""

import csv
import html
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.river_study import digest


def write_report(saved: dict[str, Any], folder: Path) -> dict[str, str]:
    if folder.exists():
        raise FileExistsError("retain complete/partial matched-update report")
    folder.mkdir(parents=True)
    profiles = {r["id"]: r for r in saved["rows"]}
    rows = []
    for pair in saved["self_pairs"]:
        profile = profiles[pair["planned_prefix_id"]]
        rows.append(
            dict(
                target_id=pair["target_id"],
                readout=pair["readout"],
                **{
                    k: profile["case"][k]
                    for k in ("spot_file", "representation", "regret_rule", "seed")
                },
                target_iteration=pair["target_iteration"],
                prefix_total_work=pair["prefix_total_work"],
                batched_total_work=pair["batched_total_work"],
                **pair["difference_prefix_minus_batched_chips"],
            )
        )
    for name, values in (("self-pairs", rows), ("fixed-pairs", saved["fixed_pairs"])):
        with (folder / (name + ".csv")).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)
    summary = dict(
        scope=saved["scope"],
        status="own_only_native_pending",
        profiles=144,
        fixed_targets=1152,
        self_pairs=144,
        fixed_pairs=1152,
        all_seeds_and_readouts_retained=True,
        uncertainty=(
            "three seeds; dependent readouts/shared games; no population interval"
        ),
        interpretation=(
            "prefix minus batched chips; negative exploitability "
            "difference favors B1 prefix; equal updates spends "
            "different work"
        ),
        new_agent_default=False,
        fresh_global_admission=False,
    )
    (folder / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    # One point per declared pair. This shows every seed/readout, rather than
    # hiding unfavorable cases behind a selected primary mean.
    width, height = 900, 470
    differences = [float(r["exact_exploitability_chips"]) for r in rows]
    extent = max([abs(x) for x in differences] + [1e-12])
    ratios = [float(r["prefix_total_work"]) / r["batched_total_work"] for r in rows]
    xmin, xmax = min(ratios), max(ratios)
    span = max(xmax - xmin, 1e-12)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" font-size="13" fill="#222">',
        '<text x="60" y="26">Known-game matched updates: '
        "all144 dependent seed/readout pairs; own audit only</text>",
        '<line x1="70" x2="850" y1="220" y2="220" stroke="#999"/>',
        '<line x1="70" x2="70" y1="65" y2="375" stroke="#222"/>',
        '<text x="60" y="410">B1-prefix node visits / batched node visits '
        "(same completed updates)</text>",
        '<text x="60" y="442">Vertical: B1-prefix minus batched exact exploitability '
        "(chips); below zero favors prefix</text>",
        f'<text x="10" y="70">+{extent:.4g}</text>',
        '<text x="10" y="225">0</text>',
        f'<text x="10" y="375">-{extent:.4g}</text>',
    ]
    for row, ratio, value in zip(rows, ratios, differences, strict=True):
        x = 75 + 765 * (ratio - xmin) / span
        y = 220 - 150 * value / extent
        title = html.escape(json.dumps(row, sort_keys=True))
        color = "#2166ac" if "-B4" in row["target_id"] else "#b35806"
        svg.append(
            f'<circle cx="{x:.4f}" cy="{y:.4f}" r="3" fill="{color}" '
            f'opacity="0.6"><title>{title}</title></circle>'
        )
    svg += [
        f'<text x="70" y="395">{xmin:.4g}</text>',
        f'<text x="805" y="395">{xmax:.4g}</text>',
        '<text x="610" y="52" fill="#2166ac">blue B4 target</text>',
        '<text x="740" y="52" fill="#b35806">brown B16 target</text>',
        "</g></svg>",
    ]
    (folder / "all-pairs.svg").write_text("\n".join(svg) + "\n")
    return {p.name: digest(p) for p in sorted(folder.iterdir())}
