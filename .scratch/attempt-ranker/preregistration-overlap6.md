# Pre-registration: U17 Revision 6, overlap judged by how far it reaches from the join

Committed **before** Revision 6's measure has run on any real attempt.
`scripts/u17_overlap.py` prints this file's commit.

## Why

Revision 5 (`preregistration-overlap5.md`, jobs 32352965, 32376045) counted the overlapped
AREA away from a one-wall strip along each break. Its drawings showed the fault: GARF seats
long seams pressed slightly into each other, so the area grows with the length of the
seam, and a correct galli_pot attempt (133) read above TORA's plate attempt with a floor
sherd lying across a rim sherd (74). Measurement broken; not adopted.

The conservator, 2026-10-12: "it is ok to have gap, not ok to stick into each other too
much." A pressed join is shallow: its overlap stays close to the break, however long the
seam. A sherd lying on or through another overlaps far from any break. So Revision 6 asks
how far the overlap reaches from the sherd's own break faces, not how much of it there is.

## The measure (fixed)

`scripts/overlap_measure.py`, field `reach`: per sherd, which of its surface samples lie
inside another sherd (as Revisions 4-5 decide inside, unchanged); for those, the distance
to the nearest sample on the sherd's own break faces (found as Layer 2 finds them); the
95th percentile of those distances, in % of pot (mm on a 100 mm pot; 0 if no overlap).
Per attempt: the worst sherd. A sherd with no break face found reads infinite and fails;
the output's `breaks_found` says so for each sherd.

Synthetic check before this file (8-sherd ring, 100 mm across, 6 mm wall = 4.75% of pot,
cloud session, `scripts/overlap_synthetic.py`): correct 1.36; every join pressed ~0.6 mm 1.63; every join
pressed ~2 mm along the full 60 mm seam 3.58 (Revision 5 area: 0, Revision 4 share: 11%);
a sherd slid half over its neighbour 15.84; a sherd laid across the pot 17.19. Drawn:
pressed joins orange near the break, the slid sherd red away from it.

## Calibration (fixed rule, as Revisions 3-5)

GARF's five calibration pots (bundles 32147567, labels 32111374): per pot the 99th
percentile over genuine attempts of the worst sherd's reach; cut-off = the largest. Order:
Layer 1 (Revision 3, unchanged) pass AND reach at or under the cut-off, then worst-sherd
gap, then profile.

## No test, said before the run

Revision 5's fresh TORA draws (seeds 101-110, 200 attempts per pot) gave no pot that
qualifies as a test (genuine present and at most 10%). So Revision 6 has **no unseen test
of its benefit** in this run; every pot where it could help has been looked at. What it
can show:

- **Cost on unseen attempts:** the share of genuine attempts it rejects on the fresh TORA
  attempts at blue_pot, narrow_bottle2, narrow_bottle4 and pink_bowl (right 45-100% of the
  time, never ranked or drawn before). This is the first out-of-sample number for any
  overlap gate.
- **Checks (seen pots):** GARF narrow_bottle3, galli_pot and TORA narrow_bottle3 keep a
  genuine attempt in the top 5; TORA plate's Revision 3 leader (floor sherd 4 lying across
  rim sherd 3) is rejected.

## Ruler checks, before reading any rank

- Every genuine attempt rejected by the gate is drawn (`overlap_look.py --failed 3`, red =
  overlap reaching beyond the cut-off, orange = within it) on every pot, before anything is
  reported. If the red runs along a join, the measure is broken again and is said so.
- Open mesh edges and sherds with no break found are listed; a rejection resting on one
  is said.
- Every failure is named: method failed, measurement broken, or reference wrong.

## Prediction, written before the run

The cut-off lands at one to three wall thicknesses, roughly 3-10% of pot. TORA plate's
lying-across sherd reaches well beyond that (it overlaps the middle of the rim sherd) and
is rejected. Genuine attempts rejected on galli_pot fall well below Revision 5's 40 of
305; on the fresh pots, under 2% of genuine attempts are rejected. As with Revision 5,
the plate's top 5 will still hold near-misses rather than genuine: overlap is not what
puts those above the correct attempt.

## Weight

Five calibration pots, four seen check pots, four unseen pots for cost only, one method's
fresh attempts. Adopting Revision 6 on this would rest on seen pots for its benefit: a
design check, not a test. If adopted, the next fresh draw where a pot qualifies is its
test.

## Result, job 32804500 (e8be068), 2026-10-12

- Cut-off **9.665% of pot**, set by blue_pot (q99 of genuine: blue_pot 9.67, narrow_bottle4
  7.72, plate 4.93, narrow_bottle2 4.68, pink_bowl 3.53). Upper end of the predicted 3-10%.
- **Cost, unseen attempts:** genuine rejected only on blue_pot: 3 of 90 fresh (3.3%, above
  the predicted 2%), 14 of 1,377 on calibration (by construction). None on narrow_bottle2,
  narrow_bottle4, pink_bowl (fresh or calibration), GARF test pots or TORA's seen pots.
  Drawn (`u17_overlap6_rejected_*_blue_pot.png`): every rejection is a few red points on one
  spot of a long seam on sherd 2, where the break face was not detected, so the nearest
  detected break is far. A ruler fault, small.
- **Checks:** GARF narrow_bottle3, galli_pot, TORA narrow_bottle3 keep a genuine at rank 1.
- **Prediction failed on the case that matters.** TORA plate's Revision 3 leader (floor
  sherd 4 lying across the rim of sherds 1 and 3) reads **5.6%**, under the cut-off, and
  stays rank 1; best genuine 84 -> 74, 32 near-misses still above it. Drawn
  (`u17_overlap6_tora_plate.png`): all of sherd 4's overlap is orange. Two reasons, both the
  ruler: sherd 4 is a small wedge, so every point on it is close to its own break; and the
  overlap sits at the plate's rim, which the break finder counts as a break face (the rim's
  top runs across the wall, as a break does).
- **Named: measurement broken.** Reach from the sherd's own break cannot see a small sherd
  lying on another. Not retuned. Revision 6 is not adopted; Revision 3 stands. A next
  version would judge the overlap from the side of the sherd being lain on (how far into
  ITS surface, away from its breaks) and tell a rim from a break; it would need its own
  pre-registration.
