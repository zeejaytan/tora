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

## Decisions for the conservator (the grilling should land these)

- **D1.** ~~Drop the Juglet?~~ **Settled: keep it.** The remaining sub-question
  is whether `e025` is reported as unreadable on the Juglet or dropped from the
  ladder entirely.
- **D2.** Is "matches real *scanned* worn fracture" the claim we want, given it
  is a training-data claim rather than a physical-fidelity one?
- **D3.** Is the Juglet (ceramic, one vessel) or RePAIR (fresco plaster, 20
  fragments) the primary worn reference? Same material as our pots against
  twenty times the sample.
- **D4.** What common point spacing do we resample everything to? The Juglet's
  0.48 mm sets the floor if it is in the comparison.

