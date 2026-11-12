# External solver validation — Phase 3.5

**Definition of done:** gated exact-game agreement, five fully specified postflop
spots, independently solved reference policies and best responses, weighted action
gaps/node frequencies/common-opponent EVs, bucket/iteration ablations, reproducible
tables/plots, license records, verified claim drafts and interview answers.
Prerequisites were met before execution: [Phase 2](phase2-solvers.md) results and
[trained Phase 3 agents](phase3-verification.md). Tier A passed before Tier B began.

The initial full pipeline passed from clean `0f6aa40` in 590.77 seconds. The
complete run including every spot heatmap and hand-EV table passed from clean
`be1badc` in 595.73 seconds on the recorded Apple M4/Python 3.11.17 environment;
reference solving/comparisons used 294.88 seconds. Raw reports preserve exact revisions, dirty flags, source and
input hashes, dependency lock hash, versions, runtime and hardware. Timings are
observations on this machine, not general performance promises. A later rerun's
manifest supersedes these timings without changing the protocol.

**Main finding:** toy-game implementation agreement is excellent; the bounded
Hold'em agent remains far from the postflop reference. Read the generated results
below together with the diagnosis and limitations. No competitive playing-strength
claim follows from this milestone.

## Reproduce and inspect

```sh
make validate-solvers
make check
```

Install uv 0.13.5 as in the README. The command uses locked optional
`solver-validation`, `validation` and `research` extras. It reruns Tier A first,
then fresh **own global self-play**, then postflop controls/reference solves/all
135 comparisons, followed by report rendering. Failed numerical/convergence gates
abort before reviewed outputs are replaced. Work products/checkpoints stay under
ignored `results/runs/solver-validation-build/`; small reviewed evidence lives in
[`results/solver-validation/`](../results/solver-validation/manifest.json).
The own checkpoints can be recreated by the command; no download or external
solver output is needed for own training. `make setup` alone does not install
optional reference libraries.

- [Raw Tier A](../results/solver-validation/tier-a.json),
  [raw Tier B](../results/solver-validation/postflop.json),
  [own training](../results/solver-validation/agent-training.json).
- [Per-spot summary CSV](../results/solver-validation/postflop-summary.csv),
  [diagnosis CSV](../results/solver-validation/diagnosis.csv),
  [ablation figure](../results/solver-validation/ablation-gaps.png).
- Each `*-seed*-nodes.json.gz` contains every primary information set's private
  combo/hand class, public node/state, legal concrete actions, both probability
  vectors, reference reach, lookup status and continuation EV gaps against both
  common opponents. Its `node_frequencies` groups bet/check/fold/call/raise by
  public decision node. Zero-reach conditionals are `null`, not fabricated zeros.
- `*-reference.json.gz` contains tagged comparison-only final reference policies,
  keys, action menus, convergence and spot/EFG hashes. Reference and node artifacts
  are listed with SHA256 in the reports/manifests. They are never agent inputs.

A separate [numeric replay audit](../results/solver-validation/reproducibility.json)
compares the initial and final runs: all 135 profiles, 58,812 detailed decision rows and all
Tier A rows reproduce exactly; all five reference-policy files are byte-identical.
It excludes timing, provenance-bearing checkpoint hashes and figure styling.
Re-run it with `uv run --locked python scripts/check_solver_reproduction.py
--reference-commit caf50a7 --output results/solver-validation/reproducibility.json`.

The renderer generates the diagnostic/Tier A tables and claim drafts below from
raw reports. The one command also replaces the marked README/writeup result
blocks. Timing/provenance fields vary between runs; fixed-seed numerical results
are the reproducibility target on the recorded locked environment. Hosted CI has
not run. Local Python 3.11: **421 passed**; Python 3.12: **418 passed, 3 skipped**
(optional native-reference/evaluator dependencies absent). Ruff and strict mypy
passed on both. Figures were visually inspected.

## Solvers, versions and licenses

| Component | Version/license | Role and obligations |
| --- | --- | --- |
| OpenSpiel | 2.0.2, Apache License 2.0 | Independent CFR variants on toy games; native EFG parser, CFRPlusSolver, expected returns and best response on spots. License/notice and applicable modification attribution obligations; patent grant and warranty disclaimer. No source copied into own core. |
| Treys | 0.1.8, MIT, copyright 2013 Will Drevo | Independent showdown rankings for card-world payout controls only. Preserve copyright/permission notice on redistribution; warranty disclaimer. |

The complete pinned [OpenSpiel license](https://github.com/google-deepmind/open_spiel/blob/v2.0.2/LICENSE)
was read and checked against the installed distribution's license. Both SHA256s:
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.

November 12, 2026: reread the complete installed OpenSpiel 2.0.2 Apache-2.0
license in the compact-own-opponent comparison environment; its bytes match
the same hash above. The new study retains the pinned scalar comparison-only
adapter. No native strategy is a learning input, and this license check does
not admit a new trajectory or replace the prospective source/compute gates.
The complete Treys installed `treys-0.1.8.dist-info/LICENSE` was also read before
this milestone's card-world controls. Installed wheels retain their notices.
OpenSpiel's native library is a comparison reference, not a replacement for the
own Python mechanics/training core. TexasSolver and postflop-solver were not used.
No Gambit implementation is used; EFG is the interchange format only.

November 6, issue #4: the full installed OpenSpiel 2.0.2 Apache-2.0 license was
read again before the [public-board comparison](public-board-comparison.md).
Its native expected-return/best-response functions check frozen own policies and
cross-play only; the new learner never loads reference outputs.

November 8, issue #4: [pipeline cost calibration](controlled-pipeline-check.md)
reuses this previously read OpenSpiel 2.0.2 license; installed bytes were rechecked
against the same SHA256. The separate native module compares old own-policy EV,
exact/restricted roots and achieved own reply/hybrid values. Tests block reference
training and policy export. No native action output enters own training; the
shared own game/export mechanics remain a limitation of this reference check.

No PioSOLVER, GTO Wizard or other commercial solver data are imported, copied or
used for training. Production `agents`, `training` and `abstraction` packages do
not import the comparison package/OpenSpiel; an AST test enforces that import
boundary. Agent loading requires the own MCCFR checkpoint format and compatible
encoder/model fingerprints; reference artifacts have a different rejected format.
These checks prevent accidental mixing, not maliciously forged file authentication.
Reference probabilities/values/gaps never enter own strategy lookup or training.

## Tier A: exact-game credibility gate

[`solver-validation-tier-a.json`](../configs/solver-validation-tier-a.json)
declares tolerances before execution: exploitability agreement 1e-8 ante chips,
unweighted mean information-set strategy L1 1e-6, independent mapped-policy BR
agreement 1e-10, plus final convergence and Kuhn value limits. All four variants
use alternating updates, target 0 then 1, frozen pass, no averaging delay. Kuhn
runs through 10,000 iterations; Leduc through 1,000. Exact full-tree CFR has no RNG;
ten separate seeded policy/BR checks supplement the deterministic trajectories.

Exploitability is **NashConv/2**, in ante chips/hand. Kuhn player-zero value error
uses -1/18. Leduc has no asserted analytical game-value target here; both
implementations' profile values are compared instead. Final strategy L1 averages
information sets equally; checkpoint-level raw data include value and BR gaps.
The initial gated run from `9245bf7` passed before Tier B; the complete pipeline
reproduced the gate. Agreement near machine precision establishes implementation
agreement on these exact games, not zero residual exploitability or Hold'em skill.

<!-- SOLVER_VALIDATION_TIER_A_BEGIN -->
| Game | Variant | Iterations | Own exploitability | Ref. exploitability | Mean strategy L1 | Kuhn value error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| kuhn | cfr | 10,000 | 0.00011332446 | 0.00011332446 | 0 | 7.9627065e-06 |
| kuhn | cfr_plus | 10,000 | 9.632757e-06 | 9.632757e-06 | 0 | 3.5556146e-09 |
| kuhn | linear | 10,000 | 8.6115641e-06 | 8.6115641e-06 | 0 | 3.5976097e-09 |
| kuhn | discounted | 10,000 | 2.3872325e-05 | 2.3872325e-05 | 0 | 4.2622052e-09 |
| leduc | cfr | 1,000 | 0.01181781 | 0.01181781 | 0 | — |
| leduc | cfr_plus | 1,000 | 0.00025715162 | 0.00025715162 | 0 | — |
| leduc | linear | 1,000 | 0.0048261327 | 0.0048261327 | 1.1067718e-17 | — |
| leduc | discounted | 1,000 | 0.00014346789 | 0.00014346789 | 9.5723021e-18 | — |
<!-- SOLVER_VALIDATION_TIER_A_END -->

## Tier B: fully specified restricted games

Each versioned [`configs/spots/`](../configs/spots/dry_high_oop.json) file declares
both weighted physical-combo ranges, board, 200/200 starting stacks, 1/2 blinds,
button, exact public action prefix, remaining stacks/pot, actor/hero and bet grid.
There are **five turn subgames**, each with two combos per player and all 44 legal
rivers for each of four private pairs: 176 worlds/spot. Dry/wet describes the flop.
This does not cover a full 169-class matrix or complete flop game.

| Spot | Board | P0 range | P1 range | Pot / remaining stacks | Hero / root SPR |
| --- | --- | --- | --- | --- | --- |
| dry_high_oop | As 7d 2c 9h | AhAd, KdQd | AcKh, JsTs | 4 / 198 each | P0 OOP / 49.5 |
| wet_high_ip | Jh Th 8s 8h | AhKh, Qc9c | JcJd, QhKd | 4 / 198 each | P1 IP, checked to / 49.5 |
| dry_low_oop | Ks 7d 2c 9h | KhKd, AhQh | KcQc, JsTs | 324 / 38 each | P0 OOP / 0.1173 |
| wet_medium_oop | Qs Js 8d 3s | AsKs, ThTd | QhQd, KcTc | 36 / 182 each | P0 OOP / 5.0556 |
| dry_medium_ip | Ad 9c 4s 6h | AhAc, KhQh | AsKd, 9d9h | 108 / 146 each | P1 IP, checked to / 1.3519 |

All listed combos have weight one. Product priors are conditioned on known-board
and mutual card removal, then renormalized. Public prefix actions do **not** infer
endogenous ranges. Future rivers and opponent cards stay hidden in decision keys.
The engine replays every prefix and verifies its declared public root.

Both policies use a **full-pot/all-in grid**, plus legal passive/fold actions;
there is no separately included minimum raise or arbitrary raise-count cap.
Sizes may clamp/deduplicate at stack bounds. A full pot means raise increment
above the call price equal to pot after calling. Concrete action menus are checked
for identity, not silently projected. All 135 comparisons had zero projection
mass and no changed shadow ledger. This excludes off-tree mapping as an explanation
*inside these games*, not in arbitrary no-limit play. Phase 3's separate off-grid
stress audit showed explicit fallback failures and remains a limitation.

The own policy ablation is **global uniform-deal self-play**, not training on the
spots or solver outputs. [`solver-agent-ablation.json`](../configs/solver-agent-ablation.json)
fixes external sampling, potential buckets 2/4/8, seeds
20261115/20261116/20261117 and checkpoints 100/300/1,000. Nine runs completed all
27 checkpoints with node/time budgets and isolated worker processes. Primary is
**8 buckets at 1,000 iterations**, declared before comparisons, not whichever
configuration happened to look best. The three checkpoints share each run's
trajectory; three seed ranges are descriptive, not confidence intervals.

The reference uses OpenSpiel 2.0.2 native deterministic CFR+ on an exact exported
spot tree. Configured iteration schedule: 64/256/1,024/4,096/16,384. Require
exploitability at most **0.001 root pots** at **two successive scheduled
checkpoints**; retain the latest policy. This strengthened stability control was
declared after a reference-only cost pilot and before main agent comparisons.
Final achieved iteration counts/convergence are in the raw report. Every parsed
node's chance/actions/payoff and the information-set bijection are checked.

**Independence boundary:** the EFG mechanics/export are own project code. OpenSpiel
independently parses, solves and best-responds to that game. It is not an
independent full postflop-engine implementation. Separate controls checked all
880 passive card worlds with Treys; Phase 1 supplies million-hand evaluator and
independent PokerKit engine evidence with its documented exceptions. Own/native
cross-play expectation error was at most 1.066e-13 chips across this run's profiles.

Root strategy heatmaps are also available for
[dry/high/OOP](../results/solver-validation/dry_high_oop-strategy.png),
[wet/high/IP](../results/solver-validation/wet_high_ip-strategy.png),
[dry/low/OOP](../results/solver-validation/dry_low_oop-strategy.png),
[wet/medium/OOP](../results/solver-validation/wet_medium_oop-strategy.png), and
[dry/medium/IP](../results/solver-validation/dry_medium_ip-strategy.png).
All show both policies on the configured hero's two root hand classes, with own
probabilities averaged across the three predeclared primary seeds.

## Metrics and EV conventions

For each exact information set, action MAE is sum of absolute probability
differences divided by **that set's legal-action count**. Average using the final
reference profile's joint reach, including chance; normalize across all compared
decision information sets. Report overall and by street. Padding is excluded.
Units are probability points (100 times this is percentage points), not L1 or
necessarily total variation. Thus unlike branching factors affect normalization.
Reference weighting can de-emphasize states the own policy reaches more often;
restricted best response and the EV decomposition complement this metric.

Range frequencies and per-node/per-class continuation EVs use the **same reference
conditional range beliefs** for both policies. That isolates policy differences
at the node; these are not each policy's endogenous realized node ranges. Node
exports contain physical combos and hand classes; only configured combos are
covered. Root class EVs instead condition on the declared range marginal.

Four exact profiles are evaluated: (reference, reference), (own, own),
(own P0, reference P1), and (reference P0, own P1). For each hero, compare own versus
reference while fixing **the same opponent**, once reference and once own. Signed
positive gap favors own; the two gaps can have opposite signs because an
equilibrium policy need not maximally exploit the own opponent. Values are net
original-hand chips; fixed prefix costs cancel in EV differences. Enumeration
covers every configured private pair/river, so these are exact restricted-game
expectations up to rounding, not sampled win rates. Native best response measures
own profile exploitability in this exact range/action game; both players' policies
are included, not only the hero.

The readable root-class table below averages the three primary seeds; signed
gaps use chips, not root-pot units. [CSV](../results/solver-validation/hand-class-ev.csv)
also retains seed minima/maxima. Node-level records contain the corresponding
conditional continuation EVs at every decision, including later streets.

<!-- SOLVER_VALIDATION_HAND_EV_BEGIN -->
| Turn subgame | Hero hand class | EV gap vs ref. opponent (chips) | EV gap vs own opponent (chips) |
| --- | --- | ---: | ---: |
| dry_high_oop | AA | -1.1559 | -25.1154 |
| dry_high_oop | KQs | -3.5430 | -6.4934 |
| wet_high_ip | JJ | -0.0345 | -35.5587 |
| wet_high_ip | KQo | -1.7758 | -23.4299 |
| dry_low_oop | AQs | -5.8579 | -56.5299 |
| dry_low_oop | KK | -54.3921 | -52.5154 |
| wet_medium_oop | AKs | -15.6145 | -39.4593 |
| wet_medium_oop | TT | -7.4871 | +13.6844 |
| dry_medium_ip | 99 | -20.3893 | +15.2468 |
| dry_medium_ip | AKo | -21.2903 | +17.6988 |
<!-- SOLVER_VALIDATION_HAND_EV_END -->

## Diagnose before attributing to compute

Implementation controls passed: all 120,947 exported nodes aligned with the native
parser, all 880 passive private-card/river controls matched Treys/expected payouts,
hidden-card tests passed, concrete action grids/ledgers matched, common-opponent
EVs matched native expectations, and self-comparisons gave zero gaps. Tests also
verify that an exact performance-difference decomposition sums back to total EV.
These checks substantially narrow bug hypotheses; they do not prove absence of
all engine, abstraction or training defects outside this scope.

<!-- SOLVER_VALIDATION_DIAGNOSIS_BEGIN -->
| Turn subgame | Ref. policy change (pp) | EV deficit accounted for at fallback nodes | Action gap: 100 → 1,000 iters (pp) |
| --- | ---: | ---: | ---: |
| dry_high_oop | 0.021 | 92.9% | 32.19 → 37.23 |
| wet_high_ip | 0.626 | 94.7% | 32.28 → 34.64 |
| dry_low_oop | 0.222 | 69.9% | 49.98 → 49.98 |
| wet_medium_oop | 0.120 | 99.7% | 31.05 → 31.05 |
| dry_medium_ip | 0.140 | 100.0% | 31.29 → 31.29 |

Fallback shares use the exact performance-difference identity, averaged across the three primary seeds. They are an EV accounting decomposition, not a causal estimate for extra training. Reference policy changes use the final reference reach weights.
<!-- SOLVER_VALIDATION_DIAGNOSIS_END -->

- **Sparse/unaveraged strategy:** fallback decisions account for about 70–100% of
  the mean hero EV deficit, using candidate reach in the exact accounting identity.
  This differs from their share of reference-reach action gaps. For example,
  very low-reference-reach unseen decisions can still cost EV under own play.
  `matched` only means a saved average row has positive mass; it can remain uniform.
- **Iterations:** 100→1,000 iterations did not consistently improve spot action
  gap/exploitability. Several curves stay flat; two high-SPR spot gaps increase.
  The measurements support poor coverage/poor current policies, not a claim that
  more compute alone would solve the gaps. Global training and conditional spot
  solving optimize different range distributions, so spot improvement is not a
  monotonic consequence of global self-play iterations.
- **Buckets:** 2/4/8 changes coverage and the metrics, with no universal winner.
  More buckets reduce these high-SPR restricted exploitabilities but do not yield
  small gaps. The models are not nested and coverage changes with capacity; this
  experiment does not identify a pure irreducible abstraction-loss floor.
- **Off-tree sizes:** not a cause within the matched grid; broader translation
  remains unvalidated strategically and is not included in these gap numbers.
- **Reference convergence:** two converged checkpoints and below 0.627 pp
  reference-policy change are small beside 31–50 pp agent action gaps. With fixed
  final reach weights, the triangle inequality bounds action-gap sensitivity to
  the preceding reference policy by that reported policy change. Residual epsilon
  is still reported, not called exact GTO.

A post-primary diagnostic also counts exact information sets that share an own
abstract key. It was added after the primary run to investigate the already
observed gaps; it did not select the primary configuration or change training.
Both hands and revealed river boards can merge. In-spot collisions are small in
reference reach for three primary spots, and substantial in the two medium-SPR
spots. This does not rule out interference from other global training states,
and a collision only costs EV if the required strategies differ materially.

<!-- SOLVER_VALIDATION_ABSTRACTION_BEGIN -->
| Spot | Merged ref. reach: 2 / 4 / 8 buckets | Exact infos → 8-bucket keys |
| --- | ---: | ---: |
| dry_high_oop | 0.005% / 0.005% / 0.004% | 9,240 → 890 |
| wet_high_ip | 100.000% / 0.187% / 0.187% | 5,540 → 470 |
| dry_low_oop | 0.014% / 0.014% / 0.014% | 376 → 42 |
| wet_medium_oop | 69.151% / 36.769% / 36.562% | 3,336 → 312 |
| dry_medium_ip | 99.999% / 99.608% / 99.608% | 1,112 → 60 |

A merged group contains multiple exact information sets with the same own abstract key, including different revealed river boards. This measures representation collisions inside these spots, not EV loss or aliases with other global states.
<!-- SOLVER_VALIDATION_ABSTRACTION_END -->

![Bucket and iteration ablations](../results/solver-validation/ablation-gaps.png)

## Limitations and what the numbers prove

This is a transfer comparison on five narrow turn games, not unrestricted
Hold'em exploitability, general solver equivalence, a full preflop solution or a
winning-agent result. The reference knows the declared fixed ranges; the frozen
global own policy does not re-solve for them. They need not equal global self-play's
endogenous conditional ranges. The agent's card abstraction, small iteration
budget and explicit uniform fallbacks are material limitations. The action grid
excludes many real bet sizes. Large SPR permits losses of many root pots; a value
above one in the exploitability/pot column is possible and is not a win rate.

Equilibria can differ in action probabilities while retaining similar EV; action
agreement alone is neither necessary nor sufficient for good play. Native BR is
independent of own solver updates, while mechanics/export remain shared. The
passive Treys check does not independently validate all betting rules. Three
fixed seeds and five selected spots do not support population confidence bounds.
All seeds/configurations and non-improving results are retained without choosing
the best seed or replacing the predeclared primary.

## Resume-ready drafts generated from verified reports

<!-- SOLVER_VALIDATION_CLAIMS_BEGIN -->
# Verified claim drafts

- Implemented four exact CFR variants for Kuhn and Leduc; matched OpenSpiel 2.0.2 exploitability within 1.39e-16 ante chips/hand at the tested equal iteration budgets. This is implementation agreement, not zero remaining exploitability.
- Built a reproducible external-solver comparison across 5 restricted turn subgames; measured 36.84 percentage points mean action-frequency gap versus OpenSpiel CFR+ (equal spot weighting, three fixed agent seeds, reference-reach-weighted node MAE). The agent had higher restricted exploitability in 5/5 spots and lower hero EV versus the reference opponent in 5/5; this is not a full-game win-rate claim.
- Verified every exported node in 120,947 restricted-game tree nodes against OpenSpiel's parser and 880 passive private-card/river worlds against independent Treys showdown ranks and expected payouts. The exported mechanics are project code, so parser/solver agreement alone is not an independent full-engine validation.
<!-- SOLVER_VALIDATION_CLAIMS_END -->

## Three interview questions

**Why isn't matching action frequencies enough?** Equilibria can use different
mixtures, and reference reach may hide own-reached mistakes. I also evaluate both
policies against the same two opponents and compute independent restricted-game
best responses. Those measure consequences rather than superficial agreement.

**Why can exact CFR match while the Hold'em policy is weak?** The toy gate checks
updates, averaging and BR on small exact games. The Hold'em policy is sampled,
abstracted and sparsely trained under different global ranges. Its explicit
fallbacks account for most of the measured EV deficit; tested bucket/iteration
changes do not establish that extra compute alone fixes this.

**How independent is this validation, and how did you avoid leakage?** OpenSpiel's
parser/CFR+/BR are independent, but my EFG mechanics are shared and I disclose that.
Treys and Phase 1 PokerKit controls address separate mechanics risks. Reference
artifacts have a distinct format and remain inside comparison/reporting code;
own self-play only consumes own configs/models/checkpoints, never solver outputs.

<!-- SOLVER_VALIDATION_RESULTS_BEGIN -->
### Reproduced external-solver comparison

Exact-game CFR variants matched OpenSpiel 2.0.2 within **1.39e-16 ante chips/hand** exploitability at matched iterations.

Five **turn subgames**, two physical combos per player, matched full-pot/all-in actions. Primary own agent: eight potential buckets, 1,000 global self-play iterations, three fixed seeds. Entries below are seed means; raw reports include seed ranges, node frequencies, hand-class EVs and all ablations.

| Turn subgame | Action gap (pp) | Turn / river (pp) | Own exploit. / pot | Hero EV gap vs ref. / pot | Trained-policy reach |
| --- | ---: | ---: | ---: | ---: | ---: |
| dry_high_oop | 37.23 | 37.23 / 37.83 | 10.6715 | -0.5874 | 58.3% |
| wet_high_ip | 34.64 | 34.64 / 37.24 | 11.0141 | -0.2263 | 58.3% |
| dry_low_oop | 49.98 | 49.98 / 34.15 | 0.1650 | -0.0930 | 8.3% |
| wet_medium_oop | 31.05 | 31.19 / 30.81 | 1.2075 | -0.3209 | 5.1% |
| dry_medium_ip | 31.29 | 44.44 / 24.92 | 0.4896 | -0.1930 | 0.0% |

Action gap is reference-reach-weighted per-node action MAE, in percentage points. Exploitability is NashConv/2; EV compares the hero policy against the same reference opponent. Pot-normalized EV gaps use root-pot units. These are exact restricted-game expectations, not measured full-game win rates.

Own restricted exploitability exceeds the reference in 5/5 spots; hero EV against the same reference opponent is lower in 5/5. Trained-policy coverage spans 0.0–58.3% of reference decision reach; the rest uses explicit uniform fallbacks. Three training seeds do not establish a population confidence interval.

![Root strategy by the two configured hand classes](../results/solver-validation/strategy-heatmap.png)

Reproduce: `make validate-solvers` (minutes on the recorded Mac; optional solver/evaluator/plot dependencies are installed from the lockfile). No commercial solver data are used. See this document for methodology, licenses, convergence, diagnostics and limits.
<!-- SOLVER_VALIDATION_RESULTS_END -->


The [controlled learning comparison](controlled-learning-comparison.md) completes
140 runs / 840 saved own policies after its separate software/compute admission.
All 840 baseline EVs, exact/restricted roots and achieved own replies/hybrids pass
comparison-only OpenSpiel 2.0.2 checks; maximum discrepancy 1.705303e-13 chips at
1e-9 tolerance. Native wall 92.193960s includes own-policy replay. The installed
Apache-2.0 license bytes match the previously read hash recorded above. Reference
training and strategy export remain prohibited; the auditor returns only scalar
comparisons. This is not a reference-equilibrium strategy match or an independent
check of every exported poker rule. All source/own/archive bindings and archived
native results also validate in a base Python 3.12 environment.

### November9: conditional reduced-backend batch comparison

Before any new-policy native comparison, the installed OpenSpiel2.0.2 Apache2
license was re-read in full and verified through `license_record`. Installed
path:`open_spiel-2.0.2.dist-info/licenses/LICENSE`; SHA256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The distinct reduced-backend adapter retains the same480-profile scalar/reply
checks and exports no reference actions. Reference data cannot enter training.
New-policy comparison is pending publication of complete own evidence; historical
own profiles used in software integration tests are not new agent results.

The new-policy reduced-backend audit subsequently completed: all480profiles pass
OpenSpiel scalar/root/achieved-own-reply checks, maximum discrepancy
1.5631940186722204e-13chips in169.194451625s (<900). Own receipt/three archives
were published67c5894 before native construction. OpenSpiel outputs remain
comparison-only; no action distributions are exported or supplied to training.
This verifies analysis on an own-game export, not reference playing strength or
an independent poker-engine implementation. See docs/reduced-batch-study.md.

### November9: saved-current and fixed-opponent diagnosis

After own publication10df9be, comparison-only OpenSpiel2.0.2 checks all216self
profiles and1728fixed targets: maximum discrepancy2.0605739337042905e-13chips,
164.198028083s<900, including zero-error own replay41.213945417s. The pinned
Apache2 installed LICENSE bytes retain SHA256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
This step uses the same fully read installed license recorded above. All216
scientific source files are bound to the observed source CI. Four finite own
full controls, not reference equilibrium opponents, define fixed targets.
The adapter exports no reference actions; native outputs are comparison-only
and cannot enter training. Shared own-game export limits mechanical independence.
See [method, all outcomes and limits](batch-current-diagnosis.md).

## November10 matched-update adapter license check

Before new optional adapter tests, the assistant read the installed
`open_spiel-2.0.2.dist-info/licenses/LICENSE` in the pinned Python3.11 environment.
It is Apache-2.0, SHA256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The new array-to-EFG adapter uses the unmodified installed reference for scalar
comparison only. It requests no reference policy or training output. This local
software coverage does not complete the new source-bound proof or admit a real
matched-update study. Historical solver results and license records remain intact.


### November 10 pinned-license recheck for the private-prefix pipeline

Before constructing a reference for the new pipeline, Codex re-read the full
installed OpenSpiel2.0.2 Apache-2.0 license at15:40 UTC. Its SHA-256 remains
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
matching the prospective config and runtime verifier. The license permits this
comparison use; its redistribution and notice conditions continue to apply.
This pipeline requests independent scalar values and best-response checks of
own policies only. It exports no reference strategy or action table to training.
This license review is not evidence that the new comparison has already run.

### November11 own-opponent adapter license recheck

Before the new optional scalar-adapter tests, Codex re-read the full installed
OpenSpiel2.0.2 Apache-2.0 LICENSE in the pinned311 environment. SHA-256 remains
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
Its license permits this comparison use with its notice/redistribution terms.
The new adapter exports scalar values and achieved own-reply checks only; no
reference strategy/action table enters learning. Optional numerical tests use
the already-published analytic mixed-view fixtures. Mocked worker/schema tests
are not independent numerical comparisons. The new trained full-shape software
proof must publish its own evidence before reference construction. No commercial
outputs are used, and this license record does not admit real training.

The real own-opponent study subsequently publishes complete own evidence at
691a7074af105b77eebbfc84b6debb2589d43217 BEFORE constructing the reference.
The full native command takes358.570928584s<900 and checks432policies/1152fixed
conditions, maxdifference1.8474111129762605e-13chips<1e-9. Its receipt verifies
the same pinned OpenSpiel2.0.2 Apache2 license and installed license files.
No reference actions or strategy enter learning. Numerical validation passes;
the study's two-game superiority condition fails, so no stronger/default/global
admission is claimed. See [complete method and outcomes](own-opponent-learning.md).

## Compact full-control reference check — November 11, 2026

For [PR #55](https://github.com/jimmy-sim/poker-ai/pull/55), Codex read the full
installed OpenSpiel2.0.2 Apache-2.0 LICENSE again before new reference use.
The installed dist-info/licenses/LICENSE SHA-256 is
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The license permits this comparison use and redistribution subject to its
license/notice conditions; no solver source is copied here. The unchanged
ScalarReference exports own finite-game topology, chance/payoffs and own policy
probabilities to OpenSpiel's independent EFG evaluator and both BR calculators.
It requests no reference strategy. Outputs remain comparison-only and cannot
enter the own learner. This checks arithmetic on the exported own game, not
independent Hold'em mechanics or general playing strength. See the
[prospective full-control protocol](compact-full-control.md) for gates and caps.

## Compact sampled comparison — November 12, 2026

[PR #56](https://github.com/jimmy-sim/poker-ai/pull/56) retains OpenSpiel2.0.2
under Apache-2.0. The selected license was read in the prior full-control step;
Codex re-read its full installed LICENSE in the new pinned Python3.11.17
environment on November12. Its SHA-256 remains
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The license permits this comparison use, subject to its license/notice terms.
The new adapter requests only the own policy value and both best-response
values. No reference policy enters the B4 trainer. Optional tiny unit comparisons
are separate from the later source-bound rehearsal and real study; those require
publication of the complete own evidence first. This verifies arithmetic on the
exported own games, not independent engine mechanics or fresh/global strength.

The complete new sampled own grid was subsequently public at9177081 before
reference construction. All324current/uniform/linear readouts pass value and
BOTH-BR scalar checks within1.2789769243681803e-13chips; complete audit41.155462s
under the unchanged900s cap. Own raw replay has zero metric change. Numerical
validation passes, while the candidate's medium LINEAR median2.389912%pot fails
the fixed1%accuracy limit. Keep that distinction: no reference strategy enters
training, and no default/fresh/global admission follows. The full method, failed
gate, every seed/control and three-seed uncertainty limitations are retained in
[the sampled writeup](compact-sampled.md).
