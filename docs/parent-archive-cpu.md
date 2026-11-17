# Where archive validation spends CPU

[PR #84](https://github.com/jimmy-sim/poker-ai/pull/84) is history-merged at b852436 after all six final roles passed on 49cb951.
Actual main passes 419 focused tests and authenticates the complete saved pair;
all three numerical exports match and all ten unrelated local results remain
preserved. Its diagnostic locates 37–39 parent CPU seconds per cost read inside
sampled-parent archive validation. That boundary contains several different jobs.

Question: how much belongs to reconstructing sampled states, scoring them,
rebuilding contexts, decoding full-control checkpoints and verifying the prior
full-control record? Separate these stages together before choosing an exact
optimization. No cache, check removal, optimizer or new learning is proposed here.

## Fixed scope and call inventory

Keep the original complete ordinary/profiled cost-audit repetition 0: all three
reads, 432 profiles, 1152 fixed conditions,three comparison-only reference workers,
original ranges/actions/seeds/member order and current suit/recall implementations.
Observe selected caller-held aliases, leaving their reusable defining functions
and modules unchanged. Module proxies must forward every unrelated attribute.

| Boundary | Parent | Calls per cost read |
| --- | --- | ---: |
| compact_fixed_inputs.replay_sources | whole read | 1 |
| compact_sampled_own.gather | archive root | 1 |
| sampled gather's materialized game_contexts | gather | 1 |
| sampled-state decode, including warm states | gather | 144 |
| sampled-state scores | gather | 108 |
| direct full materialized game_contexts | archive root | 1 |
| direct full-checkpoint decode | archive root | 72 |
| prior full-control verify | archive root | 1 |
| prior full-checkpoint decode | prior verify | 72 |

These are 401 selected calls per original cost read, 802 overall. The first
fictional-software read has no selected root. The new observer's fixed event
budget is 1024 selected calls, chosen from this declared inventory. The preceding
observer's 32-call cap, all 444 preceding scientific source files and every old
result/config stay unchanged. This is a separate observation scope, not an
extension or favorable retry of the previous run. New support/entry/config would
bring the complete source binding to 447 files, preserving old fingerprint
5b966422276208f50fff1fc4ab4126271cb4405f39edbcc7a982329c86829ee9.

Caller holders: compact_opponent_sources.sampled_parent.replay_sources;
compact_fixed_inputs.old_own.gather, old_inputs.game_contexts, files.decode and
prior_full; compact_sampled_own.inputs.game_contexts, decode and scores;
compact_sampled_prior.old.decode. The decode/scores/prior_full function aliases
are imported callers, not their defining-module bindings. Time the materialized
game_contexts return, not creation of the contexts generator.

## Acceptance before formal collection

- Test forwarding, unchanged defining identities, nested three-level clock
  arithmetic, exact typed ordering/counts, ownership, late aliases, cleanup,
  exceptions and partial failures. Reject malformed/nonfinite/boolean metadata,
  missing/duplicate/reparented events and exhausted budgets.
- Retain the corrected startup rule: finite numeric 0<inner allowance<=180 and
  complete child time strictly below it; the actual CLI-startup/publication
  round-trip is covered. The unchanged complete outer 180-second limit remains.
- A source-bound own proof compares the actual archived fictional-software replay
  before/during observation, with zero selected roots. Two separately labeled
  synthetic forwarding reads exercise all 401 ordered calls each. These fixtures
  do not establish real cost-loader coverage or new independent poker mathematics.
- Complete all four immutable local base/relevant-optional roles and both exact-
  head hosted jobs. Verify actual 3.11.17/NumPy2.4.6 and 3.12.15/2.5.4, every uv
  selection and the whole tested checkout tree. Publish all six plus exact tested
  launch/retention/publication/report tools before the formal own proof.
- Use ordinary linked-index metadata access and normal Git status after worktree
  creation; retain independent source/input hashes. Never hide changed files or
  bypass checks to repair the earlier stat-cache problem.
- Read/record the pinned installed OpenSpiel 2.0.2 Apache-2.0 license before fresh
  use. Outputs remain scalar comparison-only, never agent/training inputs.
- Publish every own-proof raw byte and actually verify successful publication
  before fresh reference work. The launcher repeats this preflight inside its
  outer clock and refuses a child after exhaustion. Check actual exit status.

## One complete pair, then interpretation

Caps remain 180 seconds for the complete own proof, 900 per complete child and
1800 shared/outer, with 120 seconds only for failure retention. All startup,
source/license/publication checks, original work, restoration and writes count.
Retain every complete/partial/failing outcome; no shortened work, reseed,
unchanged-source favorable scientific retry or selected checkpoint.

Require complete scalar/computed-replay identity across arms and the previous
unchanged numerical identity ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185.
Pin its published report summary (SHA256 af5bf0fd2dc172704338ed98028fc48b6b6c54b6caddc67afb6ae17691d3399c)
separately from the original 128 unchanged scientific input pins. No reference
strategy is used by this comparison. Original scalar tolerance 1e-9 chips and CPU
roundoff 1e-9 seconds stay fixed.

Require all 802 selected calls, complete PID/thread/event/command clocks, exact
ordered parent relationships and full alias/function restoration. Within each
parent, direct children plus residual must equal inclusive parent CPU. Archive
root plus outside CPU must equal complete-read parent CPU. Do not add a parent
to its children, or sum parallel worker CPU as elapsed time. Report every parent,
leaf, residual and both dependent cost reads; a residual is not a named pure job.

Publish all raw pair bytes and verify them before timing analysis. Reproduce all
numerical exports byte for byte on both actual runtimes with every identified
constructor/replay/scoring/solver path blocked, including new entrypoints and
captured aliases. Require zero forbidden calls, unchanged raw inputs and visual
review of every figure. Then complete all four final local roles and both
same-head hosted jobs before a history-preserving merge and protected-main checks.

Definition of done: the complete checked method, source/proof/raw receipts,
three-level tables/plots, report reproduction and final checks are public in one
coherent PR, with a plain-English journal/work-log account and the next decision.
One ordered diagnostic pair is not stable overhead, a causal speedup, production
costs or playing strength. No new Hold'em trajectory or stronger/default/fresh/
global admission. The 912.54/900-second forecast and 2.390%/1% accuracy failures
remain failed; this step cannot replace their required future gates.

Published prospectively on November 17, 2026, in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6945622230), before implementation or new timing outcomes.

## Implementation and current verification

The observer and runner are implemented in `scripts/parent_archive_support.py`
and `scripts/profile_parent_archive.py`, with the fixed
`configs/parent-archive-cpu.json`. Caller-held aliases are temporary; defining
functions remain untouched. The saved-data reader independently reconstructs the
three-level event tree and reconciles every parent's direct children and residual.
The runner requires the previous complete numerical identity as well as equality
between its new arms. Reports authenticate raw data without reconstructing games.

On November 17, the focused tests pass on actual Python 3.11.17 / NumPy 2.4.6 and
3.12.15 / NumPy 2.5.4: **139 passed, one optional plotting test skipped**, in
24.99 / 23.86 seconds. Ruff and formatting pass; full strict typing passes
816 files. Tests cover the actual archived software replay, synthetic 802-call
trees, exact clock arithmetic, corrupted events, publication and startup-budget
parsing, partial failures, aliases, cleanup and original exception identity.
The skipped plotting check remains required in the upcoming optional roles.

The initial new runner test still expected its predecessor's 14 calls; it caught
the new 802-call result. The assertion was corrected to the published inventory;
the diagnostic design and scientific work were unchanged. Complete source-bound
local/hosted qualification and tested operator publication remain before any
formal own proof or fresh reference comparison. No new measured result exists.
