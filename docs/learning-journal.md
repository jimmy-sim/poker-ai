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

The latest experiment, issue #2, is finished. A new way of handling river cards
helped one small game's final median result and hurt three. Both methods passed
the experiment's final development limits. The existing default stays in place.
Fresh validation games are the next planned step; they have not been run.

You can read this in three sittings:

- **Steps 1–5:** How the program represents cards and runs a legal hand.
- **Steps 6–9:** How it learns decisions and how we judge those decisions.
- **Steps 10–13:** What the extensions and recent experiments taught us.

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

## What comes next

[Issue #3](https://github.com/jimmy-sim/poker-ai/issues/3) plans fresh, fully
specified games and acceptance rules before collecting their outcomes. The
learning procedure must be frozen before those games are tested.
[Issue #4](https://github.com/jimmy-sim/poker-ai/issues/4) concerns a representation
that preserves useful public-board information without storing every exact case.
Neither investigation has been completed. The global training comparison remains
subject to its prerequisites.

For now, the useful achievement is a system that can test an idea, find a mixed
result, and preserve enough evidence to explain the decision.

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

## Your own learning notes

These prompts are for you to answer in your own words. Leaving one unanswered is
fine; it tells us what to explain next.

- After steps 1–5: How is “this hand wins” different from “this bet is good”?
- After steps 6–9: Why can an agent beat a simple opponent and still be exploitable?
- After steps 10–13: Why did we keep the ordinary sampler even though integration
  helped one game?

No personal learning claims have been filled in on your behalf. When you give an
answer or ask a question, we can add it here with the date and work through it.

## How this journal stays current

For each substantive implementation or research milestone, update the current
status and append a dated explanation of the question, what changed, a small
example, the actual checks/result, and the next decision. Link the technical
report and issue/PR. Explain new terms before using them.

Keep earlier failed results and distinguish corrections from new experiments.
Label teaching examples and preserve actual assistance and authorship. Personal
notes should reflect what you actually said or did. Updating happens with the
project work; this instruction does not schedule background work or filler entries.
