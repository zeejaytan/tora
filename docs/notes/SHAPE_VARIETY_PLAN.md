# Adding shape variety: the Geometric Breaks vessels

**Status:** plan, agreed 2026-08-17. Not started. Gated on the fracturing question in §5.

## 1. The gap, and why it is the binding one

The conservator's point, and it is correct: we can manufacture wear, we cannot
manufacture objects. Wear had become the focus because it was the thing being
worked on, not because it was the thing most limiting the result.

Measured on the current training source (`real_finetune.hdf5`):

| category | objects |
|---|---|
| bones | 16 |
| **ceramics** | **8** |
| egg | 3 (excluded — see `build_wear_trainset_v2.py`) |
| **total** | **27** |

The eight ceramic vessels are `blue_pot`, `galli_pot`, `narrow_bottle1-4`,
`pink_bowl`, `plate`. A model expected to reassemble a Palestinian juglet has
seen eight pots. Every wear variant, every missing-piece draw and every chip
size is drawn on top of those same eight shapes, so the dataset is wide in
damage and almost blind in form.

## 2. The source

**Geometric Breaks (GB)**, Lamb et al., Clarkson TARS lab — the group behind
Fantastic Breaks and DeepJoin.

- DOI [10.1109/IEEEDATA.2025.3611886](https://doi.org/10.1109/IEEEDATA.2025.3611886),
  IEEE Data Descriptions, article CC-BY 4.0
- Data: <https://huggingface.co/datasets/tars-home/GeometricBreaks>
- `kitchenware.zip` is 14.22 GB and holds the classes we want. `GSO.zip`
  (1.47 GB) is real scanned consumer objects and is worth including.

Vessel-shaped objects available, counted from the archive index:

| class | objects |
|---|---|
| jar | 500 |
| bottle | 447 |
| mug | 178 |
| **total** | **1,125** |

Against 8. That is the case for doing this.

## 3. What is usable, and what is not

**Do NOT use GB's fractures.** GB is a shape-*repair* dataset: the broken model
is the object with a chunk missing and the repair part is the chunk. Counted
across all 4,209 breaks in `kitchenware.zip`:

| fragments in the break | breaks | share |
|---|---|---|
| 1 | 4,097 | 97.3% |
| 2 | 60 | 1.4% |
| 3 or more | 52 | 1.2% |

Our problem is a nine-piece pot. A dataset that is 97% single-fragment does not
train it.

Its fracture surfaces are unsuitable besides: they are boolean cuts made with a
jittered cube or icosphere, so a break face is a sphere or a plane rather than a
crack path.

**DO use `model_c.ply`** — the waterproofed complete mesh, shipped for every
object. That is 1,125 clean, watertight, densely remeshed vessels. We fracture
them ourselves and wear them ourselves, and we own the ground truth.

**Resolution is adequate**, which was the risk worth checking first and is
checked: sampled fragments carry 20k–150k vertices at a median spacing of 0.193%
of fragment size, so roughly 0.1% of object size. Our blunting cutoff is
0.30–0.50% of object size, three to five times coarser than the sampling. For
comparison `blue_pot` sits at 0.068–0.082%. These meshes can carry the wear we
apply, unlike the Juglet scan, which cannot (§ `compare_wear_to_juglet.py`).

## 4. The pipeline

    GB model_c.ply  ->  visual triage  ->  fracture  ->  wear  ->  train

Wear stops being the deliverable and becomes one stage, which is what it was
always for.

## 5. THE GATE: how to fracture

Nothing in this repo or the Spartan environment can break a whole object into
pieces — every dataset used so far arrived pre-fractured. `manifold3d` is
installed, which gives boolean operations, i.e. the building block and not the
method.

This choice matters more than anything else in the chain, because **the break
surface is the signal the model learns from.** Two directions:

- **Fracture modes** (Sellán et al.), which is what Breaking Bad itself used.
  Physically motivated — it computes how the object wants to come apart — so
  the faces carry the directional structure real breaks have. Public code.
- **Voronoi cells cut with booleans.** Could be working in a day, and produces
  near-planar faces. A flat face carries almost no *curve*, and the curve is
  what we have concluded is the usable signal on worn material. This would
  undermine the point of doing any of it.

**Before committing:** read the fracture-modes documentation at its pinned
version and find how it is used on thin-walled vessels specifically. A pot is a
shell, and shells fracture differently from the solid objects these tools are
usually demonstrated on. That is the next action and it is an afternoon.

## 6. Caveats to carry

- **These are consumer objects, not archaeological vessels.** The ShapeNet
  bottle class contains plastic water bottles and spray cans. Jar is the most
  pot-like. Triage a rendered sample by eye before building anything — a
  thousand irrelevant shapes is worse than eight relevant ones.
- **CAD, not scans.** ShapeNet models are modelled, so they lack the surface
  noise and the scanner artefacts real material carries. GSO is photogrammetry
  and closer to real capture; include it for that reason.
- **This does not fix the wear validation.** We still cannot check simulated
  wear against real worn material, because no scan we have resolves the scale
  wear acts at. More shapes does not change that, and nothing in this plan
  should be read as closing it.

## 7. What not to disturb

The wear-augmented retrain (`29308186`) runs on the eight-vessel set and answers
whether wear-augmented training helps at all. Let it finish. Its result is
informative whatever we decide about shapes, and adding a dataset mid-flight
would confound it.
