# Why TORA fails to assemble the Juglet — probe findings + test plan

Question: why does TORA (checkpoint `bbad_everyday_cka.ckpt`) fail to form a
good shape on the 9-piece Juglet archaeological scan, what does that failure
have in common with — or differ from — GARF's documented Juglet failure
(`GARF/docs/notes/JUGLET_ROOTCAUSE_FINDINGS.md`), and what is the main factor?

Probed 2026-07-21 from existing Spartan artifacts (6 prior juglet eval jobs,
May 2026; the Fractura zero-shot follow-up, April–May 2026) — **no new Slurm
jobs were submitted for this pass**, per the workspace rule to ask before
submitting jobs. Section "Next experiments" lists what would need sign-off.

---

## TL;DR

**TORA's Juglet failure is not (or not only) a wear-specific perceptual
collapse like GARF's.** The decisive evidence: on GARF's own four **fresh,
un-worn** Fractura control ceramics (`pink_bowl`, `narrow_bottle2`,
`narrow_bottle4`, `blue_pot` — the exact objects GARF assembles at
part_acc ≥ 0.92), **TORA already scores at chance** — part_accuracy pinned to
exactly `1/n_parts` (only the anchor piece ever counts as correct) and
rotation error 35–82°, on a benchmark with **valid ground truth** (unlike the
Juglet benchmark itself, see below). TORA never had a working real-ceramic
fracture-matching ability to lose — GARF did, and lost it specifically to
archaeological wear (its 15-experiment arc). TORA's Juglet result is the same
chance-level anchor-only signature, just on a harder (9-piece, worn, and
benchmark-broken) instance of a domain it was already failing.

**Main factor (working hypothesis, see gates below):** a **synthetic-to-real
domain generalization gap** in TORA's fracture/contact perception — present
already on fresh real ceramics, before wear or piece-count are even in play —
compounded by the Juglet's piece count (9, past TORA's own documented
6-piece failure cliff) and by an **invalid evaluation reference** for the
Juglet benchmark specifically (flagged below; already fixed for visual QA via
`*_proposed_assembly*.png`, not yet for the scalar metrics).

---

## What's already on record and directly relevant

From `analysis_failure_patterns.md` (thin-walled Breaking Bad, 3889 samples)
and `fractura_followup_24343146.md` (real Fractura ceramics/bones/eggs):

- **Piece-count cliff at 6 pieces.** Fail rate (rot_err ≥ 30°) is ~0% at
  2 pieces, 19% at 6–10, 48% at 11–29. The Juglet's 9 pieces sit past the
  cliff even in-domain.
- **Real archaeological-style breaks are already ~2× worse than synthetic
  even before piece count bites** (Breaking Bad *artifact* zero-shot: 8.4%
  fail rate at 3–5 pieces vs 0.4% in-domain — a 20× jump).
- **Generation-to-generation disagreement is a free failure signal**: when
  3 stochastic runs disagree, TORA is reliably wrong (Q4 instability quartile:
  mean rot_err 18.94° vs Q1's 0.56°).
- **Break-pattern geometry dominates over object identity** (11° within-shape
  std vs 3.7° between-shape std) — consistent with a perception-level, not
  identity-level, bottleneck, same qualitative shape as GARF's finding.

None of this is Juglet-specific, but it already predicts a Juglet failure
before any archaeological data is involved: 9 pieces alone puts it in TORA's
"catastrophic" bucket, and real-fracture breaks independently sharpen that
cliff.

---

## The Juglet benchmark's ground truth is invalid (already documented, now confirmed still relevant)

`GARF/docs/notes/JUGLET_DEPLOY_INFERENCE_ANALYSIS.md` (2026-05-20) already
established that for all three frameworks, the Juglet HDF5's `pointclouds_gt`
is the **anchor-centered scan/table layout**, not a true reassembly — "for
archaeological deploy, part_acc / rotation error / shape_cd are not
meaningful." I re-derived this independently from `tora/eval/evaluator.py`:
`_compute_metrics` scores `pointclouds_pred` directly against
`data["pointclouds_gt"]`, and for the Juglet split that tensor **is** the scan
layout (§3 of the deploy analysis). This is a real, separate defect from the
mechanism question — it means none of the six prior Juglet eval jobs'
`part_accuracy` / `rotation_error` numbers can be read as "how good is the
assembly," only as an internal-consistency check.

**All six prior jobs still show the identical signature regardless:**

| job | config | part_acc | avg rot_err | best-of-n rot_err |
|---|---|---|---|---|
| 25118786 | juglet (raw) | 0.1111 | 100.1° | 87.0° |
| 25192222 | juglet_deploy (raw) | 0.1111 | 86.6° | 70.8° |
| 25275931 | juglet_deploy_proposed | 0.1111 | 94.5° | 81.6° |
| 25279003 | juglet_deploy_proposed | 0.1111 | 91.5° | 70.6° |
| 25528198 | juglet_deploy_local02 | 0.1111 | 71.4° | 63.4° |
| 25594802 | juglet_deploy_local02 | 0.1111 | 64.1° | 54.0° |

`part_accuracy = 1/9` **exactly**, every run, every config (raw scale,
rescaled, anchor-free, anchor-fixed, proposed-assembly variant). Only the
anchor piece ever registers as correctly placed (chamfer < 1 cm); all 8
non-anchor pieces fail the threshold in every single seed. Because the
reference is invalid, this alone doesn't prove the *assembly* is wrong — but
see below, the same exact signature reproduces on a **valid**-GT benchmark.

---

## The decisive comparison: TORA already fails on GARF's fresh control ceramics

`fractura_ceramics_24342475` (a **valid**-GT benchmark — Fractura ceramics
HDF5s store a real broken-object mesh with coherent augmentation poses, see
deploy-analysis §7) contains all four of GARF's control objects:

| object | n parts | TORA part_acc | TORA rot_err (3 seeds) | GARF part_acc (control) |
|---|---|---|---|---|
| pink_bowl | 3 | **0.333 (=1/3)** | 75.7° / 60.2° / 64.5° | ≥ 0.92 |
| narrow_bottle2 | 3 | **0.333 (=1/3)** | 58.9° / 57.6° / 35.9° | ≥ 0.92 |
| narrow_bottle4 | 4 | **0.25 (=1/4)** | 49.1° / 46.5° / 61.4° | ≥ 0.92 |
| blue_pot | 5 | **0.20 (=1/5)** | 78.7° / 71.6° / 61.0° | ≥ 0.92 |

Every single sample lands at exactly `1/n_parts` — the anchor scores, nothing
else does, on **fresh, un-worn, real ceramic** fractures. This is the same
"only the anchor" signature as the Juglet runs, but here the ground truth is
real, so the signature can't be blamed on a broken reference. **TORA cannot
solve this task on the exact objects GARF solves at part_acc ≥ 0.92, before
wear enters the picture at all.**

This is the load-bearing finding for the "what's different from GARF"
question: GARF's Juglet failure is the *loss* of a demonstrated real-ceramic
capability (control part_acc ≥ 0.92, proven to collapse specifically under
archaeological wear via Exp 6–15). TORA's Juglet failure looks instead like
the **absence** of that capability on real ceramics generally, wear aside.

---

## Visual evidence: TORA's failure geometry differs from both GARF and PF++

Pulled `*_proposed_assembly0{1,2,3}.png` (the paper-faithful Procrustes
proposal — `P_k` rigidly transformed by the fitted per-part SE(3), the
correct object to judge "what does TORA propose," per deploy-analysis §6/§12)
from job 25594802 (`artifacts/juglet_probe/`, this repo, gitignored):

- The large anchor sherd (tan) always renders in roughly the same silhouette
  and position across `input`, `scan_ref`, `generation`, and all three
  `proposed_assembly` seeds.
- The other 8 sherds cluster into a **separate satellite blob** pressed
  against one edge of the anchor — not distributed around it into a vessel
  silhouette (PF++'s outcome) and not merged into one amorphous compact pile
  with the anchor (GARF's outcome, profile-fraction 0.719 in GARF's T0 panel).
  It reads as **two lumps sitting next to each other**, closer to "barely
  moved from a plausible starting cluster" than to "wrongly compacted into
  one mass."
- Seed-to-seed instability is real and visible: `proposed_assembly02` arranges
  the same 8 sherds into a distinctly different partial-ring shape than `01`
  and `03` (which resemble each other). Consistent with TORA's own documented
  early-warning signal (generation disagreement ⇒ untrustworthy output).

This is a genuine qualitative difference from GARF's documented failure mode
(single compact pile, quantified via the T0 vessel-profile-fraction panel)
and from PF++'s (plausible vessel via curvature-coherent composition). It has
**not** yet been quantified with GARF's no-GT panel (`pfpp_layout_probes.py`)
— that's the first proposed next step below.

---

## Architecture note: TORA is not a clean analogue of either GARF or PF++

- **GARF**: dense per-point features from `FracSeg`, pretrained via synthetic
  fracture-surface *segmentation* (fracture vs non-fracture), feeding an
  input-driven flow matcher with no compositional category prior.
- **PF++**: 25 FPS-centred **discrete VQ tokens** per sherd (coarse
  macro-curvature only) feeding a **DDPM with an explicit everyday-pottery
  category prior** — it composes curvature-compatible tokens into a
  category-typical vessel regardless of true mating.
- **TORA**: its own `PointCloudEncoder` (PointTransformerV3) is pretrained
  with an **overlap-aware** objective (`_build_overlap_head` in
  `tora/modeling/encoder/point_cloud_encoder.py` — a per-point head predicting
  cross-part overlap/contact), so it is *not* purely generic like a vanilla
  shape classifier — it has its own contact-signal pretraining, more like
  GARF's fracture-awareness in spirit. On top of that, TORA's flow model is
  trained with a CKA **representation-alignment loss to a frozen general
  whole-object teacher** (`uni3d_large`, `repr_dim=3072`, trained for
  whole-shape retrieval/classification, not fracture perception) — the
  paper's actual contribution. There is **no discrete bottleneck and no
  explicit generative category prior** (unlike PF++) — assembly is direct
  continuous rectified flow per part, conditioned on cross-part attention in
  the DiT.

So TORA sits architecturally between the two: contact-aware pretraining like
GARF, but with an added whole-shape teacher signal like (in spirit) PF++'s
curvature channel — and no compositional prior to fall back on when the
fine-grained contact signal fails, unlike PF++. The open question this
motivates: **when TORA's overlap head goes blind on real ceramics, does
anything analogous to PF++'s coarse-curvature fallback kick in?** The visual
evidence (satellite-cluster, not a plausible vessel) suggests no — but this
hasn't been probed at the feature level yet.

---

## Synthesis — main factor, and the GARF comparison

| question | answer | evidence |
|---|---|---|
| Is TORA's Juglet failure driven mainly by archaeological wear (GARF's mechanism)? | **Not established, and control comparison argues against it as the primary factor** | fresh-ceramic control already at chance |
| Does TORA ever demonstrate real-ceramic fracture-assembly competence to lose? | **Not yet observed** — chance-level on the exact objects GARF solves | control-ceramics table above |
| Is the Juglet-specific benchmark scalar metric trustworthy? | **No** — invalid GT (scan layout), already flagged by the team | deploy-analysis §3/§7, confirmed independently |
| Does TORA's *proposed* assembly look like GARF's pile or PF++'s vessel? | **Neither** — anchor blob + separate satellite cluster, unstable across seeds | Procrustes PNG comparison |
| Is 9 pieces alone enough to explain it? | **No — ruled out as primary driver.** Mean rot_err is flat (~59–70°) from 3 to 12 real ceramic pieces, no cliff. May still compound the Juglet case, but isn't why real ceramics fail at all | piece-count control section |

**Working main-factor statement:** TORA's Juglet failure is best explained,
on current evidence, by a **synthetic-to-real domain generalization gap** in
its contact/overlap perception — present on fresh real ceramics already,
independent of wear — compounded by piece count past TORA's own documented
cliff. This is a different failure class from GARF's, whose Juglet failure is
a proven, wear-*specific* collapse of an otherwise-working real-ceramic
capability. The two models may converge on the same practical outcome (no
usable Juglet assembly) via different routes: GARF loses a real skill to
abrasion; TORA may never have transferred that skill from synthetic training
data to real ceramic fracture surfaces at all. This reframes "what's
different" — it may be less "wear affects TORA differently than GARF" and
more "TORA's baseline real-ceramic competence, wear aside, is the thing to
explain first."

**Not yet decided:** whether TORA's gap is (a) purely in its own encoder's
overlap head failing to generalize past synthetic breaks, (b) in the flow/DiT
joint-inference stage failing to use a signal the encoder still provides, or
(c) some mix — GARF's analogous question took a pairwise oracle (Exp 6) plus
direct encoder introspection (Exp 10) to resolve. Same instruments are
proposed below for TORA.

---

## Next experiments (require Slurm sign-off before submitting)

Ordered by information value per compute cost; all reuse GARF's existing
methodology/scripts, adapted to TORA's checkpoint and HDF5 format.

1. **T0-style no-GT quality panel on TORA's Juglet output** (cheapest, no GPU
   needed beyond what's already run). Port `GARF/scripts/pfpp_layout_probes.py`
   to read TORA's `proposed_assembly` point clouds and compute the same
   compactness / coarse-pair / vessel-profile-fraction numbers already
   reported for GARF (0.719) and PF++ (0.961), plus the random-pile null
   (0.650). Directly quantifies where the "anchor blob + satellite cluster"
   visual falls on the same scale. **No new Slurm job — operates on already-
   fetched output.**

2. **Fresh-ceramics pairwise oracle (TORA's Exp-6 analogue).** Decompose
   GARF's 4 control objects (already have valid per-object GT) into 2-piece
   subproblems and score true-mate vs non-mate separation the way
   `pair_reference_chamfer.py` did for GARF. If TORA shows no separation even
   on fresh mates (paralleling PF++'s control-calibration failure, 1.17×),
   that confirms the deficit is pairwise-perceptual and pre-existing, not
   specific to Juglet's wear or 9-piece count. **Needs a short GPU job**
   (reuse existing control-ceramics HDF5, no new data prep).

3. **Overlap-head introspection (TORA's Exp-10 analogue).** Read out
   `PointCloudEncoder`'s `overlap_head` firing rate/AUC on: (a) synthetic
   Breaking Bad fresh breaks (labeled, in-domain), (b) GARF's 4 fresh control
   ceramics (real, out-of-domain, un-worn), (c) Juglet (real, worn). If firing
   already collapses at (b), the domain gap is proven present pre-wear,
   matching this doc's working hypothesis. If (b) fires fine and only (c)
   collapses, TORA's mechanism would instead parallel GARF's wear-specific
   story. **Needs a short GPU job** — no fine-tuning, pure introspection.

4. **Erosion bridge on TORA** (only if #3 shows wear-sensitivity at all).
   Reuse `GARF/scripts/fracture_mesh_ops.py`'s validated mollifier on the same
   4 control ceramics, rerun TORA's pairwise oracle across erosion strengths.
   Mirrors GARF's Exp 7/7b. **Needs a GPU job**, contingent on #3.

5. ~~Piece-count control~~ — **already answered from existing data, see below.**

Recommend running (1) first — free, no Slurm. (2) and (3) are the
mechanism-deciding experiments; flagging for sign-off before submission.

### Piece-count control, resolved from already-fetched data

Mean rotation error per object in `fractura_ceramics_24342475` (3 seeds),
grouped by piece count:

| n_parts | objects | mean rot_err |
|---|---|---|
| 3 | pink_bowl, narrow_bottle2 | 58.8° |
| 4 | narrow_bottle4, narrow_bottle3 | 58.9° |
| 5 | blue_pot | 70.4° |
| 6 | plate | 61.0° |
| 10 | galli_pot | 66.1° |
| 12 | narrow_bottle1 | 66.4° |

**Flat at ~59–70° across the entire 3-to-12-piece range — no trend with piece
count.** This is the opposite of TORA's own synthetic Breaking Bad pattern,
where 2-piece objects average ~0.3° and only 6+ pieces triggers the cliff.
Here, even the easiest possible case (3 real ceramic pieces) is already at
the same near-chance error level as 12 pieces. **This rules out piece count
as the primary driver of the real-ceramics / Juglet failure** — the domain
gap (real vs. synthetic fracture-surface statistics) is doing the work even
before combinatorics would be expected to matter. Piece count remains a
plausible *compounding* factor for the Juglet specifically (9 pieces, so
whatever residual joint-inference difficulty the cliff reflects is still
stacked on top), but it is not the explanation for why real ceramics fail at
all.

## Artifacts

- Visual QA: `artifacts/juglet_probe/*.png` (this repo, gitignored) — pulled
  from `TORA/eval_runs/juglet_deploy_local02_25594802/visualizations/` on
  Spartan.
- Prior eval logs: `TORA/tora_juglet*.log`, `TORA/tora_juglet_local02_*.log`
  on Spartan (job IDs in the table above).
- Fractura ceramics control data: `TORA/eval_runs/fractura_ceramics_24342475/results/`
  on Spartan (valid GT, contains GARF's 4 control objects).
- Related: `GARF/docs/notes/JUGLET_ROOTCAUSE_FINDINGS.md`,
  `GARF/docs/notes/JUGLET_DEPLOY_INFERENCE_ANALYSIS.md`,
  `GARF/docs/notes/PFPP_JUGLET_SUCCESS_FINDINGS.md`,
  `docs/notes/analysis_failure_patterns.md`,
  `docs/notes/fractura_followup_24343146.md`.
