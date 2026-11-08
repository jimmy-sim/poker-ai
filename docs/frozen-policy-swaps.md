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

## Status

Plan published in [PR #21](https://github.com/jimmy-sim/poker-ai/pull/21) before
implementation/outcomes. Runner, native audit, offline report and inspector are
implemented. Local checks pass 944 all-extras tests each on Python 3.11.17/3.12.15;
base-only 911 passed/24 optional skips. Includes 30 new tests. Ruff lint/format,
strict mypy and hooks pass. New research interventions have not yet run at this
code-publication checkpoint.
