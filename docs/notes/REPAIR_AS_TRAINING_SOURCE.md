# Should RePAIR be used to train an adapter? — job 29766242, 2026-08-31

The question: RePAIR ships real worn fractures with archaeologist-verified
matches. It does not look like pottery. Can "how two fractured pieces go
together" be distilled out of it and carried into a pottery model by a LoRA, or
does the fresco shape pollute the checkpoint?

## The measurement that was supposed to settle it, and did — the other way

A fresco plaque was assumed here to be **"the thin-slab case, the same geometry
as an eggshell sherd"** (`WEAR_V3_PLAN.md` §4). If that were true, TORA's
sampling could not resolve the fracture ribbon and an adapter would necessarily
learn plaque outline instead of break shape — the pollution, arriving through
the front door.

**It is not true.** 62 fragments, `measure_repair_slab_vs_sampling.py`:

| | median | p10–p90 |
|---|---|---|
| slab thickness (cloud) | **23.46 mm** | 16.62 – 40.47 |
| slab thickness (2V/A, ribbon out of denominator) | 16.27 mm | |
| longest span | 85.26 mm | |
| fracture ribbon | **28.3 %** of surface area | |
| aspect (span / thickness) | **3.34** | |

Cells through the slab at TORA's 5000-point budget:

| pieces per object | spacing | cells | points on ribbon |
|---|---|---|---|
| 2 | 2.95 mm | 7.96 | 1415 |
| 5 | 4.66 mm | 5.04 | 1415 |
| 10 | 6.59 mm | 3.56 | 1415 |
| 20 | 9.32 mm | 2.52 | 1415 |

**Zero of 62 fragments fall under one cell.** The thinnest is 7.6 mm, still 1.63
cells. These are not eggshells; they are bricks with an aspect ratio of about 3.

Rendered before this was believed — `artifacts/repair_slab_vs_sampling.png`,
cross sections with the 4.7 mm cell drawn to scale. The red fracture band sits
on the left and right ends, the broken perimeter, with the grey flat faces top
and bottom: the classifier is picking the break, not the painted front. Four to
five rows of sampled points fit across the ribbon.

**For comparison, on the same instrument:** our own training vessels get a
median of **0.78 cells** (job 29764781), and real pot scans put only 4 % of
their points (182–212 of 5000) on a fracture. RePAIR would give TORA **1415
resolved fracture points per object — about seven times what our real pottery
delivers, and on a break face our own training data does not resolve at all.**

## What this does to the three arguments against

1. **"The join is not inside what the network reads."** Dead. It is, and more of
   it than anywhere else we have.

2. **Gate A: no fracture-like micro-texture in RePAIR** (`GATE_A_RESULT.md`,
   texture rising as R^1.7 where fresh fracture is self-affine at R^0.4–0.8;
   0.0018 mm of relief at the finest 0.40 mm scale). Still true, and still
   largely beside the point for *this* question: TORA's cell is 4.7 mm. It never
   reads sub-millimetre interlock from anything. What it reads is the coarse
   undulation of the break ribbon, and that is present and well sampled.

3. **Job 29623885, where an adapter dropped worn pottery from 79 % to 62 % of
   fragments correctly placed.** Still the governing precedent — but read its
   diagnosis. The cause was that **every training join was a perfect-contact
   join**: 44 % of vertices exactly coincident in the fresh third, the hardest
   training example still 11× tighter than the easiest test object. RePAIR is
   the one source we have that **does not share that defect** — separately
   scanned, genuinely worn, genuinely apart.

## What remains against

- **Shape mismatch is real, and it is not the one assumed.** A 23 mm plaque's
  break is a broad face through a body. A sherd's is a narrow ribbon through a
  shell. Geometrically RePAIR sits closer to the **solid** objects the corpus
  screen is currently finding in our own training set (Bottles at fill 0.97–1.00)
  than to a pot wall. That is a genuine reason for caution and it is testable.
- **The literature ceiling.** [E-M3RF](https://arxiv.org/html/2511.21422) trains
  on RePAIR and reaches **35.91 %** part accuracy on RePAIR's own test set; the
  same architecture on Breaking Bad reaches 92.01 % on Fantastic Breaks. The only
  reported transfer from a RePAIR-trained model is RePAIR→Presious (fresco→fresco,
  57.49 %). No RePAIR→pottery result exists anywhere.
- **We do not have the ground truth locally.** The Spartan copy is
  `repair/OPEN_DISCOVERY/pieces`, 62 loose fragments, no assembly grouping and no
  poses. Training on it requires fetching the full release.
- ~1 fragment in 4 is contaminated by the flat-slab assumption in the Gate A
  classifier (`RPf_00579`).

## Two corrections to existing notes

- `WEAR_V3_PLAN.md` §4 calls RePAIR "the thin-slab case, the same geometry as an
  eggshell sherd". Measured: aspect 3.34, 23 mm through. Wrong.
- The same section says "the painted surface does much of the matching work".
  E-M3RF's ablation removes colour and loses 2.2 points (35.91 → 33.71). Colour
  is not doing the matching. Nothing is — the task is unsolved on that material.

## Verdict

**Not as the fix for the current problem, and not next.** The documented cause of
the adapter failure is a defect in our own data build — perfect-contact joins —
and that is repaired by rebuilding the training set, which is already in flight.
RePAIR is a much larger change with no precedent behind it, and reaching for it
first would be treating a data-build bug with a new dataset.

**But it is now a substantially better-founded experiment than the file it
contradicts implies**, and worth running once the rebuild has been evaluated:
train `lora_repair` on RePAIR, evaluate on pottery. Either it transfers, which
would be the first such result anywhere, or it hurts — which is a clean
measurement of how much of an adapter's effect is shape carry-over, and that
number is worth having on its own.

Claim type: **(2), a broken measurement** — the "thin slab" premise this was
argued from was never measured until now, and it was wrong.
