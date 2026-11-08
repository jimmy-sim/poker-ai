# Learning journal: building the poker project

Start here if the other project documents feel too technical. This guide follows
the order in which the project was built and explains why each part exists.
Examples marked **Example** are made up to explain an idea. Recorded results link
to the reports that support them.

The first version was compiled on November 4, 2026, looking back over the work
already completed. Codex assisted with implementation and drafting. The personal
notes section is for your own questions and explanations as you work through it.

## Where the project stands

We have a working poker simulator, learning algorithms, and tools for checking
their results. The project has found useful bugs and measured weaknesses. It has
not established a competitive Hold'em agent.

Here, “AI” mainly refers to algorithms that learn probabilities for poker actions
and store them in strategy tables. The chapters below explain how that works.

The earlier study, issue #3, tested the retained ordinary learning procedure on
four newly selected small games. All four met the rules fixed before their
outcomes were measured. This is progress in validating the method; each game
received its own training. The earlier river-integration result remains mixed,
and the ordinary default stays in place.

On November 6, issue #4 adds tested, optional ways to describe the public board.
One removes arbitrary suit names; another groups boards by coarse features.
The completed fixed-work comparison found that texture saves many strategy rows
but loses too much accuracy on the deeper game. Its preset gate fails, so no
global-agent default changes. You can inspect features with the terminal command
in step 15 and read the result in step 16.

The follow-up finds concrete decisions the old representation merges and tests
one category-based replacement. It also fails the deeper-game accuracy limit.
Step 17 explains the example, result and why the larger run stops there.
Step 18 completes a best-response diagnosis: the saved candidate is nearly
stable within its compressed game but remains vulnerable to exact information.
Step 19 finds missing relative-strength, blocker and action-conditioned range
distinctions. It completes a diagnosis, without training a replacement.
Step 20 defines the next candidate and its tests. Step 21 finds a measured
improvement: range masses pass the full-control gate on both known games.
Step 22 completes the sampled comparison: the new description improves on
category but fails the deeper-game accuracy limits. Step 23 diagnoses the saved
failure: most of its exploitable value appears when an opponent can use finer
information. That value depends on the saved strategies; it is not a fixed floor.
Step 24 swaps fixed turn/river policies and finds that the saved river continuation
accounts for most of the deeper-game gap change, with interaction between streets.
Step 25 separates the training rules and checks a shared updater before the next
learning comparison. It does not yet identify the cause of the river weakness.
Step 26 checks the compute cost before the larger controlled learning study.
Step 27 tests an opt-in policy-row cache against the frozen trainer and profiles
it again without changing the learning rules.
Step 28 tests an immutable game-node cache against every original node/edge,
then checks exact training trajectories before profiling again.
Step 29 measures independent cells across CPU processes, including startup and
resource costs, without changing a cell's learning rules.
Step 30 verifies checkpoint/scoring behavior and measures the still-missing
pipeline costs on old saved policies.
Step 31 completes the original controlled learning comparison: 140 runs and 840
checkpoints, with zero own replay error and independent native checks. Clipping
and averaging interact; improving one gap can worsen another. This diagnoses
training differences without selecting a replacement or passing a fresh-game gate.
No remedy, default change or fresh/global admission follows automatically.

You can read this in three sittings:

- **Steps 1–5:** How the program represents cards and runs a legal hand.
- **Steps 6–9:** How it learns decisions and how we judge those decisions.
- **Steps 10–31:** What the extensions and recent experiments taught us.

The [work log](work-log.md) has dates and commits. This journal explains the
ideas. Some older reports say hosted CI had not run: that describes their original
checkpoint. The repository now has [hosted checks](https://github.com/jimmy-sim/poker-ai/actions).

## 1. Make the work repeatable

Before teaching an agent poker, we needed a way to tell whether a code change
broke something. The project has automated tests, checks for common coding
mistakes, and a file called `uv.lock` that records dependency versions.

A **test** runs a particular check. **CI**, short for continuous integration,
runs the project checks on GitHub when we submit changes. A **commit** saves a
version of the files. A **pull request**, or PR, groups changes so their purpose
and checks can be inspected before they enter the main branch.

**Example:** A change accidentally allows the same ace to appear twice in a
deck. A test should fail immediately, before we spend time training on impossible
hands.

A green test run means the checks passed. Whether the agent plays well needs a
different kind of evidence. We keep those two questions separate throughout the
project.

Read more: [setup verification](phase0-verification.md).

## 2. Give every card an unambiguous identity

The first poker component represents the 52 cards with numbers. It also keeps
track of which cards are present, which have been dealt, and which remain.

A **bitmask** is a compact set of yes/no flags. Here, each flag corresponds to a
card. It makes questions such as “Are these two hands sharing an impossible
duplicate card?” easy to check. A deck also needs an order: a set of cards alone
does not say which card comes next.

**Example:** If a player holds the ace of spades, that card must be removed
before choosing an opponent's cards or dealing the board.

The deck is **immutable**: dealing creates a new remaining deck instead of
silently changing the old one. Keeping the original state makes replaying a hand
and finding a bug easier. Tests check card identities, duplicates, dealing, and
repeatable shuffles.

The lesson is basic but important: every later calculation assumes the cards
describe a possible deal.

Read more: [cards and decks](phase1-cards.md).

## 3. Decide which hand wins

The **hand evaluator** takes cards and ranks the resulting poker hand. It must
recognize categories, break ties using the right remaining cards, and handle
special cases such as an ace-low straight.

**Example:** Two players can both have a pair of kings. The evaluator must then
compare their other cards, called **kickers**, in order. Calling both hands “one
pair” is not enough to settle the pot.

Hold'em makes seven cards available at showdown: two private cards and five
board cards. We kept a simple approach that checks every five-card selection;
there are 21 selections from seven cards. It gives us a readable reference when
checking a faster implementation.

The recorded validation checked all **2,598,960 five-card hands** against Treys,
an independent poker library. A further **2,000,000 sampled six/seven-card hands**
also had no disagreements. The sampled checks are extensive, but do not cover
every possible seven-card hand.

This gives confidence in hand ranking. It does not teach the agent when to bet.

Read more: [five-card ranking](phase1-five-card.md),
[best five from six/seven](phase1-best-five.md), and
[verification evidence](phase1-verification.md).

## 4. Estimate a hand's share of the pot

**Equity** is the expected share of the pot at showdown under the specified card
assumptions. A win counts as one share, a two-way tie as half, and a loss as zero.

**Example:** In 100 equally likely outcomes, suppose a hand wins 50, ties 20,
and loses 30. Its equity is `(50 + 20/2) / 100 = 60%`.

We can calculate equity by checking every legal outcome when the remaining
problem is small. For larger problems, **Monte Carlo** estimates it from random
legal deals. A **seed** lets us repeat the same random sequence while debugging.
Repeating a seeded run does not make the estimate exact.

The equity code was checked against independent card calculations and cases
where the answer can be calculated exactly. Sampled estimates also report
uncertainty: another sample could give a somewhat different answer.

Equity alone does not tell us whether a bet is profitable. That also depends on
the price, folds, future decisions, and what hands the opponent may hold.

Read more: [equity methods and checks](phase1-equity.md).

## 5. Run a legal poker hand

The **engine** manages the rules: whose turn it is, legal bets, stacks, betting
rounds, folds, all-ins, and payouts. The evaluator settles hand strength; the
engine decides who is entitled to which chips.
The engine supports two to six seats; the research agents initially play heads-up,
meaning one player against one opponent.

**Example:** Three players contribute 20, 50, and 50 chips and all reach showdown.
The main pot contains 60 chips, which all three can win. The remaining 60 chips
form a side pot for the two players who contributed 50. The short-stack player
cannot win that side pot.

We check rules with ordinary examples and **property tests**. A property test
tries many generated cases against a rule that should always hold, such as “chips
are conserved.” Independent PokerKit comparisons also checked recorded action
traces and payouts, with differences in rule conventions documented.

An engine mistake can make a poor strategy look strong. That is why the project
checked mechanics before interpreting training results.

Read more: [engine contract](phase1-engine.md) and
[fundamentals verification](phase1-verification.md).

## 6. Learn decisions in tiny poker games first

Full Hold'em is too large to be a convenient first test of a learning algorithm.
We started with **Kuhn** and **Leduc**, small poker games with hidden cards and
betting decisions. Their size lets us inspect the complete game.

A **strategy**, also called a policy, assigns probabilities to legal actions.
It can mix actions rather than always taking the same one. An **information set**
groups situations that look identical to the player making the decision. The
player knows their own cards and the public action history, but not the opponent's
private card.

The learning method is **counterfactual regret minimization**, or **CFR**. It
compares the value of possible actions with the value of the current strategy,
then gives more weight to actions with positive accumulated regret.

**Example:** In an illustrative calculation, betting has value +3 chips while
the current mix has value +1. The advantage of betting is +2. The actual algorithm
weights such comparisons by how chance and the opponent can reach the decision;
it does not simply count how many times a bet happened to win.

We implemented several CFR variants and compared them with OpenSpiel on the same
small games. We report the **average strategy** built during training because
the latest strategy can fluctuate.

We also calculate **exploitability**: a measure of the strategy's remaining
weakness against opponents specifically chosen to punish it. The reported
two-player convention averages the two players' best-response gains. Lower is
better; zero means equilibrium in the specified game. Those opponents must still
respect hidden information.

The lesson: agreement in a tiny game checks the algorithm. It does not establish
full Hold'em skill.

Read more: [toy games and solvers](phase2-solvers.md).

## 7. Make learning affordable in Hold'em

A **game tree** describes possible cards, actions, and later outcomes. Traversing
every branch of a full Hold'em game is too expensive for this project.

We use **sampling** to examine part of the tree at a time. In external-sampling
Monte Carlo CFR, chance and opponent actions are sampled while the updating
player's actions are examined. The probability weighting matters: a shortcut
must still estimate the intended update correctly.

We also use **abstraction**, which groups situations to reduce the number of
decisions the program must store. Card **buckets** group hands with similar
features. An action abstraction limits the available bet sizes.

**Example:** A training game might offer check, a pot-sized bet, and all-in.
A real opponent's half-pot bet then creates a situation outside that menu.
Mapping it back to the training game is an approximation, and an unseen strategy
entry may require a fallback action distribution.

The project added saved **checkpoints**, including the random generator's state,
so a training run can continue from where it stopped. Tests check that resumed
updates match an uninterrupted run. The initial Hold'em runs were bounded and
had sparse strategy coverage: a working training system still needed strength
testing.

Read more: [sampled training and its limits](phase3-verification.md).

## 8. Compare with an independent solver

We needed a check beyond our own code reporting a good score. An independent
**solver** computes a strategy for a fully specified game. OpenSpiel supplies
the project's open-source reference calculations.

A **spot** is a particular poker situation. To compare fairly, we specify the
board, pot, stacks, positions, possible private hands, and allowed actions.
A player's **range** lists the private hands considered possible, with weights.

**Example:** Comparing a learner allowed only pot-sized bets with a solver
allowed many bet sizes would mix two questions: how well each learned and how
much the extra actions helped.

The project compared five restricted turn spots. The trained prototype had
higher exploitability than the reference in all five. Strategy action gaps and
values against common opponents exposed weaknesses that toy-game checks could
not reveal.

The reference is used for comparison only. Its strategies do not teach or
initialize our agent. The native solver is independent, but it reads our exported
game rules; an error in those shared rules could affect both sides. Earlier
engine and evaluator checks therefore still matter.

Read more: [external validation results](phase3.5-verification.md).

## 9. Play matches without mistaking luck for skill

Actual matches ask a different question from exploitability: how does the agent
perform against these particular opponents? We tested simple opponents that
choose randomly, call, raise, play a tight/aggressive style, or use equity rules.

Poker outcomes are noisy because the cards matter. In **duplicate matches**, we
reuse a deal with the seats exchanged to reduce the influence of which player
received the better cards. Those reused deals are related observations.

**Example:** Replaying one lucky deck in several matchups does not create several
independent pieces of evidence. That is why the local study's 36,000 hands were
analyzed using 1,000 independent deck groups for each comparison.

A **point estimate** is the measured average. A **confidence interval** expresses
sampling uncertainty under stated assumptions. We also declared a rule for
judging positive advantages across several opponents before looking at results.
No positive advantage passed that rule. Unfavorable results against the
tight/aggressive and equity opponents stayed in the report.

A separate, small public Slumbot pilot also ran. Its loss and wide uncertainty
remain recorded. The server's hidden deal seeds mean we can replay the records,
but cannot recreate identical live deals.

The lesson: beating an easy opponent in a sample, or getting a positive average,
is insufficient evidence of a winning agent.

Read more: [match evaluation](phase4-verification.md).

## 10. Learn something about an opponent

You selected **Bayesian opponent modeling** as one extension. It starts with
possible opponent types and updates their probabilities as actions are observed.
The starting beliefs are the **prior**; the updated beliefs are the **posterior**.

**Example:** Suppose the model considers both a frequent caller and a selective
caller possible. Repeated calls may shift belief toward the frequent-caller type,
depending on how likely those calls are under each model. One call does not prove
which type is present.

Our experiments use simulated opponents in the small games. The learner uses
permitted observations and accounts for cards it cannot see. Prediction improves
for some fixed opponent types included in the model, but can worsen when the
model misses the opponent's behavior or the opponent changes strategy.

The prediction plots use **negative log-likelihood**, abbreviated **NLL**. It
penalizes a model for assigning a low probability to an action that actually
occurred. Lower NLL means better prediction; when the graph plots NLL
*improvement*, a positive value means the model improved over the comparison.

The project also tests a **guarded response**: exploiting a modeled weakness while
limiting how much worst-case value can be lost relative to a starting strategy,
called the **blueprint**. That bound was checked in the exact small games.
The security-degradation plots show how much this worst-case value changes;
the budget line marks the permitted loss. Their units are small-game ante chips,
not a measured Hold'em win rate.

Better prediction does not automatically mean a stronger Hold'em player. Some
measured gains already come from prior beliefs, so they cannot all be credited to
learning from new observations.

Read more: [opponent-model methods](phase5-extensions.md) and
[extension checks](phase5-verification.md).

## 11. Study risk separately from strategy strength

The other extension was **bankroll and risk analysis**. Even a favorable average
return can come with deep losses along the way. A **drawdown** measures a fall
from a previous peak; it is different from going broke.

The **Kelly criterion** chooses a stake fraction to maximize expected long-run
logarithmic growth under a specified probability and payoff model.

**Example:** In a hypothetical independent, even-money binary bet with a known
55% win probability, the full-Kelly fraction is 10% of current wealth. That
calculation is specific to those assumptions. It is not a poker staking rule or
a recommendation to risk that amount.

We varied assumed edges, stake sizes, and dependence between outcomes. When bad
outcomes cluster together, paths can look much worse than an independent model
suggests. The plots show results conditional on each model, not a forecast of
what our agent will earn.

The follow-up used the agent's measured match returns. All five conservative
sizing calculations that accounted for uncertainty selected a zero fraction
before fees. The data did not establish a positive edge to size confidently.
Resampling those same returns creates more simulated paths, not new independent
evidence of skill.

This explains why a fitted-return model can show a positive preferred stake while
the more conservative calculation shows zero: the first treats the fitted model
as given, while the second also accounts for uncertainty in the estimated edge.

Read more: [risk experiments and assumptions](phase5-extensions.md).

## 12. Find out what prevents better Hold'em learning

The earlier results suggested looking inside the learner instead of just running
it longer. We compared small turn-to-river games using exact card information
and different ways of grouping cards.

One problem was **public-board aliasing**: the representation could merge
different public boards into the same stored decision. That can discard
information the player is actually allowed to use.

**Example:** A board showing three spades can change decisions compared with a
board showing three different suits. A representation needs to preserve relevant
public information while continuing to hide the opponent's cards and cards that
have not yet been revealed.

Keeping the public board helped the medium-stack diagnostic games. But in those
games it also made the stored representation as detailed as exact cards. That
small-game improvement does not solve the memory problem for full Hold'em.

We also varied how training iterations were weighted and whether every decision
row received one exact initial update. A **row** is one stored decision and its
action values or probabilities. Initialization gave every row average-strategy
data, including rows that were never visited again. Positive data in a row
therefore cannot be treated as proof of later exploration.

The selected procedure passed development tests but missed an accuracy limit in
one reserved game: **1.0153% of the pot against a 1% limit**. A **hold-out** is a
test reserved until the procedure has been chosen. Once we inspect and use its
result to guide further work, it becomes known evidence. We kept the miss and
did not relabel it as a pass.

Each small game received its own training. These results do not mean that one
global agent learned to handle unseen boards.

We then packaged the methods, results, and failed gate in a technical brief and
interview notes. The existing Git history was published to GitHub, followed by
issues, PRs, and hosted checks for new work. The goal is to make the evidence
inspectable and repeatable. The [packaging snapshot](phase6-verification.md)
records what existed at that earlier checkpoint; the work log covers later work.

Read more: [the learning diagnostic and retained failures](holdem-strength-v2.md).

## 13. Test river integration at the same work budget

**Completed November 4, 2026 — issue #2, PRs #7 and #8.**

The next question was whether learning would improve if a pass averaged over all
legal river cards instead of randomly picking one. In these turn games, fixing
the board and both private hands leaves 44 possible river cards.

This is **integration**: combining outcomes using their probabilities. The
strategy still cannot observe the future river when making a turn decision.
Only the training calculation considers all those possible futures.

**Example:** An estimate from one river can be noisy. Averaging all rivers might
make it steadier, but takes more work. Comparing the methods after the same
number of passes would give the more expensive method extra computation.

We first tested the mathematics and saved-state continuation. Then we compared
both methods at 100,000, 1 million, and 10 million units of node work, with three
fixed training seeds in each of four known games. A **node** is one state visited
in the game tree. Work includes initialization and terminal states. A final full
iteration can go slightly over a threshold; that extra work is recorded.

The complete run saved 80 learned/control strategies. Every saved strategy passed
an independent value and best-response check. A separate experiment froze the
strategies while measuring update error, so changes during learning would not
confuse that measurement.

At 10 million node-work, the two medium-stack games gave these recorded medians:

| Position/game | Ordinary sampling | River integration |
| --- | ---: | ---: |
| Out of position, medium OOP | 0.2463% of the pot | 0.7612% of the pot |
| In position, medium IP | 0.9433% of the pot | 0.7109% of the pot |

These numbers are **restricted exploitability**, not win rates. Lower is better.
In position means acting later in the betting order; out of position means acting
earlier. The complete four-game table is in the linked report.

Integration's final median was lower in one game and higher in three. Both
methods passed the declared final development limits. The frozen experiment
found lower error per pass, but extra traversal work usually outweighed that
advantage in its error-times-work measure. Some estimates were unstable, so the
report keeps the per-seed variability and qualifications.

The decision was to keep the ordinary default. The experiment answered its
question without showing a general upgrade. All four games are now known
development evidence, including the ones with `heldout` in their filenames.

![Ordinary sampling and river integration at fixed work](../results/river-integration/report/learning-work.png)

Read this figure one panel at a time. **Blue** is ordinary sampling; **orange**
is river integration. Moving right means more work; moving down means lower
exploitability. The shaded bands span the three seeds, not confidence intervals.
Both axes use logarithmic scales: equal spacing represents multiplicative changes.
Each panel has its own vertical scale. The dotted line is the declared median
limit. Colors in other project figures can mean different things; check the legend.

Read more: [complete fixed-work study](river-fixed-work.md),
[PR #7](https://github.com/jimmy-sim/poker-ai/pull/7), and
[PR #8](https://github.com/jimmy-sim/poker-ai/pull/8).

## 14. Try the frozen procedure on fresh games

**Completed November 5, 2026 — issue #3, PR #11.**

We wanted to know whether the retained ordinary learning procedure could meet
its accuracy limits on new small games without changing the method to suit
those results. The rules, selection seed, exact case files and code/input hashes
were published before training. The admission check first replayed the accepted
development evidence and refused changes to the frozen procedure.

**Example:** A practice exam helps choose how to study. Once you use its answers
to improve the method, retaking it is less convincing evidence than trying a
reserved exam. The earlier poker games had become the practice set. The new
cases tested the method after that choice was fixed.

The run used three new seeds for each of four cases and the same 100,000,
1 million and 10 million work thresholds. It finished in about 8.3 minutes and
saved all 44 learned/control strategies. Every saved strategy passed independent
value and best-response checks. The final procedure gate passed in all four cases.

The closest case was medium dry IP: median exploitability was **0.9670% of the
initial pot**, just under the declared **1%** median limit. Its worst seed was
**0.9845%**, under the separate **2.5%** worst-seed limit. The tight result stayed
in the report; we did not add iterations or select a nicer seed.

Coverage still needs care. In medium wet OOP, 1,545 rows remained initial-only.
Later visits covered about **94.67%** by the uniform-reach weighting, even though
positive average-row coverage was effectively 100%. The original average-row
criterion passed, but it does not mean every decision was explored after setup.

The useful conclusion is that this fixed procedure met its chosen limits on
four cases reserved before testing. Each case received separate training; these
are not results from one global agent playing unseen boards. The ranges are
still tiny and artificial. These cases are now known evidence, so later tuning
needs another fresh test rather than relabeling them as unseen.

![Learning on the four fresh cases](../results/fresh-validation/report/learning-work.png)

Here the blue curve is the retained ordinary method. The panels show different
cases, not different opponents. Lower is better; the dotted line is the median
limit. The shaded range spans three seeds and is not a confidence interval.

Read more: [method, exact case inputs and results](fresh-validation.md),
[complete table](../results/fresh-validation/report/tables.md), and
[PR #11](https://github.com/jimmy-sim/poker-ai/pull/11).

## 15. Describe the board without storing every physical board

**November 6, 2026 — protocol and correctness milestone.** The question is whether
we can share strategy rows across boards without losing too much useful
information. A **strategy row** stores the probabilities of the available moves
at one kind of decision. More distinct rows mean more memory and more decisions
that training needs to visit.

Issue #4 adds two optional descriptions. The first removes suit names while
preserving public ranks and suit relationships: changing every heart to a spade
and every spade to a heart should not change the game's meaning. The second,
called **texture**, groups boards by features such as pairs, suit counts, high
cards and straight connectivity. It remembers a separate description of each
street already seen.

**Illustrative example:** `2c 3d 7h` and `3c 4d 8h` share a coarse texture. Both
have three different ranks, three different suits, no ten-or-higher card, no ace,
and at most two ranks in a five-rank straight window. Their exact ranks differ.
Grouping them may save rows, but may also force different situations to share a
bad compromise. The tests do not tell us whether that tradeoff helps learning.

The software tests check that equivalent suit names/flop orders behave alike,
actual hidden cards cannot enter the key, earlier streets stay remembered, and
the small game's legal actions and abstract memory remain consistent. The
existing three representations are retained. No default agent behavior changes.

A full check also exposed the old study's source guard: it correctly rejects the
new code as different from its frozen revision. The archived manifest remains
unchanged; historical reproduction needs its recorded checkout. Unit-test
fixtures are explicitly separate from archived admission evidence.

**Actual checks:** 29 new board/inspection tests, plus the historical source-guard
regression. Full-suite and hosted checks are recorded in the
[protocol's verification](public-board-abstraction.md#verification-and-remaining-work)
and linked PR. There is no new training or measured strength improvement here.

To explore the new description from the ordinary Terminal prompt, run:

```sh
.venv/bin/python scripts/inspect_public_board.py Ac Kc 2d 7c 7d
```

It prints the original board, a suit-renamed equivalent, and features for the
flop, turn and river. The board's suit counts go from `[2,1,0,0]` to `[3,1,0,0]`
to `[3,2,0,0]`; its river rank counts begin with `2` because the sevens pair.
The renamed board is an encoding, not a new deal. This command inspects features;
it does not play a bot or recommend a move.

**Next decision:** Run the preregistered comparisons at equal work, retaining
every result. The candidate must meet both accuracy and compression limits before
any new fresh-case stage. Read the [protocol and limits](public-board-abstraction.md)
and [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4). The code and checks
are published in [PR #12](https://github.com/jimmy-sim/poker-ai/pull/12).

## 16. Compare the board descriptions at the same work budget

**Completed November 6, 2026 — issue #4, PR #13.** We tested whether the new board
description helps learning and whether it actually saves space.
Correctness tests answered whether it follows its rules, not whether it is useful.

**Illustrative example:** Two learners both run 1,000 iterations, but one visits
twice as many game states each time. Those iteration counts do not represent the
same work. Here we count visited states plus the cost assigned to initialization,
and compare at the same declared work checkpoints. Both learners finish their
current update before stopping; we keep any small overshoot in the report.

The runner keeps every configured strategy, including bad ones. It separately
records rows that received an initial calculation and rows later visited by
sampling. It also checks **collisions**: different boards or private hands that
share a strategy row. A collision saves rows, but it may force a harmful compromise.

After training, the independent checker evaluates the saved strategies. **Cross-play**
means having two frozen strategies face each other; we exchange their seats to
account for position. All final pairings are kept, including self-play. A
strategy's seat-balanced advantage against itself is zero by definition; that
alone says nothing about how strong it is.

The runner and tests were published before the full study. It then ran for about
20 minutes, keeping all 150 strategy snapshots. The native audit checked all of
them, all 800 ordered final strategy pairings and 90 saved checkpoint pairs.
The largest native comparison error was below 1.64e-13 chips; our own replay
matched exactly. That gives us confidence that the reported calculations agree,
not that the resulting strategy is strong.

**The result is a failed candidate gate.** Here is the comparison with the
raw-public-board control at the same final work budget:

| Game | Raw-board rows | Texture rows | Raw-board median weakness (% pot) | Texture median weakness (% pot) |
|---|---:|---:|---:|---:|
| Small stacks relative to pot | 364 | 92 | <0.000001 | <0.000001 |
| Deeper stacks | 3,336 | 1,392 | 0.234 | 7.37 |

“Weakness” here is the exact-game exploitability measure: lower is better. It is
not a measured win rate against people. The texture description uses about 75%
fewer rows on the first game and 58% fewer on the second. But on the second game
it misses the preset 1% median limit and 2.5% worst-seed limit. Its full-tree
control also stays around 2.52% pot, missing its separate accuracy requirement.
We did not add training or choose a nicer seed to rescue the result.

This points toward a public representation that loses useful distinctions, under
this learner and budget. The medium game has no extra private-hand collisions,
and checks for remembering past decisions, legal actions and native values pass.
The full-tree result argues against
blaming only sampling noise. It still does not prove that every possible strategy
using texture must be bad, or that every engine detail is independently verified.

![Fixed-work board comparison](../results/public-board/report/learning-work.png)

These lines are five descriptions of the same game, not five opponents. On the
right, purple is texture and ends above the dotted 1% limit. Exact, raw-public
and suit-canonical lines overlap below it. The panels use different logarithmic
vertical scales. Shading spans three seeds, not a confidence interval.

Coverage also needs careful reading. The deeper texture learner has about 98.29%
subsequently visited-row coverage versus raw-public's 97.60%, yet plays worse by
the best-response measure. Visiting one shared row counts all situations mapped
to that row; it does not prove the action fits every one of them. Initialized
average-row coverage is 100%, and initial-only rows are reported separately.

The saved own policies look much closer in cross-play: the largest seat-balanced
advantage in that final pool is only about 0.103% pot. A small set of our own
opponents can miss weaknesses that an exact best response finds.

The key/float storage components shrink, but shared game trees and Python objects
remain. We have not measured a comparable reduction in total process memory.
No agent default changes, no new fresh cases and no global training follow this
failed gate. Issue #4 remains open for a more informative representation.

Software checks pass with 676 local tests on Python 3.11/3.12, including 26 new
runner/audit tests. Initial GitHub CI caught an optional-dependency mistake in a
timeout test; selecting NumPy in that fixture fixed it without changing the study
source, config or outcomes. Hosted checks are linked on
[PR #13](https://github.com/jimmy-sim/poker-ai/pull/13).

From Terminal, open the graph or run the small software fixtures:

```sh
open results/public-board/report/learning-work.png
.venv/bin/python -m pytest -q tests/test_public_study.py
```

Those tests use tiny fixtures; they do not repeat the 20-minute study. Native and
plot checks require their optional extras. Read the
[methods and diagnosis](public-board-comparison.md) and
[complete tables](../results/public-board/report/tables.md).

## 17. Find which shared decisions need different treatment

**November 6, 2026 — completed diagnosis and admission check.** The last test
showed that the smaller description was too weak on one game. Before adding features, we need concrete
examples of what the sharing loses.

The diagnostic looks at a row containing several exact situations. It asks which
action looks best in each situation under a frozen strategy from our own solver,
then compares that with being forced to choose one action for the whole row.
The values average possible hidden opponent hands first; the program cannot
choose a different action after secretly looking at those cards.

**Illustrative example:** One situation values check/call at 3/1 chips, another at
0/4 chips. Separately they prefer different moves. If we force them into one
row, at least one situation may receive the wrong compromise. These numbers
explain the diagnostic and are not measured poker results.

The ranking score is a local comparison under a frozen continuation. It is not
the agent's total expected loss or exploitability. Tied local actions can also
hide a need for different mixing probabilities when an opponent adapts.

At first publication, diagnosis examples and the replacement candidate were
pending. Code, tests and input hashes were published before that run.
The local checks pass with 686 tests on both Python versions, including ten new
tests for this diagnostic and viewer.
Read the [definition and limits](board-collision-diagnosis.md).

The retained diagnosis now gives a concrete example. With pocket nines, one
river makes a full house and another makes four of a kind, yet the old texture
key shares their decision row. In the frozen-control example, the full house
prefers folding to an all-in, while quads prefers calling. Another shared row
combines a straight with one pair. These are different visible hand categories.

The one proposed fix is to keep that category at every observed street. It
still groups many situations, and does not store exact tiebreakers. Its code
passes the unit/recall checks; the full local suite now has 712 tests on both
Python versions. The small full-tree admission test is now complete.

**The candidate fails.** Here all strategies receive 4,096 full-tree training
iterations. Lower exploitability means less weakness against a best response.

| On the deeper known game | Exploitability (% of initial pot) | Strategy rows |
| --- | ---: | ---: |
| Keep the exact public board | 0.000182 | 3,336 |
| Old coarse texture | 2.522516 | 1,392 |
| Texture plus made-hand categories | 2.593658 | 1,428 |

The new candidate keeps 57% fewer rows than the raw-public control, but its
excess weakness exceeds the rule set in advance. The low game passes. All
48 saved strategies pass the separate OpenSpiel value/best-response check;
that check confirms these measurements on our exported game mechanics.

There is another revealing example already in the diagnosis: pocket nines on
`Ts 9s 4d 2h` makes a full house with either `Th` or `Td` on the river. The
category history is identical, yet the frozen control prefers different moves.
The fixed opponent range includes `Tc Td`: that hand can make quads when the
river is `Th`, but cannot exist when `Td` is on the board. This is called a
**blocker** or card-removal effect. Knowing “full house” alone loses this detail.
The example does not tell us how much of the final exploitability it causes.

The lesson is that fixing an obvious local example does not automatically
improve the whole learned strategy. The larger sampled-learning comparison
stops here; fresh/global testing and agent defaults stay unchanged. The earlier
7.37% result used sampled learning, so it cannot be compared directly with this
2.59% full-tree result. The matching old full-tree number is 2.52%.

To inspect the two examples and open the measured learning curves:

```sh
.venv/bin/python scripts/inspect_board_collision.py --rank 2
.venv/bin/python scripts/inspect_board_collision.py --rank 7
open results/made-category-admission/report/full-controls.png
```

On the right-hand graph, the old and new compressed versions flatten around
2.5% of pot while the exact/raw-public controls keep falling. The vertical axis uses a
logarithmic scale: each numbered step is a factor of ten. Read the
[complete tables](../results/made-category-admission/report/tables.md) and
[method, limits and stopping decision](board-collision-diagnosis.md), published
with [PR #14](https://github.com/jimmy-sim/poker-ai/pull/14).

## 18. Ask how a counterstrategy exploits the saved agent

**November 7, 2026 — completed diagnosis.** The category experiment failed. Before
changing features again, this step will inspect the actual saved strategy.
A **best response** is the strongest counterstrategy to a fixed opponent, using
only the information its player is allowed to see.

We will compare a response that sees exact cards with one restricted to the
agent's compressed descriptions. Their difference measures extra response value
from the discarded information against that fixed opponent. We will also trace
losses to decisions and check that they add up to the measured total. This is a
stronger accounting check than the earlier local ranking, but does not tell us
what would happen after retraining with a new feature.

The [protocol](candidate-best-response.md) and input-bound config are declared
before outcomes. No new training or feature selection starts in this block.
The implementation now passes 733 local tests on Python 3.11/3.12, including
21 new checks for the math, hidden information and saved evidence. A small test
caught a native-wrapper crash: the Python policy object had to stay alive while
the C++ response calculator used it. That wrapper is fixed before any new
research results are measured. The known Kuhn equilibrium gives zero loss, and
brute-force Kuhn replies agree with the new response algorithm. Actual retained
results were still pending at that code publication.

The completed diagnosis checks all eight saved cases. For the deeper game's
category candidate:

| What the response can use | Contribution to exploitability (% pot) |
| --- | ---: |
| Only the candidate's compressed descriptions | 0.000169 |
| Additional value from seeing exact information | 2.593490 |
| Total | 2.593658 |

This means the saved strategy is close to an **equilibrium inside the compressed
game**: if both players are forced to use those descriptions, neither can gain
much by changing strategy. A player who can distinguish exact cards has much
more opportunity. That points toward the information being discarded, instead
of treating this as an obvious shortage of training iterations. It does not
prove every strategy using this abstraction must have the same weakness.

There is a useful surprise in the decision trace. Holding `Tc Td` on
`Ts 9s 4d 2h`, the saved strategy almost always bets. The exact best response
checks, because its later decisions can take advantage of the fixed opponent.
This turn row has only one exact member: no turn situations were merged there.
So “the loss appears on the turn” does not mean “add more turn features.”
Earlier choices can gain value from better decisions later in the hand.

All **32 response values and 32 own reply-profile values** pass the separate
OpenSpiel checks, with disagreement below 0.0000000000001 chips; own replay
error is zero. Each player's decision losses add up to its total gain, and
half the two gains gives exploitability. The native comparison shares our game
export and partition definitions; it does not independently prove those are
correct or establish competitive Hold'em strength.

GitHub then caught an optional Matplotlib typing issue in the new report module
that the environments with all extras had missed. Lazy optional imports fixed
it; a separate base install passes 709 tests with 15 optional skips. The first
receipts are preserved. A clean rerun reproduces all eight cases exactly and
produces a byte-identical reply-data file. This software correction did not
change the experiment's conclusion.

Try the new inspector and graph:

```sh
.venv/bin/python scripts/inspect_saved_reply.py
open results/saved-replies/report/response-values.png
.venv/bin/python -m pytest -q tests/test_reply_diagnosis.py
```

The inspector is a saved research example, not an interactive match. “Responding
seat 0” means it is exploiting the fixed seat 1 strategy. Its action values use
best-response decisions later, so copying just its first action is not the whole
counterstrategy. In the graph, blue is gain available within the descriptions;
orange is extra value from exact information. Each panel uses its own scale.

The previous failed gate stays failed; no new feature or training run follows
this diagnosis. Read the [method and limits](candidate-best-response.md),
[complete table and figures](../results/saved-replies/report/tables.md), and
[PR #15](https://github.com/jimmy-sim/poker-ai/pull/15).

## 19. Find the river details the compressed strategy misses

**November 7, 2026 — completed river diagnosis.** The last diagnosis showed that exact
information gives the counterstrategy much more opportunity. Now we will look
at the river decisions themselves. We will hold earlier choices fixed, replace
only river decisions, and check both the compressed and exact earlier choices.

A **blocker** is a card you can see that prevents an opponent from holding a
particular hand. We will investigate card removal, full hand rank and relative
strength against the declared range. These are diagnostic probes, not new agent
features or promises of stronger play. The [protocol](river-distinction-diagnosis.md)
is published before outcomes. The implementation passes 753 tests on each of
Python 3.11/3.12, including 20 new checks. A separate base install passes 728 with
16 optional checks skipped. Lint, formatting, strict typing and hooks pass.
These checks establish software behavior; retained research results were pending
at that code publication.

The results identify three useful distinctions:

1. **Strength relative to the opponent's range.** Pocket tens makes three of a
   kind on either a king or jack river here. But the possible `Kh Qh` opponent
   hand makes a straight on the jack. The saved exact reply calls one and folds
   the other against the fixed opponent.
2. **Card removal even with the same full house.** With `Tc Td` on
   `Ts 9s 4d 2h`, either `9h` or `9d` makes tens full of nines. On `9h`, the
   opponent can have `9c 9d` for quads. On `9d`, that hand is impossible because
   the diamond nine is already on the board. The saved exact reply folds on
   `9h` and calls on `9d`; the compressed reply calls both.
3. **The range after observing betting.** Some rows still have different best
   actions even when full own rank, possible opponent hands and their showdown
   outcomes match. The opponent's betting gives those hands different weights.
   Future betting behavior can matter too; this experiment does not isolate
   those effects or explain why the saved opponent uses those frequencies.

On the deeper game, after the exact earlier choices, there are **24 merged rows
with strict reachable action conflicts** across both responding seats. Grouping
by full own rank leaves 11 unresolved; compatibility alone leaves 14; the static
range-outcome probe leaves 4. These are separate diagnostic probes, not trained
agent upgrades. Removing a displayed conflict does not establish an EV gain.
The simpler game's category candidate has zero such reachable conflicts.

The earlier choices matter. Replacing only river decisions after the compressed
response's earlier choices gains about **0.000014% of pot**. Replacing them after
the exact response's earlier choices gains about **3.774592%**. These hold
different paths fixed, so do not add them together. The second comparison also
keeps the saved compressed river actions fixed, rather than fitting new ones.
This explains why the previous trace could assign a large opportunity to a turn
decision even though the exploitable distinction appears later.

All eight cases, both seats and both prefixes are retained. All **64 own hybrid
profile values** pass the native OpenSpiel check; maximum disagreement is below
0.0000000000001 chips and own replay error is zero. That checks the calculations
on our exported game mechanics. It does not prove an independently correct whole
engine or competitive Hold'em strength.

Inspect the same-full-house blocker example and the probe-count graph:

```sh
.venv/bin/python scripts/inspect_river_distinction.py --rank 2
open results/river-distinctions/report/probe-conflicts.png
.venv/bin/python -m pytest -q tests/test_river_distinctions.py
```

The graph's blue and orange bars hold the compressed and exact earlier choices
fixed, respectively. Each probe is tried separately on the same saved data. The
left panel is blank because all its conflict counts are zero. These colors have
a different meaning from the previous chapter's exploitability decomposition.

Read the [method, examples and limits](river-distinction-diagnosis.md),
[complete tables](../results/river-distinctions/report/tables.md), and
[PR #16](https://github.com/jimmy-sim/poker-ai/pull/16). We stop here: no feature
has been selected, trained or deployed, and the earlier failed gate is preserved.

## 20. Define a small range-aware description

**November 7, 2026 — completed definition and correctness tests.** The next candidate will add a river summary
of how much of the declared opponent range is blocked, beats your hand, ties it,
or loses to it. It keeps the existing buckets, board texture and hand categories.
The four amounts are grouped into fixed intervals; no exact opponent deal or
saved strategy is supplied to the feature.

The range is a fixed assumption from the spot config. It does not change after
bets, so this candidate does not solve the remaining conditional-range problem.
The [definition and acceptance protocol](range-mass-representation.md) are
published before implementation or performance outcomes. This milestone will
build correctness tests and an inspector, then stop before training. That
implementation is now complete.

A **prior** is the range and weights assumed before conditioning on the betting
we observe. A **histogram** groups that weight into a few categories. Here the
categories are blocked / opponent beats us / tie / we beat opponent. Each amount
is placed into one of eight fixed intervals, represented by numbers 0–7. The
new name is `texture_range_q8_b8`: `q8` describes these mass intervals, while
`b8` is the existing private-hand bucket count.

With equal prior weights on `Kh Qh` and `9c 9d`, holding `Tc Td`:

| River on `Ts 9s 4d 2h` | Blocked | Opponent beats us | Tie | We beat opponent |
| --- | ---: | ---: | ---: | ---: |
| `9h` | 0 | 1/2 | 0 | 1/2 |
| `9d` | 1/2 | 0 | 0 | 1/2 |

The new description separates these situations. It knows the whole declared
range, not which hand was actually dealt. The weights here are the equal
starting weights; the earlier 83.9% figure came after the opponent's betting.
Handling those changing beliefs remains future work.

The acceptance rules are fixed before training. On both known games, the future
full-tree candidate must have at most 0.5 percentage points more exploitability
than the exact control, use at most 75% of the raw-public strategy rows, and meet
coverage/recall/independent-audit checks. Only then may it enter the later sampled
comparison, whose final median/worst limits remain 1%/2.5% of pot. A good result
on one game cannot hide a failure on the other.

There are **67 new correctness and contract tests**. They check examples, hidden
information, memory of earlier observations, exact bin boundaries, context
binding and failure cases in the acceptance rules. Their hypothetical metrics
are explicitly synthetic. They also reject a record claiming initialization
while counting zero initialization work. The full local suite passes **820 tests on each of
Python 3.11/3.12**, plus lint, formatting, strict typing and hooks. A base install
passes 795 with 16 optional skips. Duplicate test-environment path files first
pointed at older worktrees; repairing those paths and rerunning resolved the
collection failures without changing the feature or its limits.

Try these from the normal Terminal prompt (leave Python with `exit()` first if
you still see `>>>`):

```sh
.venv/bin/python scripts/inspect_range_feature.py 9h
.venv/bin/python scripts/inspect_range_feature.py 9d
.venv/bin/python -m pytest -q tests/test_range_mass.py tests/test_range_protocol.py
```

Look at `prior_mass` and `feature_bins`. In blocked/loss/tie/win order, the bins
change from `(0,4,0,4)` to `(4,0,0,4)`. These numbers label intervals; they are
not betting probabilities. The context hash stays fixed because both examples
use the same range assumptions.

The prototype intentionally still merges one published example where betting
changes the opponent weights but static masses stay the same. It also pools
combo identities and small differences within each interval. We have not
measured whether the candidate learns a stronger strategy or retains enough
compression. Read the [definition and limits](range-mass-representation.md) and
[PR #17](https://github.com/jimmy-sim/poker-ai/pull/17). We stop at this protocol
and correctness milestone; no new training or default change has occurred.

## What comes next

[Issue #4](https://github.com/jimmy-sim/poker-ai/issues/4) remains open. The next
step is to implement and run the declared full-control admission for this one
candidate, preserving every control/checkpoint and the independent audit. If it
fails, stop before the larger sampled comparison. Dependence on the tiny known
ranges remains a limitation; fresh/global work waits for accepted development
results and a separately frozen fresh-case design.

## A small glossary

| Term | Meaning in this project |
| --- | --- |
| Board / street | Public cards / a betting stage: preflop, flop, turn, or river. |
| Range | Possible private hands, often with probability weights. |
| Policy / strategy | Probabilities assigned to legal actions at each decision. |
| Information set | Histories the acting player cannot distinguish from their allowed observations. |
| Expected value, or EV | Average net payoff under specified strategies and chance probabilities. |
| Best response | A strategy chosen to exploit a fixed opponent, while respecting hidden information. |
| Exploitability | A best-response-based measure of remaining weakness; its units and game scope matter. |
| Self-play | Learning through interactions between the program's own strategies. |
| Abstraction | A smaller representation that groups cards, decisions, or available actions. |
| Variance / MSE | Variation in an estimate / average squared distance from the target answer. |
| NLL | A prediction penalty; lower is better. An improvement in NLL is plotted with the opposite direction. |
| Seed | A starting value that makes a random sequence repeatable in the recorded setup. |
| Frozen policy | A saved strategy that is not learning during the measurement. |
| Checkpoint | Saved training state, including what is needed to resume it. |
| Development / hold-out | Cases used to choose a procedure / cases reserved to test the chosen procedure. |
| Gate | A pass/fail rule written before inspecting the relevant results. |
| Fallback | The behavior used when the intended learned strategy entry is unavailable. |

## Things you can try on this Mac

Use the existing project environment. For a fresh installation, follow the
[README setup](../README.md#development) first. Each command below starts from:

```sh
cd /Users/jimmysim/Projects/poker-ai
```

Read this file in Terminal:

```sh
less docs/learning-journal.md
```

Press Space to move forward and `q` to leave. GitHub displays the headings, links,
and image more comfortably than the raw Terminal view.

Run the card tests without starting a training experiment:

```sh
.venv/bin/python -m pytest -q tests/test_cards.py
```

Run the fixed-work runner and artifact checks on their small test fixtures:

```sh
.venv/bin/python -m pytest -q tests/test_river_study.py
```

That second command tests the software, including a tiny fixture run. It does not
repeat the full four-game study. See the full-study document for its separate
reproduction command and budget.

Open the recorded learning graph and inspect recent commits:

```sh
open results/river-integration/report/learning-work.png
git log -8 --oneline
```

## 21. Test whether the range-aware description is accurate enough

**November 7, 2026.** Does adding river range masses actually improve the
small-game strategies? We trained all five fixed descriptions on the same two
games, visiting the whole tree each iteration. That helps separate representation
limits from the extra noise of sampling branches during learning.

The earlier example explains the intended distinction: a river 9d blocks the
opponent's pair of nines; 9h does not. The new description can tell those cases
apart. This time we measured whether the resulting strategy improved as well.

On the deeper game at 4,096 iterations, old category exploitability was
**2.594% of the initial pot**. The new range-mass description gives **0.272%**.
Lower means a best-response opponent has less room to exploit the strategy
inside that exact small game. It does not say how often the agent wins hands.
The exact control is still much closer to zero, at **0.000182%**.

The candidate uses **1,662 strategy rows versus 3,336** for raw-public. Both games
pass the accuracy and row limits fixed before the run. All 60 checkpoints were
saved and independently checked with OpenSpiel; the largest numerical difference
was about **0.000000000000128 chips**. Own-policy replay matches exactly. Training
and setup took about 13 seconds; the separate audit took about 7 seconds.

There is a useful catch: fewer strategy rows did **not** mean less total storage.
The new keys are longer. On the deeper game, key bytes rise even though the
regret/average arrays shrink. We report both instead of claiming memory was halved.

The curves show all descriptions nearly overlap on the easy game. On the deeper
game, the new purple line falls below the old category/texture lines, then levels
off above the exact/raw-public controls. The vertical axis is a **fraction** of
the pot: about 0.00272 means 0.272%. It uses a logarithmic scale, so equal vertical
gaps represent multiplication, not equal chip differences.

Open the recorded plots from the project folder:

```sh
open results/range-mass-admission/report/full-controls.png
open results/range-mass-admission/report/row-counts.png
```

For software checks, run `.venv/bin/python -m pytest -q tests/test_range_admission.py`.
These are small fixtures, not a repeat of the research run. Local full checks
pass 845 tests on each Python version; base-only checks pass 818 with 18 optional
skips. [PR #18](https://github.com/jimmy-sim/poker-ai/pull/18), the
[method](range-mass-admission.md) and [tables](../results/range-mass-admission/report/tables.md)
contain the evidence and limits. Codex assisted with implementation and reporting;
no new personal learning or hands-on hours are inferred.

We stop here before sampled learning. The next step is to test whether this
improvement survives the fixed branch-visit budget and three training seeds.
Passing this first gate does not yet make it the global Hold'em agent.

## 22. Check whether the improvement survives sampled learning

**November 7, 2026.** The previous result used every branch of the small game
tree. Would the same description stay accurate when learning explores only
selected branches? We compared all five descriptions at the same branch-visit
budgets, counting exact initialization and the last whole iteration's overshoot.

There was a useful engineering failure first. The old replay compared calculated
collision probabilities exactly; that passed locally and failed on Linux. A new
adapter allows only a tiny rounding difference in those three probability sums,
while keeping counts, hashes, contexts and work exact. Poker performance limits
stay unchanged. Both Linux jobs passed the repair. The interrupted 20-checkpoint
run is retained separately; the complete run starts again from checked source.

The complete run saved **all 90 checkpoints** in about **21 minutes**. Here is the
important deeper-game result at 10 million node work, in percent of the pot:

| Description | Median exploitability | Worst seed |
|---|---:|---:|
| Exact/raw-public | 0.234% | 0.255% |
| Texture | 7.370% | 9.688% |
| Category | 6.723% | 7.189% |
| Range mass | 4.480% | 5.507% |
| Required exact/candidate limits | 1.000% | 2.500% |

Lower is better: it leaves a best-response opponent less room to exploit the
strategy inside this fixed game. The new description improves on category, but
**fails both deeper-game limits**. It passes the easier game. The full-tree
success from step 21 remains valid; it did not guarantee sampled learning would
meet its separate budget and targets. These numbers are not human-match win rates.

The software and numerical checks pass: **886 tests** on each Python version,
**all 90 checkpoint/visit pairs** replay exactly on this Mac, and all 90 independent
OpenSpiel value/BR comparisons agree within about **0.0000000000000853 chips**.
This is why a failed strength result can still be useful progress: we checked
that the measurement is reliable, then kept the unfavorable result.

A row can be populated yet still make poor decisions. Exact initialization gives
100% average-row coverage here; the report separately records later sampled
visits. Likewise, fewer table rows do not imply less total memory. The run's
process peak includes trees and the growing saved-receipt bundle.

In the learning plot, faint lines are individual seeds and bold lines are their
medians. Colors are blue exact, orange raw-public, green texture, red category,
purple range mass. The vertical axis is already **percent of the initial pot**
(unlike step 21's fraction axis). The dotted line marks the final 1% median target.
The second plot retains every final seed and both final limits. Small low-game
points look like zero on its linear axis; their recorded values are not all zero.

```sh
open results/range-mass-sampled/report/learning-work.png
open results/range-mass-sampled/report/final-seeds.png
.venv/bin/python -m pytest -q tests/test_range_sampled.py
```

The test command runs small fixtures, not another 21-minute research experiment.
Read the [method and limits](range-mass-sampled.md),
[tables](../results/range-mass-sampled/report/tables.md) and
[PR #19](https://github.com/jimmy-sim/poker-ai/pull/19). Codex assisted with the work;
no personal learning or hands-on hours are inferred.

We stop here. Next, inspect whether the saved candidate is still learning within
its own compressed game or mainly suffers from missing distinctions. We have not
measured that diagnosis yet, so we will not assume extra compute is the answer.
No fresh-game or global training follows this failed gate.

## 23. Separate unfinished learning from missing distinctions

**November 7, 2026.** The sampled strategy missed its limits. We kept it fixed
and asked two questions: what could an opponent gain using the same information
groups, and what extra gain could it get by distinguishing the exact poker states?
A best reply is an optimized response to this one saved opponent, not a new trained
agent or universal poker advice.

All five descriptions, both games, all three final sampled seeds and the full
controls are included: **40 saved profiles**. On the deeper game, the range-mass
candidate's sampled mean splits like this, in percent of the initial pot:

| Component | Mean across the three seeds |
|---|---:|
| Gain available within existing information groups | 0.243% |
| Additional gain using exact information | 4.111% |
| Total exploitability | 4.354% |

The earlier **median is still 4.480%**. We use the mean here because the pieces
must add. A different summary statistic is not an improvement in the agent.
Every individual seed is kept in the report; all three have a much larger
extra-information component than their within-group component.

This points to a weakness that a compressed opponent mostly cannot see. But there
is a catch: the full-tree control uses the **same description** and has only
**0.272% total exploitability**. Its opponent's saved strategy also differs.
Therefore 4.111% is not a permanent information-loss floor, and this result does
not prove that adding a feature or simply training longer will fix it.

There is a concrete example to explore. In the first sampled seed, seat 1 holds
**9c 9d** on **Ts 9s 4d 2h**. The saved policy folds about **99.24%** of the time.
The exact best reply calls against that saved opponent. Calling has a better
net-chip value than folding **when followed by the exact reply's later play**.
The reply restricted to the saved information groups still folds here. The turn
row itself is not merged: later river distinctions can make the difference.
We should not reduce that to “always call a set” or assume one turn-action edit
recovers the whole gain.

All **160 independent best-response roots** and **160 achieved own reply values**
pass OpenSpiel checks, with maximum difference about **0.000000000000121 chips**.
The complete summaries and row details replay with zero difference on this Mac;
Python 3.12 also passes replay. Local checks pass 914 tests on each Python version;
base-only passes 883 with 22 optional skips. Own diagnosis took about 26 seconds,
and the separate audit took about 49 seconds. No agent training occurred.

In the plots, **blue** is the response gain within the saved information groups;
**orange** is the extra value of exact distinctions. Each bar's total is the
saved strategy's exploitability. The candidate plot shows every seed plus the
separate full control. The all-controls plot uses means of the three sampled seeds.
The low and medium panels have different scales; compare their axis labels.

```sh
open results/range-mass-replies/report/candidate-profiles.png
open results/range-mass-replies/report/sampled-means.png
.venv/bin/python scripts/inspect_range_reply.py --seat 1
```

Try another saved seed with `--seed 20261302`, or the full control with
`--training full`. These inspect saved counterstrategy examples and do not retrain.
Read the [method and limits](range-mass-reply-diagnosis.md),
[tables](../results/range-mass-replies/report/tables.md) and
[PR #20](https://github.com/jimmy-sim/poker-ai/pull/20). Codex assisted with the work;
no personal learning or hands-on hours are inferred.

We stop at this verified diagnosis. A useful next question is why the same
information groups produce very different exact-opponent vulnerability across
the saved full and sampled strategies. We have not isolated that cause or chosen
a remedy. The failed learning gate remains in force, with no fresh/global run.

## 24. Hold the opponent fixed and swap saved decisions

**November 8, 2026.** Full and sampled training use the same card-information
groups, yet their saved policies have different weaknesses. We kept training
stopped and swapped saved decisions to find where the difference lives.

First, we crossed the four saved policies between seats. Then, for every seed,
we combined full or sampled turn decisions with full or sampled river decisions.
All five descriptions and both games stay in the study: 160 crossed profiles
and 120 street hybrids. A hybrid here is a diagnostic combination, not a new agent.

For the deeper game's range-mass candidate, the mean extra value available to an
exact-information responder is:

| Turn decisions | River decisions | Extra-information gap (% initial pot) |
|---|---|---:|
| Full | Full | 0.271% |
| Sampled | Full | 0.255% |
| Full | Sampled | 3.362% |
| Sampled | Sampled | 4.111% |

The big jump follows the **sampled river decisions**, rather than a change to
card groups. Turn and river interact: changing the earlier play can alter which
later situations are reached and the opponent's likely hand distribution there.
We averaged both swap orders so that one arbitrary order does not get all the
credit. The 3.839-percentage-point gap change splits into **0.366 points turn**
and **3.473 points river**; the interaction is already shared between them.

These figures measure the extra-information gap, not total exploitability of a
new hybrid. The earlier **4.480% median total** and failed learning gate remain.
No retraining or playing-strength improvement occurred in this step.

There is another useful finding: full has only a small seat-balanced advantage
against these sampled policies in this spot, about **0.034–0.064% of the pot**.
Two policies using the same compressed groups can look close when playing each
other while differing greatly against a responder with finer legal information.
Exact does not mean seeing hidden opponent cards; those stay hidden.

This locates a difference in saved behavior. It does not prove whether sampling,
the regret-update rule, averaging or training work caused that difference.
The full and sampled procedures differ in several ways. We need a controlled
comparison before choosing a remedy, rather than assuming a new feature or more
iterations solves it.

All fixed inputs, seeds, negative effects and interactions are retained. Complete
replay matches with zero difference on this Mac. The independent audit passes
160 crossed EVs, 120 hybrid baseline values, **480 response roots and 480 achieved
own reply values**, with largest disagreement about **0.000000000000128 chips**.
Own computation took about 60 seconds; the separate audit took about 71 seconds.
Local checks pass 944 tests on each Python version; base-only 911 with 24 optional
skips. Codex assisted; personal learning and hands-on hours are not inferred.

```sh
open results/policy-swaps/report/street-gaps.png
open results/policy-swaps/report/crossed-payoffs.png
.venv/bin/python scripts/inspect_policy_swap.py
```

In the bar chart, each bar is one turn/river combination. Check the low panel's
scientific-notation scale; its gaps are tiny. In the heatmap, a positive blue cell
favors the row policy over the column policy after balancing seats. The diagonal
is zero by construction. These are fixed-spot EVs, not full-game win rates.

The inspector defaults to the first declared seed. Try `--seed 20261302` to see
another saved seed. F means full, S sampled, and the first letter is the turn.
The [method](frozen-policy-swaps.md),
[tables](../results/policy-swaps/report/tables.md) and
[PR #21](https://github.com/jimmy-sim/poker-ai/pull/21) contain the complete evidence.
We stop here before choosing a training or feature change. Issue #4 stays open.

## 25. Change one training rule at a time

**November 8, 2026.** The last step pointed to river decisions. The next question
is what in training produced those decisions. We first checked whether the two
training procedures were doing the same calculations.

They were not. Full training deletes negative accumulated regret; sampled
training keeps it and gives later regret updates more weight. Both give later
strategy averages more weight, but collect those averages at different moments.
They also start differently and use different amounts of work. Calling the
whole difference “sampling” would combine all those changes.

**Example, not a poker result:** Suppose two equally likely sample updates are
+1 and -1. Their mean is zero. If we delete each negative result before averaging,
the mean becomes 0.5. Averaging first and then deleting negatives gives zero.
This explains why a correct sampling estimate can still lead to different
learning after clipping. It does not prove which rule hurt our river strategy.

We built an experimental trainer with separate switches for full versus sampled
traversal, clipping, regret time weights and strategy-average time weights. The
common version uses the same averaging convention and initialization. The old
trainers and saved strategies stay available for comparison.

Before any long comparison, a small software game checks every possible random
selection. Its chance probabilities are deliberately uneven. Both players and
policies with zero-probability actions are included. Tests also check shared
rows are combined before clipping, match the old trainers' specified modes,
check all 16 switch combinations, and count initialization as real work.

The short regression trace on the actual Hold'em adapter checks code compatibility
in both known games. It is not a new strength experiment. Twenty focused tests
pass. Full local checks pass **964 tests on each Python version**; base-only
931 pass with 24 optional skips. Both hosted Python jobs pass. The recorded
checks cover **54 possible selector tapes across four cases**, and replay on
both Python versions. Their largest raw-update disagreement is below
0.000000000000001 fixture chips; this is a software check, not a poker score.

The [protocol](training-isolation.md) fixes the later learning grid and separates
equal-work comparisons from equal-iteration comparisons. An **iteration** is one
update pass for each player. A **node visit** is one situation examined, including
chance and terminal situations. Sampling can complete many short iterations in
the time/work of a much smaller number of full traversals.

The [work receipt](../results/training-isolation/correctness.json) checks all
30 old control/seed endpoints. For the medium range-mass candidate, the full
control examined **174,514,176 situations**, compared with about **10 million**
for each sampled seed: roughly **17.45 times as much work** by the declared visit
count. Sampling completed roughly 298,000–316,000 short iterations, versus 4096
full ones. This tells us the old endpoints were not matched on either axis; it
does not tell us how much of the weakness the work difference caused.

You can replay these checks without training or overwriting anything:

```sh
.venv/bin/python scripts/check_training_isolation.py --replay results/training-isolation/correctness.json
.venv/bin/python -m pytest -q tests/test_controlled_training.py
```

We stop at the verified correctness gate before running the controlled learning
study or choosing a remedy. There is no new stronger agent or established training cause in this step.
Codex assisted; personal hands-on time is not inferred.

## 26. Check the cost before a large comparison

**November 8, 2026.** The trainer can change one rule at a time. Before asking it
to run a large experiment, we need to know whether the planned work fits the
two-hour computation cap. This step measures cost, not poker strength.

**Profiling** means timing the program and finding where it spends that time.
We fix the cases before looking at the measurements: both games, both card
descriptions, every rule combination and all three sampled seeds. We also include
the full-only bridge controls. That makes 140 different cases, each repeated
three times, for 420 timing rows.

Each repeat starts fresh. Full training gets 16 additional iterations; sampled
training gets 1000. We separately count and time the initial exact calculation.
We check the final training state and random-generator state are identical across
repeats. Otherwise we might mistake changed work for a speed difference.

The timing forecast uses the slowest of three estimates for each case, then
adds a fixed 2× planning margin. This is a rough projection, not a guarantee.
Later strategies can visit different situations, and scoring/checkpoint costs
need separate measurement. A result below two hours would still leave those
costs unresolved. A result above two hours would block the large study on
training cost alone. We do not change the poker-learning targets to make it fit.

The profiling tools and 13 new tests are implemented. The 33 focused checks
(including the previous 20) pass at this checkpoint. Full local checks pass **977 tests on each Python version**; base-only
944 pass with 24 optional skips. Lint/format, strict typing and hooks pass.
The full timing run has now completed; hosted CI is tracked separately. The existing correctness command still works through a
tested adapter; its old numerical receipt and mathematical code are unchanged.

The profile completed all 420 rows in **about three minutes**. Its forecast
puts the large comparison at **4.23 hours for training alone**, or **8.46 hours
with the fixed planning margin**, against a two-hour cap. Those are projected
hours, not time already spent. The large comparison stays off; no cases or seeds
were removed to make the estimate smaller.

The profiler gives us a concrete target. In its fixed medium-spot sampled case,
roughly **half the instrumented update time** goes through the routine that
rebuilds the whole current-policy table. It runs twice per iteration. The sampled
traversal only needs some of those rows, so there may be repeated work to remove.
That requires a tested alternative, not a change to the strategy rules. Other
costs remain, so one change is not guaranteed to meet the budget.

The next milestone is to preserve exactly the same updates, random choices and
work counts while reducing measured overhead, then profile again. This is a
compute barrier; it still does not explain which training rule caused the river
weakness. The [tables](../results/controlled-training-profile/report/tables.md)
come from the recorded timings, and regenerate identically on both Python
versions. Rerunning a timer would produce different times.

```sh
.venv/bin/python scripts/profile_controlled_training.py --report results/controlled-training-profile/profile.json
.venv/bin/python -m pytest -q tests/test_controlled_profile.py
```

Read the [fixed profiling plan](controlled-training-profile.md). No poker score,
new stronger agent or established cause of the river weakness follows from this
step. Codex assisted; personal hands-on time is not inferred.

## 27. Reuse policy rows within one update pass

**November 8, 2026.** The profile identified repeated work: the sampled trainer
rebuilds the full table of action probabilities before each player's pass, even
though that pass visits only some rows. This step adds an optional backend that
constructs a row when it is first needed and reuses it during that pass.

A **cache** stores a result for reuse. Its lifetime matters. Regrets stay fixed
while one pass is running, so its policy rows stay fixed too. After a player
updates regrets, we discard the cache before starting the next pass. Keeping old
rows across that boundary could silently train a different strategy.

We also keep the same padded row width. Removing extra zero entries before a
floating-point sum can change its last bits. A tiny probability change can later
change a random action choice. The new backend keeps that sum/division behavior,
checks visited rows, and computes the uniform fallback only when needed.

Before timing, both implementations must match exactly on all 96 external cells,
including both games/descriptions, all eight rules and all three seeds. Checks
cover six fixed iterations through 1001, including the exact initialization.
Regrets, average tables, policies, random-generator state and work counts must
match; a small numerical tolerance is not a substitute for this gate.

The 32 new tests and previous focused checks pass: 65 total at this checkpoint.
They cover padded rounding, stale caches, per-iteration state equality, real-game
prefixes, balanced paired timing order and incomplete/changed receipts. Full local checks pass **1009 tests on each Python version**; base-only
976 pass with 24 optional skips. Lint/format, strict typing and hooks pass.
Both code-head CI jobs passed. The complete parity/profile is now recorded below.

The complete gate passed: **96 cases matched at all 576 checkpoints**, then
all 708 timing rows and six profiler cases matched their expected states. The
measurement took about **5.4 minutes**. The median paired loop-time ratio is
**1.695× in favor of on-demand rows** across all 288 observations.

The forecast fell from **4.23 hours to 2.28 hours for training alone**. With the
same planning margin it is **4.57 hours**, still above the two-hour cap. These
are projections, not hours already spent. There is still no full learning run
or stronger-agent result. The low candidate gains little on average and some
cached repeats were slower; all those timings are retained.

The new profile points to remaining work in the unchanged state adapter: building
actions/menus repeatedly and constructing child wrappers. I will investigate
that as a separate measured change while you are away, preserving exact behavior
and profiling again. The current optimization does not change card groups,
clipping, averaging, random draws or which situations are examined.

You can inspect the [recorded table](../results/row-policy-profile/report/tables.md):

```sh
.venv/bin/python scripts/profile_policy_rows.py --report results/row-policy-profile/profile.json
.venv/bin/python -m pytest -q tests/test_row_policy.py tests/test_row_profile.py
```

The old trainer stays frozen and remains the default. The paired timing study
compares both backends on the same machine, alternating which runs first.
It retains all cases and the same two-hour forecast rule. A speed improvement
would make the larger experiment cheaper; it would not establish stronger poker
play or explain the river weakness. Read the [fixed plan](row-policy-cache.md).
Codex assisted; personal hands-on time is not inferred.

## 28. Reuse the static game-node interface

**November 8, 2026.** The row-cache profile still spends time repeatedly reading
menu metadata and creating child-state wrappers. In a fixed finite game tree,
those menus, chance probabilities and child links do not change as learning runs.
This step adds an optional immutable cache for that interface.

The two caches have different lifetimes. Policy rows change when regrets change,
so their cache lasts one target pass. Game-node metadata stays fixed for the
whole trainer. No policies, regrets, reach values or random-generator state are
stored in cached game nodes. Reusing an object changes its Python identity;
the mathematical state and its legal outgoing moves must stay identical.

We first compare every node and edge with the original adapter, including values,
types and errors for invalid accesses. The four matrices contain **48,604 nodes
and 48,600 edges**. Tests also permute node IDs, check immutability, and compare
each training iteration with the parent across cold/warm starts and all rules.
All 30 new tests and 65 previous focused checks pass at this checkpoint.

Building the cache creates more static objects up front. Its time is charged to
initialization, and its prepared-node count is recorded separately from the
unchanged CFR visit count. This is a memory/setup tradeoff, not a memory-saving
or global Hold'em scalability claim. Full local checks pass: 1039 all-extras
tests on each of Python 3.11 and 3.12, and 1006 base-only tests with 24 optional
skips. Lint, typing and hooks pass; hosted CI and the fixed complete
interface/parity/paired timing run remain pending.

Read the [fixed plan](cached-node-graph.md). The next measurement uses the same
cases, seeds, planning margin and compute cap. It will retain slow outcomes too.
No learning rule or playing-strength result changes in this step. Codex assisted;
personal hands-on time is not inferred.

The complete fixed run now passes: all four interface matrices, all 96 training
trajectories at six checkpoints (576 comparisons), 708 timing rows and six profiler
cases. It took 213.257 seconds from clean published source `1991026`. The median
parent/cache loop ratio is **1.356×**. The smallest observed ratio is 1.040×;
every repeat is retained, including setup costs in the forecast. Report files
regenerate exactly on Python 3.12; historical timings themselves will vary.

The guarded training forecast falls from 16,337.788 to **12,432.056 seconds**.
That is still above the unchanged 7,200-second limit, before other pipeline costs.
This improves engineering speed; it does not make the agent stronger or establish
why its river policy is weak. The large learning comparison remains off.

Next we will measure independent cells running in separate CPU processes. Each
cell keeps its own fixed seed and trainer; parallel execution must match serial
results. Startup and contention will be measured, not assumed away. See the
[recorded table](../results/cached-node-profile/report/tables.md) and
[PR #25](https://github.com/jimmy-sim/poker-ai/pull/25). Hosted CI remains pending
at this evidence checkpoint.

## 29. Measure several independent training cells at once

**November 8, 2026.** The cached-node result is faster, but serial training still
exceeds the two-hour planning gate. The next question is whether independent runs
can use more of this Mac's CPU cores without changing their answers.

A **process** is a separate running Python interpreter. Each receives a fixed
list of cells, builds its own game trees, and creates a separate trainer and
fixed random generator for each cell. No strategy table or random state is shared.
This does not speed up the steps within one training trajectory; it lets unrelated
trajectories proceed at the same time.

**Example:** With two workers, cells 0, 2, 4 go to one and cells 1, 3, 5 go to the
other. If the first worker has harder cells, the entire batch waits for it. We must
measure that imbalance, startup and competition for CPU time; dividing serial time
by two would hide them. More processes also replicate trees in memory and consume
simultaneous resources.

The plan fixes one, two and three processes, three balanced-order repeats, and all
140 cells each time. All **1,260 endpoints** must exactly match the saved serial
arrays/RNG/work fingerprints before we compute any forecast. Timing is a short
calibration; it does not run the large learning comparison or measure poker skill.

The first spawn tests exposed a test-module import path problem. Giving child
interpreters the test source path fixed that fixture; no training equation changed.
All 37 new tests now pass, including actual spawned toy runs, deliberately failing
workers, early exits, timeouts and child cleanup. Strict typing passes (261 files).
All 132 focused checks pass. Full local suites pass 1076 all-extras tests on
each Python 3.11 / 3.12, and 1043 base tests with 24 optional skips. Lint,
typing and hooks pass. Spawned tests confirm child CPU accounting in all three
environments. Hosted CI and the fixed calibration remain pending at this
checked-code checkpoint. Read the [fixed plan](parallel-cell-calibration.md) and
[PR #26](https://github.com/jimmy-sim/poker-ai/pull/26). Codex assisted; personal
hands-on time is not inferred.

The fixed calibration completed all nine batches in **197.722 seconds**, from
clean published source `0dd5af6`. All **1,260 endpoints** exactly match serial
results, including work and cache counters. All repeats are retained. Report files
regenerate exactly on Python 3.12; timing itself varies with machine conditions.

One / two / three processes took median **33.163 / 18.691 / 13.827 seconds** per
short batch. Three processes give a measured median 2.400× elapsed-time speedup.
Median total CPU time rises from 33.175 to 40.795 seconds, because extra processes
replicate setup and use simultaneous resources. Faster elapsed time is not less
resource consumption.

The guarded known-cost forecasts are **12,250.546 / 6,299.036 / 4,257.374
seconds**. Two and three processes are below 7,200, but scoring and checkpoint
costs are still missing. The large learning comparison remains off. Next we will
verify those functions and measure the remaining pipeline costs with a fixed
three-process candidate. This is progress toward an affordable experiment, not
proof of stronger poker play. See the [table](../results/parallel-cell-profile/report/tables.md).
Hosted CI remains separately pending at this evidence checkpoint.

## 30. Check what a training checkpoint means

**November 8, 2026.** Three processes make the known training cost affordable on
paper. We still need to check the work of saving, scoring and reporting policies.
This step tests that machinery and calibrates OLD own policies; it does not launch
the larger learning comparison.

A **checkpoint** records a policy at a declared point. A work checkpoint saves the
first complete iteration that crosses its node-visit threshold, including any
overshoot. An iteration checkpoint saves that exact iteration. They answer
different questions, so the report keeps them separate. Reading or saving a
checkpoint must not change the next training update or random sequence.

The scorer divides exploitability into improvement available within the saved
information groups and extra improvement from exact information. Those pieces
must add back to the total. A separate river-switch number keeps the saved
opponent fixed; it does not predict improvement after retraining.

One subtle diagnostic: exact warm initialization can give every row positive
average mass immediately. That makes average coverage one while later sampled
river visits are still zero. Full coverage does not mean a good strategy.

A large reporting unit test also revealed unnecessary file padding. The internal
arrays have width 44 for wider chance menus, while a betting row uses two or three
actions. Files now save legal weights only and restore exactly the same matrix
bytes. The synthetic 840-record IO fixture streams one record at a time. The first
unit was interrupted during a run that also waited for macOS font discovery;
we did not measure RAM usage or establish a sole cause for its delay.

All 56 new fast checks and seven slower integration checks pass. The latter check
all 16 old published profiles, native values/replies and all eight labeled fixture
figures (60.58 seconds on Python 3.11, 59.17 on Python 3.12). Full local suites
pass 1132 fast tests on each Python version; base 1099 pass / 24 optional skips.
Typing/lint/format/hooks pass; hosted CI and formal timing runs remain pending. Fixture figures say **SYNTHETIC IO CALIBRATION — NOT LEARNING
RESULTS** and stay in scratch space. No new playing-strength result is claimed.

Read the [fixed plan](controlled-pipeline-check.md) and
[PR #27](https://github.com/jimmy-sim/poker-ai/pull/27). Codex assisted; personal
hands-on time is not inferred.

The first own-only cost run completed all 48 cases and three reporting fixtures
in 107.725 seconds from published source `f6ca5cb`. Its receipt is retained. CI also
caught a base-environment typing problem: an optional plotting dependency was
imported directly. The poker tests had not started in that CI job. Local base
pytest had passed, but base-only typing had been missed. We will fix that import
boundary, check base typing and repeat the same calibration under the corrected
source. No scientific gate or training rule changes; native timing and the large
learning run remain off.

The import fix now passes complete base `make check` on Python 3.11 and 3.12:
1099 tests passed, with 24 optional skips each. Clean typing passes in both minimal
environments, and the rendering integration passes again. No dependency, strategy
formula or scientific tolerance changed. The same fixed cost run will be repeated
from the corrected published source.

The corrected own-only cost run now passes full replay: 48 cases and all three
reporting fixtures in **107.174 seconds**, from clean published source `8843db1`.
The guarded own-stage forecast is **4674.496 seconds**, below 7200. It includes
checkpoint scoring twice, byte/hash round trips, setup and the slowest reporting
fixture. Every repeat is kept, including font discovery. These are timing
estimates, not a guarantee. Native comparison/cost is next; the large learning
run remains off.

The native comparison has now checked all 48 cases in **31.319 seconds**. Its
largest value/root/reply discrepancy is **1.21×10⁻¹³ chips**, below the 1e-9 limit.
These are comparisons of old own policies; no reference strategy enters training.

The combined report puts the guarded own-stage estimate at **4674.496 seconds**
and native stage at **543.838 seconds**, under their separate 7200 / 3600 limits.
That makes the planned experiment feasible on paper. It does not establish a
stronger agent. The next milestone is a checked runner for the original 140 cells,
with the original seeds and budgets. Only that experiment can provide new learning
outcomes. Read the [final cost table](../results/controlled-pipeline-check/report/tables.md).

Both report files regenerate exactly in the base Python 3.12 environment. That
checks the saved evidence and forecast arithmetic; it does not reproduce timing.
Hosted CI and main-checkout verification are the remaining checks for this
milestone.

## 31. Run a fair comparison of the training choices

*November 8, 2026 — issue #4; [PR #28](https://github.com/jimmy-sim/poker-ai/pull/28).
Codex-assisted implementation and drafting; personal hands-on time not recorded.*

**Question:** With the computer cost now manageable, which training differences
change the river weakness when the agent sees the same information groups?

The comparison keeps four switches separate: full versus sampled traversal,
signed versus clipped regrets, uniform versus increasing regret weights, and
uniform versus increasing strategy-average weights. A **regret** is a stored
score for how much a different action would have helped. **Clipping** replaces
negative stored regret with zero after the declared update. The two time weights
control different things: learning updates and the final averaged strategy.

Four on/off switches make sixteen combinations. We keep all combinations in
both known games and both representations. Sampled learning uses three fixed
random seeds; deterministic full runs are performed once. The extra full-only
bridge compares the original initialization/averaging conventions. Its final
point already exists in the common comparison, so it is referenced rather than
trained twice. This makes 140 actual runs.

**Example — invented numbers:** Suppose clipping reduces a gap by two chips with
uniform averaging but increases it by one chip with increasing average weights.
Saying “clipping helps” would hide that dependence. An **interaction** measures
how one switch's effect changes when another switch changes. The report keeps
these paired differences and interactions, along with every individual seed.
A three-seed average does not establish a precise population uncertainty interval.

The runner saves each work checkpoint at the first complete learning iteration
that crosses it. It also saves the exact iteration checkpoints, kept on a
separate axis. Together these produce 840 logical checkpoints. The observer
checks that scoring and saving do not change the learner's arrays, random state,
or work counters. Each worker then reloads its own strategies and recomputes the
scores. Strategies are stored one at a time; own reply fingerprints let us check
reconstructed replies without saving six redundant reply tables per checkpoint.

**Checks at this implementation checkpoint:** 58 new fast checks pass. The real
three-process runner completes all 140 cell identities on explicitly toy worlds,
with all 840 labels and archive replay. Hand-computed factor examples check first,
second, third and fourth-order differences. Tests reject missing or duplicate
cells, false work crossings, altered policies, nonfinite metrics, failed CI
receipts and changed source. Two slower native/render integrations pass in
34.35s / 37.24s on Python 3.11 / 3.12; they use old own policies and synthetic plot fixtures,
with new poker training and reference strategy export blocked. The synthetic
figure layout was inspected; it is not a learning result. Full base checks pass
both versions with 1157 tests and 24 optional skips each. Strict typing checks
293 files. The full optional suites also pass 1190 tests each, and the clean-source
correctness receipt checks 32 toy trajectories / 136 physical snapshots in
0.539277s. Final-source slower checks pass 39.74 / 38.26s. Hosted CI passes both Python jobs on `87fb4bc`; source-bound admission is
recorded before starting. No new Hold'em learning result exists yet.

One test caught an orchestration mistake: the old cached-node timing table has
sampled cells, while its parent table holds the full controls. The new runner
now uses the already checked combined lookup, preserving all 140 prefix targets.
No learning formula, seed, work limit or acceptance rule changed.

**Execution:** Checked code, the clean-source toy receipt, both CI jobs and the
admission receipt were published before the actual known-game comparison.
Every own outcome was then published before the native comparison. No strongest
recipe, default change, fresh-game or global-agent admission follows this
investigation automatically. The earlier failed sampled gate remains recorded.

Read the [execution protocol](controlled-learning-comparison.md). The own stage now completes all 140 runs and all 840 checkpoints in **36.02
minutes**, within the two-hour cap. Reloading every saved strategy reproduces its
own score with zero error, and all serial-prefix checks pass. The small archive
holds all owned strategies; the tables and eight figures keep every combination.
The independent native audit now passes every checkpoint too: its largest
value/response discrepancy is **1.71e-13 chips**, below the fixed 1e-9 limit. It
takes 92.19s, including its own-policy input replay. A base Python 3.12 environment
also replays all strategies with zero error and rebuilds all five numerical
report files byte-for-byte. The numbers come from the scripts and saved outputs,
not from the earlier toy checks or the cost forecast.

**What we learned:** Focus on the same deeper range-mass game that failed before.
At the 10-million-work label, hold regret time weights linear. With later
iterations weighted more heavily in the final strategy average, clipping lowers
mean exploitability from **4.354032% to 2.501852% of the initial pot**. But the
components move in opposite directions:

| Stored regret rule, linear average | Total | Within compressed information | Extra exact-information value |
|---|---:|---:|---:|
| signed | 4.354032% | 0.243207% | 4.110824% |
| clipped | 2.501852% | 1.811454% | 0.690398% |

Clipping makes the strategy less vulnerable to the opponent's finer legal
observations, while making it easier to improve on inside the compressed game.
“Exact” still respects hidden opponent cards; it uses exact own cards and the
public board. Percent of initial pot is a unit for these gains, not a win rate.

With equal weights in the final average, clipping instead makes total
exploitability **worse: 2.664089% to 3.525759%**. Both directions occur in all
three declared seed pairs in their respective comparisons. This is why “just
turn on clipping” is not a justified conclusion. All combinations, including
unfavorable ones, remain in the report; three seeds are not a confidence interval.

The gap between sampled and full traversal also remains after matching the work
label in this case. Matching iteration numbers is different: at iteration 128,
full traversal has about 5.45 million visits while the original sampled seeds
have about 47 thousand. Warm initialization gives every row average mass, so
100% average coverage does not mean all those rows were sampled. The report
keeps these work, coverage and averaging distinctions explicit.

**Next useful question:** Where does the larger within-partition gain occur, and
why does the averaging choice reverse the clipping effect? Inspect fixed saved
policies and own response traces before proposing a repair. The experiment
narrows the question; it does not yet make a globally stronger agent or erase
the earlier failed gate. Read the technical protocol's three interview answers
for the exact numbers, ordered bridge and remaining limits.

## Your own learning notes

**November 8, 2026 — your report:** You ran the correctness replay and the
controlled-training tests on your Mac. The replay passed and all 20 tests passed
in 2.53 seconds. This records your reproduction of the checks, without inferring
additional review or conceptual mastery.

**November 5, 2026 — your report:** You completed the suggested terminal commands
and got the expected results. Those exercises covered project navigation, a
focused card test, card conversion, hand evaluation, exact equity and opening
the recorded graph. This records your reported completion; it does not infer
additional code changes or that every concept has been mastered.

These prompts are for you to answer in your own words. Leaving one unanswered is
fine; it tells us what to explain next.

- After steps 1–5: How is “this hand wins” different from “this bet is good”?
- After steps 6–9: Why can an agent beat a simple opponent and still be exploitable?
- After steps 10–13: Why did we keep the ordinary sampler even though integration
  helped one game?

- After step 14: Why does passing four fresh cases still leave work to do on
  the global agent?

Further answers or questions can be added here with the date and worked through
in your own words.

## How this journal stays current

For each substantive implementation or research milestone, update the current
status and append a dated explanation of the question, what changed, a small
example, the actual checks/result, and the next decision. Link the technical
report and issue/PR. Explain new terms before using them.

Keep earlier failed results and distinguish corrections from new experiments.
Label teaching examples and preserve actual assistance and authorship. Personal
notes should reflect what you actually said or did. Updating happens with the
project work; this instruction does not schedule background work or filler entries.
