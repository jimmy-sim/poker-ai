# Verified claim drafts

- Implemented four exact CFR variants for Kuhn and Leduc; matched OpenSpiel 2.0.2 exploitability within 1.39e-16 ante chips/hand at the tested equal iteration budgets. This is implementation agreement, not zero remaining exploitability.
- Built a reproducible external-solver comparison across 5 restricted turn subgames; measured 36.84 percentage points mean action-frequency gap versus OpenSpiel CFR+ (equal spot weighting, three fixed agent seeds, reference-reach-weighted node MAE). The agent had higher restricted exploitability in 5/5 spots and lower hero EV versus the reference opponent in 5/5; this is not a full-game win-rate claim.
- Verified every exported node in 120,947 restricted-game tree nodes against OpenSpiel's parser and 880 passive private-card/river worlds against independent Treys showdown ranks and expected payouts. The exported mechanics are project code, so parser/solver agreement alone is not an independent full-engine validation.
