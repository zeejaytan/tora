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

### The key nuance — this looks like a learned shortcut

Whole-object form information **is already present** in the features (that is
what the Uni3D alignment contributes, measured surviving wear at **0.88**), and
global attention has access to it. So why isn't it used to rescue placement?

Most likely because it never had to be. Training used only breaks with excellent
micro-texture, where surface matching always succeeded. The model learned the
shortcut and never needed form for placement.

**This is a testable prediction**, and S3 (wear-augmented fine-tuning) tests it:
removing the shortcut should force the model onto the form information it
already has. If S3 fails anyway, the model *cannot* use form for placement, and
an explicit matching stage stops being optional.

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

### S3 — wear-augmented fine-tuning: **running** (job 28231335)
Newly possible: the validated mollifier manufactures worn training data *that
keeps its ground truth*. 108 variants built (84 train / 24 val). Conservative
recipe (synthetic replay, low LR, few epochs) because both prior fine-tunes here
ended up worse than the checkpoint they started from. Evaluated on worn **and**
fresh material so a gain bought by wrecking fresh objects is reported as a trade.

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

## 5. Recommended order

1. **A** — measured headroom, no retraining, works on real material. Do first.
2. **B** — best fit to conservation practice; modest, well-understood work.
3. **F** — cheap, might be free improvement.
4. **C** — promising but needs a validation step first.
5. **D / E** — real method changes; justified only if S3 and A/B fall short.

## 6. What would change this ranking

- **If S3 succeeds**, the shortcut hypothesis (§2) is confirmed and retraining
  with wear augmentation becomes the primary route — A and B then become
  multipliers on a better model rather than compensations for a weak one.
- **If S3 fails**, the model cannot use form for placement under any training
  pressure, and **D** moves from optional to necessary.
- All wear findings still rest on **six pots and one genuinely worn object**.
  More worn archaeological material would firm up every number here.
</content>
