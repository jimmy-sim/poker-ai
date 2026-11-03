# External solver validation — Phase 3.5 in progress

Execution is now eligible: Phase 2 exact exploitability results are committed, and
[Phase 3 acceptance](phase3-verification.md) records trained own limit/no-limit
agents and tested inference. This milestone begins after those gates. Tier A must
pass before Tier B implementation/experiments advance. No Phase 3.5 comparison
result or resume claim exists at this initial execution checkpoint.

## Selected reference and license inventory

| Solver | Pinned version | License | Role |
| --- | --- | --- | --- |
| OpenSpiel | 2.0.2 | Apache License 2.0 | Independent exact-game CFR variants; native reference capabilities investigated for small postflop games |

The complete versioned license was read for this milestone and checked against
the installed wheel license; both SHA256 values are
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
[Official pinned license](https://github.com/google-deepmind/open_spiel/blob/v2.0.2/LICENSE).
The license permits use/modification/distribution subject to its license/notice
and applicable modification-attribution obligations, includes a patent grant and
warranty disclaimer. The installed wheel preserves its license. Source headers
attribute the implementation to DeepMind Technologies Limited. The project uses
its API for comparison; no reference implementation is copied into the own core.
The native reference library does not replace the own Python poker/training core.
TexasSolver/postflop-solver have not been selected or used; no commercial outputs
are used. Record any later additional solver here after reading its pinned license.

## Purpose and data boundary

Measure agreement and disagreement with independent, rerunnable open-source
solvers on exact toy games and fully specified postflop spots. Only use solvers
whose licenses permit the intended use. Read the license for each selected pinned
version and record its source, license text/link, obligations, and applicability
here before using it. The selected reference is listed above; other solver names
remain candidates and have not been used.

Never import, copy, or train on commercial solver outputs, including PioSOLVER or
GTO Wizard. Reference outputs are comparison artifacts only: they must never be
loaded into the agent's strategy, training data, checkpoints, or policy lookup
path. Keep the reference-artifact path separate from agent inputs and test that
boundary when implementing this milestone.

Every reported quantity must come from scripts, versioned configs, explicit seeds,
and recorded solver versions/settings. Do not fabricate or hand-tune results.

## Prerequisites and advance declarations

- Saved and validated Phase 2 exploitability results.
- A trained Phase 3 agent with reproducible checkpoint provenance.
- Declare metric conventions, convergence targets, iteration budgets, reach
  weights, tolerances, and acceptance criteria in versioned configs before runs.
- Resolve rule, payoff-unit, information-state, legal-action, and strategy-averaging
  conventions before comparing implementations. Document unavoidable differences.
- Estimate compute from pilot runs; flag work likely to exceed a few hours and
  present cheaper alternatives before launching it.

## Tier A — Exact-game validation

Compare the project's CFR variants with OpenSpiel CFR on Kuhn and Leduc at matched
iteration counts. Record which algorithm variants have direct reference matches.
Report exploitability with an explicit normalization, final average-strategy L1
distance with a defined information-state/action alignment and aggregation, and
game-value error. Kuhn's first-player target is -1/18 under the approved rules.

State pass criteria in advance in config, including documented tolerances for
exploitability differences at equal iteration counts. Strategy-distance gaps need
interpretation when different equilibrium strategies are possible. If Tier A
fails, debug before advancing to Tier B.

## Tier B — Single-spot postflop comparison

Start with 5–10 versioned spot configs. Specify both players' preflop ranges,
card-removal/weight conventions, flop and optional turn board, stack depth, pot,
player positions, complete action tree/bet-size set, and payoff units. Include dry
and wet flops, in-position and out-of-position decisions, and high/low stack-to-pot
ratios. Define reach probabilities and legal continuation behavior explicitly.

Solve each spot to a declared convergence criterion, recording achieved
exploitability (where available) and iteration count. Restrict the project agent
to the same ranges, cards, and actions. Prefer identical action abstractions;
document and quantify action mapping if the abstractions differ.

Report per hand class and decision node:

1. Mean absolute action-probability difference, weighted by a declared reach
   distribution, overall and per street. Define normalization and zero-reach
   handling before examining results.
2. Range-level bet/check/fold/call/raise frequencies at each node.
3. EV differences by hand class, evaluating both strategies against the reference
   opponent policy and against the project's opponent policy. State the two
   cross-play comparisons and common payoff convention explicitly.
4. Exploitability of the project's strategy restricted to the specified spot,
   using a validated best-response calculator with documented range conditioning.

Produce strategy heatmaps by hand class and per-spot tables of gap metrics. Label
reach weighting, normalization, and probability units in tables and plots.

## Diagnosis and ablations

For each large gap, test card-abstraction bucket count, off-tree action sizes,
training iterations, reference convergence, and implementation correctness as
possible explanations. Vary bucket count and training iterations in preregistered
ablations and plot each against the gap. Treat widespread large gaps as a likely
bug first: check evaluator, engine, action legality, observations/private-card
access, and abstraction before attributing them to compute.

## Deliverables and definition of done

- `make validate-solvers` reproduces all tables and plots from fixed configs and
  seeds after prerequisites are satisfied. Do not add a placeholder success
  command or claim this command works before implementation.
- Tests cover spot loading and gap metrics, including strategy-to-itself zero-gap
  checks, reach weighting, invalid probabilities, and action alignment.
- This document becomes the technical writeup: methodology, exact solver
  versions/licenses, spots, results, plots, failed checks, ablations, and limits.
- README includes a one-page summary with a metrics table, one heatmap, and an
  honest statement of where the agent is weaker than the reference.
- Draft resume claims only from verified numbers, such as matched OpenSpiel
  exploitability within a measured tolerance or a measured action-frequency gap
  across a stated set of spots. No numeric claims exist at planning time.
- Include three interview questions and answers grounded in the actual work.
- State what agreement does and does not prove: abstraction mismatch, single-spot
  scope, reference convergence uncertainty, and strategy non-uniqueness limit the
  interpretation. Action agreement alone is not a proof of equilibrium quality.

## Tier A execution protocol declared before this run

`configs/solver-validation-tier-a.json` preserves the already-declared Phase 2
conventions/tolerances unchanged: alternating target 0 then 1, no averaging delay,
all four direct variant matches, Kuhn through 10,000 iterations and Leduc through
1,000. Exploitability is NashConv/2 in ante chips/hand; final strategy L1 is the
unweighted mean of actionwise L1 across information sets. Kuhn error is measured
against -1/18. Five seeded independent BR-policy checks per game supplement the
deterministic solver trajectories (training seed=null).

Acceptance: exploitability agreement within 1e-8, mean L1 within 1e-6, mapped-policy
BR agreement within 1e-10, and the config's final convergence/value limits. Any
failed gate requires diagnosis before Tier B. `make validate-solver-tier-a` writes
a fresh gated report/CSV/plots under `results/solver-validation/`; it does not
overwrite historical Phase 2 evidence. The prior pilot predicts minutes of local
compute. A complete `make validate-solvers` command will be added only when all
required stages are implemented; it is not fulfilled by Tier A alone.

## Tier A acceptance result

The fresh gated run from clean `9245bf7` passed every
predeclared criterion. [Raw Tier A report](../results/solver-validation/tier-a.json)
and [CSV](../results/solver-validation/cfr-convergence.csv) preserve all checkpoints.
Maximum exploitability disagreement: 1.3877788e-16 ante chips/hand; maximum mean
information-set L1 distance: 1.4237625e-17; maximum profile-value difference from the
reference: 2.220446e-16 chips/hand. These measure implementation agreement, not
zero exploitability. The table below reports actual remaining exploitability.

| Game | Variant | Iterations | Own exploitability | Reference exploitability | Mean strategy L1 | Kuhn value error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| kuhn | cfr | 10,000 | 0.00011332446 | 0.00011332446 | 0 | 7.9627065e-06 |
| kuhn | cfr_plus | 10,000 | 9.632757e-06 | 9.632757e-06 | 0 | 3.5556146e-09 |
| kuhn | linear | 10,000 | 8.6115641e-06 | 8.6115641e-06 | 0 | 3.5976097e-09 |
| kuhn | discounted | 10,000 | 2.3872325e-05 | 2.3872325e-05 | 0 | 4.2622052e-09 |
| leduc | cfr | 1,000 | 0.01181781 | 0.01181781 | 0 | — |
| leduc | cfr_plus | 1,000 | 0.00025715162 | 0.00025715162 | 0 | — |
| leduc | linear | 1,000 | 0.0048261327 | 0.0048261327 | 1.1067718e-17 | — |
| leduc | discounted | 1,000 | 0.00014346789 | 0.00014346789 | 9.5723021e-18 | — |

Ten independently seeded policy BR comparisons also passed. The underlying games
were exhaustively checked for actions/chance/payoffs and information-set bijection.
Tier B implementation may now begin. Historical Phase 2 data remain untouched.
