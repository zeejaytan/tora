# TORA Failure-Pattern Analysis — Thin-walled Pottery Subset

- **Data**: 3889 samples × 3 generations from `bbad_everyday_cka.ckpt` run on the 3933 thin-walled val split (Bowl, Cup, Plate, Mug, Teacup, Teapot, Vase)
- **Source logs**: [eval_runs/thinwalled_24194551/results/](eval_runs/thinwalled_24194551/results/)
- **Metric basis**: best-of-3 per-sample rotation_error (same definition TORA reports as `best_of_n/rotation_error`)
- **Failure threshold**: `rot_err >= 30°` (archaeologically meaningful misalignment)

## TL;DR

```
P(failure) ≈ f(piece_count) × g(break_pattern_distinctiveness) × h(shape_symmetry)
                ↑ dominant      ↑ moderate, variable              ↑ small but consistent
```

Piece count is the main driver — not linearly, but as a **cliff at 6 pieces**. Beyond that, break-pattern distinctiveness (fracture surface geometry) matters more than object identity.

---

## Finding 1: Failure is a cliff at 6 pieces, not a gradient

| Pieces | Fail rate (rot_err ≥ 30°) | Mean rot_err (°) |
|---|---|---|
| 2 | **0.0 %** | ~0.3° |
| 3-5 | 0.4 % | ~1.9° |
| **6-10** | **19 %** | **13-20°** ← first breakdown |
| 11-29 | **48 %** | **18-38°** ← catastrophic |

The jump from 5 → 6 pieces is sharper than from 10 → 20. TORA is essentially a "simple-reassembly solver" that collapses once combinatorial complexity kicks in. Degradation is not graceful.

## Finding 2: Category matters — only at high piece counts

Per-category mean rotation error (best-of-3), restricted to 11-29 pieces:

| Category | rot_err (°) | Why |
|---|---|---|
| **Mug** | 18.5° | best — handle provides asymmetric anchor |
| Teacup | 23.8° | smaller, simpler |
| Bowl | 26.2° | rim curvature partially constrains pose |
| Cup | 31.7° | thin cylindrical — rotationally ambiguous |
| Vase | 33.4° | axial symmetry → rotational aliasing |
| **Plate** | 35.9° | flat disc, rotational symmetry kills it |
| **Teapot** | 38.2° | **worst fail-rate (13 %)** — spout + handle + lid, structurally heterogeneous |

At 2 pieces all categories are tied at ~0.3°. Category-specific difficulty only appears once combinatorics becomes the dominant driver.

Full category table (all piece counts):

| Category | N | mean° | median° | p90° | mean pieces |
|---|---|---|---|---|---|
| Bowl | 449 | 4.63 | 0.47 | 17.47 | 4.3 |
| Cup | 384 | 6.24 | 0.53 | 23.11 | 4.6 |
| Mug | 762 | 3.34 | 0.36 | 12.12 | 3.7 |
| Plate | 297 | 5.76 | 0.63 | 24.44 | 4.5 |
| Teacup | 99 | 2.47 | 0.61 | 2.30 | 3.5 |
| Teapot | 69 | 6.25 | 0.24 | 35.13 | 4.3 |
| Vase | 1829 | 6.12 | 0.84 | 26.09 | 4.3 |

Full piece-count × category interaction (mean best-of-3 rot_err, °):

| Pieces | Bowl | Cup | Mug | Plate | Teacup | Teapot | Vase |
|---|---|---|---|---|---|---|---|
| 2 | 0.28 | 0.33 | 0.21 | 0.35 | 0.39 | 0.28 | 0.48 |
| 3-5 | 0.99 | 4.28 | 1.68 | 1.66 | 1.19 | 1.01 | 1.99 |
| 6-10 | 15.96 | 12.35 | 14.30 | 14.41 | 4.08 | 20.23 | 18.31 |
| 11-29 | 26.19 | 31.71 | 18.54 | 35.88 | 23.77 | 38.22 | 33.36 |

## Finding 3: Break *pattern* dominates over object identity

For 44 shape-meshes with ≥10 break variants each:

- **Within-shape std of rot_err**: 11° — same mesh, different breaks → huge variance
- **Between-shape std**: 3.7° — different meshes → small variance

**The same pot can succeed on one break and fail catastrophically on another.** Whether TORA gets it right depends more on the fracture surfaces than the vessel type. Clean, distinctive mating surfaces succeed; planar / ambiguous mating surfaces fail.

Corroborating: BBad's two break types:

| Break type | N | Mean pieces | Mean rot_err (°) | Median° | Mean trans_err |
|---|---|---|---|---|---|
| `fractured_N` (random, few pieces) | 3053 | 2.8 | **1.87°** | 0.45° | 0.6 cm |
| `mode_N` (canonical high-piece modes) | 836 | 9.3 | **17.83°** | 12.31° | 4.2 cm |

Mode-style breaks are designed to be hard (more pieces, more ambiguity) and TORA's error rises ~10× accordingly.

## Finding 4: Generation-to-generation instability is a free failure signal

TORA is stochastic; running inference 3× produces 3 candidate assemblies. Binning samples by the std of rot_err across their 3 generations:

| Stability quartile | Mean std across gens | Mean best-of-3 rot_err | Mean pieces |
|---|---|---|---|
| Q1 (most stable) | 0.12° | 0.56° | 2.5 |
| Q2 | 0.29° | 0.56° | 2.6 |
| Q3 | 0.54° | 1.12° | 2.9 |
| **Q4 (least stable)** | **5.68°** | **18.94°** | **8.8** |

**When the three predictions disagree, TORA is wrong.** Usable as a confidence signal without ground truth: if you run TORA 3× on an input and get three different assemblies, the answer is unreliable.

## Finding 5: Scale is NOT a factor

Quartile-binned by object scale (`scales` field, physical size in metres):

| Quartile | Scale range (m) | rot_err (°) | trans_err (cm) |
|---|---|---|---|
| Q1 (smallest) | 0.49–0.51 | 5.22 | 1.34 |
| Q2 | 0.51–0.54 | 4.97 | 1.28 |
| Q3 | 0.54–0.57 | 5.62 | 1.54 |
| Q4 (largest) | 0.57–0.71 | 5.39 | 1.37 |

Within this ~1.5× scale range, physical size does not affect accuracy. (Not to be confused with out-of-distribution scales — tests stay within the training distribution.)

## Finding 6: Shape identity — universally hard vs easy meshes

Shape meshes with ≥10 break variants, ranked by mean best-of-3 rot_err across all their breaks.

**Hardest — same mesh fails across break patterns:**

| Category | Shape hash (first 16 chars) | N breaks | Mean° | Min° | Max° | Avg pieces |
|---|---|---|---|---|---|---|
| Vase | `8fb8d64e04e0be16` | 99 | 21.34 | 0.00 | 69.97 | 7.3 |
| Vase | `4995132abfa4d6f2` | 32 | 15.19 | 0.00 | 68.94 | 8.1 |
| Vase | `38db6c39ee6d8a9d` | 38 | 13.35 | 0.00 | 65.78 | 6.3 |
| Vase | `8d861e4406a9d325` | 99 | 11.06 | 0.00 | 62.11 | 5.1 |
| Cup | `29e8781a8f6fdf1f` | 99 | 9.52 | 0.00 | 74.35 | 4.6 |

**Easiest — same mesh succeeds across break patterns:**

| Category | Shape hash (first 16 chars) | N breaks | Mean° | Min° | Max° | Avg pieces |
|---|---|---|---|---|---|---|
| Vase | `de673ddf9df03b82` | 99 | 1.34 | 0.00 | 27.32 | 3.1 |
| Vase | `38e712afedf758c3` | 99 | 1.43 | 0.00 | 24.02 | 3.3 |
| Mug | `9ff8400080c77fea` | 88 | 2.11 | 0.00 | 32.36 | 3.4 |
| Teacup | `6d1b5b270329e5c4` | 99 | 2.47 | 0.00 | 55.17 | 3.5 |
| Vase | `a1fae2bdac896ab8` | 99 | 2.53 | 0.00 | 38.19 | 3.7 |

Pattern: **tall, skinny, axisymmetric** → hard; **short, broad, asymmetric features** → easy.

---

## Implications for 40-piece archaeological tray

- **Piece count**: 40 is past the catastrophic cliff. Expected failure rate: **>>48 %** — pure extrapolation beyond the training distribution (max 29 pieces in thin-walled val).
- **Break pattern**: real sherds have eroded, worn mating surfaces — effectively the "ambiguous / planar" breaks that fail worst on synthetic data. Expect worst-case modality.
- **Shape symmetry**: if the tray is from a round vessel (bowl, jar, pot), rotational-aliasing failure mode stacks on top of piece-count failure.
- **Mitigation**: run TORA 3-5× on the same input; treat agreement across generations as a confidence score. Disagreement → discard the output.

## Next experiments worth running

1. **Zero-shot on `bbad_artifact`** (same HDF5): less-controlled fractures, closer to real archaeological breaks. Expected to show a meaningful gap from `everyday`.
2. **Best-of-N sweep** (N = 1, 3, 5, 10): does more stochastic retries push the cliff outward or just reduce variance?
3. **Confidence-gated accuracy**: restrict to samples where all 3 generations agree within 2° — is TORA *accurate when confident*? If yes, agreement-gating is a practical protocol for production use.
4. **Direct run on the user's 40-piece tray** — establishes the real-world OOD performance baseline.

---

*Generated 2026-04-23 from [tora_eval_24194551.log](tora_eval_24194551.log).*
