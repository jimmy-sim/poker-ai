# Let the own training opponent use finer legal information

Issue #4 comment 6790000490 registers this software foundation before code.
It follows the static river diagnostic: finer prior masses and ordered combo
outcomes add no distinctions in the known game. This is a different hypothesis,
not another static feature or a claimed repair.

## Question and definition of done

Can the same coarse agent learn a less vulnerable strategy when its own training
opponent uses more detailed own-card/public-board information? First establish
the mixed-information game construction and coarse-policy composition. No new
Hold'em learning or reference solver construction belongs to this foundation.

Given the same finite game with legal fine and coarse information groups:

- View 0 keeps seat 0 coarse and seat 1 fine.
- View 1 keeps seat 0 fine and seat 1 coarse.
- The final coarse policy takes seat 0's own rows from view 0 and seat 1's own
  rows from view 1. Fine-opponent rows are discarded.

Keep topology, chance, payoffs, owners and concrete action menus unchanged.
Check the complete fine-to-coarse mapping, equal-depth perfect recall,
observable-only information factorization, immutable source arrays and role/
context-bound policies. Reject invalid probabilities, changed game/mapping,
wrong-role bindings and mutation. Identity views must preserve every edge/value
and reply. Test both target signs, independent terminal sums/pure replies,
the two known poker games and cached-browser compatibility.

The [config](../configs/exact-opponent-views.json) pins the existing own card
model and two spot inputs. Adding the new modules changes the source cohort;
it does not carry over any historical training admission. Existing scientific
files/data remain unchanged and available in their original commits. Complete
source checks, a conservative forecast and published admission remain required
before a later real learning comparison. Own/native long caps remain 7200/900
seconds; software fixtures do not shorten or replace them.

## A small game with a known answer

Each player has a legal own signal identifying state 0 or 1, equally likely.
The coarse view groups those signals together. The first player chooses Safe
(payoff zero) or Risk, after which the other player chooses A or B:

| State | Target payoff after A | Target payoff after B |
| --- | ---: | ---: |
| 0 | +1 | -1 |
| 1 | -1 | +1 |

A coarse opponent must use the same response distribution in both states, so
Risk averages to zero. Risk/uniform is stable within that coarse game. A finer
legal opponent can choose B in state 0 and A in state 1, making Risk worth -1.
Safe still guarantees zero without any extra information. Thus the coarse
strategy space contains a safe policy even though it also contains a coarse
equilibrium vulnerable to finer deviations.

These are fictional payoff units and analytic policies, not a Hold'em result,
new training gain or unavoidable abstraction floor. Tests independently sum the
terminal branches and enumerate pure replies for both target seats. The example
motivates a controlled learning comparison; it does not predict its outcome.

## Before measuring learning

A future design must distinguish opponent information from the cost of running
two learning games. Compare a two-path coarse-opponent control with a two-path
fine-opponent treatment at the same per-seat work, and retain ordinary one-path
coarse/exact controls for practical compute comparison. Charge both initializations
and opponent updates; retain all seeds/readouts and negative outcomes. Freeze the
actual complete grid and source/forecast/admission before any real trajectories.

All training would use our own updater and legal acting-player information.
No actual other-player hidden cards, commercial outputs or reference strategies
enter the learner. Open-source references remain comparison-only. A known-game
result cannot promote a fresh/global/default agent without its separate gates.

## Initial implementation checkpoint — November 11

The mixed-view factory and seatwise composer are implemented without changing
the existing updater or any historical source file. Views own read-only copies
of game arrays; bound policies carry view and byte fingerprints. Fine-opponent
rows are discarded during composition. The checker reports software-only status
and cannot turn its output into a real training admission.

Thirty-two focused checks pass in 3.24 seconds; Ruff/format and strict typing
pass. Independent terminal sums and pure-reply enumeration cover both target
signs. Structural tests cover every decision node in both known poker games,
including different hidden opponent deals and different unrevealed rivers with
the same acting-player observation. They check equal policy edges/values, own
coarse grouping, fine opponent grouping, recall and unchanged inputs. Failure
tests cover incorrect games/roles/mappings/policies, mutation, forgotten history,
depth, incomplete output and interruption retention. The existing cached
saved-hand browser still loads all nine original snapshots.

Full local/optional/hosted source checks and a published software receipt remain
pending. No new poker trajectory or playing-strength/compression claim. The
three old seeds, scientific caps and strength gates remain unchanged; the future
learning grid is not selected by this software fixture.

1. **Does the fine opponent see my hidden cards?** It uses its own legal private
   signal/cards and the public board. Different hidden worlds remain grouped
   when its acting-player observation is unchanged.
2. **Why charge two initializations?** The final coarse table combines two
   separately learned roles. Each game has its own warm start and opponent
   updates; hiding one would give the treatment extra compute.
3. **Did this make the poker agent stronger?** No. It validates the construction
   needed to ask that question in a prospectively admitted learning comparison.
