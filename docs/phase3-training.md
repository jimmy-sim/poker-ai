# Phase 3: sampled CFR and heads-up Hold'em

Acceptance gate, declared before implementation/training: external- and
outcome-sampling MCCFR with unbiased-update sanity checks on exact toy games;
heads-up fixed-limit before no-limit; hand-strength/expected-strength and
potential-distribution card abstractions with k-means/earth-mover comparisons and
measured information loss; explicit no-limit action abstraction/off-tree mapping;
reproducible checkpoints/resumption, multiprocessing, memory/runtime reports,
and tests. Report training budgets and weaknesses without inferring full-game
exploitability from an abstraction. Finish with three interview Q&As. Do not start
Phase 3.5 until this gate and the trained-agent prerequisite are met.

Phase 2 full-tree exact results are in `phase2-solvers.md`. Larger games cannot
materialize their entire tree in memory. MCCFR samples parts of the tree while
correcting sampling probabilities so regret updates have the intended expectation.
External sampling enumerates the updating player's actions and samples chance and
the opponent. Outcome sampling follows one explored trajectory and uses importance
weights; it is cheaper per pass but can have much higher variance.

Initial step: derive/test sampled updates before Hold'em training. Use explicit
NumPy Generator objects and fixed seed lists; no global RNG. Freeze policies for
each target-player traversal and defer regret writes until it completes. Keep
reference validation outputs out of all strategy/checkpoint inputs. No training
result or full-game strength claim exists at this planning checkpoint.

Primary method reference:
[Lanctot et al., Monte Carlo Sampling for Regret Minimization in Extensive Games](https://mlanctot.info/files/papers/nips09mccfr.pdf).

Compute policy: benchmark small pilots first. Choose bounded local experiments;
flag any proposed run likely to exceed a few hours and offer a cheaper alternative
before launching it. No C++/Rust core without the user's explicit approval.

## Sampled-update math checkpoint

`training/mccfr.py` contains own two-player external/outcome sampling. One iteration
updates player 0 then player 1 with a frozen policy during each pass. External
sampling uses standard simple two-player averaging at opponent nodes; this is not
a general multiplayer averaging implementation. Outcome sampling averages at the
updating player's visited nodes with importance correction. Exploration epsilon
is explicit and must be positive; the initial default is 0.6. No variance-reduction
baseline or clipping of importance weights is used.

For outcome sampling, let q(h) be behavior reach, pi_-i(h) opponent/chance reach,
and pi_i(h) own reach. The backward suffix already includes target/behavior tail
likelihood ratios. Only the sampled action has estimated value `suffix/q(a|h)`;
its strategy-weighted mean estimates the node value. Regret multiplies their
difference by `pi_-i(h)/q(h)`. Average mass is `pi_i(h)*sigma(I,a)/q(h)`. These
formulas require full target-action exploration and can have very high variance.
Chance is sampled on-policy, so its tail likelihood ratio is one.

Tests enumerate all external Kuhn chance/opponent sampling combinations and all
outcome-sampled terminal trajectories. Both uniform and nonuniform strategies
match analytically derived regrets; the nonuniform cases check own-reach exclusion
and behavior-policy importance corrections. Additional tests check exact seed
reproduction and a modest learning improvement over uniform. These checks precede
Hold'em training and do not constitute a trained Phase 3 Hold'em agent.

## Checkpoint contract

Own checkpoints use an explicit JSON format identifier, exact training config,
source metadata, method/exploration settings, counters, accumulated regrets and
average mass, and complete PCG64 state. Writes use a temporary file, fsync and
atomic replacement. No pickle, solver-export converter, or reference strategy
loader is used. The loader requires the own format and matching config and rejects
invalid/nonfinite accumulators. Resumption tests for both methods reproduce all
regrets, average masses, counters and random state bit for bit after split versus
uninterrupted training. This prevents accidental reference artifact loading; it
is not an authenticity guarantee against deliberately forged own-format files.

## Fixed-limit adapter domain

The first Hold'em adapter is heads-up fixed-limit: blinds 1/2, street bet sizes
2/2/4/4, four-bet cap (including the preflop big blind), and player stacks 200/200.
Stacks must exceed the maximum possible capped contribution (48 chips at these
settings). This excludes short-limit-all-in completion/reopening rules rather
than incorrectly applying no-limit rules to them. It is a fully funded capped
limit model; no claim of support for arbitrary short-stack fixed-limit games.

The adapter uses the own engine for all cards, transitions and payouts. A fresh
uniform full deck is sampled per target pass; future cards remain inaccessible
to policy keys. Sharing the sampled chance world across own branches correlates
samples without changing their expectation. Public-only observation-to-key
builders prevent access to opponent holes, burns and remaining deck. The exact
initial key retains own cards and complete public action history. Card abstraction
and no-limit action abstraction are separate subsequent steps.

## Recorded compute pilot (partial Phase 3)

`make train-mccfr-pilot` runs the committed config with three independent seeds
per method/game and two spawned workers. Each worker trains its own table; there
are no shared asynchronous regret updates. Reports: [JSON](../results/mccfr-pilot.json)
and [CSV](../results/mccfr-pilot.csv). Clean source: `16c8554`.

| Game | Method | Iterations per seed | Exact exploitability range | Training seconds range | Maximum traced peak MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| kuhn | external | 10,000 | 0.00466966–0.00635913 | 3.408–3.700 | 0.449 |
| kuhn | outcome | 10,000 | 0.0127924–0.0380382 | 3.197–3.265 | 0.019 |
| leduc | external | 10,000 | 0.288315–0.300673 | 11.562–13.624 | 1.363 |
| leduc | outcome | 10,000 | 1.14782–1.18485 | 5.343–5.640 | 0.896 |
| limit | external | 100 | not measured | 4.007–4.208 | 8.643 |
| limit | outcome | 100 | not measured | 0.242–0.249 | 0.547 |

Exploitability uses the same ante-chip convention as Phase 2 for Kuhn/Leduc.
Ranges describe these three seeds, not confidence intervals. Outcome sampling is
cheaper per pass here but converges less at this iteration budget; no universal
algorithm ranking follows. Leduc outcome tables still missed up to 26 of 936
information sets; evaluation used uniform actions at unseen sets. Every pilot gate
passed, but the limits were modest smoke targets, not a solved-game criterion.

Total elapsed time was 43.88 seconds. Tracemalloc measures allocations during
training, not entire-process RSS, and adds overhead. Worker timings include
concurrent execution; they are not isolated throughput benchmarks. The raw report
records environment, worker count, thread settings, counters and checkpoint sizes.

Fixed-limit external runs created 10,953–11,248 information sets after only 100
iterations; outcome runs created 801–876. Exact-card tables have sparse coverage.
These checkpoints demonstrate training/resumption infrastructure, not a useful
Hold'em strategy, a win rate, or full-game exploitability. Card abstraction and
no-limit action abstraction remain to be implemented before the Phase 3 gate.

Own checkpoints are retained under `results/runs/mccfr-pilot-checkpoints/` (ignored
large artifacts); JSON/CSV record each path, byte size and SHA256. The command
recreates them. They contain only own sampled training state. No reference solver
artifacts are inputs. Existing resume tests verify the two methods bit for bit.

Current fast gate: 353 tests, lint and strict types. Phase 3 is ongoing; the later
external postflop solver milestone has not begun.
