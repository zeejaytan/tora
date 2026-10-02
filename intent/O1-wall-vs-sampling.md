# O1 — Can the network resolve a real pot wall at all?

**Status:** decided 2026-10-02 — the corpus spec keeps every vessel at or above the
Juglet's ~1 cell, by object scale and point budget; still to check on the first real
Caucasus meshes · **Blocked by:** none · **Effort:** an hour per batch of meshes
· **Priority:** no longer blocks starting CSC

## Why it matters

A fracture in a vessel is a **ribbon through a wall**, not a face through a body. TORA
samples 5000 points per object, giving cells of `sqrt(2*area/5000)`. If fewer than
about one cell fits through the wall, the network never gets a row of points on the
break face — it is matching sherds on their **outer profile** instead.

Already measured: the median training vessel gets **0.78 cells** through its wall and
mates at 83–96°, against 152–177° for objects above 4 cells. Recorded by
`scripts/screen_vessel_corpus.py`.

Caucasus coarse wares run roughly **5–12 mm of wall on vessels of 15–40 cm** — a wall
of about **2–5% of object size**. Nobody has yet computed the cell size at that scale.

## The Juglet, measured (2026-10-02)

GARF also samples 5000 points weighted by area (`GARF/configs/data/breaking_bad.yaml`), so
one ratio covers both networks. `scripts/o1_juglet_wall.py` runs the corpus screen's own
functions on `artifacts/juglet_gt.hdf5` (the conservator's reassembly, 9 sherds):

| | % of object size (bbox diagonal) | cells through the wall |
|---|---|---|
| wall, exact ray | 2.86 (sherds 2.3–3.8) | **1.04** |
| wall, 2V/A (independent route) | 3.65 | **1.32** |
| point spacing | 2.76 | — |

The two routes agree within 1.3×. Looked at (`artifacts/o1_juglet_wall_section.png`, a
centre cut with the sampled points overlaid): the wall is about 1–1.4 point-gaps thick
and a break face gets **about one row of points, sometimes none**.

So the Juglet sits **at the margin**, about where the training Mug (1.07 cells) sat.
GARF's rough-break adapter still gained there (`../../GARF/intent/G1`), so ~1 cell is
enough for break texture to matter. That has been shown on one pot, and not shown to be
comfortable.

**Caucasus range, estimated from the Juglet's spacing (not measured on meshes):** with
spacing at 2.2–3.4% of object size (training vessels and the Juglet), a wall of 2–5% gives
roughly **0.5–1.8 cells**: 0.7–1.8 if "2–5%" is of the diagonal, 0.5–1.3 if of height.
Thick-walled small vessels sit at or above the Juglet; large thin-walled jars sit below
anything shown to work. Cells grow with the square root of the point budget: 10,000 points
gives ×1.4 and 20,000 gives ×2.

## Done when

- [ ] `measure_wall_vs_sampling.py` (or `scripts/o1_juglet_wall.py`) has reported the
      wall/cell ratio on **real Caucasus meshes** (the first C3 profiles revolved), not
      only the estimate below, **and** we have committed in writing to one of:

- [ ] the ratio is workable as-is, or
- [x] the corpus specification sets object scale and point budget so that it becomes
      workable, or — **chosen 2026-10-02 (conservator):** floor of ~1 cell through the
      wall, the Juglet's level, where GARF's break-face gain was seen. Vessels below it
      get more points (cells grow with √points) or are flagged as below the tested range.
- [ ] this is a **sampling-density** finding, not a data finding, and the corpus is premature.

## What it can stop

If a real pot wall at TORA's sampling density lands under about one cell, **no corpus
of any size fixes it.** That is a genuinely important negative result and belongs in
the thesis — it reframes the problem from "we need more pottery" to "the network
cannot see the surface it is supposed to match on".

## Source

`../../CSC/docs/notes/PLAN.md` §R0.
