# Fixed-policy investigation of full versus sampled vulnerabilities

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Codex-assisted implementation/reporting; personal hands-on hours not recorded.

## Question and definition of done

Why do saved full and sampled profiles have different exact-opponent weaknesses
with identical information groups? Keep strategies fixed. The pinned
[config](../configs/range-mass-policy-swaps.json) binds PR #20's diagnosis,
sidecar, audit and original input-selection config. Recheck all original policies,
checkpoint receipts, roots and prior diagonals before use. No reference actions
enter own computations.

Use every representation, both known turn-river games and all three saved sampled
seeds plus the full control. No best/worst seed selection or new training.

1. Cross all four saved whole policies between seats: 4×4×5×2 = **160 profiles**.
   Record seat-0 EV, seat-balanced row-versus-column EV `(V(a,b)-V(b,a))/2`, and
   each seat's baseline/within-partition/exact-response gains (320 target rows).
   Same-policy seat-balanced EV is zero; the matrix is antisymmetric. Cross-play
   EV is not universal strength or exploitability.
2. Per sampled seed, retain four turn/river substitutions: FF, SF, FS, SS
   (F = saved full, S = that sampled seed; first letter is turn). There are
   **120 hybrid profiles, 240 target conditions**. Each information row must
   have one street; swaps use legal observable rows, never hidden worlds. Mixed
   profiles preserve menus, private/public features and exact-to-abstract mapping.
   Responders still respect hidden opponent cards.
3. For target i and fixed opponent o, define `G_i(o)=B_i(o)-R_i(o)`: exact minus
   same-partition best-reply value. Own baseline cancels, so this gap is independent
   of the responder's saved policy. Reuse verified opponent-specific roots for
   crossed hero values; analytic tests independently check this invariance.
4. Attribute `G(SS)-G(FF)` using both orders: turn contribution is
   `[(G(SF)-G(FF))+(G(SS)-G(FS))]/2`; river contribution is
   `[(G(FS)-G(FF))+(G(SS)-G(SF))]/2`. Retain interaction
   `G(SS)-G(SF)-G(FS)+G(FF)`. Signed contributions sum to the change. This is
   an order-averaged policy-substitution identity, not a retraining or learning-
   algorithm causal claim. FF repeats across seeds as a control, not new samples.

Keep all raw chip units, each seed/seat, partition/context hashes, own hybrid
and reply profiles, source/lock/config hashes, runtime and environment. Use
arithmetic means only for additive summaries. Full and sampled training differ
in update rules, work and traversal; these interventions do not isolate which
training choice caused the policies. The prior failed learning gate remains. A street swap can expose histories rarely
reached under the original turn policy and alter the opponent's conditional
ranges. Interactions can therefore reflect incompatible saved continuations;
no hybrid is deployed or treated as a retraining result.

Publish tested implementation before new measurements. Cap own computation at
1800 seconds including prerequisite replay. Verify complete grids, prior self-
profile diagonals, exact-partition zero premiums, fixed-opponent invariance,
partition projection, street masks and attribution identities. Independently
check **160 crossed EVs, 480 exact/restricted roots and 480 achieved own reply
values**, plus all 120 hybrid baseline EVs, with OpenSpiel 2.0.2 (Apache-2.0), comparison-only, at 1e-9 chips.
Shared exported mechanics/partitions limit independence; licenses remain in
[solver validation](solver_validation.md).

Definition of done: tested runner/replay/audit/inspector, complete native checks,
rerunnable tables/two figures, plain-English journal step 24 and GitHub updates.
Reviewed evidence: `results/policy-swaps/`; reproductions: ignored `results/runs/`.
Stop after verified evidence. No training, feature/remedy choice, global admission,
default change or fresh-game run.

## Reproduction and software validation

`make study-policy-swaps` runs own computation, native audit and report in ignored
`results/runs/policy-swaps/` from a clean checkout. Existing outputs are rejected.
The 1800-second limit covers the own stage, including prerequisite verification;
native audit and later offline replay have separate timers. For reviewed evidence,
use the script defaults and publish own output/profiles before the clean-source
native audit. `make report-policy-swaps` only replays/render reviewed evidence.

`python scripts/inspect_policy_swap.py` shows the first predeclared sampled seed's
four opponent street combinations and signed contributions. It is an offline
viewer; use replay/report for numerical verification. No solver training runs in
these commands. Tests use explicitly labeled one-game/one-seed synthetic saved
policies with a mocked input loader. The real complete prior 40-profile selection,
native binding and original receipt replay are checked separately. Production
has no input-loader bypass.

## Recorded result

All **160 crossed profiles**, **320 crossed target rows**, **120 street hybrids**
and **240 hybrid target conditions** complete. Every prior diagonal and additive
identity passes. Own complete nested replay has **zero difference** on the recorded
Mac. The independent audit passes all **160 crossed EVs, 120 hybrid baseline EVs,
480 response roots and 480 achieved own reply values**. Maximum discrepancy,
including recomputed street effects, is **1.2789769243681803e-13 chips**, below
1e-9. The own stage took **60.218 seconds**, below 1800; audit including replay
**71.163 seconds**. No learning or policy deployment occurred.

### River choices explain most of the saved gap change

For medium OOP range mass, these are mean **extra-information gaps**, half-summed
over seats and averaged over all three seeds, as percent of the initial pot:

| Opponent turn policy | Opponent river policy | Extra-information gap (% pot) |
|---|---|---:|
| Full | Full (FF) | 0.271466 |
| Sampled | Full (SF) | 0.254886 |
| Full | Sampled (FS) | 3.361794 |
| Sampled | Sampled (SS) | 4.110824 |

Replacing just the saved river decisions produces a much larger gap than
replacing just the turn decisions. This pattern holds for each sampled seed.
Keeping sampled turn decisions but substituting the full river continuation
reduces the measured gap sharply. These are gap measurements, **not whole-hybrid
exploitability, retraining improvements or an accepted new agent**. The previous
sampled median total exploitability remains 4.480481% and its learning gate fails.

The mean change SS minus FF is **3.839358 percentage points**. Averaging the two
substitution orders attributes **0.366225 points to turn** and **3.473133 points
to river**. Interaction is **+0.765610 points**, already split equally between
those two order-averaged contributions; do not add it again. Turn alone slightly
reduces the gap, but its average contribution becomes positive when the other
order includes the river interaction. Signed values are retained for all controls.

The other medium compressed controls also show dominant river contributions:
texture change **3.918601** = turn **-0.071494** + river **3.990094** points;
category change **3.526579** = **-0.084256** + **3.610835** points. Exact and
raw-public medium premiums and effects are zero. Low candidate gaps remain tiny:
FF/SF are zero; mean FS **1.294951e-7%**, SS **1.292777e-8%**. The two plot panels
use different vertical scales. All individual seeds/seats are retained in raw
JSON, with per-seed half-sums and means in the CSVs.

### Why ordinary matches can miss this weakness

Within the same medium spot, full range-mass has only **0.034084–0.063799% of the
pot** seat-balanced EV advantage against the three saved sampled range-mass
profiles. Yet their vulnerability to exact-information replies differs greatly.
A match between two strategies using the same compressed information need not
expose the weakness visible to an exact responder. These are deterministic spot
EVs, not empirical win rates or population confidence intervals.

The crossed matrix holds each opponent fixed while varying the other policy.
Changing the responder's saved policy changes its baseline and within-partition
improvement, but cannot change `B_i(o)-R_i(o)`: its own baseline cancels. In the
street analysis, stored hybrid templates contain both actors' rows. For target i,
this primary gap therefore measures the opponent-row intervention alone, as
verified directly in tests. Raw hybrid baseline EVs/within-partition values can
reflect both actors' changed rows; they are not attributed as opponent-only effects.
This clarification was published in PR #21 before new outcomes.

### What we learned, and what remains untested

The observed full/sampled vulnerability difference is concentrated in the saved
river continuation, with turn–river interaction. The information groups, card
ranges, game and actions are fixed, so a representation-size change does not
explain this experiment. Exact replies still respect hidden opponent cards.

This does not identify *why training learned those river probabilities*: full
CFR+ and linear sampled MCCFR differ in update rules, traversal and work. A
street intervention is an intervention on a saved policy, not random assignment
to a training algorithm. It can also expose histories rarely visited under the
original prefix and change conditional opponent ranges. No claim of isolated
sampling variance, an irreducible information floor, or guaranteed benefit from
more iterations/new features follows. Do not deploy a hybrid from these plots.

A useful next milestone is a controlled training-method comparison with matched
update/averaging rules and documented work, or targeted inspection of the saved
river rows and their training mass, before selecting a remedy. No such new
training, remedy selection, fresh/global stage or default change runs here.

## Evidence and verification

[PR #21](https://github.com/jimmy-sim/poker-ai/pull/21) publishes the prospective
plan first. Clean checked source **c2f14c122b850cf5bc8d152ccd074236367a7335** passed
local and hosted checks before the own run. Raw own evidence was published in
**acc98d81377399d8933e3ba7e326190c1a193c6a** before the clean-source native audit.
Original model, strategies, configs, failed gates and historical source remain
unchanged. Source/lock/config/input hashes, CPU/Python/NumPy metadata, every own
hybrid and reply profile, and all raw chip values are retained. No reference
actions enter the own computation.

[Raw study](../results/policy-swaps/study.json),
[native audit](../results/policy-swaps/independent.json),
[summary](../results/policy-swaps/report/summary.json) and
[tables/two figures](../results/policy-swaps/report/tables.md) reproduce the claims.
Both figures are visually checked. Tests cover masks/partition projection,
fixed-opponent root invariance, signed attribution, diagonals/antisymmetry,
complete grids, source/context/profile/value tampering and native values themselves.
All **944 all-extras tests** pass on Python 3.11.17/3.12.15; base-only **911 passed,
24 optional skips**, including **30 new tests**. Ruff lint/format, strict mypy and
hooks pass. Hosted code CI **42463711199** passes both Linux jobs before the run;
final evidence checks are reported separately in the PR.

Stop at this verified fixed-policy investigation. Issue #4 stays open.

## Questions to practise

1. **Why hold the opponent fixed?** It separates a change in the hero's baseline
   play from a change in the opponent-specific exact/restricted reply roots.
2. **Why average both street-swap orders?** Turn and river can interact. Each order
   gives a different marginal effect; averaging shares interaction and preserves
   the exact total change, including negative contributions.
3. **Have we proved sampling caused the river weakness?** No. We located the
   difference in saved behavior. A training-cause claim needs a comparison that
   controls update rules, averaging and work, and may need more seeds/games.
