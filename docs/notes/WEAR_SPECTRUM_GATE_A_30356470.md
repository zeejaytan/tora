# Gate A on our simulated worn break faces — what came out, and why it cannot ground the wear model

**Question:** `O7`. **Jobs:** 30352180 (**void**), 30356470 (v2, quotable), 30357114 /
30357469 / 30363949 (three failed gates, kept as record). **Date:** 2026-09-10.

Gate A measures how fast break-face texture grows with patch radius, the fragment's own
curvature removed by a fitted quadric. Fresh fracture is self-affine at **0.4–0.8**. Gate A
measured **1.71** on 20 RePAIR Pompeii frescoes — real eroded archaeological fracture — and
**1.73** refitted over the 0.4–1.6 mm window alone (job 29404479). The reason to run it here
is that it needs **no before-state**, so it can ask the distributional question — *do our worn
surfaces land where real worn archaeological surfaces land* — which the paired question
cannot be asked at all.

**Headline: the instrument works and the statistic does not answer the question.** The
selection is exact, the calibration holds, and the number it produces is moved as much by the
*shape of the break* as by its wear. Category **2 — the measurement was broken**, in the
specific sense that the ruler measures something real that is not wear. This does not touch
`O8`'s finding that wear *causes* reassembly failure; that came from intervention.

## What the eight pots read (job 30356470, v2 mating selection)

Exponent at e000 → e100, all radii passing the gates on most pots:

| pot | e000 | e100 |
|---|---|---|
| blue_pot | 1.13 | 1.11 |
| galli_pot | 1.42 | 1.13 |
| narrow_bottle1 | 1.78 | 1.19 |
| narrow_bottle2 | 1.11 | 0.86 |
| narrow_bottle3 | 1.49 | 1.00 |
| narrow_bottle4 | 1.58 | 0.88 |
| pink_bowl | 1.24 | 0.67 |
| plate | 1.02 | 1.18 |

The exponent **falls** up the wear ladder on **seven of eight** pots — the opposite direction
from what burial erosion should do. **This must not be read as "the wear model does the wrong
thing", and the reason is measured, not speculative:** the point spacing within the measured
set falls 20–46% up the ladder on every pot while the mesh itself is byte-identical, so the
sampling changes alongside the entire effect. See *"The direction finding is confounded by
sampling"* below. The wear column cannot be read until every rung is subsampled to a common
spacing.

The strict e000 control gate passes **four** pots, so four is the number to quote, not six.

**Band control:** the contaminated near-only selection of job 30352180, run on the same
objects in the same job, has **0 of 5 radii passing** the v2 gates on every pot. The
correction is refused outright rather than merely disagreeing.

## Why the numbers cannot be compared with RePAIR

The dataset carries **no break-face label**, and all three routes to one are closed — each
checked rather than assumed:

- `shared_faces` is **−1** for all 48,260 faces of every piece (min −1, max −1, one unique
  value). The field exists; it was never filled.
- `full_mesh` is **not** the intact vessel. Every sherd vertex lies on it at 0.00 mm in all
  percentiles, whole-sherd break-face fraction 0.0%, and `blue_pot`'s `full_mesh` has
  1,043,149 vertices against 608,207 across its five sherds — a pre-break mesh would have
  *fewer*, since breaking duplicates every break-face vertex. It contains the break faces, so
  it cannot label them. (Job 30363949. Caught by the frame-sanity column printed *first*,
  not by a plausible-looking purity number.)
- The cut duplicated no vertices either: nearest-neighbour distance from each sherd to the
  others has no mass below 1e-4 of object size on any of `blue_pot`'s five sherds. The pieces
  were independently remeshed.

So the truth was **built** instead, on geometry carrying the confound that matters:
`scripts/selftest_wear_spectrum_pot.py`. A thin curved wall (4.5 mm on a 20 mm radius), 0.20 mm
point spacing, 0.10 mm mating gap, roughness at a known Hurst H, and a **wavy** cut — because
a flat cut lets any selection through and proves nothing. Every point is labelled by
construction, so purity and recall are exact.

### Result 1 — the selection is exact, and was never the problem

100% purity **and** 100% recall on every row, exponent matching the labelled truth to within
**0.006**. The candidate tightening (mating gap within 3 point spacings *and* an antiparallel
partner normal) is equally exact at 99.5–99.8% recall, so it is a viable narrowing of
`BAND_FRAC` — worth doing given the true mating gap on `blue_pot` is **0.07–0.13 mm** against
a 2.7 mm selection band, 20–40× too wide.

### Result 2 — a fresh break that merely meanders reproduces RePAIR's signature

Add 3 mm of waviness at ~15 mm wavelength — less than any real pot break — holding roughness
fixed:

| true H | flat: slope | flat: decline | wavy: slope | wavy: decline |
|---|---|---|---|---|
| 0.2 | 0.573 | **+0.61** | 0.546 | **−0.25** |
| 0.5 | 0.763 | **+0.52** | 0.906 | **−1.00** |
| 0.8 | 0.994 | **+0.45** | 1.618 | **−1.76** |

The decline is **+0.45 to +0.61 on a flat cut whatever the roughness, and −0.25 to −1.76 on a
wavy one**. It measures break shape, not wear. RePAIR's −0.56 sits between the H = 0.2 and
H = 0.5 **fresh** wavy rows. The slope is no better: the meander moves it by −0.03 at H = 0.2
and **+0.62** at H = 0.8 — neither a fixed size nor a fixed sign, so it cannot be subtracted.

This **strikes the two-axis rescue** written into `intent/O7-wear-grounding.md`, which held
that the decline separated genuine erosion (−0.56) from a capture artefact (+1.52). It does
separate those two. It does not separate erosion from waviness.

On a flat cut the instrument reads high but monotonically — roughly **0.7·H + 0.43** — so it
can *rank* roughness. It cannot separate roughness from break shape.

### Result 3 — contamination alone reproduces it too, on a flat fresh cut

The near-only selection of job 30352180 is **62% pure** on this pot and reads **slope
1.217–1.414, decline −1.35 to −1.68** on a cut built flat and fresh at H = 0.2–0.8. Its slope
barely tracks H at all (1.217 / 1.354 / 1.414 for H = 0.2 / 0.5 / 0.8) — the signature of a
statistic reading the vessel wall rather than the break. That reproduces job 30352180's
1.06–1.81 **from ground truth**, closing it independently of the wall-thickness argument.

### The arithmetic that makes it unanswerable

Our fresh e000 faces read **0.67–1.78**. RePAIR's real eroded fresco reads **1.71**. A fresh
synthetic break at H = 0.8 with a modest meander reads **1.62**. Those are the same number.

## Three gates that failed before this one, kept so they are not rebuilt

1. **The off-face gate inside `wear_fracture_spectrum.py`** asks whether a patch is locally
   ONE surface. A pot's outer wall *is* locally one surface, so wall passes cleanly. It cannot
   distinguish break face from wall.
2. **`face_selection.png`** projects through a hollow object, so a ribbon along a near break
   edge and a broad area on the far wall are drawn on top of each other.
3. **Both ribbon-width tests** (`check_mating_face_is_a_ribbon.py`, jobs 30357114 and
   30357469). The global-extent version was defeated by loop geometry — a break runs around
   the sherd's perimeter as a closed loop, and both principal extents of a loop are the
   loop's *diameter*, so ribbon width appears in neither; it refused all eight pots on a test
   a perfect selection would also fail. Caught by arithmetic before the refusal was reported:
   `pink_bowl` face 0 gave 4345 points over 99.5 × 56.3 mm, but 4345 points at 0.136 mm
   spacing is under ~120 mm² of surface and cannot fill that box. The local-saturation
   rewrite carried a control and **the control fired** — outer surface read as a ribbon on
   five of eight pots — because the selection is already banded to within 2% of diagonal of a
   neighbour, 2.7–6.7 mm, which equals the wall thickness to within 2×. Band width cannot
   separate two bands that are the same width by construction.

## Two errors inside the synthetic test itself

Recorded because both were invisible to purity and recall, and one had already manufactured a
finding:

- The two mating faces were first built as **reflections** about the wave rather than as one
  surface pulled apart, so they were antiparallel only where the cut was flat. With the
  wave's gradient reaching 1.26, `n_A · n_B = (|g|²−1)/(|g|²+1) = +0.23` — the two faces of a
  single break reading as facing the *same* way. That turned the `tight gap + antiparallel`
  rule into a flatness filter: recall fell 69% → 10% on a wavy cut and the 10% it kept were
  the near-flat patches, which is why it *appeared* immune to the meander and to recover the
  flat-cut exponent. It was not immune; it had discarded every part of the break that
  meanders. Corrected, its recall is 99.5%.
- The corrected face normals then pointed **away** from the partner instead of across the gap,
  so `dot > MATING_DOT` selected nothing.
- Earlier, `rough_field` was band-limited by its own grid: n = 256 over 64 mm gives 0.25 mm
  cells against 0.20 mm sampling, so the surface was smooth below the sampling scale **by
  construction** — the exact condition already shown to read falsely high. It inflated the
  flat-cut reading to 1.099 for truth 0.5. Caught by the `wave=0.0` control row. Fixed to
  n = 1024 (0.0625 mm cells).

The script now **asserts the geometry before it scores anything**: the two faces must sit
`GAP` apart with a partner-normal dot of ~−1, or it prints `GEOMETRY INVALID` and stops. It
passes at gap 0.100 mm and dot −1.000 exactly. Both sweeps were run twice and agree on all
six rows.

## Job 30356470 finished: `COMPLETED`, exit 0:0, 1:22:03, peak 3.5 GB

### Band control — the synthetic prediction reproduced on real pots

The contaminated near-only selection has **off-face 100.0% at every radius** and passes
**0 of 40** pot-rungs. Its readings, pooled per rung, are **slope 1.18–1.36 with decline
−1.06 to −1.55**, and the script's own second axis labels every rung *"erosion-like"*.

The manufactured-truth test predicted, for a 62%-pure selection on surfaces built **fresh**:
slope **1.217–1.414**, decline **−1.35 to −1.68**. The observed ranges overlap. So the
prediction made from labelled synthetic geometry reproduces what the contaminated selection
actually does on the real pots, and the two-axis test is shown being fooled **on real data**,
not only in simulation.

### Wide ladder — the script refuses its own table, and now we know why

Over Gate A's own 0.40–6.40 mm ladder the gates do **not** refuse the top radii as the job
header predicted: off-face is 0.3% at 0.40 mm rising only to 13.1% at 6.40 mm, and 40/40
pot-rungs pass at 0.80 and 1.60 mm. Fresh e000 reads **1.03–1.68, median 1.37**, and the
script stops itself: *"STILL ABOVE THE SELF-AFFINE CEILING … Do not quote the table."* It
offered two explanations — the selection is still contaminated, or our scans do not resolve
fresh fracture at all.

**Both are now wrong, and there is a third.** The selection is proven exact against labelled
truth (100% purity, 100% recall), so it is not contamination. And a fresh synthetic break at
H = 0.8 with a 3 mm meander reads **1.62**, inside the observed fresh range. The ceiling is
exceeded by **break shape**, which the calibration never modelled because it was run on a
flat plaque.

### The direction finding is confounded by sampling, not a wear-model result

The exponent falls up the ladder on 7 of 8 pots in the narrow window and on 6 of 8 in the
wide one. Two facts together stop that being read as wear:

- **The mesh is identical at every rung.** Vertex and face counts are byte-identical
  e000 → e100 on `blue_pot` (1,043,149 v / 2,086,278 f), `pink_bowl`, `plate` and
  `narrow_bottle3`. The operator displaces vertices and changes no topology.
- **But the measurement's sampling is not held fixed.** The selection keeps steadily more of
  the break face as wear rises — `blue_pot` 18.2% → 25.7% of near, 28,452 → 37,330 points —
  and the point spacing *within the measured set* therefore falls on **every pot**:

  | pot | e000 → e100 spacing | change |
  |---|---|---|
  | blue_pot | 0.106 → 0.084 mm | −21% |
  | galli_pot | 0.100 → 0.080 mm | −20% |
  | narrow_bottle1 | 0.082 → 0.065 mm | −21% |
  | narrow_bottle2 | 0.168 → 0.090 mm | −46% |
  | narrow_bottle3 | 0.118 → 0.081 mm | −31% |
  | narrow_bottle4 | 0.104 → 0.074 mm | −29% |
  | pink_bowl | 0.138 → 0.086 mm | −38% |
  | plate | 0.198 → 0.121 mm | −39% |

This statistic tracks **the finest wavelength present in the sampled set** — that is the one
thing established about it beyond doubt. A 20–46% change in the spacing of the measured points
runs alongside the entire wear effect, in the same direction on every pot, so the two cannot
be separated in this run. Plausibly the erosion smooths the normals, so more points satisfy
the mating criterion and the sample fills in.

Note this does **not** contradict the earlier density test (H = 0.5 sampled at 0.267 mm still
recovered 0.651). That coarsened a *fixed* surface whose content ran below the sampling scale.
It did not test a selection converging on the true mesh density as the surface changes.

**The fix is cheap and decisive:** subsample every rung to the coarsest rung's point spacing
before measuring, then re-read the ladder. Until that is done the wear column says nothing,
and the earlier reading that "the exponent moves the wrong way" is withdrawn — it was
category 2 as well.

**Also withdrawn:** the hypothesis that our erosion operator reduces the break's meander.
Decline falls up the ladder (`blue_pot` +0.11 → −0.31, `narrow_bottle1` +1.09 → 0.00), and
on labelled geometry a *falling* decline is what **added** waviness produces. That points the
opposite way, and is confounded by the same sampling change, so it is not evidence either.

### The plot says more than the exponent

`artifacts/wear_spectrum_30356470/wide_ladder_spectrum.png` (local, gitignored; source `eval_runs/wear_spectrum_30356470/wide_ladder/spectrum.png` on Spartan). RePAIR's curve starts **lowest**
of everything at 0.40 mm (~0.0018 mm of texture) and converges with ours at 6.40 mm
(~0.22 mm). Its steep exponent is not extra coarse roughness — it is **missing fine relief**,
which is what erosion physically does. Ours start higher at the fine end (0.002–0.009 mm) and
end at or below RePAIR at the coarse end. That is the one comparison in this whole run that
reads as physically meaningful, and it is a statement about *absolute fine-scale texture*,
not about the exponent. Whether it survives the sampling correction above is untested.

## What would still discriminate

A statistic computed *after* the break's low-frequency shape is removed — not by a quadric
over a 1.6 mm patch, which cannot see a 15 mm meander, but by subtracting a fit over the whole
face. **Untested.** And the direction finding above needs its own test: does our erosion
operator reduce the break's meander? If it does, the falling exponent is an artefact of the
operator's smoothing rather than a statement about wear.
