# 01: Does the break edge actually disambiguate the two flaps of `narrow_bottle3`?

**Type:** `wayfinder:research` (AFK)
**What to build:** The one test that separates "the information was there and the model
did not use it" from "the object genuinely has two answers and our reference is arbitrary
at that seam".

**Answers:** U2

**Blocked by:** None in principle — but **not free**, see the gate below. Needs
`narrow_bottle3`'s fragment meshes fetched from Spartan. No GPU.

**Status:** resolved 2026-09-07 — **the edges do disambiguate.** Reading (b). No GPU bought; one `scp` of four meshes and about twenty minutes of laptop CPU.

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

- [x] The resolution gate is reported first, with a number, and the test proceeds only if
      it passes
- [x] Both arrangements measured with the identical statistic, distributions shown
- [x] A render at the seam, at a view that resolves the gap being claimed
- [x] States which of the three: method failed, ruler broken, reference wrong
- [x] The answer is written back to `U2` either way — including "the object is genuinely
      ambiguous", which would refute part of U2's own framing

## What would make this not worth pursuing

If the fetched meshes turn out to be the same decimated geometry the clouds were sampled
from, there is nothing finer to look at and the question moves to capture, not analysis.

---

## Answer (2026-09-07)

**The two halves of this bottle do not fit in each other's places.** Put each flap where
the other belongs — and then let both of them shuffle about freely until the joins close
as tightly as they ever will — and the broken edges still stand open. The bottle as it
really is closes to **0.11–0.18% of its own size**, which on a 100 mm bottle is about a
tenth of a millimetre and is as tight as this scan can measure anything. The best swapped
bottle that exists sits at **0.58–0.61% typical and 3.2–5.7% at its worst tenth** — a
gape of three to six millimetres along much of the join.

**Which of the three: the method genuinely failed.** Not the reference — that was the
live alternative and this test was built to give it every chance. Not the ruler either:
the control is in the table below and it holds.

**What it means for U2.** The information that tells these two halves apart was sitting
in the break edges, in good condition, on a freshly broken pot, and the model did not use
it. This is the reading U2 argues for — the bottleneck is what the model does with what
it sees — arrived at on the one object in the corpus that could have overturned it.

### The numbers

Each fragment's break surface is its closest 2% of vertices, fixed once from the true
assembly, so the *same points* are measured in both arrangements. Gap = distance from
such a point to the nearest other fragment, as a percent of the bottle's own size.

| arrangement | | typical (p50) | worst tenth (p90) |
|---|---|---|---|
| **true**, as it really is | flap 0 / flap 3 | 0.23% / 0.12% | 0.38% / 0.17% |
| **true**, after settling — *the control* | flap 0 / flap 3 | 0.18% / 0.11% | 0.39% / 0.20% |
| **swapped**, best fit into the other's footprint | flap 0 / flap 3 | 1.10% / 2.53% | 3.41% / 5.78% |
| **swapped**, after settling — *the swap at its best* | flap 0 / flap 3 | 0.58% / 0.61% | 5.67% / 3.19% |

**The control is the row that makes this readable.** The settling procedure is run
identically on the true arrangement, and it leaves the true bottle where it is
(0.23 → 0.18%, 0.12 → 0.11%). So the optimiser is not simply dragging whatever it is
given into contact; when the pieces belong together it finds that they already do.

**Read the p90, not the p50.** Settling drops the swapped median from ~1.1–2.5% to
~0.6%, which looks like progress until you notice the *worst tenth got worse* for flap 0
(3.41% → 5.67%). That is the signature of edges that do not match: the fit can press one
stretch of the seam shut only by levering the rest of it open. The true seam has no such
trade-off — its p90 is barely above its p50.

### The resolution gate, which is why this needed meshes

Reported first, as the ticket required:

| | % of the bottle's own size |
|---|---|
| distance between neighbouring vertices within one fragment | **0.22 – 0.26%** |
| join gap in the **true** assembly | **0.11 – 0.23%** typical |
| the effect being tested | **1% and up** |

Against the 5000-point clouds those first two numbers were 1.8% and 1.8–2.3% — the
measurement and its own noise floor were the same size. On the meshes there is a factor
of five to twenty of headroom, which is what makes the comparison mean anything.

### Two instruments were built; the first one was wrong and its control said so

Worth recording because the failure was silent in every number it produced.

The first attempt defined the break surface as *every vertex within 1% of another
fragment*. Those distances came back spread almost evenly from 0 to the 1% cutoff, with
no pile-up near zero — because on a thin-walled bottle that band catches as much outer
wall near the edge as it does break face. Replaced with a fixed fraction (closest 2%),
which is rank-based and cannot be fooled this way.

The second attempt asked each flap to mate with **the anchor and the sliver alone**. It
scored a flap sitting in its own correct place at a **25% p90 gap** — an absurd answer
for a pot that is demonstrably assembled — because most of that flap's break surface
mates with *the other flap*, which had been left out of the target. Had it been run
without a control it would have produced a confident, wrong, and quite publishable-looking
number. The fix is the joint version above, where every fragment mates against every
other one.

### How much weight this can bear

**Solid for this object, and this object was the point.** One bottle, but it is the one
object in the corpus whose failure could have been no failure at all, and the test is
geometric rather than statistical — there is no run-to-run variation to worry about,
the scan either mates or it does not. The corpus's other exchange-like case (`plate`)
has not been tested this way.

**What it does not establish:** anything about the Juglet, which is *scattered*, not
exchanged (`.scratch/juglet-cause/issues/08`), and whose break edges are worn rather than
fresh. This bottle says the edges carry the answer when they are crisp; it says nothing
about whether they still do when they are abraded. That remains `O7`'s question.

### Where the work is

- `scripts/check_seam_swap.py` — the instrument, control included
- `scripts/render_seam_swap.py` — the picture
- `artifacts/nb3seam/narrow_bottle3_seam_swap.png` — rendered and inspected before any
  of the above was written. Row 1 is the true bottle, every break-surface point pale;
  row 2 the best swapped bottle, the same points orange to black along the whole join.
  **Note what the left-hand panels show:** from the outside the swapped bottle still
  reads as a closed bottle. The silhouette does not give it away. Only the seam does —
  which is a fair description of why a model might make this mistake, and exactly why
  the eval metrics could not tell an exchange from a collapse.
- `artifacts/nb3seam/nb3_mesh_vertices.npz` — the four fragment meshes (gitignored),
  from `ceramics.hdf5` on Spartan, which is a symlink to `fractura_real.hdf5`
