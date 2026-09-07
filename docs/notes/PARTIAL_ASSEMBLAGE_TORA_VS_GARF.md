# Can TORA be asked "how much of the pot do you need?" — and should GARF be asked instead

**Written 2026-09-07.** Source: reading the two codebases at the checkouts in this
workspace. **No GPU time was spent on this.** Every claim below is a line of code, not a
measurement, and is cited so it can be checked or refuted by opening the file.

This note exists because a proposed experiment — the piece-count sweep — was about to be
run, and two objections to it turned out to be correct. The first was raised by the
conservator; the second was found while checking the first.

## The question that prompted it

If you hand a reassembly model only some of a vessel's sherds, does it still place the
ones it has correctly? That is `U4` — the normal archaeological case, where most of the
pot was never recovered. `piececount_sweep.hdf5` was built to ask it of TORA: take
`galli_pot` (10 fragments), draw random subsets of size 2, 3, 4, 6, 8, 10, and read
seating against k.

**That experiment cannot answer the question, and TORA cannot be asked it in its
current form.** Three separate reasons, in ascending order of how hard they are to fix.

## 1. The subsets are not joined to each other (measured)

`scripts/build_piececount_sweep.py:84` picks fragments with
`rng.choice(P, size=k, replace=False)` and never checks whether the chosen sherds touch.
Measured on `galli_pot` by grid-hashing vertices and counting shared break surfaces:
only **19 of 45** fragment pairs share a surface at all.

Connectivity of the 26 subsets the builder actually made:

| k | subsets connected | subsets with no join at all |
|---|---|---|
| 2 | 2 of 5 | **3 of 5** |
| 3 | 2 of 5 | 1 of 5 |
| 4 | 1 of 5 | — |
| 6 | 3 of 5 | — |
| 8 | **5 of 5** | — |
| 10 | connected (whole pot) | — |

Connectedness climbs monotonically with k, so the confound runs **exactly along the axis
being tested**. A falling curve against k would be indistinguishable from "we handed it
sherds that do not go together". In conservator's terms: at k = 2 the sweep is usually
asking the model to join two sherds from opposite sides of the pot that never touched,
and then scoring it for failing.

## 2. TORA inflates whatever you give it to the size of a whole pot

This is the more serious one, because fixing the adjacency does not fix it.

TORA measures **one** number per object — the half-span of the assembled whole thing —
and normalises the geometry by it:

```python
# tora/data/dataset.py:427-430
scale = np.max(np.abs(pts_gt))     # pts_gt is the whole assembled object
...
pts_gt /= scale
```

That single number is then fed to the network at every denoising step and attached to
**every point of every sherd** (`tora/modeling/flow_model/embedding.py:151-152`):

```python
scale_emb = self.scale_embedding.embed(scales.unsqueeze(-1))  # (B, 1, dim)
scale_emb = scale_emb.unsqueeze(1).expand(B, N, -1)           # (B, N, dim)
```

So whatever set of sherds you pass in is stretched until it fills the same box a
complete vessel fills, and the model is told the resulting span is the object's size.
Two rim sherds are presented to the model as a complete small vessel. The builder makes
this explicit rather than causing it — `TARGET_MAX_ABS = 0.5`
(`scripts/build_piececount_sweep.py:43`, `:92`) pre-rescales each subset by *its own*
half-span, so `scales` reads ≈ 0.5 (whole-pot size) for every k. But even without the
builder, TORA's own dataloader would do the same thing.

**Nothing in TORA's input can express "this is a fifth of a large pot."**

## 3. GARF does not have this problem, because it normalises per fragment

GARF measures the half-span of **each sherd separately** and normalises each one in its
own frame (`GARF/assembly/data/breaking_bad/uniform.py:85-88`):

```python
scale = np.max(np.abs(pointclouds), axis=(1, 2), keepdims=True)   # one per fragment
scale[scale == 0] = 1
pointclouds /= scale
```

and hands each fragment its own size at
`GARF/assembly/models/denoiser/modules/denoiser_transformer.py:173-174`:

```python
scale_emb = self.scale_embedding(scale)   # (valid_P, 21) -- per part
scale_emb = scale_emb[latent["batch"]]    # broadcast to that part's points only
```

**Consequence:** hand GARF two sherds out of ten and *nothing about those two sherds
changes* — each still arrives in its own box, still labelled with its own true size.
Hand TORA the same two and both the coordinates and the size label change. A piece-count
curve therefore means something different in the two models: for GARF it isolates piece
count; for TORA it confounds piece count with a size lie.

## What is NOT the difference: global attention

Worth stating because it is the intuitive answer and it is wrong. TORA does **not**
reason fragment-by-fragment, but **neither does GARF**. Both run the same two attention
stages in every layer — within each sherd, then across all sherds at once. TORA's own
docstring says so and says where it came from
(`tora/modeling/flow_model/layer.py:48-57`):

> *"1. Part-wise attention, independent for points in each part. 2. Global attention,
> across all parts. … Some codes are adapted from GARF"*

TORA builds `part_cu_seqlens` from `bincount(latent["batch"])`
(`tora/modeling/flow_model/dit.py:188-191`) and uses it only for the part-wise stage
(`layer.py:132`, `:246`); the global stage (`layer.py:181`, `:254`) attends across
everything with no segmentation at all. GARF builds **both** — `self_attn_cu_seqlens`
and `global_attn_cu_seqlens` — at
`GARF/assembly/models/denoiser/modules/denoiser_transformer.py:328-339`.

So "TORA is built on knowledge of the whole object and GARF is not" is only half right.
Both reason over the whole assemblage jointly. The difference is the **frame and the
size label**, not the attention.

## GARF already ships the harness for this experiment

The finding that changes what we should do next. GARF's dataset has first-class support
for missing and for foreign fragments (`GARF/assembly/data/breaking_bad/base.py:203-247`):

```python
# Removal to simulate missing part
if self.num_removal > 0:
    num_parts -= self.num_removal
    removal_mask = h5_file[name]["removal_masks"][self.num_removal - 1]
    ...
# Redundancy to simulate extra part
if self.num_redundancy > 0:
    redundant_pieces = h5_file[name]["redundant_pieces"][: self.num_redundancy]
```

- Config knobs `num_removal` / `num_redundancy` at
  `GARF/configs/data/breaking_bad.yaml:11-12`.
- `GARF/assembly/data/breaking_bad/module.py:44`: *"num_removal and num_redundancy are
  only used in the testing phase"* — so it is an evaluation axis by design, not a
  training augmentation.
- The removal masks and the removal **order** are precomputed and stored in the HDF5, so
  which pieces come out is fixed in advance and reproducible rather than redrawn each
  run.
- `redundant_pieces` carries sherds from *other objects* — the box-of-mixed-sherds case,
  which we have never tested on anything.

TORA has no equivalent. Its only omission path is one we added ourselves
(`tora/data/dataset.py:268-285`, `omit_rank`) and it removes **exactly one** fragment,
chosen by surface-area rank. That is the "one sherd is lost" case — already run as
juglet-cause ticket 04, job 30167044, and answered: a missing sherd degrades gracefully.
It is not the "most of the pot is missing" case.

## What this means

**Which of the three:** none of them yet — nothing was measured here. This is a
statement about **what a proposed measurement would have meant**, made before spending
the GPU time rather than after.

For the piece-count question specifically:

1. Fixing adjacency alone is **not enough**. A connected 2-sherd subset is still
   inflated to pot size.
2. A TORA piece-count experiment that means anything needs the subsets carried in the
   **whole pot's frame** — sherds keep their true size, only their number changes. That
   is a change to `build_piececount_sweep.py` **and** to how `scales` is supplied, not a
   re-run.
3. Even then it measures TORA outside its design envelope, and must be reported that
   way — not as "TORA fails when pieces are missing", but as "TORA has no way to be told
   pieces are missing".
4. The same question can be put to GARF today with its own shipped, reproducible
   harness, on many objects rather than one pot.

For `U4` more broadly: the deeper rung (50% / 25% present) is **not blocked on GPU
time** — it is blocked on the fact that the model we have been using cannot represent
the condition. That is a design finding, and it is cheap to have found it by reading.

## Files read

TORA: `tora/modeling/tora.py:300-370`, `tora/modeling/flow_model/dit.py:175-215`,
`tora/modeling/flow_model/layer.py:48-260`,
`tora/modeling/flow_model/embedding.py:120-158`, `tora/data/dataset.py:268-330`,
`:400-435`, `:515-530`, `scripts/build_piececount_sweep.py`.

GARF: `assembly/models/denoiser/modules/denoiser_transformer.py`,
`assembly/data/breaking_bad/base.py`, `assembly/data/breaking_bad/uniform.py`,
`assembly/data/breaking_bad/module.py`, `configs/data/breaking_bad.yaml`.
