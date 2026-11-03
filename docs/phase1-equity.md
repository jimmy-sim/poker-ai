# Phase 1 — Heads-up equity

Equity is expected showdown pot share: win=1, tie=1/2, loss=0. It conditions on
hero's two cards, an optional fixed opponent hand, a zero-to-five-card board, and
known dead cards. None as opponent means a uniform distribution over legal
opponent combinations after card removal. Weighted ranges and multiway equity
are outside this initial interface; the eventual game engine still supports the
approved multiway seat range.

## Exact enumeration and compute budget

`equity_state_count` computes the work before traversal. A fixed opponent needs
C(n, missing_board) completions. An unknown opponent needs
C(n,2)*C(n-2,missing_board) equally weighted joint states. The first factor chooses
the opponent's unordered cards; the second chooses a completion from the remaining
cards. This models card removal between opponent hands and board runouts.

`exact_equity` rejects states above an explicit budget (default two million).
Uniform-opponent preflop enumeration exceeds that default by orders of magnitude;
use Monte Carlo or a tractable later-street case rather than launching it during
routine work. Raising max_states is an explicit caller decision. All public input
boundaries reject duplicate/invalid cards and incompatible hand sizes.

## Monte Carlo and uncertainty

`monte_carlo_equity` requires a caller-owned NumPy Generator and a fixed positive
sample count. Draw without replacement within each deal; repeat independent deals
with replacement across trials. With an unknown opponent, the first two sampled
cards form its hand and the rest complete the board. Each unordered joint state
has the same permutation multiplicity, matching the exact distribution.

For outcomes Xi in {0,1/2,1}, mean equity is (wins + ties/2)/n. The descriptive
outcome variance is E[X^2]-mean^2, with E[X^2]=(wins+ties/4)/n. Exact enumeration
returns population outcome variance. Monte Carlo standard error uses the unbiased
sample variance divided by n; n=1 has no estimated standard error.

The confidence interval inverts the two-sided Hoeffding bound:

```text
P(|sample_mean - true_mean| >= epsilon) <= 2 exp(-2 n epsilon^2)
epsilon = sqrt(log(2 / alpha) / (2 n))
```

Intersect the resulting interval with [0,1]. It is conservative, fixed-horizon,
and valid for bounded independent payoff draws, including fractional ties. It is
not an anytime stopping rule. A zero empirical standard error at all-win/all-loss
samples still has a positive-width interval. Exact results have no sampling
confidence interval or Monte Carlo standard error.

Source: Wassily Hoeffding, [Probability Inequalities for Sums of Bounded Random
Variables](https://doi.org/10.1080/01621459.1963.10500830), 1963, Theorem 2.
[Original paper copy](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf).
The displayed two-sided interval applies the bound to both tails for payoffs in
[0,1]. Confidence statements assume independent fixed-budget Monte Carlo draws;
state conditioning and range assumptions remain part of the model.

## Validation protocol

Tests cover known exact outcomes, symmetry under swapping fixed hands, ties,
card removal, RNG replay, confidence boundaries, standard error, and budget guards.
The implementation calls only the project's evaluator.

`scripts/validate_equity.py` separately builds legal decks and enumerates outcomes
using optional Treys. Exact win/tie/loss counts must match for every configured
case. Each declared Monte Carlo interval must contain that case's exact equity.
The predeclared matrix covers a locked royal-flush board, a one-out turn, a flopped
royal, a nontrivial flop, and a uniform-opponent turn. It caps exact work at 100,000
states per case and uses 50,000 Monte Carlo draws per case, with explicit PCG64
seeds. Per-case confidence is 99%; for five fixed cases the union bound gives at
least 95% simultaneous coverage under the sampling assumptions.

Reproduce with `make validate-equity` after installing the documented uv version.
The command uses only the optional validation extra and saves counts, intervals,
seeds, source hashes, revision/dirty state, environment, and runtime.

## Local status

All 300 tests, lint, formatting, and strict typing pass locally on Python 3.11
and 3.12. The equity tests were added first and initially failed because the module
did not exist. Independent results will be added after a run from committed
source. No strategic-strength claim is implied by an equity estimate.

## Observed independent results

All declared cases passed from clean source revision `22867401ee245a97a4d7e61601e42b4a280e07f5`.
Exact counts equal Treys, and all five predeclared 99% Monte Carlo intervals contain
the corresponding exact equity. These are conditional showdown checks, not agent
win rates. The [raw report](../results/equity-validation.json) retains counts,
seeds, intervals, errors, source hashes, environment, and timing.

| Case | Exact states | Exact equity | MC equity | Absolute MC error |
| --- | ---: | ---: | ---: | ---: |
| board_royal_tie | 1 | 0.500000 | 0.500000 | 0.000000 |
| turn_one_losing_out | 44 | 0.977273 | 0.977620 | 0.000347 |
| flopped_royal | 990 | 1.000000 | 1.000000 | 0.000000 |
| flop_pair_vs_overcards | 990 | 0.604040 | 0.605840 | 0.001800 |
| turn_uniform_opponent | 45,540 | 0.864405 | 0.865300 | 0.000895 |

## Interview questions

1. **How do ties enter equity?** A heads-up tie contributes half a pot share;
   treating ties as wins or dropping them biases the estimate.
2. **What is the difference between outcome variance and estimation uncertainty?**
   Deals can vary even when exact equity is known. Monte Carlo estimates introduce
   additional sampling uncertainty that shrinks with the sample count.
3. **Why use a conservative bounded interval?** Fractional tie payoffs are not
   Bernoulli observations, and a zero sample variance at boundaries can be
   misleading. Hoeffding uses the known payoff range without a normal approximation.

Next: complete the Texas Hold'em state machine, legal betting, side pots,
showdown settlement, player observations, and property/reference validation.
