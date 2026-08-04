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
| [fracture-modes](https://github.com/sgsellan/fracture-modes) (Sellán et al.) | physically-based fracture; the code behind [Breaking Bad](https://breaking-bad-dataset.github.io/) and therefore behind GARF/TORA training data | **breaks** objects, does not **wear** them |
| [soillib](https://github.com/erosiv/soillib), [hydraulic-erosion](https://github.com/mustartt/hydraulic-erosion) | geomorphology, terrain erosion | landscapes and heightmaps, not artefacts |
| [Deep Aramaic](https://arxiv.org/pdf/2310.07310) | abrades meshes for archaeological ML — smoothed edges, topological noise | **closest in spirit**, but targets inscriptions and the method lives in the paper, not a library |
| [stone-artifact weathering](https://link.springer.com/article/10.1007/s11042-015-2507-7), [Delaunay weathering](https://link.springer.com/article/10.1007/s00371-010-0506-2) | academic weathering simulation | no released code; terrain/stone rather than fragments |
| [libigl](https://libigl.github.io/tutorial/), trimesh | general geometry processing | building blocks, not a wear model |

There is a great deal of work on **breaking** things and on **eroding
landscapes**, and essentially nothing on **abrading fragments in a way that keeps
the assembly answer valid**. That last clause is the hard part: the wear has to
change the geometry without invalidating the ground-truth poses that make the
data trainable and scoreable.

---

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

## 3. What it guarantees

- **Ground-truth poses are never touched.** Geometry-only edits, so any dataset
  built with this stays scoreable.
- **Joins open** — worn fragments no longer meet tightly. This is the effect no
  earlier training data had; fragments always still mated perfectly, merely with
  smoother faces. It changes the assembly *problem*, not just its appearance.
- **Material loss stays small** (<1% of faces): chips, not demolition.
- **No corrugation.** Displacement fields are smoothed; an unsmoothed per-vertex
  displacement crumples the surface rather than retreating it.

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

## 6. Planned: genuine mesh offsetting

**Decided 2026-08-01, to be done after current testing completes.**

Recession currently displaces band vertices along a smoothed contact-relative
direction. That works, but it approximates what is properly a **solid offset** —
shrinking a closed body by a fixed distance.

[trimesh](https://trimesh.org/) and [libigl](https://libigl.github.io/tutorial/)
both implement this via signed-distance fields. Switching would:

- be mathematically correct rather than an approximation;
- handle self-intersection properly, which vertex displacement cannot;
- remove the need for direction-smoothing entirely — the offset has no direction
  ambiguity, so the whole class of normal-winding bugs disappears;
- give a defensible definition of "how much material was lost" (a distance),
  which currently has to be inferred.

**Validate the replacement against the current implementation before switching**,
the same way the 30× speedup was checked: the wear model is what every downstream
dataset depends on, so a change here must be shown not to alter behaviour beyond
the intended improvement.

---

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
