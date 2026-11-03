# Phase 2: exact toy games and counterfactual regret minimization

Acceptance criteria, declared before solver experiments: own Kuhn and Leduc rules
agree exhaustively with an independent implementation; implement CFR, CFR+,
Linear CFR and Discounted CFR; exact information-set best responses; verify the
Kuhn first-player value -1/18; convergence plots and raw iteration metrics; matched
OpenSpiel checks with conventions and tolerances fixed in versioned config;
quality checks and three interview Q&As. No playing-strength claim follows from
toy-game convergence. Phase 3.5 remains gated after Phase 3 training.

## Rules

Both games have two players, a one-chip ante, zero-sum net chip payoffs, and player
zero acting first each street. Kuhn has three ranks, one private card each, and
one permitted one-chip bet. Check/check closes; bet/call shows down; folding loses
one ante. Leduc has six physical cards (J/J/Q/Q/K/K), one private card per player,
a single public card after the first betting round, and up to two raises/bets per
round, sizes 2 then 4. A pair beats an unpaired hand; otherwise rank wins, with no
suit priority. Default information states distinguish physical copies, matching
OpenSpiel's default `suit_isomorphism=false`. Chance is uniform without replacement.
No free folds, rake, finite-stack all-ins, or no-limit bets appear in these games.

`ToyState` is own immutable game logic. The validation boundary maps Kuhn's
check/fold and bet/call action IDs to the project's fold, check/call, raise labels.
The information key contains own card, public board and complete action history;
never the opponent card. `scripts/validate_toy_games.py` checks every tree history,
legal action, chance probability, actor and payoff, plus a bijection between both
implementations' information sets.

## Independent reference license and boundary

OpenSpiel **2.0.2** is pinned in the optional `solver-validation` extra. The full
[versioned Apache 2.0 license](https://github.com/google-deepmind/open_spiel/blob/v2.0.2/LICENSE)
was read before use. It permits use, modification and distribution, subject to
license/notice preservation and applicable modification attribution; no warranty.
Its source headers attribute the implementation to DeepMind Technologies Limited.
The project uses its installed API for comparison only. No source is copied and
no reference strategy initializes, trains, or enters production strategy lookup.
The native reference wheel does not replace the project's own Python core.

This is the original Phase 2 rule/algorithm check approved in the roadmap. The
additional Phase 3.5 postflop spot and trained-agent comparison is not underway.
Its future license inventory and metrics will be recorded separately at its gate.

Rule sources: the pinned
[Kuhn implementation](https://github.com/google-deepmind/open_spiel/tree/v2.0.2/open_spiel/games/kuhn_poker)
and [Leduc implementation](https://github.com/google-deepmind/open_spiel/tree/v2.0.2/open_spiel/games/leduc_poker).

Implementation and experimental results follow in tested commits; no solver
convergence result is claimed at this initial rules checkpoint.
