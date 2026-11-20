# Batch-one signed updates on two known river spots: negative result

**Issue #4, PR #101, November 20, 2026 (PST).** This result follows the
[prospective protocol](medium-dry-b1-updates.md) published at `9c8f613`.
The question was whether one signed external-sampling update per sample
(B1) improves the unchanged `q8_turn_exact_river` learner over its published
batch-four (B4) signed control at matched 10m charged node work. Both spots
and all seeds were previously used; this is a comparison on **known** cases.
The complete machine-readable [report and 108 rows](../results/medium-dry-b1-updates/report/manifest.json)
bind the saved policies, scores, independent audits and fixed decision traces.

## Fixed final comparison

Exploitability is restricted-game NashConv/2 divided by the initial pot;
lower is better. Each row uses the preselected 10m **linear-average** policy.
The B4 control is the immutable PR #100 signed path for the same game and
seed, reused without retraining. B1 and B4 consumed different random draws
under a shared seed label, so the pair is a fixed comparison, not a
common-random-number estimate or a population confidence interval.

| Known spot | Seed | B4 | B1 | B1−B4 | Final work B4 / B1 | Path seconds B4 / B1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low/wet IP | 20261371 | 0.000945518 | 0.000966471 | +0.000020953 | 10,000,055 / 10,000,015 | 66.007 / 65.523 |
| Low/wet IP | 20261372 | 0.000909274 | 0.001040217 | +0.000130943 | 10,000,058 / 10,000,012 | 66.263 / 65.565 |
| Low/wet IP | 20261373 | 0.001146135 | 0.001038363 | −0.000107771 | 10,000,019 / 10,000,017 | 66.143 / 66.044 |
| Medium/dry OOP | 20261371 | 0.035655787 | 0.042400422 | +0.006744635 | 10,000,076 / 10,000,013 | 76.763 / 76.521 |
| Medium/dry OOP | 20261372 | 0.039541661 | 0.040639951 | +0.001098290 | 10,000,082 / 10,000,019 | 76.393 / 76.427 |
| Medium/dry OOP | 20261373 | 0.035132481 | 0.036229360 | +0.001096879 | 10,000,136 / 10,000,037 | 76.634 / 76.613 |

B1 medium/dry median **0.040639951** and worst **0.042400422** miss the
unchanged 0.01 median and 0.025 worst gates; its paired median is
**+0.001098290**, also beyond the frozen +0.001 negative threshold. B1
low/wet median **0.001038363**, worst **0.001040217**, and paired median
**+0.000020953** satisfy their absolute and low/wet paired limits. All six
candidate final policies have 100% whole positive-average coverage and zero
recall violations. Thus the preregistered classification is **negative**.
There was one fixed training run and no unfavorable retry, seed search,
budget extension, representation change or default promotion.

Both arms use the same four-float64-table memory estimate: 523,776 bytes
per low/wet policy and 4,697,088 bytes per medium/dry policy. B1 final
worker high-water RSS was 61,095,936–61,423,616 bytes on low/wet and
189,251,584–192,643,072 bytes on medium/dry. The older B4 run's RSS was
62,898,176–65,880,064 and 196,837,376–238,043,136 bytes respectively;
these are cross-run observations, not a controlled performance effect.
The B1 six-path launcher took 143.139 seconds (internal 142.760), below
its 7200-second cap. The conservative profile bound was 3698.083 seconds
and admitted this one run. The comparison-only OpenSpiel 2.0.2 audit
completed all 54 B1 scalar rows in 27.038 seconds (<900), with maximum
error `4.973799150320701e-14` chips against the `1e-9` tolerance.

## What the saved decisions show

On medium/dry seed 20261371, B1's final 1.526415-chip exploitability
decomposes into 0.439360 chips at turn decisions and 1.087055 at river
decisions. B4's 1.283608 chips decomposes into 0.264670 and 1.018938.
These are **additive best-response gain contributions**, not standalone
local action scores. The report also retains the fixed turn rows 2443,
1596 and 14 for every seed and work checkpoint.

For example, exact turn row 2443 has seat 0 holding `3s 7h` on board
`2s 6h Jc 3c`, pot 72 chips, with legal actions fold, call, raise to 144,
raise to 182. At 10m, B4 saves probabilities
`[0.651971, 0.348022, 0.000006, 0.000001]`; B1 saves
`[0.662306, 0.337679, 0.000005, 0.000010]`. B1's counterfactual and
saved-prefix reach weights are 0.385832 and 0.385820. Its conditional
alternative-action values are approximately `[-18.000, -16.150, -53.724,
-54.540]` chips, and its additive exploitability contribution is
0.236439 chips versus B4's 0.090857. The values assume the **saved
opponent strategy**, an **optimal reply continuation** for the acting seat,
and the specified reach weighting. They diagnose this finite trained game;
they are not universal poker advice or evidence that this one row caused
the full paired difference.

The medium/dry turn contribution rose for each of the three paired seeds;
river contributions were mixed. That observation is compatible with update
variance or convergence effects, but this single two-spot comparison cannot
identify a cause or justify tuning the candidate on these outcomes. The
unchanged exact-river representation still has no information collision on
the finite medium/dry spot. B1 also fails to reach the original absolute
medium/dry strength target, so no default changes.

## Reproduce and inspect

The prospective contract, isolated tested source, source qualification,
fictional proof, fixed profile, separate admission, complete own raw archive,
native audit and final report are normal-clone ancestors of PR #101. The
source fingerprint is
`64e92a742f865b6f19a87ad98e4b2ac3e94b2bf5ce8b26128fb2459a676669bd`;
historical river sources and the PR #100 B4 control archives remain pinned.
The [own archive](../results/medium-dry-b1-updates/own/manifest.json) keeps
all 100k/1m/10m current, uniform and linear policies; the
[native archive](../results/medium-dry-b1-updates/native/manifest.json)
keeps every independent scalar row. The result JSON records seeds, work,
policy hashes, coverage, memory, timing, per-street contributions and fixed
turn decision details. Human hands-on time was not reported.

### Final qualification

On exact negative-report head `583291c`, local base Python 3.11 and 3.12
each passed 5,739 tests, 73 skipped and 150 deselected, with Ruff, format,
strict mypy and pre/post source/runtime/lock/report-archive guards. Local
optional 3.11 passed 2,597 tests; optional 3.12 passed 2,595 with two
expected skips. Both optional roles passed pinned OpenSpiel 2.0.2, Numba
0.68.1 and installed Apache-2.0 license guards before and after. All-file
hooks passed. Separately, hosted [CI run 44791539576](https://github.com/jimmy-sim/poker-ai/actions/runs/44791539576)
passed both Python jobs and hooks on `583291c`. The [complete final check
receipt](../results/medium-dry-b1-updates/final-checks/manifest.json)
retains logs, receipts and checked source pins. These checks support the
software and evidence record; they do not change the negative strength gate.

From the repository root, inspect the same saved medium/dry turn decision
at all work checkpoints for seed 20261371:

```sh
jq '.cases[] | select(.game == "new_medium_dry_oop" and .seed == 20261371 and .readout == "linear_average") | {arm, work_label, exploitability_fraction_initial_pot, turn_contribution_chips, river_contribution_chips, decision: .fixed_turn_rows["2443"]}' results/medium-dry-b1-updates/report/report.json
```

**Next decision:** retain this negative experiment. A different
decision-strength hypothesis requires a distinct prospective protocol and
cannot be an unfavorable B1 retry. The current evidence does not establish
competitive full-game strength.

### Three review questions

1. **Why compare at charged node work?** It fixes measured learner work
   rather than assuming an equal iteration count means equal work for B1
   and B4.
2. **Does one B1 seed improving on low/wet reverse the conclusion?** No.
   The frozen rule uses all three paired seeds and requires both known
   spots to pass; medium/dry fails its absolute and paired gates.
3. **What does the turn-row value comparison mean?** It evaluates
   alternative actions against the saved opponent with an optimal reply
   continuation under specified reach weighting. It does not prescribe an
   action in a different game or against a different opponent.
