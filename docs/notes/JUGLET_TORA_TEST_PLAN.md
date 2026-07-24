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
| **FracSeg fracture-response introspection (Exp 10)** | **NO** | TORA's analogue (`overlap_head`) is a dead instrument — fires on 75–98% of points regardless, AUC ≈ chance, and is discarded at inference (`tora.py._encode()` keeps only `out_dict["point"]`). Replaced by **T4**, a readout of the latents the DiT actually conditions on. |
| Pair oracle scored by `rotation_error` (`analyze_pairwise_oracle.py`) | **Partly** | rot_err is scale-safe, but on the Juglet there is no valid GT rotation, so rot_err is invalid there. Use the symmetry-invariant chamfer instead on Juglet; keep rot_err only on valid-GT controls. |

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

### C2. TORA-native encoder introspection (replaces GARF Exp 10, tests H1/H3)
GARF read P(fracture) off FracSeg. TORA's `overlap_head` is a dead instrument
(see table). Instead read the **per-point / per-part latents the DiT actually
conditions on** — `tora.py._encode()`'s `out_dict["point"]` — and test whether
contact-region features are more *complementary* for true mates than non-mates
(cosine-similarity structure at the mating band, or a linear-probe AUC).
Arms: synthetic fresh breaks (labeled, must pass — the instrument validation),
fresh real ceramics (GARF assembles, TORA assembles), Juglet worn rims.

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
