# Test plan — does TORA actually fail on the Juglet, and if so why?

Status: **DESIGN** (2026-07-24). No jobs submitted yet. Pre-registered gates and
mandatory controls below; nothing here is allowed to conclude until its
known-answer control passes (see the metric-bug post-mortem in
`TORA_GOOD_VS_BAD_ANALYSIS.md` § "Correction (2026-07-22)").

---

## The problem this plan has to solve first

After the 2026-07-22 metric correction we are in an awkward epistemic spot:

1. **We cannot currently measure TORA's Juglet reassembly at all.** Every scalar
   the pipeline computes for the Juglet is scored against `data["pointclouds_gt"]`
   (`tora/eval/evaluator.py:27,35,42-43`), and for the Juglet split that tensor
   **is the scattered scan/table layout, not an assembled vessel**
   (`JUGLET_TORA_ROOTCAUSE.md`, and independently `GARF/.../JUGLET_DEPLOY_INFERENCE_ANALYSIS.md`).
   So `part_acc = 1.0`, `object_chamfer ≈ 0`, *and* `rotation_error = 46–61°`
   are all measuring against the wrong target. A "failure" number here is
   uninterpretable; so is a "success" number.

2. **The corrected whole-object result shows TORA is competent on real fracture**
   (0.861 avg / 0.928 best-of-n part-acc on 6 held-out real objects incl. a
   10-piece ceramic — `TORA_GOOD_VS_BAD_ANALYSIS.md` §Resolution). So the prior
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
| Pair oracle scored by `rotation_error` (`analyze_pairwise_oracle.py`) | **Partly** | rot_err is scale-safe, but on the Juglet there is no valid GT rotation, so rot_err is invalid there. Use the symmetry-invariant chamfer instead on Juglet; keep rot_err only on valid-GT controls. |

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

- **Trustworthy:** `part_acc` now **discriminates** real true-mates (0.943) from
  non-mates (0.769). The pre-fix "no discrimination" (both pinned 0.5) was a
  metric artifact. **TORA is not pairwise-blind on real fracture** — unlike GARF.
  → moves probability to **H0/H2**, against **H1**.
- **⚠️ rot_err anomaly — RECONCILED (control job 27979066, un-normalized pairs_real):**
  un-normalized reproduces true-mate 26.6° / non-mate 28.7° → **1.08×** (≈ the
  historical 1.03×) with part_acc pinned 0.500/0.500. So normalization moved
  rot_err 27°→15° / 1.08×→1.59× even though rot_err should be scale-invariant.
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

| k | subsets | placement rate (mean / best-of-n) | rot_err |
|---|---|---|---|
| 2 | 5 | **0.800** / 1.000 | 15.3° |
| 3 | 5 | 0.633 / 0.700 | 23.4° |
| 4 | 5 | 0.356 / 0.467 | 33.0° |
| 6 | 5 | 0.573 / 0.680 | 41.0° |
| 8 | 5 | 0.590 / 0.714 | 44.1° |
| 10 | 1 | 0.778 / 0.889 | 32.2° |

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

---

## Synthesis (2026-07-27) — what the battery establishes

| hypothesis | verdict | evidence |
|---|---|---|
| **H1** pairwise-perception failure (GARF's mechanism) | **REFUTED** | C1: 0.800 placement at k=2; C2: fresh-real AUC 0.92 |
| **H2** joint-solve / context-dependent | **NOT SUPPORTED** | C1: flat in k (ρ = −0.124, p = 0.55) |
| **H3** wear-specific degradation | **SUPPORTED, partial** | C2: 0.92 fresh → 0.74 worn (n=1, wide CI) |
| **H4** piece-count cliff | **real but secondary** | C1: rot_err 15°→44° with k, seating rate flat |
| **H0** benchmark-only | **still the leading account** | Juglet GT is an invalid scan layout; B1 shows real mate separation |

**The picture that survives all four tests:** TORA is *not* broken on real
fracture — pairwise or jointly — and on the worn Juglet it retains both mate
discrimination (B1, 1.63×) and contact-encoding in its features (C2, 0.74).
Wear costs it something (0.92 → 0.74) but nothing like GARF's collapse (0.17×
fire rate, 1.04× separation across 15 experiments). This is architecturally
coherent: TORA froze RPF's encoder, so its wear-robustness cannot come from
better fracture perception — the candidate locus is the **Uni3D CKA macro-shape
channel** in the flow backbone, exactly the form-level information GARF's
Exp-15 concluded survives abrasion and that GARF's micro-texture encoder cannot
read. **Not yet proven** — C2b (CKA-channel ablation) is the test that would
close it.

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
