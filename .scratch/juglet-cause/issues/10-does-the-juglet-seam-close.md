# 10: Do the Juglet's own joins still close, or has abrasion taken material off its break edges?

**Type:** `wayfinder:research` (AFK)
**What to build:** The seam instrument built for `narrow_bottle3`, pointed at the Juglet's
own hand-built reassembly — a gate check on whether this vessel's wear can be seen at all
in the geometry we already hold, before any decision is taken to buy a better scan.

**Answers:** O8

**Blocked by:** None. The Juglet's fragment meshes are already on the laptop
(`artifacts/juglet_gt/groundtruth.obj`, `artifacts/juglet_v2_meshes/`). No GPU, no fetch.

**Status:** resolved 2026-09-09 — **the gate is passed on data, and the answer is a
one-sided negative.** The joins close as far as this scan can tell, which does not mean
they close.

## Why it exists

Ticket 09 asked whether wear produces the Juglet's *kind* of failure and came back "no,
and on n = 1". That leaves the map's route **(a)** — buy a capture that resolves the wear —
and route **(c)** — say it cannot be attributed. Before spending a conservation lab's time
on (a), there is one cheap check that has never been run on this object: **look at its
joins.**

The logic is one-sided and worth stating before the result, because it decides what the
answer can be used for:

- **If the true joins stand open**, that is direct evidence of material loss. The reference
  was hand-seated by the conservator, and a hand fitter cannot close a join where the
  material is gone. Wear would then be *measurable* on this vessel and route (a) is
  strongly indicated.
- **If the true joins close**, that establishes very little. It is consistent with no
  material loss, and equally consistent with loss too small for this scan to see, and
  equally consistent with loss taken evenly off both faces — which lets the fitter seat the
  pieces a little deeper and close the seam anyway.

So this can find wear and cannot rule it out. That is the honest shape of the test, and it
is why it is a gate rather than an experiment.

## The gate, checked first

`narrow_bottle3`'s seam test worked because its meshes carry vertices **0.22–0.26%** of
object size apart while the effect it measured was **1% and up** — five to twenty times of
headroom. The Juglet's meshes are coarser.

| | Juglet | `narrow_bottle3` |
|---|---|---|
| distance between neighbouring vertices within one fragment | **0.445 – 0.733%** of object size | 0.22 – 0.26% |
| in millimetres, on a 65 mm vessel | **0.29 – 0.48 mm** | (0.22–0.26 mm on a 100 mm bottle) |

Two to three times coarser, and against a smaller object. **The gate passes only for a
coarse question:** anything the size of the scan's own point spacing is invisible here.
Stated in advance: this test can see a join standing about half a millimetre open. It
cannot see a tenth of a millimetre.

## What to do

1. Measure, per vertex of every fragment, the distance to the nearest vertex of any other
   fragment, in the conservator's hand-built assembly. Report as a percent of the object's
   own size **and** in millimetres.
2. Report the vertex spacing first, as the floor the measurement cannot go below.
3. Render the measured quantity itself, per vertex and unbinned — not a proxy view.
4. State plainly what a closed seam does and does not establish.

## Acceptance criteria

- [x] The resolution gate is reported first, with a number, and in millimetres
- [x] The measured quantity rendered per-vertex, unbinned, not a proxy
- [x] States which of the three: method failed, ruler broken, reference wrong
- [x] States how much weight it can bear, and states the one-sidedness explicitly
- [x] Written back to `O8` and the map either way

---

## Answer (2026-09-09)

**The Juglet's joins close — but only to about the width of the scan's own resolution, so
this cannot be read as "the edges are undamaged".** Across all nine sherds, the break
surfaces sit **0.21–0.28 mm** from their neighbours typically, and **0.44–0.52 mm** at the
worst tenth. Neighbouring points on these meshes are **0.29–0.48 mm** apart. The gap and
the measurement's own noise floor are the same size.

In conservator's terms: **the reassembled juglet has no visible open seam anywhere, at the
finest scale this scan can describe — about half a millimetre.** Whether a tenth of a
millimetre of surface has been worn off the break edges is a question these meshes cannot
answer, in either direction.

### The numbers

Object size (longest side of the assembled vessel) = 65 mm, so 1% of object size = 0.65 mm.

| sherd | vertices | share touching another sherd (within 0.33 mm) | join gap, typical | join gap, worst tenth |
|---|---|---|---|---|
| 00 (the body, largest) | 24,294 | 5.5% | 0.23 mm | 0.52 mm |
| 01 | 2,565 | 55.0% | 0.23 mm | 0.47 mm |
| 02 | 3,493 | 35.6% | 0.23 mm | 0.48 mm |
| 03 | 3,651 | 27.7% | 0.28 mm | 0.52 mm |
| 04 | 6,211 | 31.4% | 0.24 mm | 0.47 mm |
| 05 | 5,126 | 42.8% | 0.22 mm | 0.46 mm |
| 06 | 8,421 | 26.2% | 0.25 mm | 0.50 mm |
| 07 | 4,479 | 39.4% | 0.24 mm | 0.47 mm |
| 08 | 2,094 | 58.7% | 0.21 mm | 0.44 mm |

Overall **23.8% of all vertices lie within a third of a millimetre of another sherd**.
Sherd 00's low share is expected and not a warning sign — it is most of the vessel's outer
wall, and outer wall has nothing to mate with. The measurement draws the break network
cleanly by itself in the render, which is the check that it is finding joins rather than
coincidences.

### The picture

`artifacts/jugseam/juglet_gt_seam_gap.png` — every vertex coloured by its distance to the
nearest other sherd, unbinned and unprojected, in millimetres. Bright is touching, dark is
far. **The break lines draw themselves**: the network of joins across the belly and the
shoulder appears as bright seams against a dark body, with no hand-drawn overlay. That is
what makes the table above trustworthy — the statistic is finding the joins, not averaging
over the whole vessel.

`artifacts/jugseam/juglet_gt_vs_scan.png` — the hand-built assembly beside the arrangement
the sherds were scanned in, nine colours. The top row is a closed juglet with a handle and
a rim. The bottom row is the jumble on the scanning table, with the body sherd sitting
clear of the rest. Worth keeping: the same "closest 2% of vertices" statistic reads
**0.14–0.19% of object size** on the *scan* layout too, which looks like a closed seam and
is nothing of the kind — the pieces are overlapping in the jumble. A summary statistic
about seams can be produced by an arrangement that is not a reassembly at all, which is
this workspace's recurring failure mode and the reason for the render.

### Which of the three

**None of them.** The method was not on trial, the ruler is not broken, and the reference
is sound — the map already settled that `juglet_gt` is the conservator's own hand-built
reassembly, fitted to the source fragments at a residual of 0.0000%. What this ticket found
is a property of **the data**: the question is smaller than the scan.

### How much weight this can bear

**As evidence that the Juglet's edges are undamaged: none.** It is one-sided by
construction, and it fails on the side that would have been informative. Three separate
reasons, all of which were foreseeable and two of which were stated before the result:

1. **Resolution.** A gap of 0.2 mm is indistinguishable from zero when the points are
   0.3–0.5 mm apart.
2. **The assembly was seated by hand.** If wear removed material evenly from both faces of
   a break, the fitter would simply have seated the pieces slightly deeper and the seam
   would close regardless. Only *uneven* loss — enough to stop a join closing somewhere —
   could have shown up, and it did not.
3. **The vessel is incomplete.** One piece was never recovered, so one stretch of break
   edge legitimately has no mate and contributes nothing either way.

**As evidence that we cannot reach this question with the data we hold: solid, and it is
the third independent instrument to say so.** Gate A (job 29404479) found no fracture-like
roughness at any resolvable scale. Ticket 05 found the wear unmeasurable at 0.1% of object
size. This finds the joins unmeasurable at 0.3–0.5 mm. Three different quantities, three
different instruments, the same wall.

### What it means for `O8`

Route **(b)** is now spent — ticket 09 ran it and it did not attribute the failure. Route
**(a)** is the only route that can still attribute wear on this vessel, and it is
conservation-lab work, not compute: a capture finer than about 0.1 mm on this object, or
the same pot scanned before and after controlled abrasion. Everything that can be squeezed
from the existing scans has now been squeezed, by three instruments that agree.

**The recommendation this ticket supports:** close `O8` on route **(c)** — state that the
Juglet's failure cannot be attributed to its wear with the data that exists, and say what
capture would change that — unless the conservator judges route (a) worth the lab time. The
failure to attribute is a result, and it is a more useful one than a fourth instrument
finding the same wall.

### Where the work is

- `artifacts/jugseam/juglet_gt_seam_gap.png` — the measured quantity, per vertex
- `artifacts/jugseam/juglet_gt_vs_scan.png` — the assembly beside the scan-table layout
- `artifacts/jugseam/juglet_gt_gaps.npz` (gitignored) — the per-vertex distances
- `scripts/check_seam_swap.py` — the `narrow_bottle3` instrument this gate was checked
  against; **not run here**, because the Juglet is scattered rather than exchanged and
  there is no candidate swap to test
