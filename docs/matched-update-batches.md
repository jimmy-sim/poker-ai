# Matched-update batch comparison — prospective November 9

Issue #4's equal-node-work batch comparison changes how often a policy is
updated. The next diagnosis adds the other axis: compare after the same number
of complete policy updates, while honestly reporting different node work.
This plan follows the known results; it does not pretend those results were blind.

For all24 contexts (two games x two encodings x two regret rules x three seeds),
take BOTH B4/B16 final10m recorded iteration counts:48 targets. No strength
metric selects a target. Replay each original B1 path and capture current and
uniform/linear averages at those exact complete-update counts:144 new profiles.
Reuse all144 batched endpoints and their1,152 fixed-opponent target scores.
Compute all1,152 new B1-prefix fixed targets against the same four original
finite full controls and two seats. Report every144 matched-update self pair
and1,152 fixed-target contrasts, alongside the already measured equal-work view.

The target may not exceed the original B1 endpoint; reject rather than extend
its historical10m budget. Verify all original B1 state/policy/work/iteration
fingerprints at100k/1m/10m, both ledgers (144 readout checks). Preserve originals.
A new observer combines exact iteration targets with first complete work
crossings. It observes only after a full target0+target1 iteration; a guard
rejects callback mutations to RNG, regrets, ledgers, keys, counters or policies.

A matched-update improvement would spend more work in the larger batch. Equal
work and equal updates answer different compute questions. Neither identifies a
pure-variance causal effect or establishes fresh/global strength. All readouts
share trajectories; three seeds do not provide population confidence intervals.
No policy/default selection or relaxation of prior failed gates follows.

## Bounded milestone and later gates

This PR implements only a source-bound prospective grid/manifest validator and
mixed-coordinate observer, with independent analytic/tiny-game correctness,
mutation/failure checks and actual source metadata coverage. It does not replay
Holdem training, compute a new strength score or admit a long run.

The later full runner needs serialization/replay/partial-grid/barrier/reference
integration, complete local base/optional suites and both source-bound hosted CI
jobs. Publish a source-bound tiny proof and new complete fixed conservative
forecast before checked admission. Three repeats cover all24 B1 contexts and
explicit added observation/scoring/archive/fixed-target costs. Preserve the
original max-per-path formula and strict7200 guard; do not use favorable repeats.
Own7200/native900 caps include all required stage work. Publish all own outcomes
before comparison-only OpenSpiel2.0.2 Apache2 scalar/reply checks. Preserve every
partial/failure; no reference strategy/training data or commercial outputs.

The full caps plus verification do not fit the remaining one-time November9
window. Stop tonight at verified software/protocol groundwork; do not shorten
caps, run a subset as the study, claim admission or schedule another work window.

## Foundation implementation and checked scope

The new observer leaves the existing trainer unchanged. It combines iteration
labels and first complete work crossings in one callback, checks the same
complete state guard before/after, and checks the deadline after the last
callback as well. The common exact warm start counts as iteration1. The same
seed does not couple per-update random draws when batch sizes consume different
numbers of samples.

Twenty-eight observer tests pass: six independently uninterrupted tiny-game
trajectories (B1/B4/B16 x signed/clipped), all16iteration endpoints, original
work-observer identity, both ledgers/current/RNG/work equality, simultaneous
coordinates and warm crossings, invalid labels, mutation, final-callback
deadline and interrupted capture. Twenty-two grid tests cover a complete explicit
metadata fixture, omitted/duplicate sources, wrong coordinates, mismatched
readouts, forbidden budget extension, changed fixed opponents/seats/config and
the complete actual archived-source manifest. Fixture values are not poker
results. All50 focused checks pass on each base runtime1.13/1.12s.

The actual manifest validates all nine original source hashes and complete
published480-profile and216+1728target audit receipts without constructing a
learner or reference. It reads no strength metric to select targets. There are
24contexts,48logical iteration targets,144new profile identities and144reused
endpoint identities. A target is an assigned context/batch comparison, not an
independent statistical observation. Equal numeric targets, if any, would share
one underlying prefix and must not be counted as independent training.

Ruff/format547 and strict450 pass. Complete base/optional suites and hosted CI
are running. No actual Holdem replay, new score, source-bound full-runner proof,
new compute forecast or long admission exists. The earlier failed study gates
and ordinary agent default are unchanged.

## Terminal checks after merge

```sh
.venv/bin/python scripts/check_matched_update_grid.py
.venv/bin/python -m pytest -q tests/test_coordinate_observer.py tests/test_matched_update_grid.py
```

The first command prints24contexts/48targets/144pairs and explicitly says no
training or strength scores/admission. The second runs tiny-game/metadata tests,
not a new Holdem experiment. Optional `--output` writes a new manifest path and
refuses to overwrite an existing file. A future runner must still implement the
complete archive/replay/partial-failure/reference/software/forecast gates.

## Three questions to explain the design

**Is matching updates fairer than matching work?** It answers another question.
Larger batches use more samples per update, so equal updates gives them more
compute. Report both axes and actual work instead of choosing whichever favors
one method. Neither alone establishes a pure variance effect.

**Why use existing endpoint iteration counts?** They give a complete metadata-
defined target for every game/encoding/rule/seed and both larger batches. No
best score or favorable seed selects a target, and B1 never extends its old
endpoint to meet one. This is a prospective follow-up to known results, not a
blind rediscovery.

**What does the observer proof establish?** Observation preserves the tested
learning trajectory and records complete update boundaries. It does not prove
the future poker runner, convergence, playing strength or a compute admission.
Those remain separate gates.
