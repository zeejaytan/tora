# Simulating archaeological wear on 3D fragments

Reference for `scripts/wear_ops.py` — what it does, why it is built this way, what
it cannot do, and what should replace parts of it later.

Written for reuse: this is intended to generate worn training data for **future
datasets**, not only the one it was built for.

---

## 1. Why this exists — an actual gap in the ecosystem

Checked 2026-08-01. **No purpose-built tool exists for simulating archaeological
wear on 3D fragments while preserving reassembly ground truth.**

| existing work | what it does | why it does not fit |
|---|---|---|
| **[fracture-modes](https://github.com/sgsellan/fracture-modes)** (Sellán et al.) — *see §1b* | physically-based fracture; the code behind [Breaking Bad](https://breaking-bad-dataset.github.io/) and therefore behind GARF/TORA/PF++ training data | **breaks** objects, does not **wear** them |
| [soillib](https://github.com/erosiv/soillib), [hydraulic-erosion](https://github.com/mustartt/hydraulic-erosion) | geomorphology, terrain erosion | landscapes and heightmaps, not artefacts |
| [Deep Aramaic](https://arxiv.org/pdf/2310.07310) | abrades meshes for archaeological ML — smoothed edges, topological noise | **closest in spirit**, but targets inscriptions and the method lives in the paper, not a library |
| [stone-artifact weathering](https://link.springer.com/article/10.1007/s11042-015-2507-7), [Delaunay weathering](https://link.springer.com/article/10.1007/s00371-010-0506-2) | academic weathering simulation | no released code; terrain/stone rather than fragments |
| [libigl](https://libigl.github.io/tutorial/), trimesh | general geometry processing | building blocks, not a wear model |

There is a great deal of work on **breaking** things and on **eroding
landscapes**, and essentially nothing on **abrading fragments in a way that keeps
the assembly answer valid**. That last clause is the hard part: the wear has to
change the geometry without invalidating the ground-truth poses that make the
data trainable and scoreable.

### The gap is confirmed by the field's own literature

Two findings from arXiv make this stronger than "we couldn't find a tool":

**GARF's authors name eroded surfaces as their failure mode.**
[GARF (arXiv 2504.05400)](https://arxiv.org/abs/2504.05400) reports that despite
training on 1.9M fractures, it "still struggles with geometric ambiguity,
particularly when dealing with highly similar fragments and **eroded fracture
surfaces**." That is independent confirmation, from the method's own authors, of
what this investigation measured from the outside.

**The newest benchmark still has no wear.**
[SARe (arXiv 2603.21611, 2026)](https://arxiv.org/html/2603.21611v1) builds a
55K-sample reassembly benchmark from real scanned objects — and generates its
fractures "using the same pipeline as Breaking Bad". No erosion, weathering or
surface degradation. So as of 2026 the state of the art trains on **pristine
break surfaces** and then reports difficulty on eroded ones.

Related: [a survey of reassembly methods (arXiv 2410.14770)](https://arxiv.org/pdf/2410.14770);
[Deep Aramaic (arXiv 2310.07310)](https://arxiv.org/abs/2310.07310) remains the
nearest neighbour — it abrades meshes *and* procedurally removes small portions of
geometry to mimic missing stone, which is the same two-scale idea used here — but
targets inscriptions and releases no code.

**Net:** the field has identified worn surfaces as the open problem and has not
built the data to attack it. That is the gap this fills.

---

### 1b. fracture-modes — the upstream fracture generator

**<https://github.com/sgsellan/fracture-modes>**

Public code for Sellán et al., *Breaking Good: Fracture Modes for Realtime
Destruction* (ACM TOG) and *Breaking Bad: A Dataset for Geometric Fracture and
Reassembly* (NeurIPS 2022).

**This is the tool that produced the training data underneath everything in this
workspace.** Breaking Bad computed the first 20 "fracture modes" — a shape's most
geometrically natural ways of coming apart — for each of ~10k base models from
Thingi10K and PartNet, then simulated 80 fractures from them, giving ~1.05M
breakdown patterns. GARF, TORA and PF++ were all trained on subsets of that.

Worth keeping to hand for two reasons:

1. **To generate new synthetic fractures.** If a future dataset needs fractured
   objects rather than worn ones — new material, different categories, controlled
   piece counts — this is the tool, and it is the same one the pretrained
   checkpoints already saw, so the fracture statistics stay consistent with what
   the models were trained on.
2. **It defines the boundary this wear model sits on.** fracture-modes answers
   *how does this object break*. It says nothing about *what happens to the
   fragments afterwards*, which is the entire gap here. The two compose: fracture
   with fracture-modes, then wear with `wear_ops`, and the ground-truth poses
   survive both.

Together they would give something the field currently lacks: fractured objects
with **known assembly answers** whose break surfaces have been aged — which, per
§1, is precisely what GARF's authors report struggling with.

## 2. The model: wear is material loss at three scales

The organising idea, from the conservator directing this work:

> **Wear IS material loss. Smoothing is not a separate effect — it is loss of the
> sharp edges.** What differs is the *scale* of what goes.

| scale | what is lost | how it reads |
|---|---|---|
| micro | asperities on the break face | "smoothing" |
| meso | the mating surface as a whole | a receding edge, joins opening |
| macro | chunks at exposed points | chipping |

This reframing earned its place immediately: it explained a result that had been
filed as a measurement error. Abrasion was observed to open joins, which looked
anomalous under an earlier model treating smoothing and material loss as
independent. Under "smoothing is loss", it is simply expected.

**Order matters and follows the sherd's history: chip → smooth → recede.** A
sherd chips in antiquity and is *then* abraded for centuries, so its chip
boundaries end up rounded. Chipping last leaves fresh sharp edges, which are
themselves relief — that drove measured roughness *above* the untouched sherd
(galli_pot 0.457 → 0.681) until the order was corrected. Recession stays last so
the net loss from the mating face is not smoothed away.

---

## 2b. Why this matters: the two axes do different work

Conservator's synthesis (2026-08-05), and the conceptual core of the whole
investigation:

> Material loss is generally not terrible. **Smoothness is where the information
> of how sherds lock into each other is diminished.** Thus GARF, which relies
> only on the fracture surface, failed — and TORA, which also relies on the
> object's overall shape, did better.

The two axes are independent not merely because they are physically distinct,
but because they **do different work**:

| axis | what it changes | magnitude in real material |
|---|---|---|
| **material loss** | the GEOMETRY — sherds no longer meet, joins open | modest |
| **smoothness** | the INFORMATION — how sherds lock into each other | this is where it goes |

**This explains every measurement in the investigation, from a single principle.**

- **GARF reads only the fracture surface.** Abrasion destroys precisely that, so
  it goes blind: its encoder fires on 0.57% of Juglet points against 3.4% on
  fresh ceramics, and it cannot separate true mates from non-mates at all
  (1.04× across fifteen experiments).
- **TORA reads the fracture surface AND whole-object form.** The surface channel
  degrades identically (0.92 fresh → 0.71 worn), but the form channel holds
  (0.88) — so it still separates true mates at 1.63×, p = 0.025.
- **GARF's own authors name it**: "still struggles with … eroded fracture
  surfaces" ([arXiv 2504.05400](https://arxiv.org/abs/2504.05400)).
- **SARe (2026) likely inherits the same limit**, since it trains on Breaking
  Bad's pristine fractures.

### Consequences for building a dataset

The two axes need different treatment, and conflating them is what produced a
confused calibration earlier:

- **Material loss: keep it REALISTIC.** Real sherds do not lose much. An
  over-lossy dataset teaches the model to expect damage that is rare.
- **Smoothness: SPAN THE RANGE.** This is the axis that breaks the methods, so it
  is the axis the training data must cover. Under-representing smooth break faces
  trains for a problem the field has already solved.

So the sampling should not be a single "wear level" dial: wide coverage of
smoothness, modest and realistic material loss.

### And it reframes what a solution looks like

If smoothness *removes* the interlocking information rather than merely obscuring
it, then no amount of better break-surface perception recovers it — the signal is
gone from the object, not hidden. What survives is **form**: profile continuity,
wall curvature, how a sherd sits in the whole. TORA already partially exploits
this and does measurably better for it; a method that exploited it deliberately
should do better still.

That is the same conclusion GARF's investigation reached from the opposite
direction, and it is why this wear model matters: it lets the form channel be
trained deliberately instead of by accident.

## 3. What it guarantees

- **Ground-truth poses are never touched.** Geometry-only edits, so any dataset
  built with this stays scoreable.
- **Joins open** — worn fragments no longer meet tightly. This is the effect no
  earlier training data had; fragments always still mated perfectly, merely with
  smoother faces. It changes the assembly *problem*, not just its appearance.
- **Material loss stays small** (<1% of faces): chips, not demolition.
- **No corrugation.** Displacement fields are smoothed; an unsmoothed per-vertex
  displacement crumples the surface rather than retreating it.

## 3b. The hard limit of vertex displacement: fold-over

**Recession cannot exceed the local radius of curvature.** Push a concave region
inward further than that and the surface passes through itself, leaving spikes —
which register as *increased* roughness, the opposite of wear.

This is the real ceiling on the displacement approach, not a tuning error, and it
is exactly the failure that signed-distance offsetting exists to prevent
("without causing the mesh to fold over itself").

It surfaced as `worn_heavy` measuring rougher than the untouched sherd on 4 of 6
pots. **Three hypotheses were spent blaming chips** — sharp boundaries (fixed by
reordering), chip size (reduced), displacement-magnitude variation (smoothed) —
and none moved the number. The numbers had said so all along: `loss_dominant`
carries *more* chipping (4×0.0030) and *less* smoothing (0.3) yet came out
smoother (limb3 0.464) than `worn_heavy` (0.611, chips 4×0.0022, smoothing 1.0).
Chips could not be the cause. The only remaining difference was recession,
0.0025 against 0.0015.

**The render showed the folded geometry immediately.**

Displacement is now capped at 35% of local feature size, estimated per vertex as
the distance to the far end of its local neighbourhood — the opposite wall on a
thin sherd, the curvature scale in a concave dimple.

**Practical consequence for heavy wear:** if a future dataset needs recession
beyond this cap, use the SDF offset (§6) instead. A field offset has no fold-over
limit. The two methods are complementary rather than competing.

## 4. Known limits

- **Smoothing saturates.** Past roughly `kernel_frac_max=0.05` more smoothing
  removes nothing further (limb3: 0.1707 → 0.1789 → 0.1820 as the kernel grows).
  The same plateau GARF hit in Exp 7/7b. Wear does not stop there — it continues
  at a larger scale, which is what `wear_to_loss` does.
- **Some objects cannot be smoothed to a target roughness at all.** galli_pot
  stalls at 0.288 and plate at 0.234 against a 0.15 target, because they start
  unusually rough. Their wear must come from material loss instead.
- **Chipping raises measured roughness**, since chip boundaries are relief. Keep
  chips small enough to read as missing material rather than added texture.
- **Recession is an approximation** — see §6.

---

## 5. Two bugs worth remembering

Both are recorded because they were expensive and neither was found by numbers.

**Material loss by normal displacement corrugates the surface.** The first
attempt displaced each vertex along its own normal; on million-vertex scans with
noisy normals this adds high-frequency noise rather than removing material, and
measured relief rose ~6x. Loss is *removal*, not displacement.

**Mesh normals cannot be trusted for direction.** 7–17% of band normals on these
scans are wound **inward**, so recession pushed those patches *toward* the
neighbouring fragment. Damage tracked the defect exactly (blue_pot 14.5% inverted
→ gap ×0.95, going backwards; coxae 7.1% → ×1.14, correct). It survived **three
rounds of numeric validation**, because the wrongly-moved patches are the closest
points and so dominate every distance statistic — a systematic defect reading as
random noise. It was obvious within seconds of drawing the join.

**Hence the workspace rule** (`../../CLAUDE.md`): any operation that moves or
removes geometry is rendered before/after as part of its validation.

Recession now takes its direction from the **contact** — move away from the
nearest point on another fragment — which is correct by construction whatever the
winding, and is the truer statement of the physics: material is lost *at* the
contact, so the surface retreats *from* it.

---

## 6. SDF offsetting: implemented, tested, and the verdict revised twice

`scripts/sdf_offset.py`. Convert the fragment to a distance field, move the level
set, re-extract the surface. No direction is involved, so winding bugs cannot
occur — and there is no fold-over limit (§3b).

**The verdict took three attempts, and the first two were wrong. Recorded in full
because the sequence is more instructive than the conclusion.**

**1 — rejected.** "Halves the relief and closes joins." Both symptoms were real
measurements of a **sign-convention bug in my own code**: `mesh2sdf` is
NEGATIVE-inside, and raising the level to shrink only shrinks when inside is
POSITIVE, so every fragment was being *grown* (limb3 volume 0.000329 → 0.000412).
The method was rejected for a defect in the file implementing it — and the method
had been chosen specifically to eliminate sign errors.

It was caught only because the conservator asked whether a visual check had been
done. It had not: the rejection rested on numbers alone, days after visual
confirmation became mandatory for this exact class of operation. The numbers
looked conclusive enough that the rule felt already satisfied — which is the
reasoning the rule exists to override.

**2 — reconsidered.** With the sign fixed and volumes shrinking correctly, relief
is *largely preserved* (blue_pot 0.208 against 0.218 original at grid 256). The
"grid sampling destroys the fracture texture" argument was mostly wrong too. The
genuine difference is that an SDF offset shrinks the **whole fragment uniformly**
while displacement targets the **contact band**, so displacement puts all removed
material into opening the join — ×1.38 against ×1.08 for the same distance. That
also suits pottery better: a fresh break face is newly exposed and unprotected,
while a finished or glazed outer surface wears far more slowly.

**3 — current.** Displacement has a **fold-over ceiling** (§3b) that the SDF does
not. So they are complementary:

| use | method | why |
|---|---|---|
| light–moderate wear | **displacement** | concentrates loss at the join, where wear concentrates |
| heavy wear | **SDF offset** | no fold-over limit; uniform shrinkage matters less than a folded surface |
| whole-fragment loss (e.g. chemical dissolution) | **SDF offset** | uniform shrinkage is the correct model |

Backends tolerate non-watertight input, which matters: these are scanned
fragments, and holes, self-intersections and inconsistent winding are normal —
the last already caused one silent bug here.

| library | note |
|---|---|
| [mesh_to_sdf](https://github.com/marian42/mesh_to_sdf) | handles non-watertight, self-intersecting, non-manifold meshes |
| [mesh2sdf](https://github.com/wang-ps/mesh2sdf) | same tolerance; currently used |
| [MeshLib](https://meshlib.io/feature/mesh-to-sdf/) | exact-distance shrink "without folding over itself" |
| [trimesh](https://github.com/mikedh/trimesh) | already a dependency; has signed-distance support |

**Whatever replaces or extends this must be validated against the current
implementation AND rendered.** Every downstream dataset depends on it, and §5 and
§3b both exist because numbers alone missed a defect that a picture showed at
once.

## 6b. Validated state (2026-08-05)

**All 30 arms pass — 6 objects x 5 conditions.** Job 28810949,
`RESULT: conditions behave as intended`.

| object | orig relief | abraded_heavy | worn_moderate | worn_heavy | gap (worn_heavy) |
|---|---|---|---|---|---|
| blue_pot | 0.223 | 0.111 | 0.159 | 0.164 | x1.67 |
| coxae | 0.161 | 0.129 | 0.138 | 0.150 | x1.18 |
| galli_pot | 0.460 | 0.280 | 0.384 | 0.343 | x1.40 |
| limb3 | 0.309 | 0.176 | 0.221 | 0.198 | x1.11 |
| plate | 0.336 | 0.232 | 0.283 | 0.259 | x1.29 |
| vert9 | 0.211 | 0.168 | 0.183 | 0.178 | x1.30 |

Relief falls below the untouched sherd under every wear condition, joins open on
every object (x1.02-x1.67), and 99.8%+ of each fragment survives. Ceramics and
bone both behave.

**Visual confirmation done** (`artifacts/wear_viz/final/`): cross-sections stay
coherent through every condition — no fragmentation, no spikes, no
wrong-direction movement. Note what the view can and cannot do: at this zoom a
displacement of ~0.002 is sub-pixel, so the cross-section confirms INTEGRITY
while the separation histogram confirms the EFFECT. Neither alone is sufficient.
That division is the point — the cross-section is what catches folded or
inverted geometry, which is exactly what numbers missed three times.

### What it cost, and what that teaches

Five real defects were found. Two were caught by numbers; **three were not**:

| defect | caught by |
|---|---|
| corrugation from raw-normal displacement | numbers (relief rose ~6x) |
| rim recession left broad faces still mating | numbers (one pot's join closed) |
| **inverted mesh normals** (7-17% wound inward) | **the render**, after 3 numeric rounds passed it |
| **SDF sign convention** (grew fragments) | **being asked whether a visual check was done** |
| **fold-over** at high recession | **the render**, after 3 wrong hypotheses about chips |

The pattern is consistent: whenever a defect moved geometry the WRONG DIRECTION,
the wrongly-moved points were the closest ones and therefore dominated every
distance statistic — so a systematic error read as noise. **Numbers were reliable
for "how much" and unreliable for "which way".**

Worth recording that the visual rule was already written down when the SDF was
rejected on numbers alone: the numbers looked conclusive enough that the rule
felt satisfied. The rule only worked when a person applied it.

## 7. Usage

```python
from wear_ops import apply_wear, wear_to_loss, wear_conditions

# explicit doses
worn = apply_wear(pieces, smoothing=1.0, recession=0.0015,
                  chip_count=4, chip_size=0.0022)

# wear until the joins have opened by a target amount — works even on objects
# whose surfaces will not smooth any further
worn, achieved = wear_to_loss(pieces, target_gap_ratio=1.30)

# canonical conditions for building a dataset: samples the scales independently
for name, kw in wear_conditions():
    worn = apply_wear(pieces, **kw)
```

Validation:

```bash
python scripts/validate_wear_conditions.py --visual-dir artifacts/wear_viz
python scripts/diagnose_recession.py --objects blue_pot,limb3
```

`pieces` is `[(vertices, faces), ...]` in the **assembled** pose. Returns the
same structure; topology changes when chipping is enabled.
</content>
