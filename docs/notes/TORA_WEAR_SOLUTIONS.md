# How TORA actually places fragments, and what could make it work on worn material

Companion to `JUGLET_TORA_TEST_PLAN.md` (which establishes the diagnosis). This
document covers **the mechanism** — how placement is decided inside the model —
and **the candidate fixes**, with what each is worth and what it would cost.

Written 2026-07-28. Status of each idea is marked; several are already settled.

---

## 1. The diagnosis in one line

Wear destroys the fine break-surface detail. The consequence is **not** that
joins fail to close — it is that fragments end up in **the wrong place
entirely**: at full wear the typical fragment sits 2.5× beyond the seating
tolerance, and the worst land further from home than the pot is wide.

**The deficit is *which fragment goes where*, not *how precisely it is seated*.**
That single fact decides which fixes can possibly work.

---

## 2. How TORA decides placement (checked against the code, 2026-07-28)

> **⚠️ This corrects an earlier claim of mine** that TORA "never asks which
> fragment mates with which". **It does — constantly.** The question is asked
> implicitly rather than explicitly, which is a different (and more useful)
> problem.

Every layer of the assembly network (`tora/modeling/flow_model/layer.py`,
`DiTLayer.forward`) applies **two** attentions in sequence:

| | what it does |
|---|---|
| `_part_attention` | points attend **within their own fragment** — "what shape am I?" |
| `_global_attention` | **every point attends to every other point across ALL fragments** |

The second is the matching mechanism. It is not a discrete decision that emits
"fragment 3 mates with fragment 7"; it is a continuous all-against-all
comparison, repeated at every layer and at each of the ~50 integration steps.
The answer only ever appears indirectly, as *where the velocity field pushes each
fragment*.

So correspondence is **resolved implicitly, thousands of times, and never
recorded**. It cannot be inspected, corrected, or supplied with better evidence.

### Why this works on fresh breaks and collapses on worn ones

Fresh fracture faces carry distinctive complementary micro-texture — the ridges
of one face are the hollows of its partner. In an all-against-all comparison the
true partner stands out, so the field drives the pair together.

Measured distinguishability of contact points (C2 probe, AUC):

| material | AUC | assembly outcome |
|---|---|---|
| simulated breaks | 0.96 | near-perfect |
| fresh real breaks | 0.92 | works (0.867 seated) |
| **worn Juglet rims** | **0.71** | **fails** |

At 0.71 many points across many fragments look alike. The comparison stops
locking onto one partner and spreads its weight across several — mostly wrong.
The fragment is then driven toward a blurred average of several candidate
destinations, **which is a location where nothing actually belongs**. That is
exactly the gross misplacement measured in C3/S2.

With 9 fragments resolved simultaneously and continuously, weak evidence
compounds: one ambiguous sherd pushes its neighbours wrong, worsening their
comparisons in turn.

### The key nuance — a learned shortcut, now CONFIRMED

> **⚠️ Corrects an earlier overstatement.** I originally wrote that form
> information "is already present in the model's features", citing 0.88. That
> 0.88 was the **Uni3D teacher's own** features — and the teacher is
> **training-only, discarded at inference**. It showed what was *available to
> transfer*, not what TORA carries where placement happens. Three separate
> claims had been run together. Both have now been measured.

**Did the structure transfer? Partially** (job 28232465, probing the flow model's
own features at the aligned layer, stable across t = 0.1/0.3/0.6):

| features | worn Juglet | fresh real | simulated |
|---|---|---|---|
| frozen RPF encoder | 0.71 | 0.92 | 0.96 |
| **TORA's aligned flow features** | **0.77** | 0.95 | 0.99 |
| Uni3D teacher (*training-only*) | 0.88 | 0.94 | 0.99 |

TORA's own features are consistently better than the raw encoder — so the
alignment *did* hand something over — but fall well short of the teacher (0.77
vs 0.88), and the wear-induced collapse is barely softened (−0.18 vs −0.21).
**Some of it is there, and it is not enough.**

**Did S3 fix it by seeing better, or by using what it had?** Probing the
wear-trained checkpoint identically (job 28240775):

| features | baseline | wear-trained |
|---|---|---|
| encoder, worn | 0.717 | 0.693 |
| **flow, worn** | 0.758 | **0.782** |
| flow, fresh real | 0.950 | 0.947 |

**The features barely moved** — every change sits inside the ±0.02 run-to-run
noise measured in the C2b seed sweep — yet placement improved by **+0.235**
(p = 0.008). So:

> **S3 taught the model to USE the information it already had, not to extract
> better information.** Perception was never the bottleneck; the placement
> policy was.

This confirms the shortcut hypothesis directly. Consequences:

- **Better perception is not the priority.** A stronger encoder would not have
  helped; the features were already adequate and were being under-exploited.
- **D (explicit matching stage) drops further in priority** — the model can
  evidently learn worn placement from the features it has.
- **A true LoRA becomes attractive.** S3 was a *full* fine-tune, and it damaged
  fresh-material performance (§3). Since the needed change is in how features
  are *used*, not in the features themselves, a low-rank adapter on the flow
  model's later layers should capture the gain while leaving the fresh-break
  behaviour largely intact — the obvious way to remove the trade-off.

### What Uni3D actually supplies (and what it does not)

The teacher is shown `pointclouds_gt` — the **correctly assembled pot** (coords
plus a constant colour) — and the CKA loss pushes the flow model's layer-3
features (of 6) to reproduce its *pairwise similarity structure*: which points on
the vessel resemble which others.

So it conveys **generic whole-object shape structure**, learned from seeing the
pot intact. It does **not** encode wall thickness, rim curvature, or profile
continuity — Uni3D-L is a general shape model trained on complete everyday
objects for retrieval/classification; it knows nothing of pottery and never sees
fragments. Those conservation cues describe what an **explicit matching stage
could be fed** (idea D), *not* what the model currently measures. Nothing in
TORA presently quantifies the properties a conservator would reason from.

---

## 3. Settled results

### S1 — free inference knobs: **NO EFFECT** (job 28229895)
4× integration steps, `rk4` sampler, 10 generations: all within run-to-run noise
of baseline at full wear (0.435 → 0.435–0.504). The model does not need more
compute; it needs better information. Matches GARF Exp 5.

### S2 — post-hoc geometric settling: **REFUTED** (jobs 28229957, 28230423)
The "good enough, not perfect" idea: let neighbouring fragments settle until they
touch. Widening the settling reach makes it **catastrophically worse**:

| reach | Δ seating | worsened |
|---|---|---|
| 0.06 | +0.002 | 1/30 |
| 0.30 | **−0.389** | 22/30 |
| 0.50 | **−0.407** | 22/30 |

"Pull toward the nearest surface" is only correct when the nearest surface is the
*true* mate. Once fragments are misplaced, more freedom attaches them more
confidently to the **wrong** neighbour. **Local geometry cannot recover a
correspondence it does not have.** No post-hoc tidying can fix this.

### S3 — wear-augmented fine-tuning: **IT WORKS** (job 28231335)

The first lever that recovers seating under wear. Trained on 108 manufactured
worn variants (84 train / 24 val) with synthetic replay, low LR, 40 epochs.

**Leakage check first:** the 6 test pots (blue_pot, coxae, galli_pot, limb3,
plate, vert9) are exactly the held-out set; the 21 training objects are entirely
different pots. **No leakage** — the gains are on unseen objects.

| wear | baseline | wear-trained | change |
|---|---|---|---|
| 0.00 (fresh) | 0.819 | 0.704 | **−0.115** |
| 0.25 | 0.798 | 0.770 | −0.028 |
| 0.50 | 0.641 | **0.894** | **+0.253** |
| 0.75 | 0.591 | **0.770** | **+0.179** |
| 1.00 | 0.524 | **0.797** | **+0.273** |

**In the worn regime (wear ≥ 0.50): mean +0.235, 10 improved / 4 worsened /
4 tied, Wilcoxon one-sided p = 0.0078.** Statistically solid, unlike most results
in this investigation.

**At full wear, seating rises 0.524 → 0.797 — essentially recovering the
baseline's *fresh-pot* performance (0.819) on heavily abraded material.**

Per-object, the two catastrophic failures are the ones rescued:

| object | fresh (base→ft) | full wear (base→ft) |
|---|---|---|
| coxae | 0.67→0.67 | **0.00 → 0.83** |
| vert9 | 0.83→**0.00** | **0.00 → 0.67** |
| plate | 0.60→1.00 | 0.60 → 0.87 |
| blue_pot | 1.00→1.00 | 0.92 → 0.75 |
| galli_pot | 0.81→0.56 | 0.63 → 0.67 |
| limb3 | 1.00→1.00 | 1.00 → 1.00 |

**This confirms the shortcut hypothesis (§2).** The model *can* place worn
fragments — it simply never had to learn how, because training only ever offered
breaks with good micro-texture. Remove the shortcut and the capability appears.

**⚠️ It is a TRADE, not a free win.** Fresh performance drops 0.819 → 0.704, and
`vert9` fresh collapses 0.83 → 0.00 while its worn case goes 0.00 → 0.67 — the
same object trading one regime for the other. Note the training set *did* include
un-worn copies (strength 0), yet fresh still degraded: 3 of the 4 wear levels are
worn, so the mixture is worn-heavy. **Rebalancing the wear distribution is the
obvious next tuning step**, and may recover much of the fresh loss.

**Practical reading:** for worn archaeological material this checkpoint is
clearly better; for fresh breaks the original is better. Until the mixture is
tuned, treat them as two tools rather than one.

---

## 4. Candidate fixes, ranked by value ÷ effort

### A. Recognise a good attempt without the answer key — **highest value, no retraining**

**The model already succeeds on worn pots — it just cannot tell when.** Across
the 10 attempts it already makes (job 28229895, `gens10`):

| wear | worst | average | **best** | headroom |
|---|---|---|---|---|
| 0.00 | 0.730 | 0.806 | 0.915 | +0.109 |
| 0.25 | 0.646 | 0.752 | 0.915 | +0.163 |
| 0.50 | 0.544 | 0.719 | **0.915** | **+0.196** |
| 0.75 | 0.488 | 0.623 | **0.831** | **+0.208** |
| 1.00 | 0.443 | 0.485 | 0.605 | +0.120 |

At moderate-to-heavy wear the **best of ten attempts reaches 0.83–0.92 — matching
fresh-pot performance (0.875)**. The capability exists and is discarded, because
"best" is currently chosen *by consulting the ground truth*, which real
archaeological material does not have.

**Fix:** score candidate assemblies with a ground-truth-free quality measure —
do the fragments actually touch along their edges, is there interpenetration,
does the profile run continuously across joins, is the result vessel-shaped
rather than a heap. GARF already implements these (`pfpp_layout_probes.py`:
compactness, coarse adjacency, fine contact, interpenetration, vessel-profile
fraction, with published baselines PF++ 0.961 / GARF 0.719 / random 0.650).

- **Effort:** low — port the scorer to TORA's saved clouds (`save_assembly_npz`
  already exists), select argmax, re-measure.
- **Risk:** low — changes nothing about the model.
- **Deployable on real material**, unlike everything else here.
- **Ceiling:** bounded by the best attempt; will not fix full-wear cases.

### B. Human-in-the-loop partial assembly — **high value, modest effort, most conservation-relevant**

`multi_anchor` already exists (`tora/data/dataset.py:367-378`): the anchor flag is
per-fragment, `anchor_indices` is a per-point mask, and the sampler re-clamps
**all** flagged fragments to their given poses at every step
(`sampler.py:_reset_anchor`). Currently used only as a random training
augmentation and disabled everywhere.

Inverted, that is a conservator's workflow: **join the sherds you are confident
about; the software completes the rest around them.** Every pinned fragment
removes ambiguity from exactly the thing that is failing — placement. It also
fails safely: your joins are never overwritten, and a bad suggestion costs
nothing.

- **Missing:** a way to specify *which* fragments are fixed and to supply their
  poses from the user rather than from ground truth.
- **Effort:** modest — plumbing, not research.
- Directly attacks the diagnosed failure, and degrades gracefully.

### C. Start from a rough layout instead of from noise — **medium value, needs validation**

Assembly currently starts from **pure Gaussian noise** (`x_1 = torch.randn_like`)
— the pot is rebuilt from scratch with no starting hypothesis. The API already
accepts an injected start (`sample_rectified_flow(..., x_1=...)`,
`flow_sampler(x_1=...)`).

Seed it instead with a coarse arrangement — a partial hand layout, a form-based
guess, or another method's output — and let the flow refine rather than solve
blind. Since the failure is placement, starting from roughly-right placement
attacks it directly.

- **Caveat:** the model expects Gaussian noise at t=1, so a layout cannot simply
  be substituted. The standard approach is to noise the guess partway and start
  integration from an intermediate time. Needs testing, not assuming.

### D. Explicit matching stage — **high value, high effort**

Make correspondence a first-class, inspectable step: build a fragment-adjacency
graph first, then assemble under those constraints.

The point is **not** that the model lacks matching (§2 — it matches constantly).
The point is that its matching consumes **one kind of evidence, surface
similarity, which is exactly what wear destroys**. An explicit stage could be fed
the evidence that survives: vessel form, profile continuity, wall thickness, rim
curvature — what a conservator actually uses on worn sherds.

Supporting evidence that usable signal survives: TORA still separates true mates
from non-mates on the worn Juglet (1.63×, p = 0.025). Matches GARF's own closing
recommendation (form-based pairing and pose init, with fracture-feature
refinement only where signal survives).

### E. Vessel-form prior (surface of revolution) — **speculative, highest ceiling**

Most vessels are surfaces of revolution. Fit a common axis and profile, then
require fragments to lie on that surface. This makes explicit the one channel
measured surviving wear (0.88), and is closest to how reassembly is actually
reasoned about at the bench. Not present in the code; substantial work.

### F. Anchor choice — **cheap test, unknown value**

The anchor is chosen as the **largest fragment by area**
(`dataset.py:293`, `np.argmax(counts)`) — an arbitrary rule. For a worn vessel a
rim sherd or a distinctively-shaped fragment might constrain the solution far
better. Testing every fragment as anchor is cheap and would reveal how much that
arbitrary choice costs.

---

## 4b. The wear-trained checkpoint ON THE REAL JUGLET (job 28266869)

The sweep validated the fix on *artificially* abraded pots. The Juglet is the
genuine article: real archaeological wear, 9 fragments, near-symmetric vessel.

**Visual (the only honest instrument here — no valid ground truth exists).**
`artifacts/juglet_viz/wearft/COMPARISON_wearft.png`:

- **Real, visible improvement.** The sherds are markedly **more compact and
  better organised**, hugging the anchor fragment in a coherent mass that follows
  its contour, instead of fanning outward with pieces jutting into space.
- **Noticeably more consistent across attempts** than the baseline, whose
  arrangements varied considerably run-to-run (that instability was itself a
  documented warning sign).
- **Still not a vessel.** No neck, no closed body profile. **The Juglet is not
  reassembled.**

**Pairwise (PF++ pseudo-GT, form-level only), mean-over-generations:**

| | true neighbours | unrelated pairs | ratio |
|---|---|---|---|
| baseline | 65.6% | 27.8% | **2.36×** (p = 0.002) |
| wear-trained | 67.8% | **54.4%** | 1.24× (p = 0.17, n.s.) |

The wear-trained model improved only marginally on true neighbours (65.6 → 67.8%)
but **greatly** on unrelated pairs (27.8 → 54.4%), so its *discrimination ratio*
fell. This is not a regression in disguise — it is the predicted behaviour: for a
non-touching pair the pseudo-GT still specifies where the two sit in the overall
vessel, so scoring better there means **placing fragments by whole-object form
rather than by local edge-matching**. Exactly what the training targeted and what
the mechanism probes (§2) predicted: less reliance on destroyed micro-texture,
more on surviving form.

**Verdict: the lever works, and it is not sufficient for this pot.** Arranging
fragments plausibly is not the same as joining them correctly.

Two honest limits on why:

1. **The Juglet is worn beyond the training range.** Its measured roughness
   (relief_p90 **0.171**) is slightly past our most extreme simulated level
   (**0.183** — lower = more worn). We trained up to *almost* this pot's
   condition, not past it.
2. **Simulated wear is a proxy.** The mollifier smooths break faces; burial also
   rounds edges, chips rims and removes material. A real limitation of the
   approach, not a tuning knob.

**This is the most informative negative available**: it says artificial wear does
not fully substitute for the real thing, and bounds how far this route can go
without genuinely worn training material.

---

## 5. Recommended order (revised after S3 succeeded)

0. **S3 is the primary route** — it works (p = 0.008), recovers worn-pot seating
   to fresh-baseline levels, and confirms the capability exists. Immediate
   follow-up: **rebalance the wear mixture** to claw back the fresh-material
   loss, then re-run the same comparison.
1. **A** (recognise a good attempt) — now a *multiplier* on a better model
   rather than compensation for a weak one. Still no retraining, still the only
   option deployable where no answer key exists.
2. **B** (human-in-the-loop anchors) — best fit to conservation practice.
3. **F** — cheap, may be free improvement.
4. **C** — promising, needs a validation step first.
5. **D / E** — real method changes. S3's success **lowers** their priority: the
   model can evidently learn worn placement, so rebuilding the matching stage is
   no longer the only road.

## 6. What would change this ranking

- **S3 succeeded**, so the shortcut hypothesis is supported and retraining is the
  primary route. **D/E drop in priority.**
- **The pending flow-feature probe (job 28232465) still matters**: if the aligned
  features turn out *not* to carry form, then S3's gain came from something else
  (e.g. the encoder adapting), and the mechanism story in §2 needs revising even
  though the fix works.
- All wear findings still rest on **six test pots and one genuinely worn
  archaeological object**. More worn material would firm up every number here.
- The fresh-material regression is real and unexplained in detail; if
  rebalancing does not fix it, a wear-conditioned or two-checkpoint deployment
  is the fallback.
</content>
