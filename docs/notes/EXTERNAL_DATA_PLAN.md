# External data: shapes to train on, and real worn material to measure

**Status:** plan, agreed 2026-08-17. Not started. Each half is gated separately —
see §3.5 and §4.5.

Two datasets, two different gaps. They are not alternatives and the distinction
matters, because taking either for the other's purpose would waste the effort.

| gap | what we have | what fills it |
|---|---|---|
| **shape variety** — the model has seen almost no pots | 8 ceramic vessels | **Geometric Breaks**, 1,125 vessels |
| **real worn material** — one object, one afternoon | the Juglet, 9 sherds | **RePAIR**, ~1,000 fragments with expert ground truth |

---

## 1. The shape gap, and why it is binding

The conservator's point, and it is correct: we can manufacture wear, we cannot
manufacture objects. Wear became the focus because it was what was being worked
on, not because it was what most limits the result.

Measured on the current training source (`real_finetune.hdf5`):

| category | objects |
|---|---|
| bones | 16 |
| **ceramics** | **8** |
| egg | 3 (excluded — see `build_wear_trainset_v2.py`) |
| **total** | **27** |

The eight are `blue_pot`, `galli_pot`, `narrow_bottle1-4`, `pink_bowl`, `plate`.
A model expected to reassemble a Palestinian juglet has seen eight pots. Every
wear variant, missing-piece draw and chip size is layered on those same eight
shapes, so the dataset is wide in damage and nearly blind in form.

---

## 2. The validation gap

We cannot check simulated wear against real worn material. The Juglet's break
faces are sampled at 0.243% of object size, so nothing finer than about 0.5% is
recorded, and our blunting acts at 0.3-0.5%. Every scale a comparison can reach
lies above where the wear acts (`compare_wear_to_juglet.py`). It is one pot,
reassembled once, by one person, and it cannot answer the question.

---

## 3. Geometric Breaks — for shapes

Lamb et al., Clarkson TARS lab (the Fantastic Breaks / DeepJoin group).

- DOI [10.1109/IEEEDATA.2025.3611886](https://doi.org/10.1109/IEEEDATA.2025.3611886),
  IEEE Data Descriptions, article CC-BY 4.0
- Data: <https://huggingface.co/datasets/tars-home/GeometricBreaks>
- `kitchenware.zip` 14.22 GB holds the classes we want; `GSO.zip` 1.47 GB is
  real scanned consumer objects and is worth including for its capture realism.

Counted from the archive index:

| class | objects |
|---|---|
| jar | 500 |
| bottle | 447 |
| mug | 178 |
| **total** | **1,125** |

### 3.1 Do NOT use its fractures

GB is a shape-*repair* dataset: the broken model is the object with a chunk
missing, and the repair part is the chunk. Across all 4,209 breaks in
`kitchenware.zip`:

| fragments in the break | breaks | share |
|---|---|---|
| 1 | 4,097 | 97.3% |
| 2 | 60 | 1.4% |
| 3 or more | 52 | 1.2% |

Our problem is a nine-piece pot; a 97%-single-fragment dataset does not train
it. The fracture surfaces are unsuitable besides — boolean cuts made with a
jittered cube or icosphere, so a break face is a sphere or a plane rather than a
crack path.

### 3.2 DO use `model_c.ply`

The waterproofed complete mesh, shipped for every object: 1,125 clean,
watertight, densely remeshed vessels. We fracture them ourselves and wear them
ourselves, and we own the ground truth.

### 3.3 Resolution is adequate — checked

Sampled fragments carry 20k-150k vertices at a median spacing of 0.193% of
fragment size, so roughly 0.1% of object size, against a blunting cutoff of
0.30-0.50%. `blue_pot` sits at 0.068-0.082%. These meshes can carry the wear we
apply.

### 3.4 The pipeline

    GB model_c.ply  ->  visual triage  ->  fracture  ->  wear  ->  train

### 3.5 GATE: how to fracture

Nothing in this repo or the Spartan environment can break a whole object into
pieces — every dataset used so far arrived pre-fractured. `manifold3d` is
installed, which is the building block and not the method.

This choice matters more than anything else in the chain, because **the break
surface is the signal the model learns from.**

- **Fracture modes** (Sellán et al.), which Breaking Bad itself used. Physically
  motivated, so the faces carry the directional structure real breaks have.
- **Voronoi cells cut with booleans.** A day's work, and it produces near-planar
  faces. A flat face carries almost no *curve*, and the curve is what we have
  concluded survives on worn material. It would defeat the purpose.

**Next action:** read fracture modes at its pinned version and find how it is
used on thin-walled vessels. A pot is a shell, and shells fracture differently
from the solids these tools are demonstrated on.

### 3.6 Caveats

- **Consumer objects, not archaeological vessels.** The bottle class holds
  plastic water bottles and spray cans. Jar is the most pot-like. Render a
  sample and triage by eye first — a thousand irrelevant shapes is worse than
  eight relevant ones.
- **CAD, not scans.** ShapeNet models lack the surface noise and capture
  artefacts real material carries. GSO is photogrammetry and closer to real.

---

## 4. RePAIR — for real worn material

[arXiv 2410.24010](https://arxiv.org/abs/2410.24010), NeurIPS 2024 Datasets and
Benchmarks track. Fresco fragments from the House of Painters at Work, Pompeii,
destroyed in AD 79 and again by WWII bombing.

- **16,000 fragments**, of which **~1,000 reassembled by archaeologists** across
  years of excavation, cleaning and manual puzzle-solving.
- Multi-modal: high-resolution images, 3D scans, archaeologist metadata.
- **Ground truth poses are included** — "the meshes are already in the assembled
  position and orientation". We hand-built `juglet_gt.hdf5` for nine sherds;
  this is a thousand pieces, already solved by specialists.
- Data: [Zenodo 15800029](https://zenodo.org/records/15800029) — 3D_SOLVED
  43.9 GB, 3D_OPEN_DISCOVERY 3.0 GB, 2D_SOLVED 1.1 GB. OBJ + MTL + PNG texture.
- Licence: custom, scientific and cultural use, **non-commercial**, terms to be
  accepted. Fine for the PhD.
- Benchmark with five published baselines
  ([3D-baselines](https://github.com/RePAIRProject/3D-baselines)):
  PointNet-global, LSTM, DGL, SE(3)-equivariant, DiffAssemble. Metrics: Q_pos,
  RMSE translation (mm) and rotation (deg), neighbour consistency.

### 4.1 Resolution — measured, with a trap on the way

Sampled fragments: **110,757-193,143 unique vertices**, median spacing **0.113%
of fragment extent**. Fragments are 40-196 mm, so roughly **0.05-0.2 mm**.

**The trap, recorded because it is the recurring one here.** The OBJs store one
vertex per face corner because of the texture coordinates, so the raw arrays hold
about three times as many vertices as the geometry has, all exact duplicates. A
nearest-neighbour spacing computed on them comes out at **0.000%** — a
measurement reading the file format rather than the object, and one that looked
decisive. Merge coincident vertices before measuring anything on these meshes.

**And a comparison not to make.** The 0.113% above is relative to a FRAGMENT.
Our 0.3-0.5% cutoff is relative to an OBJECT. Different denominators, and
putting them side by side is the same category error as the fine/coarse ratio in
`compare_wear_to_juglet.py`. Whether these scans resolve the erosion signature
has to be settled by measuring the break faces, not by comparing spacings.

### 4.2 What it is for

**To measure.** A thousand real eroded fracture surfaces with a correct answer,
against our current one pot. If real erosion has a measurable signature at these
scales, the wear model can be aimed at something real instead of at a physical
argument alone.

**To test against.** An established benchmark with published baselines. Results
there are comparable with other work in a way that results on one juglet never
will be.

### 4.3 Caveats, and they are not small

- **Frescoes are not pottery.** Flat plaster slabs with no vessel curvature, and
  curvature is a major cue for sherds — it tells you where on the pot a piece
  came from. RePAIR cannot fill the shape gap.
- **Frescoes are reassembled largely by the painting.** Pictorial continuity is
  the dominant cue, and our methods are geometry-only. A 3D-only method may do
  badly on RePAIR for reasons that say nothing about pottery. Any result there
  must be read with that stated.
- The fracture is a ribbon around a thin slab — the conservator's eggshell case,
  and the one where our own blunting is weakest at the edges (§ known limits in
  `build_wear_trainset_v2.py`).

### 4.4 The pipeline

    RePAIR 3D_OPEN_DISCOVERY  ->  merge duplicate vertices  ->  break-face
    spectrum on real eroded surfaces  ->  compare with our simulated wear

### 4.5 GATE: does real erosion leave a measurable signature?

Run our own break-face relief spectrum on RePAIR fragments — the actual relief,
not the vertex spacing. If real eroded surfaces differ measurably from fresh
ones at scales these scans resolve, we have the calibration the Juglet could not
provide. If they do not, we have learned that the signature is below what
archaeological scanning delivers, which is itself worth knowing and would settle
the question rather than leaving it open.

**Next action:** pull the 3 GB open-discovery subset and measure. A few hours,
and the highest-value experiment currently available.

---

## 5. What not to disturb

The wear-augmented retrain (`29308186`) runs on the eight-vessel set and answers
whether wear-augmented training helps at all. Let it finish. Its result is
informative whatever we decide here, and adding data mid-flight would confound
it.

## 6. What neither dataset fixes

Neither gives paired fresh-and-worn scans of the same object. That remains the
only clean way to isolate what wear does to a fracture surface, and as far as
can be found, nobody has published it.
