# Pre-registration: U17 Revision 4, an overlap gate (after ticket 06)

Committed **before** any overlap is measured on a real attempt. `scripts/u17_overlap.py`
prints this file's commit.

## Why

TORA's plate (job 32330575): the four rim sherds right, the two small floor sherds put on
the rim or swapped at the hub, ranked above every correct attempt. The conservator saw it
first: "there are more overlaps of sherds in the top 5 assembly" (2026-10-05). Neither
layer measures overlap. Layer 2 takes the distance from a sherd's break to its
neighbours', so a sherd sunk into another reads as a tight join. Thesis aim 2 already asks
for hard rejection of interpenetrations. Decision to build it: conservator, 2026-10-05.

## The measure (fixed)

`scripts/overlap_measure.py`, label-free, on the same bundles the ranker reads. Each
sherd's whole surface is sampled evenly (1% of pot spacing, as Layer 2). A sample is
inside another sherd if it lies behind that sherd's surface by more than a quarter of its
wall, or lies on that surface facing the same way with the other skin reaching round it on
every side (a sherd stacked on another). Faces meeting at a correct break face each other
and count as neither. Per attempt: the worst sherd's share of surface inside another, %.

Synthetic check before this file (12-sherd ring, 6 mm wall, cloud session): correct ring
0.25-0.38% (specks at join corners), a sherd slid half over its neighbour 34%, a sherd
sunk half a wall 3.7%, a sherd pulled out 8 mm 0.08%.

## Calibration (fixed rule)

On GARF's five calibration pots (blue_pot, narrow_bottle2, narrow_bottle4, pink_bowl,
plate; bundles of job 32147567, labels 32111374): per pot, the 99th percentile over genuine
attempts of the worst sherd's inside share; the cut-off is the largest of the five, the way
Revision 3 set its profile cut-off. Revision 3 is kept exactly (Layer 1 profile 0.873%,
judged near joins only, a sherd touching no neighbour fails; inside-out reported only).
Revision 4 order: Layer 1 pass AND overlap at or under the cut-off, then worst-sherd gap,
then profile.

## What this run can and cannot show

Every Fractura pot with genuine attempts has now been seen, so **this run has no fresh
test**. It is the calibration plus checks on seen pots, reported as checks:

- Non-regression: GARF narrow_bottle3 and galli_pot (test 32317912) and TORA narrow_bottle3
  (32330575) keep a genuine attempt in the Revision 4 top 5. A loss there is reported as
  Revision 4 failing, whatever plate does.
- The motivating case: TORA plate, Revision 3 vs Revision 4 top 5. A plate hit shows the
  gate does what it was built to do; it is **not** evidence that it works, since the gate
  was designed after looking at plate.
- A real test needs attempts nobody has looked at. Proposed, not part of this run: new
  attempts (another method, new seeds on the Juglet, or new pots), with this file's
  cut-off fixed.

## Ruler checks, before reading any rank

- Open edges per sherd mesh (written by the measure) must be 0. If not, the outward
  direction is unreliable for that sherd and its overlap is not read.
- Any genuine attempt failed by the overlap gate on any pot is drawn
  (`overlap_look.py`) before anything is reported: a misplaced sherd, or a measure fault
  (a stacked-skin false alarm at a join, a wrongly signed normal).
- GARF's bundles were built by the converter before it undid a run's scale and shift
  (0dce053). The job prints GARF's clouds' scale and shift against the scans per pot; if
  either is outside the converter's tolerance, the GARF calibration bundles are rebuilt
  before anything is read.
- Amended 2026-10-06, before any overlap was measured (job 32331355 stopped at this
  check, 14 s in): the converter's frame check compared sherd centres by plain vertex
  means, which lean towards dense parts of a mesh, and refused GARF's galli_pot at 3.2%.
  Centres are now area-weighted, as the runs' clouds are (`rank_convert.area_centre`;
  synthetic uneven mesh: vertex means 4.2% off, area-weighted 0.6%). TORA's bundles
  (32330575) used the old shift estimate; the job prints how far the new one differs. If
  more than 0.3% of pot, TORA's bundles are rebuilt and re-ranked before anything is read.
- Every failure is named: method failed, measurement broken, or reference wrong.

**Prediction, written before the run.** Genuine GARF attempts overlap little (cut-off
under 2%). TORA plate's Revision 3 top 5 are well above the cut-off. Plate's genuine
attempt reaches the top 5 under Revision 4: uncertain. The 71 near-misses keep every sherd
in its own place, turned, so they do not overlap and still compete on gap. No pass lost
on the three non-regression pots.

**Weight.** Calibration on one method's five pots; checks only. Nothing here can be
written into U17 as established.

## Result (job 32345673, 2026-10-06), appended after the run

Cut-off 37.8% (GARF plate). Non-regression held on all three pots. TORA plate not
rescued (84 -> 81). Ruler fault, found on the drawings: join bands counted as overlap, a
large share of a tiny sherd. Prediction "cut-off under 2%" was wrong. Details: ticket 06.
