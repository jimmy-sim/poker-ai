# Read a saved hand's four continuation columns

This exercise uses the completed continuation report already merged in your
main project. It reads saved simulation results. It does not deal new hands,
train a model or change a strategy. Completing it is optional; no personal
practice or time is recorded until you report it.

## 1. Open the saved nines example

At the normal Terminal prompt, enter these commands one at a time. If you see
Python's `>>>` prompt, enter `exit()` first. Do not copy prompt symbols.

```sh
cd /Users/jimmysim/Projects/poker-ai
.venv/bin/python scripts/inspect_turn_continuations.py
```

The default is the harder known spot, seed 20261302, mixed method, responding
seat 1. Its first displayed turn group holds `9c 9d` on `Ts 9s 4d 2h` and faces
a 36-chip bet with pot 72. The responding seat is the one allowed to change its
choices in the calculation. The opposite seat stays at its saved policy.

Find the `fold` and `call` rows. The call has four later-continuation values:

| Continuation | Call value, net chips |
| --- | ---: |
| Saved | -25.894981 |
| Best current-group river | -18.808061 |
| Best fine-information river | -16.994315 |
| Full fine reply | -16.994315 |

Folding is -18 in every column. Compare each call value with that number. The
first two prefer folding; the last two prefer calling. Negative means net
chips lost over the hand, not the immediate amount needed to call.

The first three columns keep every turn probability fixed when constructing
the continuation. The last column allows earlier turn choices to change too.
An action row evaluates choosing that action now and using the named later
continuation. The saved probability beside it tells you what the saved policy
actually does, not what the diagnostic recommends deploying.

## 2. Inspect the other large turn group

The first command prints and returns to your shell. Then enter:

```sh
.venv/bin/python scripts/inspect_turn_continuations.py --rank 2
```

This shows `Qh Kh` at the same board and bet. Calling is approximately -29.02,
-18.44 and -17.45 under the first three continuations, versus folding for -18.
The same preference switch appears. This is specific to the saved opponent and
game; another seed or opponent can change it.

## 3. Explore interactively

```sh
.venv/bin/python scripts/inspect_turn_continuations.py --interactive
```

At the browser's own prompt, type one letter and press Enter:

| Key | What changes |
| --- | --- |
| `n` / `p` | Next / previous turn group |
| `s` | Next training seed |
| `o` | Next saved method |
| `g` | Other known game |
| `t` | Other responding seat |
| `q` | Leave the browser and return to Terminal |

Use `q` before pasting another shell command. This browser's four columns stay
visible together; it has no separate suffix-toggle key.

Try `o` until the header says `fine_self`. Its restricted-river and fine-river
columns agree because its declared information groups are already fine. This
does not mean its saved play is optimal. Try `g` to compare the game with a low
stack-to-pot ratio (SPR), meaning little stack remains relative to the pot:
its tiny gaps and lack of additional fine-river gain are a useful control.

## 4. Connect an individual call with the root totals

Return to the default command from step 1. At the top, the target root values
change by approximately:

| Stage | Extra target chips |
| --- | ---: |
| Improve river play within current groups | 0.032537 |
| Add fine river information, saved turn play still fixed | 0.007434 |
| Allow the full reply to change turn play too | 0.638238 |

They sum to the original 0.678209-chip unilateral gap for this responding seat.
The fine river stage looks small at the root because saved turn play mostly
folds before those calls reach a river. A valuable conditional call and a small
realized root change can therefore coexist.

These stages describe replies to a fixed saved opponent. They are not measured
learning improvements, general poker advice, a win rate or a newly deployed
agent. The [method and all-seed report](turn-continuations.md) retain the limits.

## Questions to answer in your own words

- Why does the call become preferable only with finer river information here?
- Why can its conditional value matter when the fine river root stage is small?
- Which columns must agree in `fine_self`, and why can its total gap still be positive?

You can tell me which comparison made sense or felt confusing. That becomes a
dated learning note; simply providing this exercise does not record completion.
