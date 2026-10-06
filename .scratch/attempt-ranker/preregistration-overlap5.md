# Pre-registration: U17 Revision 5, overlap by area away from joins, tested on fresh attempts

Committed **before** the fresh attempts exist and before Revision 5's measure has run on
any real attempt. `scripts/u17_overlap.py` prints this file's commit.

## Why, and what was looked at first

Revision 4 (`preregistration-overlap.md`, job 32345673) gated on the SHARE of a sherd's
surface inside another. Its drawings showed the fault: GARF seats joins slightly pressed
in, every join reads as a thin band of overlap, and on a tiny sherd that band is most of
it (GARF plate sherd 5, 59 of 5,000 points, 38-47% on correct attempts), so the cut-off
came out at 37.8%. The same drawings showed the overlap the conservator saw on TORA's
plate is real and seen: floor sherd 4 lying across rim sherd 3, 17%, against 1.6% on the
correct attempt. Revision 5 was designed after looking at those two drawings, so neither
pot's existing attempts can count for it. Decision to build it: conservator, 2026-10-06.

## The measure (fixed)

`scripts/overlap_measure.py`, field `area`: per sherd, the area of its surface inside
another sherd (as Revision 4 decides inside, unchanged), leaving out its own join strip
(its break faces, found as Layer 2 finds them, and one wall thickness either side), in
(% of pot)^2, i.e. square millimetres on a 100 mm pot. Per attempt: the worst sherd.

Synthetic check before this file (13-sherd ring, 6 mm wall, one small 12 mm piece, cloud
session): correct 1.0; every join pressed ~0.35 mm in 3.0; the small piece laid inside
another sherd's wall 363; a sherd slid half over its neighbour 514.

## Calibration (fixed rule, as Revisions 3 and 4)

GARF's five calibration pots (bundles 32147567, labels 32111374): per pot the 99th
percentile over genuine attempts of the worst sherd's area; cut-off = the largest. Order:
Layer 1 (Revision 3, unchanged) pass AND area at or under the cut-off, then worst-sherd
gap, then profile.

## The test: fresh TORA attempts

New TORA draws nobody has looked at: the untouched model (no adapter), Fractura's eight
unworn pots, sampling seeds 101-110, 20 draws each = 200 fresh attempts per pot
(`scripts/hpc/u10_juglet_arm.slurm`, `SET=fractura ARM=untouched`, seeds 101-110 in one or two submissions;
seeds 42 and 7 were the only ones used before). One arm, not 28 pooled, so the attempts
are one model's spread.

- **Which pots:** labelled first (`label_attempts.py`, same ruler); a pot is tested if it
  qualifies by the existing rule: genuine present and at most 10% of attempts. Decided by
  the job from the labels before any score is joined. If none qualifies, there is no test
  and the run says so.
- **Pass, per tested pot:** a genuine attempt in the Revision 5 top 5.
- Revision 3 is scored on the same fresh attempts, side by side, so the gate's effect is
  read on new material.
- **Checks, not tests** (seen pots): GARF's test pots and TORA's 32330575 attempts
  re-ranked under Revision 5; GARF narrow_bottle3, galli_pot and TORA narrow_bottle3 must
  keep a genuine in the top 5.

## Ruler checks, before reading any rank

- Converter self-check passes; GARF frame check as before.
- Open mesh edges per sherd are printed; a sherd with open edges has an unreliable
  outward direction; if a gate failure rests on one, it is said.
- Every genuine attempt failed by the gate is drawn (`overlap_look.py`: red = counted,
  orange = inside but within the join strip) before anything is reported.
- Every failure is named: method failed, measurement broken, or reference wrong.

**Prediction, written before the run.** The cut-off falls to a few tens of (% of pot)^2
(GARF's pressed joins now orange, not counted). Attempts with a sherd lying on another
fall out. That alone may not put a genuine attempt first: near-misses (every sherd home,
one turned) do not overlap, and on TORA's plate 32 of them ranked above the best genuine.
So on any fresh plate-like pot, expect the top 5 to fill with near-misses rather than
genuine; on a bottle-like pot, a pass as before.

**Weight.** One method's fresh attempts, one arm, the pots that qualify (likely one to
three). A pass is a lead for U17, not a finding.

## Result, job 32352965 (draws 32352963, 32352964), recorded before the rejected genuine attempts are drawn

**No test happened.** No fresh pot qualified: narrow_bottle3 and plate drew 0 genuine in
200 each (6 and 0 near-misses); galli_pot and narrow_bottle1 0 genuine; blue_pot,
narrow_bottle2, narrow_bottle4 and pink_bowl right 45-100% of the time. Revision 5 is
therefore **untested on unseen attempts**. (Earlier TORA rates, 9/560 and 5/560, make 0 in
200 likely-ish for the plate, about 1 in 25 for narrow_bottle3; the same labeller found
200/200 on narrow_bottle2, so the labeller is working.)

- Cut-off **71.0 (% of pot)^2**, set by GARF narrow_bottle4 (q99 of its genuine). Upper end
  of "a few tens".
- Checks hold: GARF narrow_bottle3, galli_pot and TORA narrow_bottle3 keep a genuine at
  rank 1.
- TORA plate (seen, design data): best genuine 84 -> 53, 32 near-misses still above it;
  top 5 now 3 near-miss + 2 other, worst overlap 4-23. Drawing `tora_plate.png`: the
  Revision 3 leader (floor sherd 4 lying across rim sherd 3) reads 74 and is out, only just;
  the new leader has small floor sherds 4 and 5 jumbled at the hub with little overlap (11).
  Prediction held: what remains above the genuine is misplacement without overlap.
- GARF plate drawing: correct attempt, every join orange (strip), nothing counted. The
  join-strip fix works as designed there.
- **Cost:** genuine attempts rejected: galli_pot 40 of 305 (13%, worst sherds 7 and 8,
  closed meshes), narrow_bottle4 12 of 1,394, narrow_bottle3 1 of 39. Kept attempts on
  galli_pot fall 1,162 -> 454. To be drawn (`scripts/hpc/u17_overlap5_look.slurm`) before
  this is called a real overlap or a ruler fault.
