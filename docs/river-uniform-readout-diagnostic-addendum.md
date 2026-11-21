# Prospective diagnostic detail for the fixed average-readout panel

This addendum refines only the representative-decision readout in the
[already published contract](river-uniform-readout-spots.md). It precedes
cohort selection, training, profile and outcome scores. The original
protocol, seeds, work, controls, thresholds and caps remain byte-identical.

For each of the four fixed spots, calculate additive exact best-response
contributions for the final 10m **linear control** in all three fixed seeds.
Average each exact information row's contribution across seeds. Among rows
with positive mean contribution and positive summed saved-prefix reach,
rank turn and river separately by descending mean; break ties by ascending
exact information index and retain at most three per street. If fewer than
three qualify, report all qualifying rows and the count. At each selected
row report both final 10m readouts for all three seeds, including own hole
cards, public board, legal actions, saved probabilities, counterfactual and
saved-prefix reach, conditional best-response suffix action values, local
saved-continuation action values and additive contributions. The selected
rows are fixed from the control before looking at candidate contributions;
they cannot change the experiment classification. Recompute and verify the
two-seat trace sum against every published own exploitability score within
1e-9 chips. Cap the complete diagnostic at 900 seconds; retain failure and
partial report if this added cap fails, without rerunning for a favorable
selection. These values describe the saved opponent profile and exact
best-response continuation in the finite restricted game, not universal
poker advice.

The isolated diagnostic code will be included in the exact-source fingerprint
before any training. Codex assisted; human hands-on time was not recorded.
