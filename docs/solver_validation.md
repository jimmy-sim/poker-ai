# External solver validation — planned, execution gated

This file records the requested future milestone. It is not a results report.
Do not start solver selection, license review, implementation, or solver runs until
Phase 2 exploitability results and a trained Phase 3 agent both exist. Execute this
milestone after Phase 3 and before Phase 4; maintain the original phase order.

No reference solver or version is selected yet. No license has been reviewed for
this milestone, and there are no comparison results or resume claims.

## Purpose and data boundary

Measure agreement and disagreement with independent, rerunnable open-source
solvers on exact toy games and fully specified postflop spots. Only use solvers
whose licenses permit the intended use. Read the license for each selected pinned
version and record its source, license text/link, obligations, and applicability
here before using it. Candidate examples supplied by the user are OpenSpiel,
TexasSolver, and postflop-solver; these are candidates, not approved selections.

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
