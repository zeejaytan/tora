# Pre-registration: U17 ranker, test on the held-out Fractura pots (ticket 05)

Committed **before** any Layer 1 rank of a test pot exists and before any score of a test
pot is joined to a label. `scripts/u17_test.py` prints this file's commit and refuses to
run if the cut-offs it is given differ from the calibration run's.

## What is being tested

The ranker exactly as calibrated (`calibration-fractura.md` Revision 3, run 32274553,
looked at by the lead and the conservator 2026-10-05), on GARF's 1,400 attempts at each
of the two pots held out of calibration. Nothing is tuned on these pots.

| Pot | Sherds | Genuine | Near-miss | Random top 5 | Role |
|---|---|---|---|---|---|
| narrow_bottle3 | 4 | 39 | 21 | 13.2% | **the test** (right answer rare but present) |
| galli_pot | 10 | 305 | 257 | 70.8% | side case: right often, so top 5 says little; read for near-miss separation |

Counts from the label run 32111374 (ticket 04); labels as there: *genuine* every sherd in
its own place and the right way round, *near-miss* every sherd in place, at least one
turned.

## Fixed settings

- Layer 1: `--profile outer --cover-pct 2 --io-gate off --near-pct 12 --unjudged fail`,
  pass if profile deviation ≤ **0.873% of pot** and no sherd unjudged. Inside-out reported
  only.
- Layer 2: gaps from job 32147567 (settings of `preregistration-l2.md`, ed7bd42).
  "Unfixable" flag at **2.31% of pot** (reported, not used in the order).
- Order (Layers 1+2): Layer 1 pass, then worst-sherd gap, then profile deviation.
- Pot size: nominal 100 mm, longest box side, as in calibration.
- Job: `scripts/hpc/u17_test.slurm`; renders of the top 5 per pot (`l2_top_look.py`) and
  the median genuine attempt's profile (`l1_look.py`) in the same job.

## Read-outs

Per pot: best genuine rank and top-5 hit, Layer 1 alone and Layers 1+2; the random
baseline; the classes in the Layers 1+2 top 5; near-misses ranked above the best genuine;
near-miss vs genuine worst-gap AUC; share of genuine attempts failed by Layer 1 and why
(profile or unjudged); share flagged unfixable; inside-out share (reported).

## Decision rule (fixed)

- **narrow_bottle3 passes** if a genuine attempt is in the Layers 1+2 top 5. Random choice
  does that 13.2% of the time, so one pass is a lead, not evidence the ranker works.
- **galli_pot** is read, not passed or failed: worst-gap AUC (calibration pots
  0.66–0.94) and how many of the top 5 are genuine against the 1.1 random choice gives.
- **Ruler checks, before reading any rank.** If any genuine attempt fails Layer 1 because
  a sherd is unjudged, Revision 3's rule is wrong for that pot: a broken measurement, said
  so, not a method failure. If genuine attempts fail on the profile cut-off, the
  `l1_look` render decides between a misplaced sherd and a measure fault before anything
  is reported.
- Every failure is named as one of: the method failed, the measurement was broken, or the
  reference answer was wrong.

**Known risk, written before the run.** narrow_bottle3 is **not round in section**: seen
down its axis the true reassembly is lobed (`u17_true_look`, below). Layer 1 compares each
sherd with its neighbours' outline in distance-from-axis and height, which assumes a round
pot, as SfS++ does. Judging only near joins (Revision 3) should keep neighbouring sherds
at similar distances, but the calibration pots were all round, so this is untested. If
genuine narrow_bottle3 attempts fail on the profile cut-off, that is first read as a
**broken measurement** for a non-round pot, checked on the render, not as the method
failing. (The earlier note in ticket 05 that narrow_bottle3 is "the same kind of bottle"
as narrow_bottle4 was about S-shaped sherds; the section shows it is not.)

**Prediction, written before the run:** narrow_bottle3, uncertain: either a top-5 hit as
on narrow_bottle4, or genuine attempts dropped by Layer 1 on the non-round section.
galli_pot (round, flared, flat base): genuine attempts pass Layer 1; worst-gap AUC
0.75–0.9.

**Weight.** One test pot of 4 sherds and one side case, one method (GARF), 1,400
attempts each from 70 runs. Whatever comes out is a lead for U17, not a finding.

## What was looked at before this file was committed

- Label counts per pot (ticket 04) and the label-free Layer 2 gap summaries (ticket 02
  groundwork). No rank of a test pot, and no score joined to a test-pot label.
- The correct reassembly of each test pot, drawn alone (`scripts/u17_true_look.py`; no
  attempts, labels or scores), to check for handles (Spartan, 2026-10-05, run `rwlora_eval_fresh_ds1_fractura_fresh_31835634`).
  Neither pot has a handle. narrow_bottle3: 4 sherds (one small, 111 of 5,000 points),
  tall, closed-looking top, lobed section. galli_pot: 10 sherds, round section, flat base
  (sherd 0), wall flaring to an open rim, several small sherds near the base.
