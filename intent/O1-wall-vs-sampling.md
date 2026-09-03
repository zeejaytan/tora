# O1 — Can the network resolve a real pot wall at all?

**Status:** open · **Blocked by:** none · **Effort:** ~1 day · **Priority:** highest

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

## Done when

`measure_wall_vs_sampling.py` has reported the wall/cell ratio at real Caucasus
dimensions, **and** we have committed in writing to one of:

- [ ] the ratio is workable as-is, or
- [ ] the corpus specification sets object scale and point budget so that it becomes
      workable, or
- [ ] this is a **sampling-density** finding, not a data finding, and the corpus is premature.

## What it can stop

If a real pot wall at TORA's sampling density lands under about one cell, **no corpus
of any size fixes it.** That is a genuinely important negative result and belongs in
the thesis — it reframes the problem from "we need more pottery" to "the network
cannot see the surface it is supposed to match on".

## Source

`../../CSC/docs/notes/PLAN.md` §R0.
