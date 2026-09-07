# 01: Does the break edge actually disambiguate the two flaps of `narrow_bottle3`?

**Type:** `wayfinder:research` (AFK)
**What to build:** The one test that separates "the information was there and the model
did not use it" from "the object genuinely has two answers and our reference is arbitrary
at that seam".

**Answers:** U2

**Blocked by:** None in principle — but **not free**, see the gate below. Needs
`narrow_bottle3`'s fragment meshes fetched from Spartan. No GPU.

**Status:** ready-for-agent

## Why it exists

`narrow_bottle3` is the corpus's only clean **exchange**: the model puts each of the
bottle's two halves where the other belongs, the same way in all ten attempts
(`.scratch/juglet-cause/issues/07`). The bottle is **freshly broken** — its break edges
are crisp and undamaged, unlike the Juglet's.

So one of two things is true, and they demand opposite responses:

- **(a) The edges do not disambiguate.** A lengthwise split of a near-symmetric vessel
  can leave two nearly mirror-image edges. Then the object has two near-equal correct
  answers, no perception could have chosen between them, and our reference is arbitrary
  at that seam — which also means one of the corpus's failures is not a failure.
- **(b) The edges do disambiguate.** The information was sitting there in good condition
  and the model did not use it. That is a real failure, and it is evidence for
  [U2](../../../intent/U2-perception-or-placement.md)'s reading that the bottleneck is
  what the model does with what it sees.

Nothing measured so far separates these. Shape similarity (3.1% of pot size between the
two flaps, PCA-aligned) says the *bodies* are alike; it says nothing about the edges.

## The gate that was checked first, and it failed (2026-09-07)

**The test cannot be run on the saved point clouds. They are too coarse to see a seam at
all.** Measured on `artifacts/nb3/whole`, `narrow_bottle3`:

| | as a percent of the bottle's own size |
|---|---|
| distance between neighbouring points *within* one sherd | **1.8%** (median) |
| gap at the joins in the **correct** assembly, 10th percentile | 1.8 – 2.3% |

The correctly assembled bottle already reads as having a **2% open seam** — about 2 mm on
a 100 mm bottle — purely because that is how far apart the points are. The whole pot gets
5000 points, so each sherd is a sparse shell, and the quantity this test needs to measure
is the same size as the sampling interval. A seam measurement here would be measuring the
sampler.

This is the rule in the workspace `AGENTS.md` — *check the view resolves the scale being
tested* — doing its job before the instrument was built rather than after. Four wear
renders were lost to exactly this once (`docs/lessons.md`).

**What it needs instead:** the source fragment meshes, at full vertex resolution, from
the ceramics dataset on Spartan (`/data/gpfs/projects/punim2657/TORA/dataset/`). One
object, a few fragments — a small `scp`, not a job. `scripts/render_join_gap.py` already
measures nearest-other-fragment distance per vertex on meshes and is the prior art.

## What to do

1. Fetch `narrow_bottle3`'s fragment meshes to `artifacts/`.
2. Confirm the resolution gate passes on the meshes: the join gap in the **true**
   assembly must sit well below the effect being tested. If it does not, stop and say so
   — the answer is then "not decidable with the scans we have", which is a real result
   and is the same shape as `O7`'s capture problem.
3. Best rigid fit of flap 0 into flap 3's true footprint and the reverse (PCA
   initialisation over the proper sign flips, then ICP), leaving the anchor and the
   111-point sliver where they are.
4. Measure the seams in both arrangements with the same statistic — per-vertex distance
   to the nearest other fragment, low percentile — and report the distributions, not just
   the summary.
5. Render both arrangements at the seam, plus the measured quantity itself, per-vertex
   and unbinned.

## Acceptance criteria

- [ ] The resolution gate is reported first, with a number, and the test proceeds only if
      it passes
- [ ] Both arrangements measured with the identical statistic, distributions shown
- [ ] A render at the seam, at a view that resolves the gap being claimed
- [ ] States which of the three: method failed, ruler broken, reference wrong
- [ ] The answer is written back to `U2` either way — including "the object is genuinely
      ambiguous", which would refute part of U2's own framing

## What would make this not worth pursuing

If the fetched meshes turn out to be the same decimated geometry the clouds were sampled
from, there is nothing finer to look at and the question moves to capture, not analysis.
