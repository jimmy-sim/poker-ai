# Explore public blockers to both ranges

This exercise browses saved simulation results. It does not train an agent or
accept a live hand. A **range** is a list of possible two-card hands. A public
**blocker** is a board card that makes one of those hands impossible.

Start in Terminal:

```sh
cd /Users/jimmysim/Projects/poker-ai
.venv/bin/python scripts/inspect_two_sided_blockers.py
```

The default is the previously investigated harder spot, second seed, mixed
training, seat 1 and the finer own river continuation. Read the five controls:

- `source_static`: the earlier groups, including own rank and opponent
  compatibility/showdown information.
- `own_public`: split further when public cards remove different hands from
  the responding player's declared alternative range.
- `both_public`: also distinguish public removal from the other player's range.
- `both_public_joint`: add the full compatible-hand table. With these fixed
  ranges, its information is already determined; it must match `both_public`.
- `exact_information`: give each exact own-information row its own group. Zero
  local disagreement here is a mathematical control, not optimal saved play.

The two costs use the earlier actual-posterior and compatible-prior action
values. **Lower cost means less disagreement within these groups under fixed
saved continuations.** It is not a win rate, exploitability or training gain.
Support and exposure weights are unchanged between controls. Compare each cost
with its own starting value; do not compare different denominators as if they
were independent hands.

For each example, read the complete declared range order. `True` means a hand
survives the public board; `False` means it is blocked. The joint table's rows
refer to seat 0's alternatives and columns to seat 1's. Our actual private hand
does not remove alternative hands from this public feature: the opponent does
not get to see it.

Now browse:

```sh
.venv/bin/python scripts/inspect_two_sided_blockers.py --interactive
```

Use **n/p** for another old source group, **s** for seed, **o** for training
method, **g** for game, **t** for responding seat, **r** for own river suffix,
and **q** to leave. A suffix is how our saved reply continues later in the hand.
The examples shown are selected for display; all rows remain in the report.

Try changing one setting at a time. Does the cost fall after `own_public`?
Does `both_public` lower it further? Does disagreement remain? These are
questions to investigate, not a quiz with an assumed favorable answer.

After the completed report is published, open its all-case figure:

```sh
open results/two-sided-report/dev_medium_oop.png
```

Every cell has the same meaning in all five panels. The figure uses one color
scale within this game: darker means less local disagreement. The last panel's
zero cost is expected from singleton groups. The all-case numeric table is
`results/two-sided-report/tables.md`; it retains zero and unfavorable outcomes.
