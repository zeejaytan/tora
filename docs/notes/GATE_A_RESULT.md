# Gate A: what real eroded fracture looks like

**Answered 2026-08-19**, on 20 Pompeii fresco fragments from RePAIR
(`repair_fracture_spectrum.py`, job 29404479). Gate A of `WEAR_V3_PLAN.md`.

## The finding

**Real eroded archaeological fracture carries no fracture-like roughness at any
scale these scans resolve.**

With the fragment's own shape removed by a locally fitted quadric, texture rises
as **R^1.7** from 0.4 mm to 6.4 mm — a clean straight line on log axes, no kink,
consistent across all 20 fragments.

| scale | 0.40 mm | 0.80 | 1.60 | 3.20 | 6.40 |
|---|---|---|---|---|---|
| texture | 0.0018 mm | 0.0049 | 0.0197 | 0.0685 | 0.2091 |

A fracture surface is self-affine with a roughness exponent of **0.4 to 0.8**
across metals, ceramics and rocks. R^1.7 is nothing like that — it is what a
smooth surface with mild residual shape produces.

## What cannot be concluded

**Whether the ground removed the roughness or the scanner never recorded it.**
The finest readable scale is 0.4 mm, about three times the 0.119 mm point
spacing, and photogrammetric reconstruction smooths at roughly that scale. The
two explanations are not separable with this data, and settling it needs
sub-0.1 mm scanning, which RePAIR does not have either.

Two more limits worth carrying:

- **A quadric only removes second-order shape.** At the larger radii the outline
  departs from a quadric, so some residual shape survives into the measurement
  and the exponent there is an upper bound on the true texture exponent.
- **About one fragment in four is contaminated.** The classification assumes a
  flat slab; on lumpy fragments (`RPf_00579`) it bleeds onto the face. Verified
  by rendering, which is why it is known rather than suspected.

## What holds regardless

> At every scale these scans resolve, real digitised archaeological fracture has
> no interlocking texture. Whether the ground removed it or the scanner did, it
> is not in the file — and the file is what a model sees.

Three consequences.

**1. Scan-realistic variants should be the default, not half the training set.**
We currently build seven crisp variants per object and five blurred to scan
resolution. Training on synthetic fracture that carries self-affine roughness at
0.4–6.4 mm teaches the model to read a signal that does not exist in any real
scanned artefact.

**2. The blunting cutoff is in the right place, and now has outside support.**
0.3–0.5% of object size on a ~100 mm juglet is 0.3–0.5 mm, which is where real
digitised fracture stops carrying texture. That value was chosen from geometry
and the conservator's description of wear; this is the first independent
evidence for it.

**3. A hypothesis, flagged as such:** this may be why GARF struggles on real
worn material. GARF reads fracture-surface micro-texture. If that texture is not
present at the resolution real scans deliver, no fine-tuning recovers it — the
information is not in the data. Testable by measuring GARF's own training
material with this instrument and comparing.

## The instrument, and the fault it had first

The first version measured deviation from the local **mean** and returned an
exponent of 1.75, which looked like a result. It was the plaque's own outline:
a rim curving with radius rho departs from its chord by R²/2rho, and with
rho ≈ 40 mm that predicts **0.51 mm** at a 6.4 mm radius against **0.49 mm**
measured. Almost the entire signal was the shape of the fragment.

Fitting a quadric per neighbourhood absorbs curvature by construction and leaves
texture — the same distinction as blunting the teeth while keeping the curve,
applied to the instrument rather than the model. The corrected exponent, 1.71,
is barely different, which is itself informative: the conclusion did not depend
on the fault, but it could not have been known without fixing it.

Caught before the result was reported, because the acceptance criterion was
written into the script before it was run.
