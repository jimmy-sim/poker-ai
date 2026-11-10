# Why can a river continuation change a turn decision?

November 10, 2026. Issue #4 comment 6776137714 registers this saved-data contrast
before measuring the new action values. Keep all nine primary profiles, both
seats, every previously ranked top-five group and every exact member.

For the same fixed saved opponent, compare the own exact best reply, the own
information-constrained reply, and a hybrid with exact pre-river rows but
constrained river rows. Compute conditional action values using the existing
own function. The hybrid changes only the responding player's river strategy;
opponent probabilities stay identical.

Check all three root values against the audited source, all policies legal,
unchanged opponent and pre-river rows, unchanged inputs, finite values, complete
group/member inventory and identical opponent/chance support within 1e-12.
Root tolerances stay at 1e-9 chips. Unsupported rows remain present with no
preferred action; supported ties use the first legal maximizer.

These are continuation contrasts against a fixed opponent. They can explain
why changing later choices changes an earlier action's value. They do not
measure the benefit of retraining, isolate extra-information-only row losses,
or establish poker advice. Keep the failed strength gate and all seeds, caps,
defaults and historical source/data unchanged. No learner or native reference
is constructed; no reference strategy enters the calculation.

The final decision report must be hash-checked and pinned before execution.
The prospective summary hash comes from the retained complete initial report;
require the safeguarded final report to reproduce those exact bytes. If it
does not, investigate rather than changing the prospective hash. All local and
both hosted checks must pass before merge.

## Implementation checkpoint

The report entrypoint reuses the completed decision panel/archive loader, own
scoring context and conditional-action helper. It validates the exact/restricted/
hybrid roots against the audited source, fixes opponent rows, checks that the
hybrid changes only own river rows, and retains all 90 groups / 415 exact members.

Thirteen checks pass in 0.52 seconds. A fictional two-decision example has a
stop payoff of 1, continuation payoff of 4 with a good later choice, and 0 with
a bad later choice. It verifies both target signs and that own past reach is
excluded from counterfactual support. These are constructed continuation
profiles, not CFR training or equilibrium results. Failure tests cover changed
roots, nonfinite values, prefix/river/opponent/mask/trio changes, unsupported/tied
choices, unitless support errors below the chip tolerance, and no overwrite.
Ruff, formatting and strict typing pass. Actual saved-poker values and full
local/hosted checks remain pending.

## Retained support-scope failure and correction

The first complete saved-data attempt, source e92d0cc, fails before completing
any contrast. Its helper compared support at both actors' information sets.
Only the responding player's chance-times-opponent support must remain fixed;
the other player's support legitimately changes when the responding strategy
changes. A separate Kuhn fixture reproduces zero change at the responding
player's rows and a 1/6 change at the other player's rows.

The original source, raw failure log, independent fixture and four passing
initial suites remain retained in results/private-prefix/continuations-initial-
e92-failure. The initial suites (2,317 base / 2,373 optional per environment)
missed this valid two-player case. The added regression tests it explicitly.

The correction checks the same 1e-12 tolerance on responding-player information
sets. Opponent-policy identity remains checked across every opponent row.
All original profiles, groups, members, roots, chip tolerances, seeds, caps and
thresholds stay fixed; no model source changes. Fourteen focused checks now
pass in 0.45 seconds. The corrected saved-data reproduction and full checks
follow; no continuation result is claimed at this checkpoint.
