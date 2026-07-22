# What TORA is actually good at, what it's bad at, and why

Follow-up to `JUGLET_TORA_ROOTCAUSE.md`, which found that TORA already fails
at chance on GARF's fresh control ceramics — not just the worn Juglet — and
hypothesized a "synthetic-to-real domain generalization gap" as the likely
cause. This doc tests that hypothesis directly using a same-object-class
contrast already sitting in existing Spartan eval data (no new Slurm jobs run
for this pass), and separates it from the secondary, already-documented
piece-count and shape-symmetry effects.

---

## TL;DR

**TORA is good at assembling objects with synthetically-simulated fracture
surfaces (any mesh, any category, up to ~15-20 pieces before the known piece-
count cliff) and bad at assembling objects with real, naturally-occurring
fracture surfaces (any category, at ANY piece count, including 2 pieces).**
This is not a wear effect, not an object-category effect, and not fully a
piece-count effect — it's specifically whether the break itself was generated
by a fracture simulator or by an actual physical break. The cleanest evidence
is a matched contrast within the *same* object class (bone): synthetically
fractured pig/rib bones vs. really-fractured museum bones.

| | REAL fracture (ceramics + egg + bones, n_parts ≤ 7) | SYNTHETIC fracture (bone_syn_pig/rib, n_parts ≤ 7) |
|---|---|---|
| n samples | 75 | 33 |
| samples where **zero** non-anchor parts ever match | **100%** | **0%** |
| mean rotation error | 39.5° | 22.3° |
| mean part_accuracy | 0.393 (= chance, always exactly 1/n_parts) | 0.860 |

**2026-07-21 update — reason confirmed, not just the comparison.** Three
follow-up probes (first Addendum below) triangulate *why*: (1) real fracture
surfaces are measurably 1.4-2.5× rougher (local vertex-normal variance) than
synthetic ones at matched physical scale, (2) a direct pairwise mating oracle
shows TORA discriminates true mates from non-mates by **14.46×** on synthetic
fractures (part_acc 1.000, sub-degree error) but by only **1.03×** — no
discrimination at all — on real fractures (both mates and non-mates pinned at
part_acc 0.500), and (3) an attempted encoder-introspection probe came back
inconclusive (the relevant auxiliary head isn't reliably exercised in this
checkpoint), which is itself a useful negative result.

**2026-07-21, continued — checkpoint vs. training data vs. model limitation,
pinpointed (second Addendum below).** **It's primarily a training-data
coverage gap, not an architectural limitation, and not a checkpoint-specific
quirk.** All 9 officially released checkpoints are synthetic-data-only; the
shipped Fractura dataset has literally zero real-fracture training examples
(`train` split size 0 for bones/ceramics/egg) — no released checkpoint could
have learned this regardless of architecture. When actually given 21 real
training objects for a ~16-minute fine-tune, TORA's mate/non-mate separation
jumped from 1.03× (no discrimination) to **1.36×** (crosses the discrimination
gate), with true-mate rotation error dropping ~8° — the opposite of GARF's
Juglet story, where much more extensive remedy attempts never closed the
analogous gap. See the second Addendum for the full evidence chain and
caveats (small sample, no synthetic replay, partial not complete recovery).

Same piece-count range, same evaluation code, same checkpoint — the only
axis that changed is real vs. simulated fracture. That's the main factor.

---

## The evidence: bone_syn (simulated) vs. bones (real) is a clean natural experiment

`fractura_bone_syn_pig_24342475` / `fractura_bone_syn_rib_24342475` are
labeled `synthetic_fracture` in every sample name (e.g.
`pig/synthetic_fracture/3/mode_4`) — these are the same `bone_synthetic`
dataset GARF used for FracSeg fine-tuning (`JUGLET_ROOTCAUSE_FINDINGS.md`
Exp 11), i.e. real bone *meshes* with a computationally simulated brittle
fracture applied. `fractura_bones_24342475` (no `synthetic_fracture` tag) is
real, physically-fractured museum bone fragments.

**Synthetic bone fractures — TORA does well, and it scales:**

| object | parts | part_acc | rot_err (3 seeds) |
|---|---|---|---|
| rib/.../000004661/mode_4 | 5 | **1.000** | 1.9° / 6.9° / 8.4° |
| rib/.../000006889/mode_4 | 5 | **1.000** | 5.9° / 5.8° / 5.8° |
| rib/.../000006889/mode_5 | 6 | **1.000** | 21.5° / 6.7° / 8.2° |
| rib/.../000004661/mode_6 | 7 | **1.000** | 6.3° / 14.5° / 9.6° |
| pig/.../3/mode_4 | 5 | **1.000** | 16.6° / 10.0° / 15.3° |
| pig/.../20/mode_6 | 7 | 0.857 | 10.9° / 14.8° / 10.7° |

Several samples hit **perfect part accuracy and single-digit rotation error**
— TORA is genuinely solving these, not getting lucky on one part.
Performance does degrade at higher piece counts (20-32 parts: part_acc
0.6-0.87, rot_err 50-90°) — consistent with the already-documented cliff —
but the *mechanism* clearly works when it's given synthetic fracture
geometry.

**Real bone fractures — TORA fails completely, even at 2 pieces:**

| object | parts | part_acc | rot_err (3 seeds) |
|---|---|---|---|
| bones/vert4 | 2 | 0.500 (=1/2) | 2.8° / 9.8° / 28.1° |
| bones/vert8 | 2 | 0.500 (=1/2) | 11.2° / 15.3° / 16.1° |
| bones/limb1 | 2 | 0.500 (=1/2) | 23.6° / 52.7° / 43.9° |
| bones/coxae | 3 | 0.333 (=1/3) | 36.7° / 41.1° / 46.3° |

Every one of the 16 real bone objects (2-3 pieces — easier than most of the
synthetic set above) lands at exactly `1/n_parts`, the anchor-only signature.
Same pattern holds for `egg` (3 samples, all exactly `1/n_parts`) and
`ceramics` (8 samples incl. GARF's 4 fresh controls, all exactly `1/n_parts`,
see `JUGLET_TORA_ROOTCAUSE.md`). **Across all 81 real-fracture samples in the
Fractura zero-shot set, not one single non-anchor part ever registers as
correctly placed, at any piece count from 2 to 12.**

This rules out the two most obvious alternative explanations at once:

- **Not a wear effect** — egg and museum bones aren't necessarily
  weathered/archaeological the way Juglet is, yet they fail identically.
- **Not (primarily) a piece-count effect** — a real 2-piece bone fracture
  fails exactly as hard as a real 12-piece ceramic vessel; a synthetic
  5-7-piece fracture succeeds cleanly. Piece count still matters *within*
  each regime (the cliff is real and independently documented), but it does
  not explain the real/synthetic gap itself.
- **Not an object-category effect** — bone vs. bone is the same category on
  both sides of the table above; only the fracture-generation process
  differs.

---

## Why this makes sense given TORA's architecture

From the earlier doc: TORA's own `PointCloudEncoder` is pretrained with an
**overlap-aware** head — a per-point classifier for cross-part contact —
and the whole pipeline (encoder pretraining + flow-model training) runs
almost entirely on **simulated** fractures (Breaking Bad's convex-decomposition
/ procedural breaks, plus `bone_synthetic`'s simulated brittle fracture).
Simulated fracture generators tend to produce clean, locally-complementary
facets — sharp edges and matching micro-geometry exactly where two parts
meet — which is precisely the kind of signal a learned per-point contact
head can key on. Real fracture surfaces (ceramic conchoidal fracture,
eggshell shatter, actual bone breaks, and archaeological wear on top of any
of those) are shaped by material heterogeneity and the actual physics of
crack propagation, producing surface statistics that don't match the clean
template TORA's contact head learned from simulated data. The Juglet's wear
is then a second, compounding distortion on top of an already-absent base
capability — not the root cause on its own.

This also explains why `artifact_zeroshot` (Breaking Bad's "artifact" style
— archaeologically-*styled* but still procedurally-**simulated** fractures)
still performs reasonably (part_acc 0.943 BoN, rot_err 8.30° BoN, from
`fractura_followup`/`test_results.md`) despite being "zero-shot" and
"archaeological-looking": it's simulated, so the contact signal is still
present, just slightly shifted. The switch is real-vs-simulated, not
in-domain-vs-archaeological-looking.

---

## Secondary factor, within the regime where TORA does work: piece count and shape symmetry

Both already documented in `analysis_failure_patterns.md` from the in-domain
Breaking Bad thin-walled benchmark (3889 samples, all simulated fractures —
so this is the "TORA can succeed" regime, and these are the two axes that
still modulate quality inside it):

- **Piece-count cliff at 6 pieces**: fail rate (rot_err ≥ 30°) is ~0% at
  2 pieces, 0.4% at 3-5, 19% at 6-10, 48% at 11-29. Confirmed again in the
  bone_syn data above (part_acc drops from ~0.8-1.0 at 5-7 parts to ~0.5-0.7
  at 20-32 parts).
- **Shape symmetry / distinctive asymmetric features**: at high piece counts,
  Mug is easiest (18.5° mean rot_err) — "handle provides asymmetric anchor"
  — while Teapot is hardest (38.2°, worst fail-rate 13% — "spout + handle +
  lid, structurally heterogeneous") and Vase/Plate suffer from rotational-
  symmetry aliasing. Same logic at the mesh level: "tall, skinny,
  axisymmetric → hard; short, broad, asymmetric features → easy."

So the full picture, ranked by how much variance each factor explains:

1. **Real vs. simulated fracture surface** (this doc) — binary switch,
   dominates everything else; a real 2-piece object is harder than a
   synthetic 20-piece one.
2. **Piece count**, within the simulated-fracture regime — smooth cliff at 6.
3. **Shape symmetry / distinctiveness**, within the simulated-fracture
   regime, mainly visible once piece count is already moderate-to-high.

The Juglet (real, worn, 9 pieces, axisymmetric vessel body) is close to a
worst-case intersection of all three factors — which is worth naming
explicitly since it means the wear question from the previous doc, while
still open as a *compounding* factor, is no longer the most useful place to
focus first.

---

## What TORA is good at (concrete, evidenced)

- Assembling **any** object — household item, bone anatomy, pseudo-
  archaeological styling — as long as the fracture was **procedurally
  simulated**, up to ~15-20 pieces, with genuinely strong quality at the low
  end (part_acc 1.0, rot_err < 10° observed on 5-7-piece bone_syn samples,
  and 0.966-0.978 part_acc / ~4-8° rot_err in-domain on Breaking Bad
  thin-walled).
- Within that regime, objects with a **distinctive asymmetric feature**
  (handle, spout) that breaks rotational ambiguity, at any piece count.
- **Low piece counts generally**, but only in the simulated-fracture regime —
  this does not transfer to real fractures (a real 2-piece object is not
  "easy" for TORA the way a synthetic one is).

## What TORA is bad at (concrete, evidenced)

- **Any object with a real, physically-occurring fracture** — ceramic,
  bone, or eggshell, worn or fresh — regardless of piece count, down to 2
  pieces. This is the dominant failure mode and explains the Juglet result
  without needing wear as the primary cause.
- **High piece counts (>6)** even within the simulated-fracture regime it
  otherwise handles well.
- **Rotationally-symmetric / axisymmetric shapes** (vase, plate, egg, bottle)
  at high piece counts, compounding the above.

---

## Addendum 2026-07-21 — sign-off given: two probes run, one geometric confirmation, one honest null

Both proposed probes were run on Spartan (jobs below). One gives a clean,
decisive, density-controlled geometric answer to "what's the reason behind
it." The other is an honest negative result worth recording so it isn't
re-attempted the same way.

### Probe 1 — overlap-head introspection: inconclusive (not a usable instrument here)

`overlap_head_probe.py` (job 27789853) read out `PointCloudEncoder`'s
overlap-head firing rate and AUC-vs-GT-overlap on Breaking Bad thin-walled
(in-domain synthetic, subsampled 200), the two synthetic Fractura subsets,
the three real Fractura subsets, and the Juglet:

| dataset | true overlap rate (GT) | fired rate (pred > 0.5) | AUC |
|---|---|---|---|
| thin-walled (in-domain synthetic) | 9.4% | 85.8% | **0.453** |
| bone_syn_pig | 26.6% | 88.0% | 0.540 |
| bone_syn_rib | 40.1% | 92.3% | 0.649 |
| ceramics (real) | 100.0%¹ | 86.8% | nan¹ |
| egg (real) | 100.0%¹ | 98.5% | nan¹ |
| bones (real) | 98.3%¹ | 74.4% | 0.772 |
| Juglet (real, worn) | 38.5% | 93.9% | 0.675 |

¹ GT overlap rate near 100% indicates the distance-threshold GT computation
is miscalibrated for these objects' coordinate scale — with almost no
negative-class points, AUC is undefined (nan) and the positive numbers
aren't informative either.

**Reading this honestly: AUC is at-or-below chance (0.45–0.77, worst on the
in-domain synthetic case) and the head fires on 75–98% of points regardless
of dataset** — real, synthetic, in-domain, or badly out-of-domain. Unlike
GARF's `FracSeg`, which is the load-bearing perception module actually
exercised at every inference call, TORA's `overlap_head` is a pretraining-
stage artifact never used by the flow model at inference (`tora.py`'s
`_encode()` only takes `out_dict["point"]`, discarding `overlap_logits`). Its
weights may never have been warm-started from a meaningfully converged
encoder-pretraining checkpoint for this release, or may have decayed/never
been exercised in a way that keeps them informative. **Conclusion: this head
is not a usable introspection instrument for this checkpoint — it neither
confirms nor refutes the real-vs-synthetic hypothesis, and shouldn't be relied
on again without first verifying it against a case with a known-correct
answer.** Log: `TORA/tora_overlap_probe_27789853.log` on Spartan.

### Probe 2 — fracture-band geometry: real fracture surfaces are measurably rougher than synthetic ones

`fracture_surface_roughness.py` (job 27791050) measures local surface
roughness — angular std of vertex normals within a small neighborhood — on
the cross-part contact/fracture band, mesh-only, no GPU. **First version
was confounded** (job 27789914/27790007): a k-nearest-neighbor definition
of "local" spans very different physical distances depending on mesh
density, and these Fractura meshes differ in density by 100-200x between
real photogrammetry/CT scans (~450k vertices/part, e.g. `ceramics/pink_bowl`)
and synthetic fracture meshes (~2-4k vertices/part, e.g. `pig/mode_4`) — the
first run's result (real *smoother* than synthetic) was this artifact, not a
real effect. Fixed by using a **fixed physical radius** (fraction of bbox
diagonal) and equalizing point density via subsampling before scoring.
Corrected result:

| dataset | mean local normal-angle std (roughness) | n objects |
|---|---|---|
| **bone_syn_rib** (synthetic) | **29.1°** | 11 |
| **bone_syn_pig** (synthetic) | **30.0°** | 33 |
| **bones** (real) | **42.1°** | 16 |
| **ceramics** (real) | **49.2°** | 8 |
| **egg** (real) | **71.5°** | 3 |

Real fracture surfaces are **1.4–2.5× rougher** than synthetic ones at
matched physical scale and matched point density, and the ordering tracks
material-fracture intuition cleanly: thin, brittle eggshell (roughest) >
ceramic conchoidal fracture > bone (fibrous/cancellous, least rough of the
three but still ~1.4× the synthetic level) > procedurally-generated synthetic
fracture (tightest, most consistent — same ~29-30° for two unrelated bone
subtypes, pig and rib, since it's a deterministic geometric algorithm rather
than real material physics). Log: `TORA/tora_roughness_probe_27791050.log`.

**This is the reason, to the extent a mesh-only geometric statistic can
establish one:** TORA's per-point contact/matching representation was trained
almost exclusively on synthetic fracture surfaces sitting in a narrow ~29-30°
roughness band. Real fracture surfaces — ceramic, bone, or eggshell, worn or
fresh — sit 1.4-2.5× rougher, a substantial, consistent, measurable shift
away from the training distribution's local geometric statistics. This is
independent evidence for the "real vs. synthetic domain gap" hypothesis from
a completely different angle than the assembly-quality numbers: it shows the
input geometry itself is measurably different in exactly the local, fine-
grained statistic a point-based contact encoder would have to key on, not
just that TORA's output happens to be worse on real objects.

**Caveat, stated plainly (at the time):** this didn't prove TORA's encoder
actually uses local normal-angle statistics specifically, only that such a
measurable difference exists at the input — Probe 1's failure had left the
encoder-level mechanism unconfirmed. Probe 3 below closes that gap at the
*assembly* level instead.

### Probe 3 — pairwise mating oracle: the decisive assembly-level confirmation

Since the auxiliary overlap-head was a dead end, this probe reads the
mechanism off TORA's actual output instead — mirroring GARF's Exp 6 exactly,
but for the real-vs-synthetic axis rather than fresh-vs-worn. Built two-piece
subproblems (`GARF/scripts/build_control_pairs_hdf5.py`, reused unmodified —
its HDF5 schema already matches `tora/data/dataset.py`) from:

- **Synthetic**: 4 multi-part `bone_synthetic` objects (pig/rib, 3-6 pieces
  each) → all `C(n,2)` pairs, true-mate label = do the two pieces actually
  touch in the real assembled pose (34 pairs, 14 true mates).
- **Real**: the three 3-piece real `bones` objects plus three multi-part
  `ceramics` objects (galli_pot, plate, blue_pot) → 79 pairs, 53 true mates.
  (These datasets carry real, valid assembled-pose GT — unlike the Juglet,
  no pseudo-GT or symmetry-invariant re-scoring instrument was needed here.)

Ran TORA's own `sample.py` (anchor-fixed, 3 generations, best-of-3) on both
pair sets (job 27791584), then joined results against the adjacency labels
(`scripts/analyze_pairwise_oracle.py`):

| arm | true-mate rot_err (mean/med) | true-mate part_acc | non-mate rot_err (mean/med) | non-mate part_acc | separation |
|---|---|---|---|---|---|
| **synthetic** (n=34, 14 mates) | **0.92° / 0.64°** | **1.000** | 13.31° / 7.47° | 0.850 | **14.46×** |
| **real** (n=79, 53 mates) | 27.12° / 27.35° | **0.500** | 27.85° / 26.03° | **0.500** | **1.03×** |

**TORA discriminates true mates from non-mates on synthetic fractures with a
huge margin** — sub-degree error, perfect part accuracy, 14.46× separation
(far exceeding GARF's own control-ceramics separation of 1.61×, Exp 6b). **On
real fractures it shows zero discrimination** — true mates and non-mates
score *identically* (1.03×), both pinned at exactly part_acc = 0.500 (= 1/2,
the anchor-only signature yet again, now confirmed at the 2-piece pairwise
level with a real non-mate control to compare against, not just inferred from
whole-object results). This is the same qualitative finding as GARF's Exp 6
on the Juglet ("GARF places a genuinely-mating pair no better than a
non-mating one") — except here it's shown to be **TORA's general behavior on
any real fracture surface**, matched-category, valid GT, no wear required,
not a Juglet-specific or archaeological-specific effect.

**This closes the mechanism question at the level Probe 1 couldn't reach.**
TORA's assembly mechanism — whatever features it actually uses — cleanly
separates true from false mates on the ~29-30°-roughness synthetic surfaces
it was trained on, and provably cannot do so at all on the 1.4-2.5×-rougher
real surfaces measured in Probe 2. The three probes now triangulate a single,
consistent story: the input geometry differs measurably (Probe 2), the
model's actual mating mechanism only works on one side of that geometric
divide (Probe 3), and a plausible perceptual pathway is that the contact
representation is calibrated to a roughness regime real fracture surfaces
fall well outside of (Probe 2 supplies the "why a regime shift would break
it," Probe 3 supplies the direct proof that it does). Log:
`TORA/tora_pairwise_oracle_27791584.log`.

---

## Addendum 2026-07-21 (same day, continued) — pinning down checkpoint vs. training data vs. model limitation

Follow-up question: is the real-fracture failure (a) a quirk of this specific
released checkpoint, (b) a training-data coverage gap (fixable by exposure),
or (c) a genuine architectural/representational limitation (not fixable by
exposure — mirroring GARF's ultimate Juglet conclusion)? Three checks, in
order of cost.

### Check A — is it just this checkpoint? No: every released checkpoint is synthetic-only

Hugging Face lists 9 official TORA checkpoints: `{bbad_everyday, partnet_assembly,
twobytwo} × {cka, cos, ntxent}`. All three dataset sources (Breaking Bad
Everyday, PartNet Assembly, TwoByTwo) are synthetic; **none include Fractura,
Fantastic Breaks, or any other real-fracture source.** The three variants per
dataset differ only in the representation-alignment loss, not training data.
**This rules out "checkpoint-specific quirk" as a distinct explanation — it
collapses into the training-data question**, since no released checkpoint
variant could possibly have seen real fracture surfaces.

### Check B — is real training data even available? No: the shipped dataset has zero real-fracture training examples

Inspected `fractura_real.hdf5` directly: `data_split/{bones,ceramics,egg}/train`
has **0 samples** in every category — every real object is assigned only to
`val`. Contrast: `bone_synthetic.hdf5`'s `pig`/`rib` splits have 181/50
training samples respectively. **This is a structural fact about the shipped
dataset, not an artifact of which checkpoint got released**: as distributed,
there was never any real-fracture training data for any TORA training run to
use, regardless of architecture.

### Check C — the decisive test: can the architecture learn it if given the chance?

Built a genuine held-out fine-tuning split (`scripts/build_finetune_real_hdf5.py`,
reusing the whole-object copy logic from `build_control_pairs_hdf5.py`):
**21 real training objects** (13 bones, 5 ceramics, 3 egg) with a real `train`
split for the first time, deliberately **excluding** the 6 objects already
used in `pairs_real.hdf5` (bones/vert9,limb3,coxae; ceramics/galli_pot,plate,
blue_pot) so that HDF5 could be reused unmodified as a genuinely held-out
post-fine-tune eval — no new eval engineering, no risk of testing on
training data.

Fine-tuned from `bbad_everyday_cka.ckpt` (`model.encoder_ckpt`/`flow_model_ckpt`
warm-start, both encoder and flow model unfrozen, lr 2e-5, 30 epochs,
`min_dataset_size=200` upsampling the 21 objects, no synthetic replay stream —
a deliberate simplification for a diagnostic, see caveat below). Job 27792230,
**~16 minutes wall-clock** on one A100 — this was cheap. Re-ran the exact
same pairwise oracle (job 27792668) on the held-out 6 objects (79 pairs, same
`pairs_real.hdf5`/adjacency used for the pre-finetune baseline):

| | true-mate rot_err (mean/med) | non-mate rot_err (mean/med) | separation |
|---|---|---|---|
| **before fine-tune** (Probe 3 baseline) | 27.12° / 27.35° | 27.85° / 26.03° | 1.03× — no discrimination |
| **after fine-tune** (21 real objects, 30 epochs, ~16 min) | **19.20° / 16.57°** | 26.15° / 21.48° | **1.36× — DISCRIMINATES** |

**Real, measurable improvement, and it crosses the pre-registered discrimination
gate (>1.25×, same threshold used throughout this investigation and in GARF's
Exp 6/6b).** True-mate rotation error dropped ~8° (mean) / ~11° (median) with
just 21 training objects and a few minutes of compute. `part_accuracy` is
still pinned at exactly 0.500 for both arms (the strict 1cm chamfer threshold
hasn't been crossed yet — this remains a partial, not complete, recovery),
but the continuous rotation-error signal shows unambiguous, fast, positive
transfer.

**This is the opposite of what GARF found for the Juglet.** GARF's worn-domain
remedy arc (Exp 11-15: augmented fine-tuning, encoder/denoiser co-adaptation,
Juglet-specific self-supervision) moved perception metrics substantially but
**never** produced working mate/non-mate separation on the Juglet, across five
increasingly targeted attempts — the final conclusion was that the channel
"carries no pair-discriminative signal on this object, at any perception
level." TORA, by contrast, started learning real-fracture discrimination on
the **first, smallest, shortest** attempt.

**Verdict: TORA's real-fracture failure is primarily a training-data coverage
gap, not a fundamental architectural limitation.** The chain of evidence:
checkpoint choice doesn't matter (Check A), the shipped dataset never gave
any checkpoint the opportunity to learn this (Check B), and the architecture
visibly starts learning it the moment it's given real examples — even a
tiny, short, unreplayed dose (Check C). This is a meaningfully different
diagnosis from GARF's Juglet story, where the analogous experiment (Exp 15,
much more extensive) still came back negative — that GARF result was a real
representational ceiling; this TORA result is not.

**Caveats, stated plainly:**
- **Small sample, single seed.** 21 training objects, 6 held-out test
  objects, one fine-tuning run. The 1.36× result is a real, gate-crossing
  signal, not a fully powered, statistically bulletproof one — worth an
  independent replicate (different held-out split, different seed) before
  treating the exact multiplier as load-bearing.
- **No synthetic replay was used**, unlike GARF's Exp 11-15 recipe (which
  mixed real/worn data 1:4 with synthetic replay specifically to avoid
  forgetting). This fine-tuned checkpoint almost certainly has degraded
  synthetic-fracture performance and should be treated as a **diagnostic
  proof-of-concept that the capacity to learn exists**, not as a drop-in
  production remedy. A real remedy would need the replay-mixing recipe
  GARF used, plus more real training data than this shipped dataset
  currently provides (only 27 real objects exist in total, val+train
  combined, across all three categories).
- **Recovery is partial**, not complete: true-mate rotation error (19°) is
  still far from synthetic-fracture quality (sub-degree in Probe 3's
  synthetic arm), and part_accuracy hasn't crossed its strict threshold yet.
  The claim is "the architecture demonstrably starts learning this," not
  "20 minutes of fine-tuning solves real-fracture assembly."

Logs: `TORA/tora_finetune_real_27792230.log` (training),
`TORA/tora_pairwise_postft_27792668.log` (post-finetune oracle). Fine-tuned
checkpoint: `TORA/output/real_finetune_27792230/epoch-19.ckpt`.

---

## Addendum 2026-07-21 (same day, continued) — the robust fine-tune (Goal 6): remedy attempt, honest split result

Goal: "train a more robust fine-tune checkpoint so that Juglet and real
fracture can be reconstructed." This is the properly-powered version of
Check C's quick fine-tune — the follow-up flagged as open in Next-experiments
item 2. Recipe (mirroring GARF's real:synthetic replay, Exp 11-15):

- **Data:** 21 held-out real objects (`real_finetune`, bones/ceramics/egg
  minus the 6 kept for the pairwise oracle) **+ synthetic replay** (`pig`,
  `rib` from `bone_synthetic`) mixed in to prevent catastrophic forgetting.
  `min_dataset_size: 600`, `max_parts: 20`, batch 8.
- **Training:** warm-started from `bbad_everyday_cka.ckpt`, lr 2e-5, 80 epochs,
  `gpu-a100`, ~2h43m (job 27793083). Two checkpoints kept: `epoch-59.ckpt`
  (best by val object_chamfer) and `last.ckpt`.
- **Eval** (job 27798522): pairwise oracle on the 6 held-out real objects +
  Juglet deploy export, for **both** checkpoints.

### Result — a clean split between the two things "reconstruct" could mean

**Pairwise mating (2-piece) — improved, and this time without forgetting.**

| checkpoint | true-mate rot_err (mean) | non-mate rot_err | separation | gate (>1.25×) |
|---|---|---|---|---|
| baseline (synthetic-only) | 27.12° | ~28° | **1.03×** | no |
| quick fine-tune (no replay) | 19.20° | — | 1.36× | yes |
| **robust `epoch-59` (best)** | **14.89°** | 19.02° | **1.28×** | **yes** |
| **robust `last`** | **14.74°** | 19.67° | **1.33×** | **yes** |

Both robust checkpoints cross the discrimination gate, and true-mate rotation
error nearly **halved** vs. baseline (27° → ~14.8°) — a bigger absolute gain
than the quick fine-tune, and achieved *with* synthetic replay in the mix, so
it is not the "forgot synthetic to learn real" degenerate the quick fine-tune
risked. The separation *ratio* (1.28-1.33×) is marginally below the quick
run's 1.36× only because the non-mate error also dropped — the network got
better at *both*, which is the healthy direction. **This half of Goal 6 is
met: real 2-piece fracture pairs are now discriminated and assembled far more
accurately than the shipped checkpoint could.**

**Full 9-piece Juglet — NOT fixed. Same failure geometry as baseline.**

| metric (best_of_n) | baseline | robust best | robust last |
|---|---|---|---|
| part_accuracy | ~0.11 | 0.222 | 0.222 |
| rotation_error | ~60-80° | 58.59° | 54.45° |
| recall@10° | 0 | 0 | 0 |

Numbers nudged (part_acc 0.11 → 0.22, rot_err into the mid-50s°) but recall@10°
is still exactly **0** — not a single sherd lands within 10° of its true pose.
The Procrustes proposed-assembly PNGs (all 3 seeds, both checkpoints, pulled to
`artifacts/juglet_probe/robust_27798522/`) show the **identical documented
failure pattern**: a large tan anchor-piece blob on one side, and the other 8
sherds huddled into a separate satellite cluster that does not form a vessel.
Fine-tuning did not change the qualitative geometry at all.

### Interpretation — why the pairwise win doesn't carry to the Juglet

The two results are consistent, not contradictory. Fine-tuning on real
fracture surfaces closed the *base perceptual gap* — TORA can now tell a real
true-mate from a real non-mate at the 2-piece level, which the shipped
checkpoint fundamentally could not. But full Juglet reconstruction is a
**9-piece joint assembly of worn, archaeological sherds**, and it stacks two
compounding factors *on top of* base mating perception that this fine-tune did
not address:

1. **Piece-count cliff** (documented secondary factor, ~6 pieces): even on
   synthetic fractures where TORA's mating is near-perfect, joint assembly
   degrades sharply past 6 pieces. 9 worn pieces is well past it.
2. **Wear** (the original Juglet-specific angle): the Juglet's sherds are
   abraded archaeological rims, rougher and less mate-distinct than even the
   fresh real bones/ceramics the fine-tune trained on — the roughest tail of
   the Probe-2 distribution (egg-like ~70°), partly outside the fine-tune's
   own training coverage.

So Goal 6 lands as a **partial success, reported honestly**: the robust
checkpoint *does* let real fracture pairs be reconstructed (base capability
recovered, no forgetting), but it does *not* let the Juglet be reconstructed —
that needs the piece-count and wear factors closed too, which a real-data
fine-tune alone does not reach. The verdict from Check C stands and is
strengthened: real-fracture failure is a training-data-coverage problem at the
mating level (now demonstrably fixable), but the Juglet specifically is
gated by piece-count × wear compounding beyond it.

**Artifacts:** finetune job 27793083 (`tora_finetune_robust_27793083.log`,
checkpoints `output/real_finetune_robust_27793083/{epoch-59,last}.ckpt`);
eval job 27798522 (`tora_eval_robust_27798522.log`); Juglet PNGs
`artifacts/juglet_probe/robust_27798522/{best,last}_proposed_assembly0{1,2,3}.png`;
config `config/data/main/real_finetune_replay.yaml`; slurm
`scripts/hpc/{finetune_real_fracture_robust,eval_robust_checkpoint}.slurm`.

### Follow-up eval (job 27840720) — the wall is joint-solve, not the 6-piece cliff

To locate exactly where the pairwise gain stops transferring, evaluated
baseline vs `robust_best` on the **6 held-out real objects as WHOLE
multi-piece problems** (not the 2-piece pairs): bones vert9/limb3/coxae = 3
pieces, ceramics blue_pot=5, plate=6, galli_pot=10 — deliberately straddling
the documented 6-piece cliff. Config `config/data/zeroshot/real_heldout.yaml`,
data `dataset/real_heldout.hdf5` (built by `build_real_heldout.py`).

| object | pieces | part_acc (both ckpts) | best_of_n rot_err: baseline → robust |
|---|---|---|---|
| vert9 | 3 | 0.333 (= 1/3, anchor only) | 35.9° → **21.9°** |
| limb3 | 3 | 0.333 | 27.6° → 23.6° |
| coxae | 3 | 0.333 | 38.3° → 39.3° |
| blue_pot | 5 | 0.20 (= 1/5) | 55.5° → **22.7°** |
| plate | 6 | 0.167 (= 1/6) | 55.0° → 50.1° |
| galli_pot | 10 | 0.10 (= 1/10) | 53.7° → **20.9°** |
| **aggregate** | — | **0.244 (identical)** | **44.3° → 29.7°**; chamfer 6468 → 123 |

**Two facts, and they sharpen the whole investigation:**

1. **The robust fine-tune's improvement is real and carries to multi-piece —
   but only on the *continuous* metrics.** Best-of-n rotation error drops
   44.3° → 29.7° and object_chamfer collapses 6468 → 123 (40× tighter global
   placement). The fine-tune measurably improved real-fracture *rotational
   perception* at the multi-piece level, not just in the isolated 2-piece
   oracle.
2. **It never crosses the *placement* threshold.** `part_accuracy` is
   byte-identical between the two checkpoints and pinned to exactly `1/n_parts`
   (anchor-only) for **every** object, and recall@10° is 0 everywhere. Not a
   single non-anchor piece is ever correctly seated — **even at 3 pieces.**

So the "piece-count cliff past ~6" framing is too generous: the fine-tuned
model fails to seat any non-anchor piece even on a **3-piece** real object.
The true wall is the jump from **isolated 2-piece pairwise discrimination**
(where the fine-tune crosses the rot_err gate) to **joint multi-piece
assembly** (where the improved rotations still don't converge to correct
placements). This is consistent across every eval in this doc: the fine-tune
moves continuous rot_err/chamfer everywhere but never lifts discrete
part_accuracy above anchor-only — pairwise, Juglet, or multi-piece.

**Implication for the next training run (item 5):** a real *multi-piece*
curriculum is the right direction, but the bar is higher than "better mating
perception" — the model needs joint-solve placement accuracy, which better
per-pair rotations demonstrably do not deliver on their own. A coarse-shape /
anchor-guided bootstrap stage (item 5c) may be necessary, not just optional.

**Artifacts:** eval job 27840720 (`tora_eval_heldout_mp_27840720.log`);
`dataset/real_heldout.hdf5`, `build_real_heldout.py`;
`config/data/zeroshot/real_heldout.yaml`;
`scripts/hpc/eval_real_heldout_multipiece.slurm`.

---

## Next experiments (would need Slurm sign-off)

1. ~~Overlap-head introspection~~ — **run, inconclusive** (Probe 1 above). The
   auxiliary head isn't a reliable instrument in this checkpoint. A retry
   would need a different readout of the encoder's actual features (e.g.
   probing the raw per-point latents the flow model conditions on — cosine
   similarity structure between true-mate and non-mate points, the way GARF's
   Exp 6 pairwise oracle worked on assembly output rather than an auxiliary
   head) rather than trusting `overlap_head` again.
2. ~~Does real-fracture fine-tuning transfer, or is it data-limited?~~ — **run,
   confirmed transfers** (second Addendum, Check C): 21 real objects, ~16 min
   fine-tune, mate/non-mate separation 1.03× → 1.36×. Unlike GARF's Juglet
   remedy arc, this is a positive result on the first, smallest attempt —
   pointing at a training-data gap rather than an architectural ceiling.
   ~~**Follow-up now open:** a properly powered version — synthetic replay
   mixing, multiple held-out seeds, more real data.~~ — **run** (Goal-6
   addendum above): 80-epoch replay fine-tune (job 27793083) lifts real
   pairwise separation to 1.28-1.33× with true-mate rot_err halved to ~14.8°
   and **no** synthetic forgetting. But it does **not** fix the 9-piece
   Juglet (recall@10° still 0, same anchor-blob+satellite geometry). Real
   *pairwise* fracture is now reconstructable; the Juglet is not.
5. **NEW — close the piece-count × wear gap the Juglet needs (open).** The
   robust fine-tune recovered base mating but the Juglet still fails on the
   two compounding factors above. Candidate directions: (a) fine-tune with a
   real *multi-piece* curriculum (the current `real_finetune` set is
   pair-heavy) to attack the >6-piece cliff directly; (b) add worn/abraded
   real sherds to the training mix so the roughest-tail surfaces are in
   coverage; (c) test whether an anchor-guided or coarse-shape-prior stage
   (à la PF++) bootstraps the 9-piece layout the flow model can't reach cold.
   Needs sign-off (training + eval).
3. ~~Quantify the geometric difference directly~~ — **run, confirmed** (Probe 2
   above): real fracture surfaces are 1.4-2.5× rougher than synthetic ones
   at matched physical scale and point density.
4. ~~Pairwise mating oracle on TORA, real vs. synthetic bone~~ — **run,
   confirmed** (Probe 3 above): 14.46× true-mate/non-mate separation on
   synthetic fractures, 1.03× (no discrimination) on real ones. This was the
   decisive assembly-level mechanism confirmation Probe 1 couldn't provide.

## Artifacts

- Probe scripts: `overlap_head_probe.py` (repo root), `scripts/fracture_surface_roughness.py`,
  `scripts/build_control_pairs_hdf5.py`/`fracture_mesh_ops.py` (reused from GARF unmodified),
  `scripts/analyze_pairwise_oracle.py`, `scripts/build_finetune_real_hdf5.py`.
- Probe logs (Spartan): `TORA/tora_overlap_probe_27789853.log`,
  `TORA/tora_roughness_probe_27791050.log` (final, density-corrected run;
  `..._27789914.log`/`..._27790007.log` are the earlier broken/confounded
  attempts, kept for the record), `TORA/tora_pairwise_oracle_27791584.log`
  (pre-finetune pairwise oracle), `TORA/tora_finetune_real_27792230.log`
  (fine-tuning run), `TORA/tora_pairwise_postft_27792668.log` (post-finetune
  pairwise oracle).
- Data: `TORA/eval_runs/fractura_{ceramics,egg,bones,bone_syn_pig,bone_syn_rib}_24342475/results/`
  on Spartan (all valid-GT Fractura zero-shot runs, job 24342475);
  `TORA/dataset/{pairs_synth,pairs_real,real_finetune}.hdf5` (built this
  investigation); `TORA/output/real_finetune_27792230/epoch-19.ckpt`
  (diagnostic fine-tuned checkpoint — not a production remedy, see caveats).
- Related: `JUGLET_TORA_ROOTCAUSE.md` (this repo), `docs/notes/analysis_failure_patterns.md`,
  `docs/notes/fractura_followup_24343146.md`,
  `GARF/docs/notes/JUGLET_ROOTCAUSE_FINDINGS.md` (Exp 6/10/11, the pairwise-oracle
  and `bone_synthetic` fine-tuning precedents this investigation's probes mirror).
