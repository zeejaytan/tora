# Test plan — does TORA actually fail on the Juglet, and if so why?

Status: **DESIGN** (2026-07-24). No jobs submitted yet. Pre-registered gates and
mandatory controls below; nothing here is allowed to conclude until its
known-answer control passes (see the metric-bug post-mortem in
`TORA_GOOD_VS_BAD_ANALYSIS.md` § "Correction (2026-07-22)").

> **⚠️ CORRECTION (2026-09-05) — every absolute rotation figure in this plan and
> its results log is too kind; every ratio and every gate verdict is unchanged.**
>
> **Which of the three: the measurement was broken.** Stored `rotation_error`
> skips the anchor fragment when summing and still divides by the total fragment
> count (`eval/metrics.py`), so it carries a free zero: **×2.000 on any pair,
> ×1.125 on the nine-sherd Juglet.** This plan leans on rot_err specifically
> *because* it is scale-invariant and therefore immune to the 2026-07-22 bug —
> that reasoning was sound and the conclusion was wrong, because scale-invariant
> is not the same as bug-free. `recall@Ndeg` moved with it (thresholded on the
> diluted mean) and is a **per-object 0 or 1 on the whole pot's average turn**,
> not a fraction of fragments.
>
> Corrected figures are set beside the originals in the results log below.
> Recomputed through `scripts/readout.py`, the single gated reader; nothing
> re-run. Ticket `.scratch/eval-readout/issues/03`.

---

## The problem this plan has to solve first

After the 2026-07-22 metric correction we are in an awkward epistemic spot:

1. **We cannot currently measure TORA's Juglet reassembly at all.** Every scalar
   the pipeline computes for the Juglet is scored against `data["pointclouds_gt"]`
   (`tora/eval/evaluator.py:27,35,42-43`), and for the Juglet split that tensor
   **is the scattered scan/table layout, not an assembled vessel**
   (`JUGLET_TORA_ROOTCAUSE.md`, and independently `GARF/.../JUGLET_DEPLOY_INFERENCE_ANALYSIS.md`).
   So `part_acc = 1.0`, `object_chamfer ≈ 0`, *and* `rotation_error = 46–61°`
   (corrected 2026-09-05: **52–69°**)
   are all measuring against the wrong target. A "failure" number here is
   uninterpretable; so is a "success" number.

2. **The corrected whole-object result shows TORA is competent on real fracture**
   (0.861 avg / 0.928 best-of-n part-acc on 6 held-out real objects incl. a
   10-piece ceramic — `TORA_GOOD_VS_BAD_ANALYSIS.md` §Resolution; corrected
   2026-09-05, **0.819 / 0.915 of the loose fragments seated at a mean turn of
   38.7°**, which is "places most fragments, orientations still visibly wrong"
   rather than "competent"). So the prior
   is no longer "TORA fails on real ceramics"; it is "unknown whether TORA fails
   on the *Juglet specifically*, and we lack a valid instrument to check."

3. **There is a live internal contradiction to resolve.** The scale-invariant
   pairwise oracle (Probe 3, `rotation_error`, unaffected by the scale bug) found
   **1.03× — no true-mate/non-mate discrimination on real 2-piece pairs**, yet
   whole 5–10-piece real objects assemble well. Isolated-pair perception looks
   blind; joint multi-piece assembly looks fine. Both cannot be the whole story.

So the battery has three jobs, in order: **(A) get a valid instrument**, **(B)
decide whether a real Juglet failure even exists**, and only then **(C) localize
its mechanism.** GARF's probes are reused wherever the instrument transfers, but
two of GARF's decisive tools do **not** port cleanly and are replaced (below).

### What ports from GARF, what doesn't

| GARF instrument | Ports to TORA? | Note |
|---|---|---|
| PF++ pseudo-GT true-mate labels (`derive_pfpp_adjacency.py` → `adjacency.json`) | **Yes, as-is** | Already computed; object-level, model-agnostic. Reused verbatim. |
| Symmetry-invariant pairwise chamfer (`pair_reference_chamfer.py`) | **Yes, as-is** | Scores any model's posed pair vs a reference; TORA output feeds it directly. This is the metric that sidesteps the broken GT. |
| No-GT layout quality panel (`pfpp_layout_probes.py`) | **Yes, adapt I/O** | Reads posed part clouds; feed TORA's `proposed_assembly` clouds. Baselines already exist (PF++ 0.961, GARF 0.719, random 0.650). |
| Validated erosion / de-weather mollifier (`fracture_mesh_ops.py`) | **Yes, as-is** | Pure mesh op, no model. Reused for the wear-bridge. |
| **FracSeg fracture-response introspection (Exp 10)** | **NO** | Confirmed against the TORA paper (App. 0.A.1): overlap/mating prediction is a **linear probe of teacher-feature quality by design**, never an assembly module; the inference path uses only the frozen encoder's per-point conditioning features **c** (`_encode()` keeps `out_dict["point"]`). `overlap_head` also reads as dead (fires 75–98%, AUC ≈ chance). Replaced by **C2**, a paper-faithful readout of the on-path features. |
| Pair oracle scored by `rotation_error` (`analyze_pairwise_oracle.py`) | **Partly** | rot_err is scale-safe, but on the Juglet there is no valid GT rotation, so rot_err is invalid there. Use the symmetry-invariant chamfer instead on Juglet; keep rot_err only on valid-GT controls. **⚠️ 2026-09-05: "scale-safe" is not "bug-free".** Stored `rotation_error` skips the anchor when summing and divides by the total fragment count, so it carries a free zero — **×2.000 on any pair**. Every absolute degree figure in this document doubles; every mate/non-mate *ratio* is untouched, because the same factor sits on both sides |

### Architecture, confirmed against the paper (arXiv 2604.04050v1, 2026-07-24)

- The **encoder is Rectified Point Flow's (RPF, Sun et al. 2025), reused frozen
  and unmodified**: *"a frozen overlap-aware encoder extracts per-point
  conditioning features **c** ∈ ℝ^{N×D}"*, which condition the flow DiT. TORA
  does **not** alter perception.
- **TORA's contribution is a CKA alignment** of the flow backbone's intermediate
  features to a frozen **Uni3D-L** whole-object teacher — *training-only, zero
  inference overhead*.
- The paper's mating/overlap prediction is a **linear probe of teacher-feature
  quality** (App. 0.A.1: *"whether the teacher features encode contact-aware
  geometry … a point is labeled mating if it has ≥1 neighbor from a different
  part within an adaptive overlap threshold"*) — it is a diagnostic, not a
  pipeline stage. This is why `overlap_head` is the wrong readout (C2 fixes it).
- **Consequences that shape the mechanism tier:**
  1. TORA **cannot** have fixed GARF-style fracture perception — it froze RPF's
     encoder. Any TORA≠GARF behaviour on the Juglet must originate in the **flow
     backbone**, not the perception front-end.
  2. The only channel that can differ is the **Uni3D CKA signal**, and Uni3D-L is
     a *whole-object shape* model — exactly the macro-geometry channel GARF's
     Exp-15 says carries the surviving Juglet mating cue and that GARF's
     micro-texture encoder cannot read. The "TORA is more wear-robust" hypothesis
     thus has a concrete, testable locus (C2b).

---

## Hypotheses under test

- **H0 (null / benchmark-only):** TORA does *not* fail at Juglet assembly in any
  model sense; the apparent failure is entirely the invalid-GT benchmark. Given
  §Resolution this is now a serious candidate, not a strawman.
- **H1 (pairwise-perception failure, GARF-style):** TORA extracts no mating
  signal from the Juglet's worn rims — true mates score like non-mates at the
  2-piece level (would mirror GARF exactly).
- **H2 (joint-solve / context-dependent):** TORA's mating signal is *global, not
  pairwise* — it needs ≥k-piece context. This is what the 1.03×-pairwise-vs-0.86-
  whole-object contradiction hints at, and it would be a genuine TORA/GARF
  structural difference (GARF's signal is fundamentally pairwise).
- **H3 (wear-specific):** worn archaeological surfaces are the carrier (like
  GARF), separable from piece-count and from real-vs-synthetic.
- **H4 (piece-count cliff):** 9 pieces alone, past TORA's documented ~6-piece
  cliff, on an axisymmetric vessel.

The battery is designed so each test moves probability between these, and no
single test is trusted without its control.

---

## Tier A — build a valid instrument (prerequisite, cheap, no GPU)

### A1. Symmetry-invariant scorer, validated on TORA output
Port nothing new — run GARF's `pair_reference_chamfer.py` on a TORA-produced
pair. **Mandatory control first:** score TORA's predictions on the 4 fresh
control ceramics (valid real GT, TORA assembles these — blue_pot etc.). The
scorer must show true-mate chamfer clearly below non-mate (GARF's control:
0.024 vs 0.039). *If the metric cannot register a real mate on TORA's known-good
output, stop — the instrument is broken and no Juglet number counts.* This is
the exact check the metric-bug post-mortem says was skipped last time.

### A2. No-GT layout panel, baselines re-confirmed
Adapt `pfpp_layout_probes.py` I/O to read TORA's `proposed_assembly` clouds
(`sample.py … +visualizer.save_procrustes_assembly=true` already emits them).
Sanity gate: the random-pile null must reproduce ≈0.650 and PF++ ≈0.961 from
the existing GARF run — if not, the port is wrong.

**Cost:** CPU only, minutes. Operates on already-fetched output + existing
assets. **No Slurm.**

---

## Tier B — does a real Juglet failure exist? (decisive, short GPU)

### B1. TORA pairwise mating oracle on the Juglet (direct GARF Exp-6 port)
Build the C(9,2)=36 two-piece Juglet subproblems in TORA's HDF5 format
(`build_juglet_pairs_hdf5.py` exists in GARF for GARF's schema; the TORA
equivalent reuses the whole-object copy logic already in
`scripts/build_finetune_real_hdf5.py` + the normalization in
`normalize_real_hdf5.py` so thresholds match synthetic). True-mate labels =
GARF's existing `adjacency.json` (18/36 mates). Run TORA anchor-fixed,
`n_generations` ≥ 3, best-of-n; score with **A1's symmetry-invariant chamfer vs
the PF++ pseudo-GT reference** (not rot_err — no valid GT rotation on Juglet).

- **Pre-registered gate (mates vs non-mates):** separation ≥ 1.25× AND true-mate
  median chamfer/diag ≤ 0.045 (same gates GARF used, so results are directly
  comparable to GARF's 0.070/0.073 = no-separation Juglet result).
- **Mandatory control:** the *same* pipeline on fresh control ceramics must clear
  the gate (A1 already establishes this).
- **Reads on the hypotheses:**
  - Clears gate on Juglet → **H0/H2 up, H1 down**: TORA perceives Juglet mates
    where GARF cannot — a real, publishable TORA>GARF result on the worn object.
  - Fails gate like GARF → **H1/H3 up**: TORA shares GARF's worn-rim perceptual
    blindness; proceed to Tier C mechanism.

### B2. Whole-Juglet no-GT layout quality (H0 discriminator)
Run TORA's full 9-piece Juglet (already done, job 27859890 — reuse those
`proposed_assembly` clouds) through A2's panel. Compare TORA vs the existing
PF++ (0.961, vessel), GARF (0.719, pile), random (0.650) numbers.

- **Interpretation:** if TORA lands vessel-like (≈PF++) the "failure" was purely
  the benchmark (**H0 confirmed**); if pile-like (≈GARF/random) there is a real
  layout failure to explain even though the scalar metric is broken.
- This is the cleanest single test of H0 and it needs **no new GPU** — it only
  rescoring existing output.

**Cost:** B1 ≈ one short `gpu-a100-short` job (36 pairs × 3 gen + control, TORA
already ran a 79-pair version in ~6 min). B2 = CPU rescore.

---

## Tier C — localize the mechanism (only if B1 shows a real failure)

### C1. Piece-count sweep — pairwise vs joint (tests H2 directly, resolves the contradiction)
The 1.03×-vs-0.86 contradiction is the highest-value thing to resolve regardless
of B1's outcome. Take one **known-good real object** (galli_pot, 10 pieces,
valid GT, TORA assembles it) and evaluate progressively larger sub-assemblies:
2, 3, 4, 6, 8, 10 pieces (anchor-fixed, valid GT so rot_err *is* valid here).
Measure at what k correct non-anchor placement emerges.

- **H2 signature:** discrimination/placement is absent at k=2 but emerges by
  k=3–4 → TORA's mating signal is contextual, not pairwise. This would *explain*
  the whole-object competence + pairwise blindness and reframe the Juglet as a
  joint-solve/context problem, not a perception one.
- **H1 signature:** placement never emerges at any k on real fracture → genuine
  pairwise perceptual deficit (then the whole-object 0.861 needs its own audit —
  possibly anchor-clamp leakage inflating part_acc; flag for a separate check).
- **Control:** identical sweep on a synthetic object (should place from k=2).
- **Cost:** one short GPU job.

### C2. On-path feature introspection (replaces GARF Exp 10, tests H1/H3) — paper-faithful
GARF read P(fracture) off FracSeg, which *is* its mechanism. TORA's `overlap_head`
is not on the inference path (confirmed: it is the paper's teacher-quality linear
probe, App. 0.A.1). So mirror the paper's own methodology — a **mating linear
probe** — but point it at the features TORA actually uses:
  (i) the **frozen encoder's per-point conditioning features c** (`_encode()`'s
      `out_dict["point"]`), and
  (ii) the **CKA-aligned intermediate flow-backbone features** (TORA's actual
      contribution).
For each, test whether mating-band points are separable / more complementary for
true mates than non-mates (the paper's own quality readout, plus a cosine-
complementarity variant). Arms: synthetic fresh breaks (labeled, must pass — the
instrument validation), fresh real ceramics (both models assemble), Juglet worn
rims.

- **Validation gate:** the readout must separate mates on the synthetic labeled
  arm (AUC ≥ 0.75) or it is discarded, exactly as `overlap_head` was.
- **H3 signature:** feature complementarity present on fresh real ceramics but
  collapses on Juglet worn rims → wear-specific, mirroring GARF Exp 10's
  0.57%-vs-3.4% blindness but measured on TORA's live features.
- **Optional C2b — CKA-teacher ablation:** does the whole-object teacher channel
  (uni3d CKA alignment, TORA's actual contribution and the macro-shape signal
  GARF *lacks*) carry Juglet mate signal the point features don't? This is the
  most TORA-specific probe and directly tests whether TORA's extra channel buys
  worn-object robustness GARF can't have.
- **Cost:** GPU forward passes only, no training. Short.

### C3. Wear bridge, both directions (tests H3 causally; reuses GARF's validated mollifier)
Reuse `fracture_mesh_ops.py` unmodified (pure geometry, already causally
validated in GARF Exp 10b/14). (a) **Erode** fresh control ceramics toward
Juglet roughness → does TORA's B1 pairwise separation collapse toward Juglet's?
(b) **De-weather** Juglet rims (unsharp) → does separation return? Sweep
strength; the mollifier's known plateau (GARF Exp 7b) is expected — pre-register
that a *monotone* trend, not full calibration, is the pass condition.

- **Control:** off-band sharpening must NOT move the metric (specificity), as in
  GARF Exp 14 Arm C.
- **Cost:** one medium GPU job (pairwise × strengths).

---

## Execution order & sign-off

Recommended sequence (each stage gates the next; `/goal` gives standing GPU
sign-off for this task):

1. **A1 + A2** (CPU, no Slurm) — build & validate the instrument. **Do first.**
2. **B2** (CPU rescore of existing job 27859890) — cheapest test of H0.
3. **B1** (short GPU) — the decisive "is the failure real / does TORA beat GARF
   on the worn object" test.
4. Branch on B1:
   - failure real → **C2**, then **C1**, then **C3**.
   - failure not real (H0) → stop; write up "Juglet is benchmark-only for TORA
     too, but for a *different* reason than the metric bug — TORA's layout is
     actually vessel-like" (B2), and close.
5. **C1** is worth running regardless — it resolves the pairwise/whole-object
   contradiction that currently undermines confidence in *all* TORA real-fracture
   claims.

### Pre-registered global rules (from the metric-bug post-mortem)
- No test concludes until its **known-answer control** passes.
- A **suspiciously constant** or internally inconsistent metric is a bug until
  proven otherwise.
- **Cross-check scale-dependent against scale-invariant** metrics on every arm.
- On the Juglet, **never** trust anything scored against `pointclouds_gt`.

---

## Results log

### 2026-07-24 — normalized pairwise oracle (job 27976473, baseline ckpt)
Re-ran the pairwise mating oracle on **scale-normalized** real pairs so
`part_accuracy` is valid (the pre-norm 0.5-pin was the metric bug). Synthetic
control clears the instrument gate (13.35×, true-mate part_acc 1.000).

| arm | true-mate part_acc | non-mate part_acc | true-mate rot_err | non-mate rot_err |
|---|---|---|---|---|
| synthetic (control) | 1.000 | 0.850 | 0.99° | 13.16° |
| real, normalized | **0.943** | **0.769** | 15.17° | 24.13° |
| — *corrected 2026-09-05, ×2.000 (pairs)* — | | | | |
| synthetic (control), corrected | 1 of 1 seated | 0.700 seated | **1.98°** | 26.32° |
| real, normalized, corrected | **0.886 seated** | **0.538 seated** | **30.34°** | 48.26° |

**Corrected 2026-09-05.** Every sample is a pair, so the free-anchor discount is
×2.000 on both rot_err columns and the **1.59× separation is unchanged**. `part_acc`
restated as the fraction of the *loose* piece seated — 0.943 → **0.886**, 0.769 →
**0.538** — which is the same discrimination, on a scale that starts at zero
instead of at 0.5. The physical reading changes a good deal: TORA puts a real
**true mate about 30° out, not 15°**, and a non-mate about 48°. The claim that it
discriminates stands; the claim that it places true mates accurately does not.

- **Trustworthy:** `part_acc` now **discriminates** real true-mates (0.943) from
  non-mates (0.769). The pre-fix "no discrimination" (both pinned 0.5) was a
  metric artifact. **TORA is not pairwise-blind on real fracture** — unlike GARF.
  → moves probability to **H0/H2**, against **H1**.
- **⚠️ rot_err anomaly — RECONCILED (control job 27979066, un-normalized pairs_real):**
  un-normalized reproduces true-mate 26.6° / non-mate 28.7° → **1.08×** (≈ the
  historical 1.03×) with part_acc pinned 0.500/0.500. So normalization moved
  rot_err 27°→15° / 1.08×→1.59× even though rot_err should be scale-invariant.
  *(Corrected 2026-09-05: 53.2° / 57.4° un-normalized, 30.3° / 48.3° normalized —
  ×2.000 throughout, so both ratios and this whole anomaly are unchanged. The
  anomaly is not the anchor bug: `scales` is a conditioning **input** to the model,
  so re-scaling changes the prediction itself. See `FRACTURA_WHY_IT_FAILS.md` §2,
  which resolved exactly this — it is the model being told a size it was never
  trained at, not the metric misbehaving.)*
  **Conclusion:** `part_acc` is the robust signal (0.5-pin → 0.943/0.769 is the
  expected metric-bug fix); `rot_err` here is **scale/stochastic-sensitive and
  the less reliable metric** — do not lead with the rot_err delta or compare
  rot_err across differently-scaled datasets. (Nail with a seed-repeat only if
  the rot_err number is ever load-bearing.)

### 2026-07-24 — B1: Juglet pairwise mating oracle (job 27982824)
36 Juglet pairs (18 true mates) scored against **PF++ form-level pseudo-GT**.
`part_accuracy` is **binary** on a 2-piece problem (0.5 = anchor only, 1.0 =
non-anchor correctly placed), so it is a per-generation *placement success rate*.

**⚠️ The shipped analyzer's best-of-N saturates and HIDES the signal** (mate
0.944 vs non-mate 0.861 → "no discrimination"). The honest mean-over-generations
statistic is the one to read:

| ckpt | mate success | non-mate success | ratio | per-pair MWU (1-sided) | per-gen Fisher |
|---|---|---|---|---|---|
| **baseline** | **63.3%** (57/90) | **38.9%** (35/90) | **1.63×** | **p = 0.025** | OR 2.71, p = 0.0008 |
| robust | 51.1% (46/90) | 36.7% (33/90) | 1.39× | p = 0.146 (n.s.) | OR 1.81, p = 0.036 |

- **Baseline separates true mates from non-mates on the Juglet** (1.63×, crosses
  the pre-registered 1.25× gate, p = 0.025 per-pair). GARF, by contrast, found
  **no** separation on this same object (0.070 vs 0.073 = 1.04×) across its
  entire 15-experiment arc. This is the first quantitative sign of a real
  TORA-vs-GARF difference on the worn Juglet.
- **Robust fine-tune is again worse than baseline** (1.39×, per-pair n.s.),
  consistent with §Resolution's "fine-tuning degraded a competent checkpoint".

**⚠️ Proximity confound — do NOT upgrade this to "TORA perceives Juglet mates":**
true mates are adjacent in the pseudo-GT layout (mean centroid gap 0.429) while
non-mates are far apart (0.639), and success correlates negatively with gap
across all 36 pairs (Spearman ρ = −0.334, p = 0.046). So part of the 1.63× may
be "closer pieces are easier targets," not mating perception. Within-group
correlations are n.s. (mates ρ = −0.11 p = 0.67; non-mates ρ = −0.16 p = 0.52),
and the distance-matched window retains the effect direction (1.50×) but is far
too small to confirm (n = 4 vs 3, p = 0.36).

**Supported claim:** TORA shows a statistically significant mate/non-mate
separation on the Juglet where GARF shows none — *partly confounded by
proximity, magnitude not yet established.* **Not** supported: that TORA achieves
true contact-level mating (the pseudo-GT cannot test that — pieces don't touch).

**Refinement for a decisive rerun:** score with a distance-normalized metric
(GARF-style chamfer / pair-diagonal) and/or build a distance-matched pair set, so
proximity is controlled by construction rather than post-hoc.

### 2026-07-27 — C1: piece-count sweep, galli_pot, REAL valid GT (job 28198773)
Sub-assemblies of one 10-piece real ceramic at k = 2…10 (5 replicates each,
k=10 has 1). Rate = anchor-corrected non-anchor placement rate.

| k | subsets | placement rate (mean / best-of-n) | rot_err | rot_err **corrected 2026-09-05** |
|---|---|---|---|---|
| 2 | 5 | **0.800** / 1.000 | 15.3° | **30.6°** (×2.000) |
| 3 | 5 | 0.633 / 0.700 | 23.4° | **35.1°** (×1.500) |
| 4 | 5 | 0.356 / 0.467 | 33.0° | **44.0°** (×1.333) |
| 6 | 5 | 0.573 / 0.680 | 41.0° | **49.2°** (×1.200) |
| 8 | 5 | 0.590 / 0.714 | 44.1° | **50.4°** (×1.143) |
| 10 | 1 | 0.778 / 0.889 | 32.2° | **35.8°** (×1.111) |

The placement-rate column was already anchor-corrected, so **the load-bearing
result — 0.800 at k=2 versus 0.778 at k=10, H2 not supported — is untouched.**
The rot_err column was not, and its discount is a function of k, the axis being
plotted.

**H2 is NOT supported** (k=2 → k=10: 0.800 → 0.778; Spearman ρ = −0.124, p = 0.55).
More context does **not** unlock placement — and crucially **k=2 is the *best*
arm (0.800)**. TORA seats 80% of isolated real 2-piece fractures correctly.

**This dissolves the contradiction that motivated C1.** There was never a
"pairwise-blind but competent-jointly" paradox: the old 1.03×/0.5-pinned pairwise
number was the metric artifact, not a perceptual finding. Corrected, TORA is
competent *both* pairwise and multi-piece. **H1 (pairwise perception failure) is
refuted on real fracture.** (rot_err does climb with k, 15°→44° — the documented
piece-count cliff is real, but it degrades *pose precision*, not seating.)
Caveat: 5 subsets/k is noisy (the k=4 dip to 0.356 is small-sample), and k=10 is
a single subset; the *level* at k=2 is the load-bearing result, not the curve shape.

> **⚠️ Corrected 2026-09-05 — the parenthesis above overstates the pose cliff.**
> "rot_err does climb with k, 15°→44°" was read off diluted figures whose discount
> shrinks as k grows: ×2.000 at k=2 down to ×1.111 at k=10. On the same ruler the
> climb is **31° → 50°**, and it is not monotone (k=10 comes back to 36°). So pose
> precision does still degrade with piece count, but from a much worse starting
> point: **even the two-piece case is about 31° out — a third of a right angle on a
> single loose sherd.** The sentence "TORA seats 80% of isolated real 2-piece
> fractures correctly" remains true about *seating*, and should not be read as
> "places them accurately". Seating and orientation are different claims here, and
> this is the table that shows the gap between them.

### 2026-07-27 — C2: mating linear probe on ON-PATH features (job 28198811)
Paper-faithful probe (App. 0.A.1 methodology) on the frozen encoder's per-point
conditioning features **c** — what the flow DiT actually consumes.

| arm | objects | GT mating-label rate | linear-probe AUC |
|---|---|---|---|
| synthetic fresh breaks (**validation**) | 34 | 2.13% | **0.9625 — PASS** |
| fresh real fracture (`real_heldout_norm`) | 6 | 7.29% | **0.9208** |
| **Juglet, worn** (`juglet_norm`) | 1 | 3.30% | **0.7396** |

- **Instrument validated.** Synthetic AUC 0.96 clears the 0.75 gate, and label
  rates are sane (2–7%) — *not* the ~100% degenerate case that made the old
  `overlap_head` probe meaningless. The scale-normalized splits fixed it.
- **No real-vs-synthetic perceptual gap**: fresh real 0.92 ≈ synthetic 0.96.
  Independently corroborates §Resolution — the founding premise really is void.
- **Wear does degrade contact encoding**: Juglet 0.74 vs fresh real 0.92 — the
  **H3 signature**. But it degrades *partially*; 0.74 is still well above chance
  (0.5), i.e. the worn rims retain usable contact signal in TORA's features.
- **Contrast with GARF**: GARF's encoder fires on 0.57% of Juglet points vs 3.4%
  on fresh ceramics (0.17× — effectively blind). TORA's on-path features stay
  informative on the same worn rims. Same object, same wear, different outcome.
- ⚠️ **Caveat:** the Juglet arm is **one object / 5 000 points** — the 0.74 has
  wide uncertainty. Directionally consistent with B1, but it needs more worn
  objects (or bootstrap CIs) before the magnitude is load-bearing.

### 2026-07-27 — C2b: which channel survives wear? (job 28200043)
Same probe, same labels, both feature sources, both cut to 64-d by PCA so probe
capacity is equal; each arm also fits on scrambled labels as an overfitting
control (must sit near 0.5).

| material | **encoder** (frozen RPF, break-surface) | **teacher** (Uni3D, whole-object form) |
|---|---|---|
| synthetic fresh breaks | 0.9644 *(ctrl 0.49 ✓)* | **0.9928** *(ctrl 0.51 ✓)* |
| fresh real fracture | 0.9173 *(ctrl 0.50 ✓)* | **0.9385** *(ctrl 0.52 ✓)* |
| **Juglet, worn** | **0.7165** *(ctrl 0.39 ⚠)* | **0.8583** *(ctrl 0.53 ✓)* |
| **drop, fresh real → worn** | **−0.200** | **−0.081** |

**The macro-shape channel degrades less than half as much under wear**
(−0.081 vs −0.200), and on the worn Juglet it retains clearly more
mating-relevant information (0.858 vs 0.717). This is the predicted signature:
TORA reuses RPF's fracture encoder **frozen**, so its wear-robustness cannot
come from better break-surface perception — and the one channel it adds, the
Uni3D whole-object form teacher, is exactly the macro-geometry cue GARF's
Exp-15 concluded survives abrasion and that GARF cannot read.

**⚠️→✅ The one failed control is RESOLVED (job 28200111).** The encoder/Juglet
run had returned a scrambled-label AUC of 0.39 rather than ~0.5 (~1.5 SE out on
~50 held-out positives). Re-running both channels across 3 further point
samplings: **all 6 controls now pass** (0.458–0.545), confirming the 0.39 was
small-sample noise, not overfitting. The channel gap is stable and the two
distributions never overlap:

| sampling | encoder | teacher | gap |
|---|---|---|---|
| seed 42 (orig) | 0.7165 | 0.8583 | 0.142 |
| seed 0 | 0.7102 | 0.8753 | 0.165 |
| seed 1 | 0.7121 | 0.8960 | 0.184 |
| seed 2 | 0.7045 | 0.8817 | 0.177 |
| **mean** | **0.711** | **0.878** | **0.167** |

Using the 4-sampling means, the drop from fresh real fracture to the worn Juglet
is **−0.206 for the break-surface channel vs −0.061 for the whole-object form
channel** — the form channel loses roughly **a third** as much. The C2b
conclusion stands on repeated measurement, not a single run.

---

## Synthesis (2026-07-27) — what the battery establishes

| hypothesis | verdict | evidence |
|---|---|---|
| **H1** pairwise-perception failure (GARF's mechanism) | **REFUTED** | C1: 0.800 placement at k=2; C2: fresh-real AUC 0.92 |
| **H2** joint-solve / context-dependent | **NOT SUPPORTED** | C1: flat in k (ρ = −0.124, p = 0.55) |
| **H3** wear-specific degradation | **SUPPORTED, partial** | C2: 0.92 fresh → 0.74 worn (n=1, wide CI) |
| **H4** piece-count cliff | **real but secondary** | C1: rot_err 15°→44° with k, seating rate flat |
| **H0** benchmark-only | **PARTLY WITHDRAWN 2026-07-28** — see below | the scores are meaningless, but the *reconstruction* genuinely fails |

### ⚠️ Correction (2026-07-28) — H0 was overstated

Earlier wording said the model "was never asked to reassemble the Juglet, it was
asked to reproduce a table layout." **That is wrong.** In anchor-free mode (used
for the Juglet) `_transform` centres every part *including* the anchor and
randomly rotates all non-anchor parts, so the model's input is nine loose sherds.
The reference is consumed **only by the evaluator, after inference, to score** —
it is a yardstick, never an instruction, and the model cannot copy it.

Consequences:
- The proposed assembly **is TORA's own unaided reconstruction**, so judging it
  visually is legitimate — and it is the *only* honest instrument when no true
  answer exists, which is the normal archaeological case.
- Judged that way (`artifacts/juglet_viz/`): anchor sherd with the other eight
  clustered against one side, **no vessel** ⇒ **a genuine failure to reassemble
  this pot**, not merely a scoring artifact.
- **Two independent faults, both real:** (1) the method fails on this vessel;
  (2) the reference is an invalid scan layout so every score from it is
  meaningless. (2) *concealed* (1) — it does not excuse it.
- Still true: no *numerical* claim about Juglet reassembly is possible without a
  correct assembled reference. The *qualitative* verdict does not need one.

This is compatible with B1/C2b rather than contradicting them: TORA has better
fragment-level signal than GARF (mate separation 1.63×; form channel surviving
wear) **and still cannot converge on a correct 9-piece worn vessel**. Good local
signal is not a global solution — consistent with C1, where rotation error grew
15° → 44° as piece count rose even while seating stayed flat.

**The picture that survives all five tests:** TORA is *not* broken on real
fracture — pairwise or jointly — and on the worn Juglet it retains both mate
discrimination (B1, 1.63×) and contact-encoding in its features (C2, 0.74).
Wear costs it something (0.92 → 0.74) but nothing like GARF's collapse (0.17×
fire rate, 1.04× separation across 15 experiments). This is architecturally
coherent: TORA froze RPF's encoder, so its wear-robustness cannot come from
better fracture perception.

**C2b locates the surviving channel, and it replicates.** Across 4 point
samplings the whole-object form channel loses ~a third as much to wear as the
break-surface channel (−0.061 vs −0.206) and stays clearly more informative on
the worn Juglet (0.878 vs 0.711, gap stable at 0.14–0.18, distributions never
overlapping, all 8 scrambled-label controls passing). That is the Uni3D teacher
TORA aligns to — the form-level cue GARF's own Exp-15 said survives abrasion,
and which GARF's micro-texture encoder cannot read. The hypothesis now has
direct, repeated supporting evidence rather than architectural plausibility.

**The remaining limit is what the probe can address at all:** it shows what
information the form channel *contains*, not that the flow model *uses* it at
inference. The decisive version compares a CKA-aligned checkpoint against a
non-aligned RPF baseline on the same Juglet pairs — that needs an RPF checkpoint
not currently on Spartan (only `bbad_everyday_cka.ckpt` + the Uni3D teacher are
present). Also note the Juglet remains a single object; the *direction* is now
well established, the exact magnitudes are still one-pot numbers.

---

## 2026-07-28 — SECOND measurement bug found: broken part-matching corrupts rotation error

Chasing "why did the Juglet fail, and did TORA do well on Fractura?" surfaced a
discrepancy that could not be explained: **blue_pot scores rot_err 71.6° in the
raw-scale run but 4.5° in the normalized run — the same pot, same checkpoint,
same `anchor_free: false`.** Rotation error is supposedly scale-invariant, and
its ICP does run in normalized space, so scale alone cannot do this.

**Mechanism (found in `tora/eval/metrics.py`).** `compute_part_acc` builds its
assignment cost as a *boolean*:

```python
cost_mat = (cd_mat >= threshold).float()      # all-ones when nothing passes
row_ind, col_ind = linear_sum_assignment(cost_mat)
```

On raw-scale real data the absolute `CD < 0.01` threshold is unreachable, so
**every** entry is 1, the matrix is uniform, and `linear_sum_assignment` returns
an **arbitrary** permutation. That permutation is returned as `matched_part_ids`
and handed to `compute_transform_errors`, which reorders the predictions by it:

```python
rotations_pred = rotations_pred[batch_idx, matched_part_ids]
```

⇒ **rotation error then compares the wrong fragment to the wrong fragment.** The
55–72° "rotation errors" on raw-scale real objects are not rotations at all;
they are the signature of scrambled correspondences.

**Evidence (identical objects, both `anchor_free: false`):**

| object | raw-scale part_acc | = 1/n? | raw rot_err | normalized part_acc | normalized rot_err |
|---|---|---|---|---|---|
| blue_pot (5) | 0.2000 | **exactly** | 71.6° | 1.00 | **4.5°** |
| galli_pot (10) | 0.1000 | **exactly** | 72.4° | 0.90 | 27.2° |
| plate (6) | 0.1667 | **exactly** | 72.4° | 0.67 | 29.9° |
| narrow_bottle1 (12) | 0.0833 | **exactly** | 64.8° | — | — |
| pink_bowl (3) | 0.3333 | **exactly** | 60.2° | — | — |

Every raw-scale object sits at *exactly* 1/n — the tell this document already
names as an instrument failure.

**This retroactively explains the rot_err anomaly flagged on 2026-07-24**
(`pairs_real` 26.6° vs `pairs_real_norm` 15.2°), which was recorded as
"scale/stochastic-sensitive, unexplained". It is neither: the un-normalized arm
had scrambled part correspondences. The note is now resolved.

**Consequence:** the metric bug is *worse* than previously documented. It did not
only pin `part_accuracy`; it silently corrupted `rotation_error` too, via the
matching handoff. Both of the metrics that drove the original "TORA is bad at
real fracture" narrative were broken **by the same root cause**, and
`rotation_error` was wrongly treated as the trustworthy scale-invariant fallback
throughout the earlier investigation.

**Rule going forward:** `rotation_error` is only meaningful when `part_accuracy`
on the same run is *not* pinned at 1/n. Check the matching before quoting a
rotation.

---

## 2026-07-28 — ROOT CAUSE: why TORA fails on the Juglet

### The 2×2 that closed it (job 28228263)

The Juglet was the only evaluation running `data.anchor_free=true`, paired with
`model.anchor_free=false` — a combination matching neither training nor any
other test. Prime suspect. It is now **exonerated**:

| arm | result |
|---|---|
| real held-out, `anchor_free=false` (known-good) | part_acc **0.867**, rot 30.6° |
| real held-out, **under the Juglet's setting** (`true`) | part_acc **0.817**, rot 33.6° — *essentially unchanged* |
| Juglet, `anchor_free=true` (known failure) | no vessel |
| **Juglet, under the WORKING setting** (`false`) | **still no vessel** |

Good objects do not break under the Juglet's setting, and the Juglet does not
recover under the working setting (`artifacts/juglet_viz/anchor2x2/`, all
generations show the same anchor-sherd-plus-fan geometry). **The task setup is
not the cause.**

### What is ruled out

| candidate | verdict | evidence |
|---|---|---|
| real (vs simulated) fracture | **ruled out** | real Fractura pots reassemble well once measured correctly — blue_pot 5 pieces @ 4.3°, part_acc 1.00 |
| thin walls | **ruled out** | `narrow_bottle1/2/3/4` are thin-walled and sit in the same competent set |
| piece count | **ruled out** | `galli_pot` has **10** pieces — more than the Juglet's 9 — at 0.867–0.900 seated |
| anchor / task setup | **ruled out** | the 2×2 above |
| broken measurement | **real, but a separate fault** | two independent metric bugs; they hid the failure, they are not it |

### The cause: wear removes the fine break-surface detail needed to *seat* a fragment

What survives on the Juglet and what does not, measured (C2, C2b):

- **Break-surface reading** — the fine texture that says *these two faces mate
  exactly here* — degrades from **0.92 on fresh real breaks to 0.71 on the
  Juglet's abraded rims**.
- **Whole-object form reading** holds up at **0.88** (loses ~⅓ as much).
- Consistently, TORA still tells Juglet true neighbours from unrelated pairs
  (B1, 1.63×, p = 0.025) — coarse grouping survives.

So the deficit is specific: TORA retains enough signal to work out **which
sherds belong near each other**, but not enough to work out **exactly how they
seat against each other**. Abrasion destroyed the fine interlocking detail;
what is left positions fragments in roughly the right neighbourhood without ever
locking them into a closed vessel profile — precisely what every visualization
shows (sherds fanned around the anchor, never closing).

At 9 worn fragments those seating errors compound, which matches C1: seating
rate stays flat with piece count while **rotation error grows 15° → 44°**. The
failure mode is *loss of precision*, not loss of grouping.

### How this differs from GARF's failure

Same root cause — wear — but **different severity**, and that difference is the
substantive TORA-vs-GARF result:

| | GARF | TORA |
|---|---|---|
| break-surface perception on worn rims | **collapses** (fires 0.57% vs 3.4% fresh = 0.17×) | **degrades** (0.92 → 0.71) |
| tells true mates from non-mates on the Juglet | **no** (1.04×, across 15 experiments) | **yes** (1.63×, p = 0.025) |
| fallback channel | none — micro-texture only | **whole-object form, 0.88** |
| rebuilds the Juglet | no | **no** |

GARF goes blind; TORA goes imprecise. Both fail to rebuild this pot, but TORA
fails from a materially better starting position — it still knows which sherds
are neighbours, which is the part GARF has lost entirely.

### C3 — the causal test: RUN, and wear is confirmed as the cause (job 28228655)

Intervention, not comparison: six real pots TORA already reassembles were
progressively abraded **on their break surfaces only**, with pieces, poses and
ground truth held fixed (GARF's validated mollifier, vertex-only, fixed physical
radius). The only variable is wear.

| wear | seating rate | achieved relief_p90 |
|---|---|---|
| 0.00 (fresh) | **0.875** | 0.2844 |
| 0.25 | 0.785 | 0.2680 |
| 0.50 | 0.758 | 0.2320 |
| 0.75 | 0.627 | 0.2012 |
| 1.00 | **0.524** | **0.1829** |

**Monotonic dose-response across every step** — seating falls 0.875 → 0.524, a
40% relative loss, as the surfaces are worn and nothing else changes.
Spearman ρ = −0.442, p = 0.0144 (n = 30 object×level).

**Calibration succeeded where GARF's Exp 7 failed.** Achieved relief reaches
**0.183** against the Juglet's real **0.171** — i.e. our most extreme condition
is *still slightly less worn than the actual Juglet*, and seating had already
lost 40%. GARF's bridge plateaued above the target and could not be interpreted;
this one lands on it, so the result is not an undershoot artifact.

**Per-object, and the honest statistics:**

| object | fresh → full wear | |
|---|---|---|
| vert9 | 0.833 → **0.000** | total collapse |
| coxae | 1.000 → 0.333 | collapse |
| blue_pot | 1.000 → 0.583 | collapse |
| galli_pot | 0.815 → 0.630 | degraded |
| plate | 0.600 → 0.600 | unchanged |
| limb3 | 1.000 → **1.000** | **immune** |

**4/6 decreased, 2/6 unchanged, 0/6 improved.** Paired tests give p = 0.0625
(Wilcoxon and sign test) — *just above* the conventional 0.05 threshold with only
six objects. So: the direction is unambiguous (nothing improved, ever), the
effect is large where it occurs, and there is a clean dose-response — but the
formal significance is **marginal, limited by six objects**. Stated plainly:
strong causal evidence, not yet a fully powered result.

**`limb3` being immune is informative, not noise.** It is a long bone with a
highly distinctive overall shape — exactly the case where the whole-object form
channel (C2b, 0.88 under wear) can carry the assembly without fine break detail.
Wear costs you the seating cue; distinctive form can substitute for it. That is
the same split C2b measured, now visible at the object level.

### What would still change the answer

- **Six objects.** p = 0.06 needs more pots to become a firm result.
- **No off-band control yet.** Abrading a *non*-fracture region by the same
  amount should leave seating untouched; that would prove the effect is carried
  by the break faces specifically rather than by generic mesh smoothing.
- Still only **one genuinely worn archaeological object** (the Juglet itself).

---

## 2026-07-28 — SOLUTIONS: what recovers seating under wear?

Test bed for every candidate: the C3 erosion sweep — real pots with **valid
ground truth**, progressively abraded, seating known to fall 0.875 → 0.524. The
Juglet cannot serve here (no correct answer to score against).

### S1 — free inference knobs: **NO EFFECT** (job 28229895)

| arm | seating @ full wear |
|---|---|
| baseline (euler, 50 steps, 3 gens) | 0.435 |
| 200 steps (4× compute) | 0.504 |
| rk4 sampler | 0.463 |
| 10 generations | 0.485 |

All within run-to-run noise. The model does not need more compute; it needs
better information. Matches GARF's Exp 5. **Cheap to rule out, and now ruled out.**

### S2 — post-hoc geometric settling: **REFUTED, and instructively so**
(jobs 28229957, 28230423)

The idea (user's): don't demand a perfect join — let neighbouring fragments
settle until they touch. Sound *if* the failure were "nearly right, not quite
closed".

**It is not.** Measured per-fragment displacement from the correct position
(object half-extent = 1.0; seating tolerance ≈ 0.14):

| wear | median error | 90th pct | within 0.06 |
|---|---|---|---|
| 0.00 | 0.139 | 0.814 | 42% |
| 1.00 | **0.346** | **1.226** | 12% |

At full wear the typical fragment sits **2.5× beyond the seating tolerance**, and
the worst are **further from home than the pot is wide**. This is *gross
misplacement*, not a join that failed to close — and it corrects an earlier
claim in this document that fragments land "roughly in the right neighbourhood".

Retuning the settling reach to the measured scale makes it **catastrophically
worse**, which is the decisive evidence:

| reach | Δ seating | worsened |
|---|---|---|
| 0.06 | +0.002 | 1/30 |
| 0.15 | −0.009 | 8/30 |
| 0.30 | **−0.389** | 22/30 |
| 0.50 | **−0.407** | 22/30 |

**Why more freedom hurts:** "pull toward the nearest surface" is only correct
when the nearest surface is the *true* mate. Once fragments are misplaced, the
nearest surface is usually the *wrong* partner, so every extra degree of freedom
attaches them more confidently to the wrong neighbour. Local geometry cannot
recover a correspondence it does not have.

**Conclusion: no post-hoc tidying can fix this.** The deficit is *which fragment
goes where*, not *how precisely it is seated*. That must be fixed in the
prediction, not after it.

### S3 — wear-augmented fine-tuning: **the remaining candidate** (job 28230079)

Newly feasible: until now the only genuinely worn object (the Juglet) had no
ground truth, so there was nothing to learn from. The validated mollifier
manufactures worn training data **that keeps its answer key**.

Deliberately conservative (synthetic replay, low LR, few epochs) because *both*
previous fine-tunes here ended up worse than the checkpoint they started from,
and evaluated on **worn and fresh** material so a gain bought by wrecking fresh
objects is reported as the trade it is.

> **Mechanism and the full solution roadmap now live in
> `TORA_WEAR_SOLUTIONS.md`** — how placement is actually decided inside the model
> (global all-against-all attention at every layer and step), why that works on
> fresh breaks and collapses on worn ones, and six candidate fixes ranked by
> value ÷ effort with the measured evidence for each.

### Forward direction if S3 also fails

The measurements point somewhere specific. TORA *does* retain partial
correspondence signal on worn material (B1: true mates separated from non-mates
at 1.63×, p = 0.025) and a strong whole-object form channel (C2b: 0.88). What it
lacks is a stage that *uses* that pairwise signal to constrain the global
assembly — it currently solves all fragments jointly in one flow, with no
explicit "which fragment mates with which" step. A matching/graph stage seeded
from the surviving pairwise signal is the architecturally-indicated next lever,
and matches GARF's own closing recommendation (form-based pairing and pose init,
with fracture-feature refinement only where signal survives).

---

## Assets (all present, verified 2026-07-24)

- Juglet normalized data: `TORA/dataset/juglet_norm.hdf5` (Spartan).
- Valid-GT controls: `TORA/dataset/pairs_real_norm.hdf5`, `real_heldout_norm.hdf5`,
  `fractura_real.hdf5` (bones/ceramics/egg).
- PF++ pseudo-GT for the Juglet: `GARF/logs/diagnostics/juglet_adjacency/adjacency.json`
  (+ `derive_pfpp_adjacency.py`) on Spartan.
- GARF scorers (Spartan `GARF/scripts/`, reuse unmodified): `pair_reference_chamfer.py`,
  `pfpp_layout_probes.py`, `fracture_mesh_ops.py`.
- TORA scaffolding (`tora/scripts/`): `analyze_pairwise_oracle.py`,
  `build_finetune_real_hdf5.py`, `normalize_real_hdf5.py`;
  slurm `scripts/hpc/eval_pairwise_oracle.slurm`, `eval_juglet_normalized.slurm`.
- Existing Juglet output to rescore (B2): `TORA/eval_runs/juglet_norm_{baseline,robust}_27859890/`.
- Encoder readout point (C2): `tora/modeling/tora.py` `_encode()` → `out_dict["point"]`;
  do **not** reuse `overlap_head_probe.py`'s head (dead instrument).

## Related
- `TORA_GOOD_VS_BAD_ANALYSIS.md` (corrected results + metric-bug post-mortem),
  `JUGLET_TORA_ROOTCAUSE.md` (invalid-GT finding, architecture notes).
- `GARF/docs/notes/JUGLET_ROOTCAUSE_FINDINGS.md` (Exp 6/10/11–15 — the probes
  this plan mirrors and the conclusions to compare against).
</content>
</invoke>
