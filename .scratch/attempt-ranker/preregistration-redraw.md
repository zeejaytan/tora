# Pre-registration: U17 ranker, re-drawn point sample on the Juglet (ticket 03)

Committed **before** any re-drawn Layer 2 score exists. `scripts/u17_redraw.py` prints
this file's commit and refuses to run if it has uncommitted changes.

## What is being tested

U17's second refute condition: *a scorer whose top 5 changes completely when the same
attempts are re-sampled with a different point draw ranks the sampling, not the
reassembly.*

Layer 1 reads each sherd's mesh vertices and has no random step, so it is not re-run.
Layer 2 (`l2_measure.py`) resamples each sherd's surface at random, evenly by area, at 1%
of pot (0.65 mm on the Juglet), before finding break faces and measuring gaps. Every run
so far used one draw (seed 3). This test changes only that draw.

- Attempts: the Juglet's 1,400 GARF attempts (bundles `juglet_32107634`), Layer 1 ranks
  `jug_v2_32274553/ranks.json` (Revision 3), unchanged.
- Original Layer 2: `l2_32147567/juglet_l2.json` (seed 3).
- Re-draws: seeds **11, 12, 13**, all other settings as `preregistration-l2.md` (ed7bd42).
- Control: seed **3** re-run, which must reproduce the original top 5 exactly. If it does
  not, the test is void (broken measurement: the score is not repeatable even without a
  new draw).
- Order, as the ranker: Layer 1 pass, then worst-sherd gap, then profile.

## Read-outs (per re-draw)

The re-drawn top 5 and how many of the original top 5 it keeps; where each original top-5
attempt now sits; the classes in the top 5 and the genuine attempts' ranks (key read only
after the order is fixed); how far each attempt's worst-sherd gap moved, in mm (median,
90th percentile, largest).

## Decision rule (fixed)

- **Refuted**: any re-drawn top 5 shares **none** of the original five.
- **Pass**: every re-drawn top 5 keeps **at least 3** of the original five **and** holds a
  genuine attempt.
- Anything between is **weakened**, reported with the per-draw read-outs.

## Prediction, written before the run

The original rank 1 (genuine, the one the conservator confirmed) leads rank 2 by only
**0.027 mm** of worst-sherd gap. A new draw moves gaps by some fraction of the 0.65 mm
sample spacing, likely more than 0.027 mm, so **rank 1 is expected to change in at least
one re-draw**. Predicted: pass on the "at least 3 of 5" count, but the genuine attempt
may drop out of the top 5 in one draw (the second genuine sat at rank 13). If rank 1 does
change, that is reported plainly: the conservator's pick-1 result rests partly on the draw.

## Weight

One pot, 2 genuine attempts among 1,400, three re-draws. It can refute; passing it adds
only that the Juglet result is not an accident of one draw.
