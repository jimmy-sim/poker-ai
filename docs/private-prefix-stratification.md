# Private-deal stratification: prospective test

November 10, 2026. Issue #4. This document and its versioned
[configuration](../configs/private-prefix-stratification.json) precede the new
algorithm implementation and all new measurements. They do not admit training.
The matched-update study is complete; the default learner remains unchanged.

## Question and method

Can spreading a frozen batch over private-deal probability bins improve the
known-game learning result at fixed work? The earlier matched-update results
do not isolate a pure variance cause. This is a new candidate, with its own
correctness, software, time and scientific gates.

The finite spot engine first samples seat 0's hand, then seat 1's compatible
hand. These are **two chance nodes**, followed by public-card chance and betting.
Flatten those first two levels in original edge order. Each joint outcome gets
its marginal times conditional probability. Do not sort by strength or EV.
Reject a tree with a decision/terminal node before the two-level prefix ends,
invalid probabilities, or an empty legal prefix. Zero-probability edges remain
legal in the plan but cannot be selected.

For each target-player pass and batch size B, traverse one sample from each of
B equal-probability bins of this joint distribution. Before trajectory i, draw
one independent U from the explicit generator and use u=(i+U)/B. Invert the joint
CDF; force the corresponding first two chance choices. Validate each forced
selector call against the planned node's probability vector. Require both
choices to be consumed; all later chance/opponent choices use the original
generator's categorical choice. The tree walk still charges both chance nodes.
Sampling occurs in stratum order, without random permutations or outcome-based
selection. Floating boundary handling must keep u inside its declared half-open
stratum, including a generator value immediately below one.

After each frozen target pass, sum the original sparse raw increments in
encounter order, divide once by B, and use the original updater. Clipping occurs
after the mean. Target 1 observes target 0's update, as before. The warm start,
linear time weights and separate uniform/linear average books stay unchanged.
B1 delegates the original implementation exactly, without imposing a two-level
tree requirement. The optional B4/B16 learner must not replace existing defaults.

**Illustration, not a result:** with four equally probable private deals and
B4, each frozen pass sees each private deal once. River and opponent decisions
still vary. This does not enumerate the full game or remove all sampling noise.

## Mathematical check and its limits

For a fixed policy and one component Y of the raw update, write m_i and v_i for
its mean and variance conditional on probability bin i. Independent downstream
randomness gives E[mean]=sum(m_i)/B and Var(mean)=sum(v_i)/B². An IID batch with
the same joint distribution has that variance plus Var(m_i)/B. This is a
component-wise statement about raw regrets/average increments before clipping
or normalization. It assumes ideal independent uniform random variables and
valid normalized finite probabilities; finite precision must be tested.

The proportional-allocation identity is described in
[Owen, Monte Carlo chapter 8, section 8.4](https://artowen.su.domains/mc/Ch-var-basic.pdf).
Its application to the fixed-policy external-sampling raw update here is our
derivation to test, not a claim about this adaptive learner's convergence.
[Lanctot et al., MCCFR](https://proceedings.neurips.cc/paper/2009/file/00411460f7c92d2124a67ea0f4cb5f85-Paper.pdf)
provides the original external-sampling context. No implementation is copied.

The new sampler uses one joint uniform instead of two factorized draws and
changes RNG consumption, dependence and generation cost. Same-seed trajectories
are not coupled to the old ones. Smaller raw variance would not establish better
adaptive learning, faster convergence, or stronger play at equal work.

## Correctness before poker

- Independently enumerate rational nonuniform joint probabilities and bins;
  verify unbiased means and covariance/variance for a fixed policy. Include
  zero probabilities, unequal conditional menus, exact CDF boundaries and values
  immediately below one. Test invalid trees/probabilities and booleans as sizes.
- Use an independent dense finite updater and independently written joint-CDF
  selector to check adaptive endpoints, target ordering, clipped/signed regrets,
  both books, warm origin, counters and RNG states. Check B1 bit identity against
  the old implementation on ordinary one-chance and factorized games.
- Test clipping after the batch mean, not before. Charge every visited node,
  initialization, sampling/selector setup and archive/report work. An observer
  must not mutate policies, books, RNG, counters or a cached prefix plan, even
  on its last callback. Reconstruct and bind immutable plans during replay.
- Keep information keys and owned observations unchanged. Private chance draws
  select simulated worlds; they must not expose opponent cards or future cards
  to the decision policy. No reference strategy is a feature or training input.
- Before real trajectories, complete the runner/archive/replay, grid/schema,
  missing/duplicate rows, worker/IO/deadline/partial-failure retention and source
  tests. Run relevant base/optional checks and both source-bound hosted CI jobs.

The full tiny proof uses a deliberately factorized, nonuniform Kuhn deal with
two initial chance levels. It covers the complete new output shape:432 profiles,
288 ledgers and1,152 final fixed conditions. Repeated logical contexts are
labeled as duplicates, not independent poker games. It is not standard Kuhn's
-1/18 value test. Own publication, independent comparison and final replay share
one180-second allowance. Passing it admits only the subsequent short forecast.

## Complete comparison and gates

The same two known turn spots, exact/q8 encodings, signed/clipped rules and all
three original seeds define24 contexts. Only B4/B16 change:48 new paths. Observe
all three original work labels and current/uniform/linear readouts:432 new
profiles and288 raw average books. Compare each against both its original IID
batch counterpart and B1 at that work label:864 self contrasts. At the final
label, retain the original four own full-control opponents in both seats:
1,152 new fixed targets and2,304 paired contrasts. Baseline policies are reused
and remain dependent; they are not newly trained or independent replicates.

Before long training, measure three repeats of **all48** changed100k prefixes,
including setup/exact warm start and repeated-state checks:144 timing rows.
Use each path's worst repeat and the original three fixed worker partitions.
Let T be the maximum partition sum of setup+warm plus extrapolated incremental
cost to10m. The unchanged conservative formula is **2*(2*T+600)<7200**.
Within the900-second own profiling cap, also run the complete old-policy
432/288/1152 IO/replay/scoring/report workload below600 seconds. Publish own
evidence before the independent old-policy audit. Its complete command must
satisfy both900 seconds and the stricter forecast **2*complete<900**.

Source/config/input identities, required local/hosted checks, full tiny proof,
whole stage clocks, complete forecast and native checks must bind a published
checked admission. Recompute that admission from published bytes without
constructing a learner or reference. Only then can a new real trajectory study
start. Its complete own cap stays7200 seconds and native cap900; all setup,
capture, replay, scoring, archive and report work counts. Native construction
follows own publication. Keep all partial/failing outcomes; never substitute a
favorable retry with unchanged source or shrink the grid to pass a cap.

The primary remains q8/B4/signed/linear; B16 is a dose control, exact a control,
and every clipped/current/uniform result remains visible. Report the historical
known-game1% median/2.5% worst exploitability and95% coverage limits without
changing them. This diagnostic cannot select a default, and a failed primary
cannot be rescued by choosing a secondary result. Any future default/fresh/global
admission needs its own prospective protocol. Never change seeds, gates or caps
to fit the clock. Start a long stage only when its full caps plus safe
verification fit the current authorized window.

OpenSpiel2.0.2 remains comparison-only under the pinned Apache-2.0 license
already recorded in the parent protocol. Re-read/verify the pinned installed
license before using it for this new stage; record the bytes and version in
the new evidence. Never export its strategies or load outputs into the agent.

## Reporting and next decision

Retain every seed, work/update/overshoot/traversal count, raw mass and support
measure; separate warm-only coverage from post-warm coverage. Report all self
components and fixed-opponent results in chips and percent initial pot, paired
with both unchanged baselines. Means/ranges describe these dependent cases;
three fixed seeds do not justify a population confidence claim.

For each milestone record the question, change, actual checks, outcome, limits
and next decision in the work log and plain-English journal. This is AI-assisted
research, with human practice/time recorded only when the user reports it. A
software milestone may finish without a real training admission. Results are
currently absent. The first decision is whether independent correctness supports
the new sampler; strength and runtime remain unmeasured.
