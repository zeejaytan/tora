# Job 29623885 — the first genuine adapter run (LoRA on 371 vessel shapes)

Completed 2026-08-27 01:08, 02:31:35 wall, A100. Supersedes job 29527496, which
was a full fine-tune wearing an adapter (see `docs/lessons.md`).

> **⚠️ Corrected 2026-09-05 — the conclusions all stand, the numbers are worse
> than printed.** The evaluator averaged each fragment's error over the *loose*
> fragments but divided by *all* of them, so every rotation and translation figure
> carried one free zero for the anchor fragment; `part_accuracy` counted the free
> anchor as a success. Both are fixed below by recomputing from the stored result
> files (`artifacts/notes_recheck/lorav_*_29623885/`, fetched 2026-09-05) — nothing
> here is hand-scaled.
>
> **Why the argument survives.** Every arm was scored on the same objects, so the
> per-object correction factor is identical on both sides of every comparison and
> cancels out of every ratio. "Rotation rises 26 % and translation 35 % with the
> adapter on" is still 26 % and 36 % corrected. The *absolute* level is what moves,
> and it moves a lot: the untouched baseline on the worn sweep is **49.5°**, not
> 36.9°. Read as: even before the adapter, the model was turning a typical fragment
> most of a right angle away from where it belongs. Nothing in this run was close
> to assembled.
>
> **The one figure that reverses** is `rec@10deg` on the worn sweep, which is not
> load-bearing here: `adapter_off` printed 0.167 against the baseline's 0.100 and
> corrects to **0.078 against 0.089** — slightly worse, not better. It is a
> per-object all-or-nothing count on a diluted average, so it was the most fragile
> column in the tables.
>
> The geometry sections (join gap, contact band, wall thickness, fill ladder) come
> from mesh measurements, never touch the evaluator, and are unchanged.

## The freeze held this time

Stage 5 gate, `scripts/diff_adapter_checkpoint.py --fail-on-frozen`:

```
FROZEN encoder:         0 changed, 492 identical
FROZEN flow backbone:   0 changed, 171 identical
POSE HEAD final_mlp:    5 changed        (train_head=true, expected)
```

Training log: `[lora] freeze holds: 5,113,344 trainable after the training loop's
own hooks ran, 15 norm layers holding eval`. Lightning summary: 5.1M trainable,
398M frozen, `feature_extractor ... eval`.

So the on/off comparison is real. It was not real last time.

## Training

r=128, alpha=256, dropout=0.1, last_n_blocks=6, train_head=true, lr 2e-4,
60 epochs. Train 2521 / val 262 fragmented vessels, parts [3,20].
Checkpoint saved is `epoch-59.ckpt` (= `last.ckpt`); no best-on-val selection.

In-domain validation (every 10 epochs, 262 held-out simulated-fracture vessels):

| epoch | part_acc | chamfer |
|---|---|---|
| 9  | 0.805 | 4.87e-4 |
| 19 | 0.807 | 4.68e-4 |
| 29 | 0.820 | 3.96e-4 |
| 39 | 0.807 | 4.31e-4 |
| 49 | 0.808 | 4.28e-4 |
| 59 | 0.816 | 3.90e-4 |

*(`part_acc` here counts the free anchor as correctly placed, so it reads a few
points high; the trained vessels run 3–20 fragments, so the inflation is between
5 and 33 points depending on the object and cannot be undone from the logged
average alone. The **trend** is unaffected — every epoch is inflated the same
way.)*

+1.1 points over fifty epochs, non-monotonic. The adapter had essentially
converged by epoch 9 and then wandered. Per-batch train loss is flat and noisy
from epoch ~8 (0.03-0.19, no trend).

## Nine evaluation arms

`adapter_off` is NOT the untouched baseline: the pose head was retrained and has
no off switch. Three arms, not two.

Worn erosion sweep, n=30 — the arm that matters:

| arm | part_acc | best-of-5 | rot_err | rec@10deg | rec@5cm | chamfer |
|---|---|---|---|---|---|---|
| adapter_on  | 0.6163 | 0.7144 | 46.57 | 0.0444 | 0.0889 | 0.0024 |
| adapter_off | 0.7337 | 0.7878 | 33.94 | 0.1667 | 0.3778 | 0.0017 |
| baseline    | 0.7941 | 0.8622 | 36.86 | 0.1000 | 0.3222 | 0.0010 |

**Corrected 2026-09-05** — 30 objects (3–10 fragments), 3 draws each. `seating` is
the fraction of the *loose* fragments placed correctly, with the free anchor taken
out; `best-of-3` is the best of the three draws, so the plain column is the honest
one.

| arm | seating | best-of-3 seating | rot_err | trans_err | rec@10deg | rec@5cm | chamfer |
|---|---|---|---|---|---|---|---|
| adapter_on  | **0.4765** | 0.6150 | **62.47** | **0.1319** | 0.0444 | 0.0667 | 0.0024 |
| adapter_off | **0.6398** | 0.7176 | **45.61** | **0.0938** | 0.0778 | 0.3222 | 0.0017 |
| baseline    | **0.7201** | 0.8170 | **49.51** | **0.0970** | 0.0889 | 0.2111 | 0.0010 |

**In plain terms.** On worn vessels the untouched model seats about **72 % of the
loose sherds** and leaves a typical misplaced one turned **50°** — half a right
angle, obviously wrong on sight. Switching the adapter on drops that to **48 %
seated** and **62°**. The damage is bigger than the printed table showed: the
seating gap between baseline and adapter-on is **24 points**, where the
part-accuracy columns made it look like 18.

Fresh (unworn) real held-out, n=6:

| arm | part_acc | best-of-5 | rot_err | rec@10deg | rec@5cm | chamfer |
|---|---|---|---|---|---|---|
| adapter_on  | 0.7593 | 0.8722 | 38.55 | 0.0000 | 0.1667 | 0.0010 |
| adapter_off | 0.8537 | 0.8722 | 31.12 | 0.0556 | 0.4444 | 0.0006 |
| baseline    | 0.8481 | 0.9278 | 36.52 | 0.0556 | 0.2778 | 0.0005 |

**Corrected 2026-09-05** — 6 objects, 3 draws each:

| arm | seating | best-of-3 seating | rot_err | trans_err | rec@10deg | rec@5cm | chamfer |
|---|---|---|---|---|---|---|---|
| adapter_on  | **0.6741** | 0.8315 | **52.24** | **0.1029** | 0.0000 | 0.1111 | 0.0010 |
| adapter_off | **0.8037** | 0.8315 | **42.04** | **0.0771** | 0.0000 | 0.2778 | 0.0006 |
| baseline    | **0.7975** | 0.9148 | **48.94** | **0.0950** | 0.0556 | 0.1667 | 0.0005 |

Six objects. Any ordering here is a lead, not a result.

Juglet, n=1 object, 9 fragments, 5 runs:

| arm | part_acc | best-of-5 | rot_err | rec@5cm | chamfer |
|---|---|---|---|---|---|
| adapter_on  | 0.5111 | 0.6667 | 58.56 | 0.0000 | 0.0021 |
| adapter_off | 0.6444 | 0.7778 | 61.40 | 0.0000 | 0.0011 |
| baseline    | 0.6222 | 0.7778 | 46.75 | 0.2000 | 0.0011 |

**Corrected 2026-09-05** — one object, 9 fragments, so the factor is a flat
×1.125 and every ordering is preserved exactly:

| arm | seating | best-of-5 seating | rot_err | trans_err | rec@5cm | chamfer |
|---|---|---|---|---|---|---|
| adapter_on  | **0.4500** | 0.6250 | **65.88** | **0.1459** | 0.0000 | 0.0021 |
| adapter_off | **0.6000** | 0.7500 | **69.08** | **0.1669** | 0.0000 | 0.0011 |
| baseline    | **0.5750** | 0.7500 | **52.60** | **0.1106** | 0.2000 | 0.0011 |

Nine fragments on one pot, five runs. Read the renders below, not this table.

## What the renders show (mitsuba, `artifacts/lora29623885/`)

Reference: juglet on its side, neck left, closed rounded base right.

All three arms seat the body and neck correctly -- the single large fragment
carrying most of the vessel. Every difference between the arms is in the small
fragments at the base end (1-3 sherds out of 9).

- `adapter_off` best run (7/9): base end CLOSES. Blue/green/yellow sit as a
  rounded cap in roughly the right place. Best of the three by eye.
- `baseline` best run (7/9): base end splays outward like a fan, green/magenta/
  blue well outside the silhouette. Vessel does not close.
- `adapter_on` best run (6/9): base end loose, fragments hanging below and one
  flying outside the silhouette on the right.

Visual ranking (off > baseline > on) matches the numeric part_acc ranking on this
object. The renders agree with the metric here; they are not adding a correction,
they are confirming one. Colour differs between arms because the fragment-index
to colour map is run-dependent; the input scramble is pixel-identical across arms,
so the comparison is fair.

## Reading -- CORRECTED 2026-08-28, see below

The original reading of this run was WRONG and is kept here only so the
correction is legible.

> The adapter HURTS, on every arm. Worn sweep: 0.794 baseline -> 0.734 with the
> retrained head -> 0.616 with the adapter on. This is claim (1) -- the method
> genuinely did not transfer.

Two things were wrong with that.

**The stated mechanism was wrong.** I argued the Breaking Bad fragments carry no
fracture texture, so the adapter could only learn silhouette. Gate A
(`GATE_A_RESULT.md`, 20 RePAIR fresco fragments) found real eroded archaeological
fracture carries no interlocking texture at any scale a scan resolves EITHER. The
absence of micro-texture is not a difference between train and test, so it cannot
explain a train/test gap. The conservator caught this.

**The evaluation did not test what was trained** -- but not for the reason I first
gave. That reason (below, struck) was itself wrong, and the measurement is now in.

> The two sets use different, near opposite, wear operations: recession preserves
> curvature and opens the gap, erosion rounds curvature away and opens no gap.

`erode_fracture_band` DOES open the gap: measured, +9.5% at strength 1.0. I had
read "the ground-truth pose is preserved" as "the gap is preserved"; vertices can
retreat on both faces and leave the pose valid. And the conservator is right that
recession and erosion are one severity axis, not two kinds of damage -- that is
what `WEAR_SIMULATION.md` §2 says and what `wear_to_loss` implements. So the
question was never "which kind of wear", it was "how much", and both sets can be
put on the one ruler `wear_to_loss` is written in: how far the joins have opened.

### Both sets on one ruler (`scripts/compare_wear_severity.py`, 12 + 6 objects)

Join gap = 10th-percentile distance from each fragment to its nearest neighbour,
as a percentage of object size. Coincident = fraction of a fragment's vertices
lying EXACTLY on another fragment.

| set | level | join gap, % of object | coincident vertices |
|---|---|---|---|
| **train** bbad_vessels | fresh | **0.0000** | **44.4 %** |
| | worn_light | 0.0454 | 0 |
| | worn_moderate | **0.0978** | 0 |
| **test** erosion_sweep | 000 unworn | **1.1159** | 0 |
| | 050 | 1.1532 | 0 |
| | 100 full | **1.2294** | 0 |

**The dose of wear matches. The baseline it sits on does not.** Erosion at full
strength adds 0.11 points of gap; the moderate training dose adds 0.10. Those are
the same severity, exactly as argued. But the training joins start far tighter. In
the FRESH third, 44% of a fragment's vertices are literally the SAME POINTS as its
neighbour's, because they were cut from one mesh. In the two WORN thirds that is
not true -- both faces are receded, and coincidence is 0% -- but the recession is
so small (0.05-0.10% of object) that the faces are still effectively in contact.
A completely untouched real pot already sits 1.12% apart. The hardest training example is still **11x tighter than the easiest test
object**. On a 20 cm vessel: trained on joins 0 to 0.2 mm apart, tested on joins
2.2 to 2.5 mm apart.

Rendered, not just measured: `scripts/render_join_gap.py` -> `artifacts/join_gap.png`.
The per-vertex histograms show it directly. The fresh training object has a spike
at exactly 0 holding a third of its vertices and nothing structured after it. The
real pot has NOTHING below 0.15% -- about 3x its own vertex spacing, so this is a
real separation and not a sampling floor -- rising to a broad contact peak at 0.45%.

**This replaces the earlier hypothesis, which was backwards.** I guessed the
training gaps were ~5x too WIDE. They are ~11x too NARROW. In the fresh third,
nearly half of each fragment's mating surface is a literal copy of its
neighbour's, and a model can seat those by matching identical points without ever
reading curvature. The worn thirds share no vertices -- corrected 2026-08-28,
the earlier wording claimed they did -- but their joins are still tight enough to
be indistinguishable from contact at the network's input resolution (see below).
Neither situation exists on any real object.

**It also explains the residual the wear story could not.** The FRESH unworn real
arm fell too (0.848 -> 0.759; corrected seating **0.798 -> 0.674**), with no
abrasion applied. Under the wear-mismatch
story that made no sense. Under this one it is the same failure: the problem is
not wear, it is that every training join is a perfect-contact join and no real
join ever is.

Claim: **(2), the measurement measures a different thing than was trained** -- and
the cause is in our data build, not in TORA. This run still cannot say whether the
adapter works.

### WHY it harms: where the damage lands (2026-08-28)

Split the error into orientation and position, over all saved result JSONs.

| set | arm | part_acc | rot err | trans err | chamfer |
|---|---|---|---|---|---|
| sweep (n=90) | baseline | 0.794 | 36.86 deg | 0.0724 | 0.00100 |
| | adapter_off | 0.734 | **33.94** | **0.0701** | 0.00167 |
| | adapter_on | 0.616 | **46.57** | **0.0977** | 0.00244 |
| fresh (n=18) | baseline | 0.848 | 36.52 | 0.0716 | 0.00054 |
| | adapter_off | 0.854 | **31.12** | **0.0577** | 0.00062 |
| | adapter_on | 0.759 | **38.55** | **0.0766** | 0.00105 |

**Corrected 2026-09-05 — the split is unchanged, the level is not:**

| set | arm | seating | rot err | trans err | chamfer |
|---|---|---|---|---|---|
| sweep (n=90) | baseline | 0.720 | 49.51 deg | 0.0970 | 0.00100 |
| | adapter_off | 0.640 | **45.61** | **0.0938** | 0.00167 |
| | adapter_on | 0.477 | **62.47** | **0.1319** | 0.00244 |
| fresh (n=18) | baseline | 0.798 | 48.94 | 0.0950 | 0.00054 |
| | adapter_off | 0.804 | **42.04** | **0.0771** | 0.00062 |
| | adapter_on | 0.674 | **52.24** | **0.1029** | 0.00105 |

Because every arm ran on the same objects, the percentage changes the argument
below rests on are almost identical corrected: adapter-on raises rotation by
**26 %** (was 26 %) and translation by **36 %** (was 35 %). The reasoning holds
line for line; only the numbers it quotes change.

**This refutes the mechanism I was about to give.** "The model learned push-until-
contact, so it misjudges distance" predicts damage concentrated in TRANSLATION.
It is not: with the adapter on, rotation error rises 26% and translation 35% --
both, roughly together. A distance rule cannot make a fragment face the wrong way.

**What survives, and fits better.** The adapter sits in `self_qkv_proj`,
`self_out_proj`, `global_qkv_proj`, `global_out_proj` (`lora.py:76`) -- the
attention projections, i.e. the layers where fragments compare THEMSELVES TO EACH
OTHER. Our training set lets that comparison succeed by finding the neighbour
whose vertices are identical (44% coincident, gap exactly 0). That is a lookup,
not a reading of break shape. Sixty epochs tuned the comparison layers toward it.
On a real pot no vertex is shared, the nearest is ~2 mm away, and the only cue
left is the SHAPE of the break -- which the tuned comparison no longer grips.

Orientation is where that shows first, and does. A body sherd off a smooth wall is
a nearly featureless curved patch; the only thing saying which way round it goes is
the outline and relief of its broken edge. Rotation error 37 -> 47 deg is that
ability degrading. *(Corrected: **50 -> 62 deg**. Same 26 % degradation, from a
starting point that was already half a right angle out.)*

**It also localises the harm, and NOT to the pose head.** Retraining the head alone
(adapter_off) did not damage orientation -- it improved it, 36.5 -> 31.1 deg on the
fresh real pots, with part_acc level (0.848 -> 0.854). *(Corrected: **48.9 -> 42.0
deg**, seating level at 0.798 -> 0.804. Unchanged conclusion.)* The harm appears only when
the adapter in the comparison layers is switched on. So the earlier worry that
`train_head=true` bakes in irreversible damage is not supported: the head is fine.

UNEXPLAINED: on the sweep, adapter_off's part_acc falls (0.794 -> 0.734) while both
its mean errors improve. *(Corrected: seating falls further, 0.720 -> 0.640, so the
puzzle is real and slightly larger than printed — not an artefact of counting the
anchor.)* part_acc is a threshold count, so a distribution can shift
across the threshold while the mean improves, but that is a guess, not a finding.

Weight: one training run, no seed repeats; 30 objects x 3 draws (sweep), 6 x 3
(fresh). The mechanism is inferred from where the damage lands, not observed in the
features.

### What could still overturn this

The 1.12% gap on the real objects could be genuine material loss, or it could be
slop in the assembled ground-truth pose of `real_heldout_norm` -- claim (3). The
slab view looks like a consistent thin separation rather than floating fragments,
but that view cannot fully separate the two. Checking it means seating one real
object by hand and re-measuring.

### The join at the resolution the network is actually given (2026-08-28)

Everything above measures the join on the **mesh**. TORA never sees the mesh. It
samples 5000 points per object, allocated by fragment area (`tora/data/dataset.py`
`_sample_points`), and that is the entire input. So the question is not "is there
a gap" but "is the gap bigger than the spacing between the points the network
gets". `scripts/measure_gap_as_network_sees.py` replicates that allocation
verbatim and reports **gap / spacing**.

Below 1, the two faces fall inside one sampling cell: at the network's resolution
they are touching, whatever the mesh says.

| set | level | gap % of object | TORA spacing % | gap / spacing |
|---|---|---|---|---|
| train `bbad_vessels` (n=8) | fresh          | 0.741 | 2.950 | **0.277** |
|                            | worn_light     | 0.832 | 2.827 | **0.281** |
|                            | worn_moderate  | 0.761 | 2.854 | **0.281** |
| test `erosion_sweep` (n=6) | 000            | 1.423 | 2.337 | **0.620** |
|                            | 025            | 1.463 | 2.334 | 0.686 |
|                            | 050            | 1.517 | 2.327 | 0.680 |
|                            | 075            | 1.610 | 2.317 | 0.724 |
|                            | 100            | 1.743 | 2.310 | **0.788** |

Uniform sampler; Poisson-disk on the training set gives 0.266 / 0.273 / 0.267 --
same answer. The real scans are too dense for Poisson-disk on the login node.

Two things fall out, and they are different things.

**1. The wear ladder is invisible.** Fresh, light and moderate come out at 0.277,
0.281, 0.281 -- a 1.4% spread. The recession is 0.05-0.10% of object size; the
network's points sit 2.85% apart, roughly **thirty times coarser**. Fresh has 44%
of its vertices exactly coincident, i.e. a true zero gap, and still reads 0.277:
that number is the sampling floor for two surfaces in contact, not a measurement
of separation. All three training levels are at the floor. The adapter spent 60
epochs being asked to tell apart three inputs that are, to it, the same object.

**2. The real joins are not at the floor.** 0.62 at e000 rising to 0.79 at e100 --
roughly **2.3x the training figure**, and the erosion sweep's own dose axis moves
the ratio 27% where the entire training wear ladder moves it 1.4%. So the gap is
resolvable; the training set simply does not contain it. The absolute gap is also
~2x wider (1.42% vs 0.74%) with comparable spacing, so this is a wider join, not
a spacing artefact.

Together these say the adapter was trained on joins about twice as tight as any
real one, with a wear signal below its input resolution. Whatever it learned in
those 60 epochs, it cannot be "how worn sherds sit together" -- worn and fresh
were the same picture. Being in the attention projections, what it learned instead
is a change to how fragments compare to one another, which is precisely the
faculty reassembly depends on. That is consistent with the split above: rotation
and translation degrade together, and retraining the head alone *improves*
rotation.

This is claim (2) of the three, not claim (1): the method was not shown the thing
it was supposed to learn. It does not yet say TORA cannot learn it.

Caveat on the dose fix: raising the recession to reach a real-sized gap means a
~30x increase, not a nudge. At that size the recession is no longer a micro-scale
effect and must be checked against `docs/notes/WEAR_SIMULATION.md` -- and rendered
-- before it is trained on.

### The contact band, on the mesh (`scripts/measure_join_uniformity.py`)

Percentiles of the contact band only, as % of object size, against the mesh's own
vertex spacing. A p10 below the spacing is two surfaces still touching, sampled.

| set | level | p10 | p50 | p90 | vtx spacing |
|---|---|---|---|---|---|
| train | fresh         | 0.0000 | 0.0000 | 0.3909 | 0.2024 |
|       | worn_light    | 0.0079 | 0.0737 | 0.7827 | 0.2032 |
|       | worn_moderate | 0.0153 | 0.1554 | 0.6136 | 0.2112 |
| test  | 000           | 0.1667 | 0.6395 | 3.4922 | 0.0730 |
|       | 100           | 0.1794 | 0.7521 | 3.6856 | 0.0664 |

Training p10 and p50 sit at or below the mesh's own vertex spacing. The real p50
is ~9x its spacing. The same conclusion one level up from the sampling.

### The fracture surface, at the resolution the network is given (2026-08-28)

The gap result above drew a fair objection: if TORA's sampling is too coarse to
resolve a tenth of a millimetre of simulated recession, how does it match fresh
sherds by their fracture surface at all? The gap is only one of the channels the
network has, and the objection is about a different one.

**The encoder is fed six numbers per point, not three.**

    tora/modeling/encoder/point_cloud_encoder.py:113
        "feat": torch.cat([part_coords, part_normals], dim=-1)

The normal comes from `mesh.face_normals[fidx]` -- the orientation of the single
triangle the point landed on. That is a **sub-spacing** cue. It reports surface
orientation at triangle scale, ~0.07-0.20% of object here, roughly thirty times
finer than the 2.9% spacing between the points themselves. So "TORA cannot see
the wear" was proved for the GAP only. The orientation channel had to be measured
separately, on the exact points the network receives
(`scripts/measure_faces_as_network_sees.py`).

| set | level | contact % | face spacing % | mating angle | roughness | mate>135° | mate<45° | break pts /5000 |
|---|---|---|---|---|---|---|---|---|
| train (n=8) | fresh | 43.1 | 1.250 | 93° | 54.9° | 22.7% | 17.8% | 548 |
| | worn_light | 42.4 | 1.255 | 91° | 52.9° | 25.3% | 18.6% | 508 |
| | worn_moderate | 43.7 | 1.254 | 92° | 53.0° | 24.7% | 19.3% | 580 |
| real (n=6) | e000 | 19.1 | 0.698 | 88° | 29.7° | 19.5% | 18.1% | 182 |
| | e025 | 19.0 | 0.729 | 90° | 27.2° | 19.7% | 16.1% | 212 |
| | e050 | 17.9 | 0.684 | 89° | 26.6° | 20.5% | 16.4% | 199 |
| | e075 | 15.4 | 0.704 | 91° | 24.3° | 23.7% | 18.4% | 203 |
| | e100 | 15.0 | 0.670 | 93° | 22.2° | 23.7% | 15.4% | 195 |

**The mating angle is the load-bearing column.** Two faces pressed together point
away from each other, so a true mate reads 180°. A point on the outer wall
opposite another point on the outer wall, either side of the join, reads 0° --
the vessel surface simply continuing across the break. The median is ~90° on
every row, which is not "no signal": it is the arithmetic signature of a mixture
of those two populations, and the split columns confirm it. Only about **23% of
what TORA's own overlap rule calls contact is across a genuine fracture**; about
**18% is wall continuing across the join**.

It is also strongly bimodal by vessel, which is what a wall-thickness effect
looks like: BeerBottle 154-155°, Bottle 165-177°, DrinkBottle 152-174° against
Bowl 85-91°, Mug 91-96°, Teapot 88-89°, Vase 83-88°. Thick-walled objects get a
real break face; thin-walled ones do not.

**So the fracture channel exists, and it is thin.** Genuine fracture points are
548 of TORA's 5000 inputs (~11%) on the training vessels and only 182-212 (~4%)
on the real scans. That answers the objection in both directions: TORA does have
a fracture-shape channel independent of the gap, which is how it matches fresh
sherds -- and on this material that channel is carried by a few hundred points.

**This does not rescue the wear.** Along the training ladder fresh to
worn_moderate, contact% moves 43.1 to 43.7, mating angle 93° to 92°, roughness
54.9° to 53.0°, break points 548 to 580. Nothing moves. Along the real erosion
sweep, over the same axis, contact% falls 19.1 to 15.0 and roughness falls 29.7°
to 22.2° -- a clear, monotone response. The orientation channel *can* register
erosion; it does not register ours. The conclusion from the gap measurement
stands, now on the channel that was supposed to overturn it.

The real objects also carry a **less rough break** than the training ones (22-30°
against 53-55°), which is the opposite of what a "real fractures are messier"
intuition predicts, and is worth remembering when reading any transfer result.

### Look at it: `scripts/render_break_face_sampling.py` -> `artifacts/break_face.png`

The section is cut so that the vertical axis is *through the wall* and the
horizontal axis is *across the break*, with TORA's 5000 points drawn at one
sampling cell across so the picture cannot flatter the resolution, and genuine
fracture points ringed in black.

It matches the numbers. The vase rows show a thin curved wall with sampling dots
each wider than the wall itself, and 4 fracture points (fresh) / 2
(worn_moderate) in the entire slab. The bottle row shows a clean vertical column
of 87 ringed points -- a thick wall does get a proper break face. The real scan
shows 16. One caveat on the picture, not on the result: the bottle's left mesh
panel is nearly empty, which is that object's slab orientation, not evidence.

### Why the fracture channel is thin: wall thickness against sampling spacing (2026-08-31)

`scripts/measure_wall_vs_sampling.py`, job 29764781. The bimodality above --
bottles mating at 152-177 degrees, bowls and vases at 83-96 -- has a mechanism,
and it is measurable rather than inferred. TORA samples 5000 points per object,
so its cells are `sqrt(2 * area / 5000)` across. Ask how many of those fit
through the wall.

The estimator casts real rays (Moller-Trumbore, exact ray-triangle) inward from
area-weighted points on the surface and takes the median first back-facing hit.
It is checked against icosphere shells of known wall thickness before every run
(`--selftest`, 1%, 2.5%, 7.5% of object, all within 0.1%), and cross-checked by
`2V / (A - A_break)` -- mean shell thickness with the fragments' break faces
removed from the denominator. Two earlier versions of this script returned
confident wrong numbers and neither was caught by reading the code; both were
caught by the two routes disagreeing. See `docs/lessons.md`.

Training vessels, fresh level, per object:

| object | wall (ray) % | wall (2V/A) % | spacing % | cells through the wall | mating angle |
|---|---|---|---|---|---|
| Bottle__81bbf3134d1c | 14.72 | 24.00 | 3.38 | 4.35 | 165-177 |
| BeerBottle__2927d6c8438f | 12.66 | 15.36 | 2.77 | 4.58 | 154-155 |
| DrinkBottle__1ef68777bfdb | 10.39 | 14.34 | 2.55 | 4.07 | 152-174 |
| Mug__c51b79493419 | 3.06 | 5.10 | 2.86 | 1.07 | 91-96 |
| Vase__7545c5b77008 | 1.42 | 2.28 | 3.06 | 0.46 | 83-88 |
| Vase__d2b45cdfcfb7 | 1.21 | 1.77 | 3.30 | 0.37 | 83-88 |
| Bowl__50ad83141272 | 1.10 | 2.56 | 2.24 | 0.49 | 85-91 |
| Teapot__7c381f85d3b6 | 0.81 | 1.09 | 3.04 | 0.27 | 88-89 |

**The split is complete.** Every object above 4 cells mates at 152-177 degrees;
every object at or below 1.07 cells mates at 83-96. On eight objects that is a
lead rather than a law, but it is the mechanism the bimodality predicted, and it
is not a coincidence of one metric: the two wall columns are independent and
they order the objects the same way.

Medians over the ladder are flat, as everything else about our wear has been:

| level | wall ray % | wall 2V/A % | spacing % | cells | break faces % |
|---|---|---|---|---|---|
| fresh | 2.24 | 3.83 | 2.95 | 0.78 | 67.1 |
| worn_light | 2.22 | 3.62 | 2.83 | 0.79 | 63.0 |
| worn_moderate | 2.22 | 3.85 | 2.85 | 0.76 | 64.4 |

**The median training vessel gets 0.78 cells through its wall.** Below one cell,
a single sampled point straddles the whole thickness, so the break face never
gets a row of points to itself -- which is exactly the "few hundred fracture
points out of 5000" from the section above, arrived at from the geometry
instead of from the point cloud.

### And it is not eight objects: the whole corpus, screened (2026-08-31)

`scripts/screen_vessel_corpus.py`, job 29765705, all **1053** fracture instances
in `bbad_vessels.hdf5`. The eight-object ladder above holds across the corpus,
and it brings a second finding with it that nobody was looking for.

**Cells through the wall.** 23.6% of instances get under HALF a cell, 18.2%
under one, 21.4% between one and two, 18.2% two to four, 18.5% above four.
Median **1.20**. So roughly two in five objects are ones where a single sampled
point straddles the entire wall and the break face gets no row of points at all.

**And 37% of this corpus is not a vessel.** Section fill was measured by an
even-odd scanline count -- the fraction of a cut plane that lies inside the
object -- because shapely's `polygons_full` returns nothing on a section broken
into fragments, which is why an earlier hollowness figure came out blank.
Checked against a solid sphere (1.000) and two shells of known thickness
(0.097, 0.277) before use:

| fill | what it is | n | wall by 2V/A | mean cells |
|---|---|---|---|---|
| <0.25 | thin shell | 394 | 2.75% | 0.61 |
| 0.25-0.5 | thick shell | 212 | 5.41% | 1.19 |
| 0.5-0.8 | mostly filled | 59 | 6.39% | 1.46 |
| >=0.8 | **SOLID -- not a vessel** | **388** | **17.14%** | 3.95 |

`2V/A` shares no code with the scanline and orders the bins the same way, so the
label is not an artefact of one routine. And it was **rendered before it was
believed** (`artifacts/fill_ladder.png`, job 29768556): eight objects on a
ladder from 0.04 to 0.99, sectioned on the MEDIAN of three cuts rather than the
flattering one, with every scanline's measured interior shaded in. The first
version of that figure drew outlines only, confirmed the two ends and left the
middle -- where the threshold sits -- unreadable; that is the "the view answers
the wrong question" trap from `docs/lessons.md`, and it was caught by redrawing
the measured quantity itself rather than a proxy for it. Shaded, all eight walk
from a thin pink ring to a solid pink lump exactly in step with the number, and
if anything the 0.8 threshold is conservative: the 0.55 Vase and the 0.75 Bowl
already look solid by eye.

**This corrects `GATE_B_DECISION.md`**, which said a wall was found in 72 of 72
objects. That figure came from `wear_ops._wall_estimate`, whose search reach is
about 2% of object, so it reports a wall of roughly its own reach on anything,
solid included. Both `validate_wall_estimator.py` and
`check_wall_estimator_noise.py` had already flagged it and neither conclusion was
written back. The conservator's warning that some Breaking Bad meshes are solid
rather than thin-walled was right.

**The two defects are the same objects.** Cross-tabulating fill against cells:

| | TORA resolves the break (>=2 cells) | it does not (<2) |
|---|---|---|
| **solid lump** (fill >=0.8) | **370** | 18 |
| **hollow vessel** (fill <0.8) | 17 | **648** |

**97% on one diagonal.** Where the network can see a break face, the object is
not a pot; where the object is a pot, the network cannot see the break. Only
**17 instances** are both. A `cells >= 1 & fill < 0.5` screen keeps **207 of
1053 (19.7%)**.

By class, the solid lumps are Bottle 173, WineBottle 51, Vase 28, PillBottle 22,
BeerBottle 21, DrinkBottle 20 -- the closed forms, which fracture-mode
tetrahedralisation fills through its cage. The thin shells are Vase 211, Bowl 34,
Cup 31, Mug 30, Bottle 22, DrinkingUtensil 20, WineGlass 17, Teapot 11.

**What this means for the work.** The variety this corpus was built to supply is
partly an illusion. A large share of the "vessel shapes" are lumps with a broad
solid break face, which is a different assembly problem from seating a sherd,
and the genuinely vessel-shaped ones are mostly ones TORA cannot resolve. That
is a *separate* defect from the perfect-contact joins, and rebuilding the joins
does not touch it. The screen is therefore carried in the rebuilt file's manifest
as `passes_screen`, with `train_screened` / `val_screened` splits alongside the
full ones, so the trade -- 207 honest examples against 1053 mixed ones -- is made
deliberately at training time rather than inherited.

Claim type: **(2) the measurement was broken**, twice over. The wall probe had a
reach shorter than the thing it measured, and the corpus was believed hollow on
its word.

## Next, cheapest first

1. DONE, twice, and it inverted the guess -- see above. The training joins are
   11x TIGHTER than the test joins on the mesh, and at the resolution the
   network is given they are at the sampling floor while the real ones are not.
2. Rebuild the training set so its joins start where real joins start. The
   fragments must not share mating vertices: recede BOTH faces to a target gap
   ratio with `wear_to_loss`, aiming at a fresh-real gap of ~1.1% of object, and
   assert coincident vertices == 0 in the builder. This is the fix the
   measurement points at. CPU only.
3. Only then rerun the adapter. Building a recession-based evaluation sweep is no
   longer the decisive test -- the training data is.
4. Score the untouched baseline on the bbad_vessels val set -- still missing, so
   81.6% at epoch 59 currently has nothing to be compared against.
5. Lower lr (2e-5) / early stop ~epoch 10. The val curve flattened at epoch 9 and
   the remaining 50 epochs bought 1.1 points in-domain. Limits damage; does not
   make the data teach more.
6. train_head=false, so adapter_off becomes a true baseline. A diagnostic, not an
   improvement.

RETRACTED: widening the LoRA target set to GARF's full list. That assumed the
adapter was too small to learn the lesson. If the data or the evaluation is the
problem, more reach makes it worse, not better.
