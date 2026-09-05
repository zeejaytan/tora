# TORA Failure-Pattern Analysis — Thin-walled Pottery Subset

> ## ⚠️ CORRECTION (2026-09-05) — every finding here survives; the failure
> ## rates were understated, worst in the middle of the piece-count range
>
> **Which of the three: the measurement was broken.** Nothing about the method
> or the reference answers is in question. The evaluator skipped the anchor
> fragment when summing rotation error but still divided by the **total**
> fragment count (`eval/metrics.py:compute_transform_errors`), so every stored
> figure carried a free zero — **×2.000 at two fragments, ×1.111 at ten,
> ×1.036 at twenty-nine.** The "failure threshold" of 30° was then applied to
> that diluted number, so runs were let through that should have been counted
> as failures.
>
> **This note could be recomputed rather than estimated.** All 3889 samples ×
> 3 generations were fetched back from `eval_runs/thinwalled_24194551`, and
> every table below regenerates from them to the printed digits. The corrected
> columns are therefore measured, not scaled by hand.
>
> **All six findings stand.** The 6-piece breakdown, the category ranking, the
> dominance of break pattern over object identity, the disagreement-as-warning
> signal, scale being a non-factor, and the hard/easy mesh lists are all
> unchanged in direction and in ordering — the correction is monotone within
> any fixed fragment count, so nothing that compares like with like can flip.
> **What changes is how bad the failures were**, and by how much depends on the
> piece count, which is the axis Finding 1 plots. Corrected rows are added
> beside the originals below.
>
> Ticket `.scratch/eval-readout/issues/03`; the full write-up of the bug is the
> 2026-09-05 banner in `TORA_GOOD_VS_BAD_ANALYSIS.md`.

- **Data**: 3889 samples × 3 generations from `bbad_everyday_cka.ckpt` run on the 3933 thin-walled val split (Bowl, Cup, Plate, Mug, Teacup, Teapot, Vase)
- **Source logs**: [eval_runs/thinwalled_24194551/results/](eval_runs/thinwalled_24194551/results/)
- **Metric basis**: best-of-3 per-sample rotation_error (same definition TORA reports as `best_of_n/rotation_error`)
- **Failure threshold**: `rot_err >= 30°` (archaeologically meaningful misalignment)
  — ⚠️ *as printed, applied to the diluted mean; corrected fail rates below*

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

**Corrected 2026-09-05**, recomputed from the same 11667 result files:

| Pieces | N | fail rate as printed | fail rate **corrected** | mean turn as printed | mean turn **corrected** |
|---|---|---|---|---|---|
| 2 | 2012 | 0.0 % | **0.0 %** | 0.37° | **0.74°** |
| 3-5 | 1095 | 0.4 % | **0.7 %** | 2.04° | **2.77°** |
| **6-10** | 437 | 19.0 % | **24.5 %** | 16.4° | **18.7°** |
| 11-29 | 345 | 48.1 % | **53.3 %** | 30.4° | **32.7°** |

**The finding holds and gets slightly stronger**: about a quarter of six-to-ten
piece pots and **more than half of the eleven-plus pots** come out with the
average sherd a third of a right angle or worse from correct, against
essentially none of the two-piece cases.

**But "cliff" overstates it — piece by piece it is a ramp, and the ramp is
steeper than printed.** The bin boundaries hid this, and the correction (which
is largest at low piece counts) had been flattening it further:

| pieces | N | fail rate as printed | fail rate **corrected** | mean turn **corrected** |
|---|---|---|---|---|
| 2 | 2012 | 0.0 % | 0.0 % | 0.74° |
| 3 | 629 | 0.2 % | 0.3 % | 1.79° |
| 4 | 298 | 0.3 % | 0.7 % | 3.04° |
| 5 | 168 | 1.2 % | 2.4 % | 5.98° |
| 6 | 103 | 5.8 % | **9.7 %** | 9.98° |
| 7 | 96 | 5.2 % | **15.6 %** | 14.6° |
| 8 | 78 | 20.5 % | **25.6 %** | 19.9° |
| 9 | 83 | 36.1 % | **38.6 %** | 24.8° |
| 10 | 77 | 33.8 % | **39.0 %** | 27.6° |
| 11 | 50 | 42.0 % | **48.0 %** | 27.9° |
| 12 | 64 | 26.6 % | **34.4 %** | 26.1° |

The worst under-reporting is at **seven pieces, where the failure rate was
printed as 5.2 % and is actually 15.6 % — three times understated**. The
practical reading for a conservator is unchanged in kind but firmer: the method
is reliable to about five fragments, is losing roughly one pot in ten at six,
one in four at eight, and about two in five from nine fragments up.

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

Corrected 2026-09-05 — **the ranking is unchanged**, which is expected: within
this bin the fragment counts are similar across categories, so the correction is
close to a common factor. The fail-rate column is the one that moves:

| Category | N | turn as printed | turn **corrected** | fail rate **corrected** |
|---|---|---|---|---|
| **Mug** | 44 | 18.5° | **20.1°** | 18.2 % |
| Teacup | 7 | 23.8° | **25.8°** | 42.9 % *(7 samples — no weight)* |
| Bowl | 52 | 26.2° | **28.1°** | 42.3 % |
| Cup | 41 | 31.7° | **33.9°** | 48.8 % |
| Vase | 157 | 33.4° | **35.9°** | 63.7 % |
| **Plate** | 36 | 35.9° | **38.3°** | **66.7 %** |
| **Teapot** | 8 | 38.2° | **40.9°** | 87.5 % *(8 samples — no weight)* |

⚠️ The two extremes of the ranking rest on **seven and eight samples**. Mug
(44), Bowl (52), Cup (41), Plate (36) and Vase (157) carry the finding; Teacup
and Teapot are anecdotes and the "worst fail-rate (13 %)" tag on Teapot was
computed over the whole category, not this bin. Corrected, **two thirds of
eleven-plus-piece plates and vases fail** — the flat and the axially symmetric
shapes, which is what the symmetry explanation predicts.

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

Corrected 2026-09-05 (same N, same ordering):

| Category | N | mean° | median° | p90° | mean pieces |
|---|---|---|---|---|---|
| Bowl | 449 | **5.27** | **0.86** | **20.14** | 4.3 |
| Cup | 384 | **7.29** | **0.96** | **27.00** | 4.6 |
| Mug | 762 | **3.96** | **0.64** | **13.35** | 3.7 |
| Plate | 297 | **6.53** | **1.07** | **25.70** | 4.5 |
| Teacup | 99 | **3.01** | **1.09** | **2.83** | 3.5 |
| Teapot | 69 | **7.00** | **0.46** | **37.40** | 4.3 |
| Vase | 1829 | **7.13** | **1.41** | **29.01** | 4.3 |

Note the **medians roughly double** while the means rise by ~15 %. That is the
correction doing what it must: the median sample is a two- or three-piece break,
where the free zero was half or a third of the number.

Full piece-count × category interaction (mean best-of-3 rot_err, °):

| Pieces | Bowl | Cup | Mug | Plate | Teacup | Teapot | Vase |
|---|---|---|---|---|---|---|---|
| 2 | 0.28 | 0.33 | 0.21 | 0.35 | 0.39 | 0.28 | 0.48 |
| 3-5 | 0.99 | 4.28 | 1.68 | 1.66 | 1.19 | 1.01 | 1.99 |
| 6-10 | 15.96 | 12.35 | 14.30 | 14.41 | 4.08 | 20.23 | 18.31 |
| 11-29 | 26.19 | 31.71 | 18.54 | 35.88 | 23.77 | 38.22 | 33.36 |

Corrected 2026-09-05:

| Pieces | Bowl | Cup | Mug | Plate | Teacup | Teapot | Vase |
|---|---|---|---|---|---|---|---|
| 2 | 0.57 | 0.66 | 0.43 | 0.70 | 0.78 | 0.57 | 0.97 |
| 3-5 | 1.35 | 5.77 | 2.29 | 2.30 | 1.64 | 1.41 | 2.70 |
| 6-10 | 18.22 | 14.12 | 16.39 | 16.21 | 4.64 | 22.79 | 20.87 |
| 11-29 | 28.12 | 33.90 | 20.05 | 38.30 | 25.84 | 40.90 | 35.94 |

"At 2 pieces all categories are tied at ~0.3°" reads **~0.6°** corrected — still
a tie, still negligible: a two-piece break is essentially solved regardless of
vessel type.

## Finding 3: Break *pattern* dominates over object identity

For 44 shape-meshes with ≥10 break variants each:

- **Within-shape std of rot_err**: 11° — same mesh, different breaks → huge variance
- **Between-shape std**: 3.7° — different meshes → small variance

*(Corrected 2026-09-05: **12.0°** within-shape and **4.1°** between-shape across
the same 44 meshes. The 3× separation that carries this finding is unchanged.)*

**The same pot can succeed on one break and fail catastrophically on another.** Whether TORA gets it right depends more on the fracture surfaces than the vessel type. Clean, distinctive mating surfaces succeed; planar / ambiguous mating surfaces fail.

Corroborating: BBad's two break types:

| Break type | N | Mean pieces | Mean rot_err (°) | Median° | Mean trans_err |
|---|---|---|---|---|---|
| `fractured_N` (random, few pieces) | 3053 | 2.8 | **1.87°** | 0.45° | 0.6 cm |
| `mode_N` (canonical high-piece modes) | 836 | 9.3 | **17.83°** | 12.31° | 4.2 cm |

Mode-style breaks are designed to be hard (more pieces, more ambiguity) and TORA's error rises ~10× accordingly.

> **⚠️ Corrected 2026-09-05 — the "~10×" is a comparison across piece counts and
> so is exactly the kind the correction distorts.** `fractured_N` averages 2.8
> fragments (discount ≈ ×1.6) against `mode_N`'s 9.3 (≈ ×1.12), so the two rows
> were divided by different numbers:
>
> | Break type | N | Mean pieces | as printed | **corrected** | median **corrected** |
> |---|---|---|---|---|---|
> | `fractured_N` | 3053 | 2.8 | 1.87° | **2.45°** | **0.83°** |
> | `mode_N` | 836 | 9.3 | 17.83° | **19.70°** | **13.99°** |
>
> The gap is **8×, not 10×** — same conclusion, and the direction was never in
> doubt. But note what this row cannot separate: `mode_N` breaks have both more
> pieces *and* harder fracture surfaces, so this table does not isolate break
> pattern from piece count. Finding 3's within-versus-between-shape comparison
> above does, and that one is unaffected.

## Finding 4: Generation-to-generation instability is a free failure signal

TORA is stochastic; running inference 3× produces 3 candidate assemblies. Binning samples by the std of rot_err across their 3 generations:

| Stability quartile | Mean std across gens | Mean best-of-3 rot_err | Mean pieces |
|---|---|---|---|
| Q1 (most stable) | 0.12° | 0.56° | 2.5 |
| Q2 | 0.29° | 0.56° | 2.6 |
| Q3 | 0.54° | 1.12° | 2.9 |
| **Q4 (least stable)** | **5.68°** | **18.94°** | **8.8** |

Corrected 2026-09-05 (quartiles re-formed on the corrected spread, so the
membership shifts slightly):

| Stability quartile | Mean std across gens | Mean best-of-3 turn | Mean pieces |
|---|---|---|---|
| Q1 (most stable) | 0.22° | **1.04°** | 2.8 |
| Q2 | 0.52° | **1.15°** | 2.7 |
| Q3 | 0.93° | **1.64°** | 2.7 |
| **Q4 (least stable)** | **6.79°** | **20.78°** | **8.6** |

**The practical rule is unchanged and is the most useful thing in this note:**
run the method three times, and if the three assemblies disagree, the answer is
wrong. Corrected, the least-stable quarter averages **20.8° — a fifth of a right
angle on every sherd** — against about **1°** for the other three quarters. This
works without any ground truth, which is the normal archaeological case.

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

*(Corrected 2026-09-05: **5.97 / 5.82 / 6.60 / 6.24°**. Still flat, still no
trend — the finding stands.)*

> **2026-09-05, worth stating explicitly since it became load-bearing later:**
> the parenthesis above is the important sentence in this section. These scales
> are **0.49–0.71, i.e. inside or just above the trained band `[0.375, 0.625]`**,
> so what Finding 5 establishes is that size does not matter *within the band the
> model was trained on*. It says nothing about the out-of-band case, and several
> later real-object runs were scored at 0.04, 2.5, and 18–243 — where size
> emphatically does matter, because `scales` is fed to the model as a
> conditioning input at every denoising step. See `FRACTURA_WHY_IT_FAILS.md` §2.
> This table must not be cited as "scale is not a factor" without that
> qualification.

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

Corrected 2026-09-05 — **same five meshes, same order**: 24.22 / 16.43 / 14.91 /
12.96 / 11.13° mean, with worst-case single breaks at 73.9 / 71.9 / 75.2 / 71.3 /
77.0° — i.e. **the worst break of a hard mesh puts the sherds three-quarters of a
right angle out**.

**Easiest — same mesh succeeds across break patterns:**

| Category | Shape hash (first 16 chars) | N breaks | Mean° | Min° | Max° | Avg pieces |
|---|---|---|---|---|---|---|
| Vase | `de673ddf9df03b82` | 99 | 1.34 | 0.00 | 27.32 | 3.1 |
| Vase | `38e712afedf758c3` | 99 | 1.43 | 0.00 | 24.02 | 3.3 |
| Mug | `9ff8400080c77fea` | 88 | 2.11 | 0.00 | 32.36 | 3.4 |
| Teacup | `6d1b5b270329e5c4` | 99 | 2.47 | 0.00 | 55.17 | 3.5 |
| Vase | `a1fae2bdac896ab8` | 99 | 2.53 | 0.00 | 38.19 | 3.7 |

Corrected 2026-09-05 — **same five meshes, same order**: 1.80 / 1.91 / 2.52 /
3.01 / 3.07° mean, worst break 32.8 / 28.0 / 35.6 / 60.2 / 43.0°. The last column
is the point of the section: **even an "easy" mesh has at least one break pattern
that fails outright** — the Teacup's worst is 60°. There is no such thing as a
safe vessel, only a safe break.

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
