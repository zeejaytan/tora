# Pre-registration: U17 ranker, Layer 2 (per-sherd nudge), Juglet (ticket 02)

Committed **before** any Layer 2 score is joined to a label. The report
(`scripts/l2_report.py`) prints the commit hash of this file; any change after that hash is
a new pre-registration and must say why. Layer 1 is unchanged (`preregistration.md`, e3f1b27).

## What is being tested

Can the break-gap check tell a sherd turned the wrong way on its own face from one turned
the right way, on GARF's real Juglet attempts? And does adding it to Layer 1 lift the 2
genuine attempts (Layer 1 alone: ranks 142 and 299 of 1,400) towards the top 5?

## The score (fixed)

Settings exactly as `scripts/l2_measure.py` at this commit: resampling 1% of pot, break if
|normal · wall| < 0.5 (wall direction within 3 wall thicknesses), neighbour zone 7.7%,
nudge at most 7.7% of pot and 20° (trimmed ICP keeping 70%, 30 iterations). Units: % of
pot size (Juglet: 1% = 0.65 mm).

| Item | Definition |
|---|---|
| Sherd gap | median distance from its break samples to the neighbours' break samples, after its nudge, over samples within the zone; no contact (< 10 samples) = infinite |
| Attempt score | **worst-sherd gap**: the largest sherd gap in the attempt; smaller is better |
| Least-sure sherd | the sherd with the worst gap (Layer 1's inside-out sherd if it failed Layer 1) |
| Layers 1+2 order | Layer 1 pass first, then worst-sherd gap ascending, then Layer 1 deviation |

No pass/fail cut-off is used. A cut-off (for an "unfixable" flag) would have to come from
real scanned sherds, not the Juglet, whose broken faces fit unrealistically perfectly
(true-assembly floor 0.6% against 1.0–1.9% on Fractura's real scans; ticket 02 log). That
is a separate decision; this ranking needs none.

## Read-outs

1. **Per-sherd separation, real near-misses.** In the 19 real near-miss attempts (9/9 own
   place, at least one not the right way round, by `own_place.score_draw`): the gaps of
   the wrongly turned sherds against those of the right-way sherds of the same attempts.
   AUC = chance a wrongly turned sherd reads the larger gap (0.5 = no better than a coin).
2. **Per-sherd separation, synthetic spins.** Each sherd of each of the 2 genuine attempts
   spun 180° about its own wall direction through its centre (18 synthetic near-misses);
   the spun sherd's gap against the unspun sherds' gaps in the same attempts. AUC.
3. **Least-sure sherd named right:** in how many of the 19 real near-misses the worst-gap
   sherd is a wrongly turned one (chance: wrongly turned / 9 per attempt).
4. **Attempt level:** worst-sherd gap of the 2 genuine against the 19 real and 18
   synthetic near-misses; attempt A (`garf_juglet_spun_t06`, worn_d400 ds1 #19) must score
   worse than B (`garf_juglet_genuine_t06`, noise_d100 ds1 #19).
5. **Ranks** of the 2 genuine among 1,400 and top-5 hit, Layer 1 alone against Layers 1+2.

## Controls (the ruler, not the method)

- **Spin on the true assembly:** each sherd of the correct reassembly spun 180° as above,
  one at a time, against the unspun true sherds. Must separate (AUC ≥ 0.9); if not, the
  ruler is broken and read-outs 1–5 mean nothing.
- **Small moves are forgiven:** the correct reassembly with every sherd moved 1–3 mm
  (1.5–4.6% of pot) in a random direction, 5 draws; and the same for each genuine
  attempt. The worst-sherd gap must stay below the true-assembly spins' median worst gap.

## Decision rule (fixed)

Layer 2 **earns its place on the Juglet** if read-out 1 AUC ≥ 0.75 **and** at least one
genuine attempt ranks higher under Layers 1+2 than under Layer 1 alone. Otherwise it is
reported as not separating on this pot, with the controls saying whether that is the
method (loose placement) or the ruler.

**Prediction, written down before the run:** weak. GARF places Juglet sherds at a typical
gap of 1.5% (about 1 mm), 2.5× the correct-fit floor; in development on the true assembly,
1 mm of jitter already made true joins and spins overlap heavily (close fraction 0.74–1.00
against 0.06–0.95). Expected AUC 0.55–0.70.

## What was looked at before this file was committed

- Label-free gap distributions of all 1,400 Juglet attempts (`l2_32147567/juglet_l2.json`,
  job 32147567): typical sherd 1.48%, worst sherd 2.37% median, 3 no-contact attempts. No
  label was joined to these scores.
- True-assembly floors and debug sections (jobs 32149018, 32149051, 32149123).
- Development on the true Juglet with synthetic damage (gap, overlap, spins, jitter),
  which set the nudge and zone sizes; no GARF attempt was used.
- Layer 1 results with labels (ticket 01): which attempts are genuine and near-miss, and
  their Layer 1 ranks. The Layer 2 settings above were chosen after that (16c67d3), but
  only from the true assembly with synthetic damage; no Layer 2 score of a GARF attempt
  has been read against its label.
