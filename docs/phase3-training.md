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
