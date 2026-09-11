# Design brief — rebuild the break-face wear ruler

**Question:** `O7` (distributional half). **Feeds:** `/grill-with-docs`.
**Written 2026-09-10**, after Gate A's exponent was refuted (job 30356470).
Read `docs/notes/WEAR_SPECTRUM_GATE_A_30356470.md` first; this brief is only the
design constraints the grilling has to satisfy.

## What we are trying to measure

Do our **simulated worn** break faces land where **real worn archaeological**
break faces land, and away from **fresh** fracture? Distributional, not paired —
no before-state needed. The paired question is struck permanently (see `O7`).

## What killed the last ruler

The roughness-scaling exponent responds to the break face's **large-scale
meander** as strongly as to wear. Fixed known roughness + a 3 mm undulation:
0.99 -> 1.62. Real eroded RePAIR reads 1.71. Not a bug — the wrong instrument.
The break-face *selection* is exact (100% purity, 100% recall on labelled
synthetic truth) and is not the problem.

## The three data sources and their point spacing — THE binding constraint

The quantity we want to measure (fine-scale texture) is the quantity point
spacing controls. The three sources do not share one.

| source | role | point spacing | relative | finest honest scale |
|---|---|---|---|---|
| RePAIR Pompeii fresco, 20 frags | real WORN | **0.119 mm** | 0.113% | 0.40 mm (3.4x spacing; photogrammetry smooths ~here) |
| Juglet (real archaeological ceramic) | real WORN | **0.29-0.48 mm** | 0.243% | ~0.5% of object size |
| our sim pots (blue_pot etc.) | FRESH + sim-worn | **0.084-0.198 mm** | 0.068% (blue_pot) | 0.20 mm |

The blunting our operator applies acts at **0.2-0.3 mm** on a juglet-sized vessel.

## Constraint 1 — CORRECTED. The Juglet stays in. My objection was wrong.

**Withdrawn 2026-09-10, on the conservator's objection, after reading the
operator instead of the notes.** I argued the Juglet cannot be the worn
reference because its break faces are sampled coarser than the wear is deep.
The second half of that is false.

**CORRECTED AGAIN, by measurement — job 30385594.** The paragraph below argued
from the operator's nominal kernel. That is also wrong, in the other direction,
and the original 0.25 mm figure was right.

`fracture_mesh_ops.erode_fracture_band` mollifies over
`r = strength * kernel_frac_max * piece_scale` with `kernel_frac_max = 0.05`
and `piece_scale = max(mesh.extents)`, using `sigma = 0.5 * r`. But `sigma` is
the **width of the smoothing, not the depth of removal**, and it **saturates**:
the operator queries `k=knn=48` neighbours out of a fixed `n_self_samples=20000`
(`fracture_mesh_ops.py:169-176`), so once `r` holds 48 samples every extra
millimetre of radius buys nothing, all neighbours sit well inside `sigma` at
weight ~1, and the target degenerates to the unweighted centroid of those 48.
The nominal `0.05 * max(extents) * strength` then describes nothing the code
does. Any depth read off it — including the table this replaces — is fiction.

Measured instead by subtracting vertex arrays (the ladder's topology is
byte-identical across rungs, so vertex *i* is the same speck of clay at every
rung). **Median displacement over the moved band, in mm, job 30385594:**

| rung | strength | measured depth, 8 pots | vs Juglet spacing 0.29-0.48 mm |
|---|---|---|---|
| e025 | 0.25 | 0.022 - 0.042 mm | **far below spacing — unreadable there** |
| e050 | 0.50 | 0.049 - 0.093 mm | **below spacing** |
| e075 | 0.75 | 0.083 - 0.206 mm | below spacing |
| e100 | 1.00 | 0.121 - 0.311 mm | reaches the low end of it |

Per pot at e025/e050/e075/e100: blue_pot 0.030/0.070/0.122/0.181; galli_pot
0.042/0.091/0.154/0.222; narrow_bottle1 0.022/0.049/0.083/0.121;
narrow_bottle2 0.041/0.091/0.193/0.311; narrow_bottle3 0.037/0.093/0.206/0.309;
narrow_bottle4 0.037/0.080/0.138/0.203; pink_bowl 0.041/0.090/0.157/0.231;
plate 0.042/0.093/0.161/0.233.

**The wear magnitude is nonetheless the right order for real burial wear** —
the Juglet's own break-face relief is ~0.17 mm, inside the e075-e100 range. The
difficulty is comparing against a reference sampled coarser than the effect,
not wear that is unrealistically shallow.

**`scripts/measure_sherd_scale.py`'s "clears the Juglet's spacing" verdict
column is built on the nominal kernel and must not be quoted.**

Where "0.2-0.3 mm" came from: that is the **blunting cutoff** — the scale at
which real *digitised* fracture stops carrying texture
(`docs/notes/GATE_A_RESULT.md`, 0.3-0.5% of object size). It is a property of
the reference scans, not of what our operator does. I conflated the two.

**What survives, after job 30385594:** the opposite of what this section
originally claimed. `e025` through `e075` all sit **below** the Juglet's point
spacing; only `e100` reaches its low end. The reference's coarseness is the
binding constraint on which rungs are comparable at all.

**What the earlier "cannot tell" results actually showed:** the fine-over-coarse
ratio put the worn Juglet at 0.169 against fresh `blue_pot` 0.167 inside the
fresh range 0.167-0.386. That statistic put its *fine* band below 0.5 mm — the
one band the Juglet does not resolve. The statistic was resolution-blocked; the
object is not.

## Constraint 1b — the instrument must live where all three sources agree

This is the real constraint, and it replaces the one above.

- the wear operator removes **0.02-0.31 mm** of material (measured, job
  30385594), not the 0.25-1.0 mm the nominal kernel suggests;
- the Juglet resolves down to about **3 x 0.4 = 1.2 mm** honestly (Gate A's own
  rule: finest readable scale ~ 3x point spacing);
- RePAIR resolves down to **0.40 mm**; our sim pots to **0.25-0.6 mm**.

**So the shared, honest measuring band is roughly 1.2-6 mm** — and that band
contains where the wear acts. The instrument must be built to read *that* band.

**This withdraws the "absolute fine-scale texture" candidate.** It targeted
0.1-0.4 mm, which is (a) below what the Juglet supplies and (b) not where our
operator acts. Wrong axis, twice over.

## Constraint 1c — the conservator's design point, accepted

*"All the data incoming will be on the same photogrammetry detail."* Correct,
and it is the right design. If every object -- Juglet, incoming real pots, and
our simulated pots after being resampled to the same spacing -- shares one
capture, then capture is a **constant** rather than a confound, and a difference
between objects is a material difference. Combined with 1b (the wear acts above
the shared resolution) the comparison is sound.

The one thing this does NOT buy: it does not license the claim
"our wear reproduces burial *physically*". See Constraint 3.

## Constraint 2 — the null model is still worth running, but it is no longer a blocker

RePAIR's own note (`docs/notes/GATE_A_RESULT.md`) says its finest reading sits at
3.4x point spacing, where photogrammetric reconstruction smooths, and that
"the ground removed it" vs "the scanner never recorded it" **cannot be
separated** with 0.4 mm data. Worse, we have already shown a **known-fresh**
H=0.5 surface blurred by only **0.20 mm** reads 1.445 while its true roughness
falls 3%.

**Downgraded 2026-09-10.** This bites at 0.4 mm, which Constraint 1b has just
moved *out* of the measuring band. An instrument reading 1.2-6 mm is not
competing with photogrammetric smoothing at 0.4 mm. Still worth running as a
control -- degrade our **fresh** synthetic faces to the shared spacing and check
they do not drift toward the worn end -- but it no longer gates the design.

- If they do -> the reference carries no wear signal a capture artefact does not,
  and **no statistic built on RePAIR can ground the wear model**. Route closes;
  stop before designing a ruler.
- If a gap survives -> that surviving gap is the only honest axis, and the ruler
  should be designed to read it and nothing else.

Cheap, decisive, and it can refute the whole plan. It goes first.

## Constraint 3 — the claim the surviving route can support

`O7` already fixes this: "our simulated wear matches real **scanned** worn
fracture", because the file is what the model sees. It does **not** support
"our wear reproduces burial physically". The grilling must not let the wording
drift back.

## Constraint 4 — sampling must be equalised, not assumed equal

Our erosion ladder e000..e100 leaves the mesh byte-identical but the measured
point spacing falls **20-46%** up every ladder, because the selection keeps more
of the face. Every rung must be subsampled to a **common** spacing before any
reading is compared. Untested; the wear column says nothing until then.

## Candidate instruments (both untested)

1. **Texture after removing the whole-face shape** — subtract a fit over the
   entire break face, not a quadric over a 1.6 mm patch (which cannot see a
   15 mm meander). Directly targets the confound that killed the exponent.
2. **~~Absolute fine-scale texture at a fixed point spacing.~~ WITHDRAWN
   2026-09-10** — it reads 0.1-0.4 mm, below what the Juglet supplies and away
   from where the operator acts. Wrong band.
3. **Relief amplitude in the 1.2-6 mm band, at a common point spacing** — the
   band all three sources share and the band the operator acts in. This is the
   candidate the grilling should develop. Note RePAIR's measured texture there:
   0.0197 mm at 1.60 mm, 0.0685 at 3.20, 0.2091 at 6.40 (job 29404479).

## Non-negotiable gates carried from the last round

- Manufactured truth gets its own geometry gate before any scoring
  (`scripts/selftest_wear_spectrum_pot.py` — two mating faces must read
  partner-normal dot ~= -1). Purity and recall cannot see bad geometry.
- Patch radii are **not** transferable between objects: carry the ratio to wall
  thickness, never the millimetres. Gate A's 12.8 mm patch is 0.55x a 23.5 mm
  fresco plaque and 2.9x a 4.5 mm pot wall.
- **MEASURED WALLS, job 30385552** (median 2V/A per sherd, mm): plate 5.01,
  galli_pot 4.71, pink_bowl 4.49, narrow_bottle4 3.36, blue_pot 3.08,
  narrow_bottle2 2.73, narrow_bottle3 2.52, narrow_bottle1 2.14 (min 1.57),
  **Juglet 1.79** (1.58-2.52). The 4.5 mm working figure used throughout this
  brief fits only pink_bowl and galli_pot; the corpus median is ~3 mm.
- **Round patches cannot measure the Juglet at all.** Floor: 3 x 0.48 mm
  spacing = 1.44 mm radius, i.e. **2.88 mm across**. Ceiling: the repo's own
  rule (1.60 mm patch on a 4.5 mm wall = 0.356 x wall) gives 0.64 mm radius,
  **~1.3 mm across**, on a 1.79 mm wall. Ceiling below floor, so no round
  radius is valid. Four of nine objects fail the 2.88 mm floor. This is a
  measured answer to Q1: only strips along the ribbon can carry the Juglet.
  Drawn to scale in `artifacts/explain_disc_vs_strip.png`.
- Calibrate at the data's own resolution. A band-limited synthetic field faked
  a reading once already.
- Render the measured quantity per-vertex, unbinned, before reporting.


## What Q8 asked for, and what came back -- jobs 30386369 (VOID) and 30386546

**Job 30386369 is VOID. None of its numbers may be quoted.** It asked whether
the break ran at least L mm as seen from inside a ball of radius L/2 -- a
window L across, so the spread inside it cannot exceed L, and the 2-98
percentile trims that to 0.88 L. Every object read 0.0% at every length and
the "available run" column tracked 0.88 x L exactly.

**Job 30386546 replaces it** with arc length along the ribbon (walk the face
points as a graph, take the longest shortest-path through the largest
connected piece), gated first on manufactured truth by
`scripts/selftest_traceable_length.py`: a 30 mm-radius 60-degree ribbon reads
31.54 against a true arc of 31.42 (0.4%) rather than the 30.00 mm chord; a
flat 20 x 20 mm patch reaches its 28.28 mm diagonal instead of saturating; a
ribbon with a 3 mm gap reports the longer piece, 16.27 against 15.85 (2.6%).

**Measured point spacing on break faces, e000, mm** (median over faces, and
the range): blue_pot 0.122 (0.079-0.200), galli_pot 0.119 (0.080-0.250),
narrow_bottle1 0.083 (0.075-0.113), narrow_bottle2 0.200 (0.112-0.202),
narrow_bottle3 0.148 (0.088-0.206), narrow_bottle4 0.129 (0.087-0.202),
pink_bowl 0.177 (0.147-0.200), plate 0.201 (0.078-0.242), **JUGLET 0.212
(0.202-0.385)**.

**Traceable arc length, mm** (median over faces / shortest face / longest):
blue_pot 25.29/6.39/56.76, galli_pot 52.67/18.99/129.69, narrow_bottle1
43.96/16.77/69.85, narrow_bottle2 53.23/51.94/86.83, narrow_bottle3
72.87/29.80/115.22, narrow_bottle4 57.91/27.41/62.11, pink_bowl
18.73/17.10/26.23, plate 81.74/26.51/102.92, **JUGLET 19.32/7.34/25.10**
(per face 7.34, 9.36, 17.40, 19.32, 23.43, 24.02, 25.10).

Every object meets its own ISO floor on every face. The Juglet's floor is
5.31 mm at 0.212 mm spacing, and 5 of its 7 faces also clear 12 mm.

### THE JUGLET SPACING FIGURE IS NOT 0.29-0.48 mm ON THIS FILE

`juglet_gt.hdf5`, assembled in ground-truth pose and scaled to a 65 mm vessel,
gives **median nearest-neighbour 0.222 mm whole-mesh** (per-sherd range
0.203-0.338) and 0.212 mm on the mating-selected break faces. Ticket
`.scratch/juglet-cause/issues/10` quotes 0.29-0.48 mm from the same 9
fragments and the same 60,334 vertices, so the difference is a definition, not
a file: on those meshes nn-median is 0.203-0.338, nn-mean 0.250-0.349,
triangle-edge median 0.315-0.530, edge mean 0.450-0.562 mm. ISO 3274's rule is
on the SAMPLING INTERVAL, i.e. the step between recorded points, so
nearest-neighbour distance is the right definition and the coarse end of it --
**0.338 mm, the coarsest sherd** -- is the honest input. That gives
**lambda_c >= 1.69 mm and a profile >= 8.4 mm**, not 2.4 and 12.

`juglet.hdf5` must not be used for this: 229,373 vertices with median nn
0.000 mm (duplicates) and fragments not in assembled pose. `juglet_norm.hdf5`
is per-fragment normalised, so its extent is not the vessel.

### BLOCKING: the selection is too sparse on the Juglet to trust its length

Rendered per-point in `artifacts/juglet_traceable_ribbon.png` (job 30386693).
The walk does not sweep along a continuous ribbon; it threads a sparse
scatter. `mating_faces` keeps only **4,187 of 25,534 near points** on the
Juglet, and the largest connected piece holds just **24.0%** of a face's
points (median) against 34-59% on the sim pots. So the Juglet's arc lengths
above are a path through a scatter, not an arc along clay, and must not be
quoted as ribbon length until the selection is fixed.

Two further honesty notes on the same job:

- **The width control did not pass.** The across-wall extent from the local
  frame exceeds the measured wall on 6 of 9 objects: blue_pot 4.50 vs 3.08,
  galli_pot 6.13 vs 4.71, narrow_bottle1 2.52 vs 2.14, narrow_bottle3 3.21 vs
  2.52, plate 5.16 vs 5.01, **JUGLET 2.02 vs 1.79**. Under the wall only on
  narrow_bottle2 (2.49 vs 2.73), narrow_bottle4 (3.24 vs 3.36), pink_bowl
  (2.75 vs 4.49). The 10-30% overshoot is the size and direction the
  known-wide `BAND_FRAC = 2%` of diagonal predicts (2.7 mm band against a
  0.07-0.13 mm true mating gap on blue_pot), so narrowing the band is now
  blocking rather than pending.
- **The render did not resolve the ribbon width.** 1.8 mm across a ~16 mm box
  drawn at ~300 px is about 34 px, which is the "check the view resolves the
  scale being tested" failure. A zoomed, equal-aspect view of one face is
  still owed before the width figure is read either way.

### The proposed selection fix fails its own test at the Juglet's geometry

`scripts/diagnose_juglet_selection.py --synthetic`, run locally (22 s). A
labelled synthetic pot, wavy cut, every point known to be break face or not.
The **control** rebuilds the geometry the tight-gap rule was proven on (4.5 mm
wall, 0.10 mm gap, 0.20 mm spacing) and reproduces it: tight + facing +
opposite 100.0% pure, 99.6% recall. So the harness is sound.

At the **Juglet's geometry** (1.79 mm wall, 0.22 mm spacing, gap 0.24 mm
typical and 0.48 mm worst tenth), purity / recall:

| rule | exact normals, 0.24 | estimated, 0.24 | exact, 0.48 | estimated, 0.48 |
|---|---|---|---|---|
| v2 (current: near 2% diag + facing) | 100.0 / 100.0 | 98.7 / 96.8 | 100.0 / 100.0 | 95.9 / 97.2 |
| gap < 3 spacings only | 64.8 / 100.0 | 64.8 / 100.0 | 80.5 / 100.0 | 80.5 / 100.0 |
| gap + facing + opposite (candidate) | 100.0 / 97.0 | 100.0 / **86.8** | 100.0 / 94.1 | 99.4 / **85.2** |
| gap + opposite partner | 100.0 / 97.0 | 98.8 / **86.8** | 100.0 / 94.1 | 99.0 / **85.2** |

"Estimated" re-derives normals from 8 neighbouring points, which blurs the
corner where the break face meets the wall; a mesh's averaged normals do this
too, though less. Every passing rule holds a ribbon as continuous as the truth
(largest piece 50%, the two break strips of the synthetic pot).

**So the current rule is not what makes the real Juglet a scatter.** At its
geometry it keeps a continuous, clean ribbon. The candidate replacement is
the worse rule there: the opposite-partner test drops 13-15% of the true face
when normals are blurred. That retires "narrow `BAND_FRAC` to fix the Juglet"
as a fix for the Juglet (it may still be worth doing for the wide-band
contamination on the sim pots, which is a separate problem). The cause is
something in the real Juglet data that the synthetic pot lacks -- job below
reads it term by term.

### Job 30419474 -- the real Juglet, term by term (COMPLETED 0:0)

Same script, `--synthetic --juglet juglet_gt.hdf5`. The synthetic control
passed again in the same log before the Juglet was read.

**The files are not the problem.** All nine sherds are closed and wound
outward, so no inside-out sherd and no hole is flipping the normals.

**The gap finds the join; the facing test throws most of it away.**

| rule | kept | faces | largest piece | arc, median |
|---|---|---|---|---|
| v2 (current) | 4,187 | 7 | 24.0% | 19.3 mm |
| gap < 3 spacings only | 21,675 | 9 | 99.8% | 50.1 mm |
| gap + facing + opposite | 2,126 | 0 | -- | -- |
| gap + opposite partner | 8,247 | 9 | 76.2% | 48.9 mm |

On the 21,675 dots within 3 spacings (0.89 mm) of another sherd, per sherd
only 12-27% pass the facing test (the synthetic pot at the same geometry:
~100%). Percentiles 10/25/50/75/90:

- facing dot (kept if > 0.50): -0.79 / -0.49 / -0.11 / 0.36 / 0.74 -- spread
  almost evenly; for a tenth of the join dots the neighbour sits squarely
  **behind** the break face.
- partner dot (kept if < -0.70): -0.99 / -0.93 / -0.37 / 0.22 / 0.52 -- a
  real population of face-to-face twins (a quarter at -0.93 or below), plus
  the skin beside the join.

"Gap only" being continuous does not make it clean: on the synthetic pot the
same rule was 65-80% pure, because it also takes the outer and inner skin
beside the join.

Spacing note: this script reports **0.295 mm**, a nearest-dot median pooled
over all 60,334 vertices, so the big sherd 0 (24,294 vertices) weighs heavily.
The per-sherd median is still 0.222 mm (range 0.203-0.338). The tight gate
was therefore 0.89 mm, not 0.67.

The render printed 53 px/mm, i.e. **95 px across the wall, under its own
100 px gate, so it was not read.** The window is narrowed to +-2.5 mm for the
rerun.

**Next (job below):** does the hand reassembly set sherds slightly *into*
each other? An unsigned 0.24 mm "gap" (ticket 10) cannot tell a gap from an
overlap, and an overlap puts the neighbour behind the face, which is exactly
what a negative facing dot means. Tested without normals: a generalised
winding number (solid angles; the tora env has no ray library) says whether
each join dot lies inside the closed neighbouring sherd, and an exact
point-to-triangle distance says how deep. **Prediction, written before the
run:** overlap is the cause if a third or more of the join dots are inside
the neighbour, concentrated where the facing test fails; refuted if under 5%
are inside, in which case the mesh's surface directions are the suspect.
Control: each sherd's own dots pushed 0.05 mm in must read inside, and
pushed out must read outside, at 95% or better.

### Job 30420351 -- the sherds sit into each other (COMPLETED 0:0, commit 18876e4)

**Prediction met.** Control TRUSTED (pushed in: 99.4% inside; pushed out:
99.9% outside). Known-answer gate `scripts/selftest_juglet_overlap.py` all
pass, including the refuting case (boxes 0.1 mm apart read 0% inside).

| where | dots | inside the neighbour |
|---|---|---|
| all join dots (gap < 3 spacings) | 21,675 | **33.2%** |
| where facing FAILS (dot <= 0) | 12,291 | 44.3% |
| where facing PASSES (dot > 0.5) | 4,143 | 13.3% |
| face against its twin (partner < -0.7) | 8,247 | **61.7%** |

Signed gap, mm (minus = inside), p10/25/50/75/90: all join dots
-0.182/-0.042/+0.086/+0.305/+0.541; twin faces -0.278/-0.128/-0.030/+0.035/+0.096.
Every join overlaps somewhere (19-68% of its dots inside). Worst: sherd 3
against 6 (64.0% / 67.8% inside, median -0.15 mm, p10 -0.52 mm). Typical:
median +0.02 to +0.16 mm, p10 -0.03 to -0.29 mm.

**Reading.** The reassembled break faces cross through each other by about
0.1-0.3 mm, roughly one point spacing: a very tight fit whose two surfaces
interleave. Wherever they cross, the neighbour is *behind* the face, so the
facing test (which assumes the neighbour is in front) throws the dot away,
and the kept set becomes a patchwork. Category (2): the selection rule is
broken for this data; the reference is not wrong. Ticket 10's 0.21-0.28 mm
"gaps" were unsigned; on the twin faces the signed median is -0.03 mm.
Weight: one object, 9 sherds, 31 joins, all in the same direction, from a
deterministic measurement with a passing control.

**Its picture was wrong and was not read.** It resolved the wall (84 px/mm,
151 px) but `frame_at` fitted its plane to every gap-only dot on the sherd,
both skins and several joins, so the "face" ran 3 mm across a 1.79 mm wall.
The px gate checked scale, not orientation. Replaced in commit fc0d06c by
`join_frame` (one join's twin dots; must be flat to 0.3 mm rms and span
0.5-1.5 walls) and `render_overlap` (cuts through both meshes, plus a
face-on view coloured by signed gap), checked on the box pair. Rerun as
job 30420961.

### Job 30420961 -- the overlap, drawn (COMPLETED 0:0, commit fc0d06c)

All gates pass: frames flat to 0.12-0.22 mm rms and spanning 1.71-2.11 mm
across the 1.79 mm wall (sherd 6 against 3, 5 and 8); 120 px/mm, so 0.1 mm
is 12 px. Overlap numbers reproduced exactly (deterministic).
Picture: `artifacts/juglet_selection_overlap.png`.

- **Worst join, 6 against 3:** in all three slices (2 mm apart) the
  neighbour's break face lies 0.2-0.5 mm *inside* sherd 6, up to about
  0.8 mm at +2 mm (offset along the slice; the 3-D closest distance is
  smaller, p10 -0.52 mm).
- **Typical join, 6 against 5:** the two faces lie on top of each other and
  cross back and forth within about 0.1 mm.
- Face-on panels agree (68% red against 29%).
- The selection picture is now in a correct frame: sherd 6's face against 8
  is one line across the wall at the join, with the skins beside it.
- **Noticed, not explained, not read into:** in 6 against 5, below the
  contact, the two sherds' surfaces part in a V (black running down-left at
  about 45 degrees, blue nearly level) instead of continuing into each other.
  The face-on views are arch-shaped because the break line curves within
  12 mm; the frame is local, so that is expected, not a fault.

## Decisions for the conservator (the grilling should land these)

- **D1.** ~~Drop the Juglet?~~ **Settled: keep it.** Sub-question settled by
  Q10 below: e025-e075 are reported as unreadable against the Juglet, not
  dropped.
- **D2.** Is "matches real *scanned* worn fracture" the claim we want, given it
  is a training-data claim rather than a physical-fidelity one? **Settled by
  Q16:** claim (a).
- **D3.** ~~Juglet or RePAIR primary?~~ **Settled by Q4:** the Juglet sets the
  target value, RePAIR is the sample-size check, side by side, never averaged.
- **D4.** ~~Common point spacing?~~ **Settled by Q11** (below), with the figure
  itself reopened as Round 3 Q12.

## Grilling record

**Round 1 (accepted as recommended).** Q1 strips along the break ribbon, not
discs. Q2 absolute millimetres, never pooled across objects, wall thickness
printed beside every figure. Q3 an explicit-cutoff filter (ISO 16610-21
Gaussian), not a fitted quadric. Q4 Juglet primary for the target value,
RePAIR the sample-size check, side by side, never averaged. Q5 vocabulary:
relief / wear depth / roughness exponent; "texture" retired (umbrella
`docs/glossary.md`, commit 7387d45).

**Round 2 (accepted as recommended, 2026-09-11).**

- **Q6.** Three cutoffs reported side by side. Never fitted to a slope, never
  averaged, no arithmetic across them -- a fitted line across cutoffs is the
  refuted statistic rebuilt.
- **Q7.** "Along the break" = the local in-surface frame of
  `check_mating_face_is_a_ribbon.py:70-102`. The elongation comes from where
  the clay ends, not from the surface being measured, so wear cannot bias the
  direction. Built-in control: across-wall extent saturates at the wall; the
  outer skin must not. Whole-face PCA is banned (pink_bowl face 0 read
  99.5 x 56.3 mm on a closed-loop break).
- **Q8.** The cutoff is taken from ISO, not chosen by us: ISO 3274 sampling
  interval <= lambda_c / 5, ISO 21920 evaluation length = 5 lambda_c. ONE
  cutoff set for every object, fixed by the coarsest source (the Juglet). The
  write-up says in print that ISO's rules assume far denser sampling than
  photogrammetry gives.
- **Q9.** Report a robust centre (median absolute height, robust Ra) AND the
  90th-percentile height. Not full Rz. Wear removes peaks, so a centre-only
  number under-reports it.
- **Q10.** (a) Compare against the Juglet at e100 only; e025-e075 are reported
  as unreadable against it. (b) A deeper-ladder regeneration (raise `knn` /
  `n_self_samples` in `erode_fracture_band`) is queued as its own data job.
  (c), statistics below the point spacing, rejected. Consequence: one worn
  comparison point against the Juglet, no dose-response curve against it yet.
- **Q11.** Resample every object and every rung to the coarsest source in the
  comparison, and print the achieved spacing beside every figure. **Caveat
  carried to Q12:** the recommendation text named "the Juglet's 0.48 mm", but
  job 30386546 and the reconciliation above show 0.48 is a triangle-edge
  figure; the sampling-interval figure ISO means is nearest-neighbour, 0.338 mm
  at the Juglet's coarsest sherd.

**Round 3 (Q12, Q14-Q17 accepted as recommended, 2026-09-11; Q13 deferred).**

- **Q12.** The ruler's spacing is the nearest-neighbour figure, 0.338 mm at the
  Juglet's coarsest sherd, so the three cutoffs are 1.7 / 2.5 / 3.4 mm (longest
  profile 17 mm). The triangle-edge figure, 0.48 mm, is printed beside it.
- **Q13.** Break-face selection: **deferred.** The conservator asked for the
  overlap to be dealt with first: the hand reassembly may have set sherds a
  little too close, which does not mean they do not match. See "Separating the
  reference sherds" below. The options on the table stay as presented: (a)
  unsigned facing plus the tight gap, recommended, gated on a synthetic
  overlapping-faces test and on the sim pots staying unchanged; (b) gap plus
  opposite partner; (c) neighbour-free selection.
- **Q14.** The null-model control is a gate, run per pot: the fresh sim faces
  are thinned to the Juglet spacing and must not drift toward worn, measured
  against the spread between that pot's own fresh faces. Pots that fail are
  excluded.
- **Q15.** The match rule is written before measuring, per pot and per cutoff:
  match / moves toward / no match. Pots are counted in each class, never
  pooled; RePAIR is reported separately. The result is stated as a lead.
- **Q16.** Claim (a) -- this settles **D2**.
- **Q17.** The deeper ladder's rungs are defined by measured wear depth in
  Juglet dot-steps (1 / 2 / 3, about 0.34 / 0.68 / 1.0 mm). The setting is
  tuned until each rung is reached, checked by measurement and by render, and
  the top rung must be deep enough to bracket the Juglet.

## Separating the reference sherds (before Q13)

**Why.** Jobs 30420351 / 30420961: 33.2% of the Juglet's 21,675 join dots, and
61.7% of its 8,247 face-to-face dots, lie inside the neighbouring sherd. Worst
join 3-6: median -0.15 mm, 10th percentile -0.52 mm. Typical join 6-5: the
faces lie on top of each other, crossing within ~0.1 mm. The conservator's
reading (2026-09-11): the sherds match, but by hand they were set a little
too close; moving them apart is permitted. Category 2 for the old selection
(it assumed the neighbour is in front of the face), not category 3: nothing
here says the reassembly is the wrong answer.

**Opinion, with sources.** Sound and standard. Reassembly pipelines finish
with a simultaneous, non-penetrating rigid registration of all fragments
(Huang et al. 2006, ACM TOG 25(3)); the 2025 survey (arXiv 2410.14770) and
SARe (arXiv 2603.21611) treat interpenetration as a defect to measure and
remove. What it can and cannot do: a rigid move fixes a sherd pushed in as a
whole (3-6, ~0.5 mm). It cannot remove two rough faces crossing back and forth
at one point spacing (6-5, ~0.1 mm) without opening a gap about that wide
elsewhere. So Q13 stays open: future hand reassemblies will have the same
touch-level overlap, and the ruler must tolerate it.

**Method** (`scripts/separate_juglet_overlap.py`). Sherd 0 (largest) held
still; the other eight each get one small turn and shift, solved together.
Every dot within 1.2 mm of a neighbour is a constraint: signed distance to the
neighbour's surface (winding number for inside, exact point-to-triangle
distance) must end at or above a target. Of the moves that meet it, the one
taken moves the surfaces least from the ORIGINAL pose, so real gaps are not
pulled shut. Steps of at most 0.2 mm, re-measured exactly each time.
Two targets, both written: **strict** (no dot inside) and **tolerant**
(overlap up to one point spacing, what the scan cannot tell from touching).

**Gates.**
- G0 `scripts/selftest_separate_juglet.py`, boxes with exact answers: 0.1 in ->
  out 0.1 unturned; 0.1 apart and exactly touching -> nothing moves; three in
  a row -> 0.1 and 0.2; 0.05 allowed -> out 0.05; turned 3 deg -> cleared with
  a smaller mean move than a plain shift. **ALL PASS on the laptop,
  2026-09-11.**
- G1 run again from the strict result: nothing moves more than 0.01 mm.
- G2 one sherd pushed 0.2 mm into its neighbour, the rest held: comes back to
  within 0.05 mm of its strict place.
- Every sherd's move printed (shift mm, turn deg, mean and furthest point); a
  move over half the wall is flagged to look at before accepting.
- Render: worst and typical join, before / strict / tolerant, cut across the
  join through the meshes, in the left sherd's own frame, with the px-per-mm
  and frame checks.

**Outputs.** `juglet_gt.hdf5` is only read. Copies go to
`eval_runs/sherd_scale/juglet_gt_separated_{strict,tolerant}.hdf5` with the
per-sherd transforms in `juglet_separation.json`, written only if every gate
and both targets pass. The same Slurm job then reruns
`diagnose_juglet_selection.py` on each copy (`--scale-from` the original, so
the millimetres match), which is the evidence Q13 needs. **The copies are not
swapped into any TORA evaluation without the conservator's say-so.**

