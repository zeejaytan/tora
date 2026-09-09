# Wear v3 read out: the switchable adapter did not earn its place (job 29880370)

**Run:** `sbatch scripts/hpc/finetune_lora_vessels_v3.slurm`, job **29880370**,
`sacct: COMPLETED|0:0`, 2026-09-02, 1 h 14 m on `gpu-a100` (after 29825847 FAILED
`1:0` the previous day, at the close of epoch 0, on a dataloader worker teardown).
Read out **2026-09-10** — the job finished eight days before anyone opened its
results. Twelve evaluation arms fetched to `artifacts/lorav3_29880370/runs/`
(14 MB, gitignored).

What changed between wear v2 and wear v3, and why, is a separate note:
[`WEAR_V2_TO_V3.md`](WEAR_V2_TO_V3.md). This one is the result.

---

## The three-line background this conclusion depends on

The conservator named a gap: the model has never been trained on the **shape** of a
pot like the Juglet — the fine-tuning source holds eight ceramic vessels. Wear v3
answered it with 203 synthetic vessel shapes and, instead of rewriting the whole
network as every previous fine-tune here did, a **switchable attachment** (a LoRA
adapter, 2.69% of the weights) that can be turned off to restore the original model
bit-for-bit. The point of the switch is that the previous approach bought +0.235
seating on worn material by losing 0.115 on fresh, with no way to undo it.

## The answer, plainly

**The engineering worked and the result did not.** The adapter switches off exactly,
the frozen parts of the network genuinely did not move, and two serious defects in
the vessel corpus were fixed. But on reassembly the adapter **makes things slightly
worse, not better** — and it is worse on the very data it was trained for.

**Which of the three:** this is **the method genuinely not helping**, not a broken
measurement and not a wrong answer key. All twelve arms were scored on the corrected
unit-box ruler (every one carries `part_accuracy_absolute`, the post-`0d6a85f`
marker), the comparison is paired object-by-object against the untouched model, and
the ground truth on the synthetic and Fractura material is not in doubt. Two
measurement problems *are* recorded below, but neither of them rescues the result;
one of them makes it worse.

---

## 1. On its own training distribution the adapter loses

107 held-out synthetic vessel shapes, three draws each. Compared **per object** —
did this arm seat more of *this* object's sherds, fewer, or the same — because a
pooled mean over objects with different fragment counts is what `intent/O2` exists
to forbid.

| comparison | better | worse | same | sign test |
|---|---|---|---|---|
| **adapter on vs untouched model** | 30 | **49** | 28 | **p = 0.042** |
| adapter off vs untouched model | 39 | 30 | 38 | p = 0.34 |
| **adapter on vs adapter off** (same file, switch flipped) | 20 | **53** | 34 | **p < 0.001** |

The middle row is the control and it behaves: with the adapter off, the trained file
is indistinguishable from the untouched model, as it should be. The first and third
rows are the result: **turning the adapter on costs seating on its own validation
shapes.**

### And the training curve says the same thing, from the other end

Seating on the validation set, epoch by epoch:

```
0.843  0.783  0.773  0.768  0.750  0.747  0.748  0.746  0.758
0.743  0.742  0.727  0.754  0.762  0.752  0.753  0.761
```

**The best epoch was epoch 0** — the adapter after a single pass — and the run
selected it correctly. Every one of the next nineteen epochs was worse, and it never
came back. So "the adapter" is one epoch of training, and even that one epoch does
not beat the model it started from. This is not a checkpoint-selection failure; the
selection worked. There was simply nothing here to learn that helped.

## 2. On the worn sweep — the gain it was bought for — there is nothing

15 ceramic ladder points (three pots × five abrasion rungs), three draws each. Free
anchor named, turn corrected for it.

```
pot         sherds free  rung      untouched      adapter off       adapter on
blue_pot         5    1  e000      5.0/5 13d        5.0/5  6d        5.0/5 18d
blue_pot         5    1  e025      5.0/5  9d        5.0/5  9d        5.0/5  8d
blue_pot         5    1  e050      5.0/5 33d        5.0/5 11d        3.7/5 28d
blue_pot         5    1  e075      4.7/5 34d        4.7/5 20d        4.3/5 21d
blue_pot         5    1  e100      2.3/5 37d        1.7/5 64d        2.0/5 62d
galli_pot       10    1  e000     7.0/10 31d       8.0/10 25d       7.7/10 32d
galli_pot       10    1  e025     8.7/10 27d       7.7/10 34d       8.7/10 21d
galli_pot       10    1  e050     8.0/10 41d       8.3/10 23d       7.7/10 32d
galli_pot       10    1  e075     7.7/10 34d       7.0/10 44d       5.0/10 52d
galli_pot       10    1  e100     4.7/10 54d       5.3/10 51d       4.3/10 54d
plate            6    1  e000      4.3/6 41d        4.3/6 55d        4.0/6 52d
plate            6    1  e025      4.0/6 47d        4.0/6 65d        4.0/6 54d
plate            6    1  e050      4.0/6 54d        4.0/6 43d        4.0/6 56d
plate            6    1  e075      2.0/6 83d        4.0/6 76d        4.0/6 51d
plate            6    1  e100      3.7/6 78d        3.3/6 79d        4.0/6 65d
```

Paired over those 15: adapter on is better on 3, worse on 7, unchanged on 5
(p = 0.34). **No effect either way, and too few objects to have detected a small
one.** The individual movements cancel — the adapter loses `blue_pot` at e050
(5.0 → 3.7 of 5) and `galli_pot` at e075 (7.7 → 5.0 of 10) while gaining `plate` at
e075 (2.0 → 4.0 of 6). A pooled mean over this table would have reported a
confident, meaningless zero.

**Half of this sweep is not pottery.** The `erosion_sweep` and `fresh` arms both come
from the six-object `real_heldout_norm.hdf5`, and three of those six — `coxae`,
`limb3`, `vert9` — are **bones**. That is exactly the defect ticket 11 found in the
ticket-09 sweep, recurring here because the same source file was used. The bone rows
are reported separately in the summariser and are excluded from every count above.
`limb3` in particular sits at 3.0/3 on every arm at every rung and would have padded
any pooled figure with a constant.

## 3. On fresh pots — what we might be paying with — the seating count hides the cost

Three real unworn ceramics (the bones again excluded):

| object | sherds | untouched | adapter off | adapter on |
|---|---|---|---|---|
| `blue_pot` | 5 (1 free) | 5.0/5 seated, **6°** turn | 5.0/5 seated, **53°** | 4.7/5 seated, **19°** |
| `galli_pot` | 10 (1 free) | 8.3/10, 41° | 8.3/10, 28° | 7.7/10, 29° |
| `plate` | 6 (1 free) | 4.0/6, 51° | 4.0/6, 65° | 4.0/6, 48° |

`blue_pot` is the one to look at. Seating does not move at all — 5.0/5 on both
trained arms — while the average turn on the four sherds it had to place goes from
**6° to 53°**. In physical terms: the same five pieces are all inside the seating
tolerance, but the pieces are rotated most of the way to a right angle from where
they belong. **A seating count alone would have called this "no change".** This is
the collapsed-turntable failure in miniature: a single summary number rating a wrong
answer as fine.

Note that the 53° belongs to **adapter off** — the arm with the adapter disabled and
only the retrained pose head left in. That is the clearest evidence that the pose
head, which the switch does **not** cover, carries real damage of its own.

## 4. The Juglet — nothing on any arm is a juglet, and the score is mostly relabelling

Only the Juglet arms saved point clouds, so this is the only part of the run that
can be looked at. Five draws per arm.

**Render:** `artifacts/lorav3_29880370/juglet_arms_per_sherd.png`. Whole-pot outline
is not admissible on this material, so the lower row is the measured quantity itself
— per sherd, unbinned, all five draws — and the upper row draws the **median** draw
so picture and figure describe the same attempt.

Looking at it settles the question the numbers were arguing about: **all three arms
produce a diffuse cloud, not a vessel.** (An earlier reading of the job's own
assembly PNGs suggested the adapter arms held a juglet silhouette better than the
baseline. The per-sherd measure and the median-draw renders do not support that; the
apparent difference was in the visualisation, not the geometry.)

Two rulers, because they disagree and the disagreement is the finding:

| arm | sherds in their **own** place | sherds credited after **relabelling** | worst free sherd | turn |
|---|---|---|---|---|
| untouched model | **3.4** of 9 | 5.0 of 9 | 31.9% of pot size | 63° |
| adapter off | **2.6** of 9 | 3.8 of 9 | 52.3% | 72° |
| adapter on | **1.2** of 9 | 4.0 of 9 | 36.8% | 69° |

One of the sherds in every "own place" column is the **anchor**, which is clamped at
ground truth by construction and is not evidence. So the adapter-on arm earns
**0.2 of the 8 sherds it had to place.**

The right-hand column is what `part_accuracy` reports, and it is what the summariser
prints. `compute_part_acc` runs a Hungarian assignment: sherds may be **relabelled**
to whichever pairing passes the most of them, so a piece standing in another piece's
place can be counted as correct. On the adapter-on arm **2.8 of the 4.0 credited
sherds — 70% — exist only because of that relabelling**, against 1.6 of 5.0 (32%) on
the untouched model. The adapter's Juglet score is very largely an artefact of the
scoring convention.

All three turn figures are above the **~50°** collapse threshold, so by the standing
criterion nothing is assembled on any arm, which is what the renders show.

**What the Juglet can and cannot adjudicate.** It **does** have a valid answer key:
`juglet_gt.hdf5`, the conservator's hand reassembly in Blender (2026-08-10), fitted
back to the source fragments as a rigid transform with **0.0000% residual**. All three
arms here were scored against it (`data=zeroshot/juglet_gt`), so these scores are real
scores — `intent/O6` records that the failure survives the valid reference. What limits
it is **weight, not validity**: one pot, one reassembly, five draws. And the pot is
**incomplete** — a visible piece is missing and no reassembly can put it back, so a
reconstruction that leaves that gap open is correct and any metric rewarding contact
everywhere still misleads here.

## 5. What was measured badly, recorded rather than buried

- **The free anchor.** Every stored `part_accuracy` counts the anchor — clamped at
  truth — as a fragment the model placed, and `compute_transform_errors` skips the
  anchor when summing rotation error but divides by *all* fragments. Corrected at
  read time in `scripts/readout.py`, never at source: fixing
  `tora/eval/metrics.py` would silently change every historical `results/*.json`.
  The correction is ×1.125 on the nine-sherd Juglet and ×2.00 on a two-fragment pair.
- **Only the Juglet arms saved clouds.** The vessel, sweep and fresh arms saved
  metrics only, so **they cannot be rendered and cannot be identity-checked.** Given
  that 70% of the adapter's credited Juglet sherds turned out to be relabelling, the
  seating counts in sections 1–3 should be read as an upper bound on how much is in
  the right place. Any rerun must save clouds for every arm.
- **The size input was out of the trained band on 108 of 1302 draws** (0.3186–0.3342,
  against a trained band of 0.375–0.811). `scales` is fed to the flow model at every
  denoising step, so those draws asked the network about a size it was never trained
  on. A further 50-odd sit in the bottom 5% of the band.
- **The code changed underneath the running job.** `sbatch` freezes the *script* text
  at submission (15:32) but Python is imported at *runtime* (the evaluation arms ran
  16:29–16:46, after a mid-run `git pull`). So this job ran a 5-draw Juglet arm from a
  pre-`39fe1e8` script while using post-`0d6a85f` evaluator code. All twelve arms are
  internally consistent, so the arm-versus-arm comparison stands, but this is a real
  integrity problem and the fix is to pin the checkout before submitting.
- **`config/data/main/bbad_vessels_v3.yaml` misstates its own doses** (says 0.05% /
  0.10%; the built file uses 0.15% / 0.30%). Documentation only — the data is what the
  builder wrote — **corrected 2026-09-10**.

## 6. How much weight this bears

- **Section 1 is the strong part**: 107 objects, paired, one trained model,
  three draws each, p = 0.042 against the untouched model and p < 0.001 against its
  own off-switch. That is enough to say the adapter did not help on the material it
  was trained for.
- **Section 2 is weak**: 3 ceramic pots, 5 rungs, 3 draws. It can only say "no effect
  detected", not "no effect".
- **Section 3 is very weak**: 3 pots. The `blue_pot` turn jump is a lead about the
  pose head, not a result.
- **Section 4 bears little weight on its own** — one pot, five draws, scored against a
  valid but single hand reassembly — except for the relabelling finding, which is about
  the scoring convention and applies everywhere.
- **One trained model throughout.** Nothing here separates "adapters do not help on
  this task" from "this particular adapter, at this learning rate, on this corpus,
  did not help". The validation curve falling from epoch 1 onwards is consistent with
  both.

## 7. What this means for the work

1. **Keep the corpus fixes and the switch; do not keep the adapter.** The
   coincident-vertex rebuild, the lump filter and the verified freeze are worth
   having whatever happens next. The trained adapter itself should not be used, and
   nothing should be built on top of it.
2. **`train_head=false` next time.** "Reversible" was only three-quarters true — five
   pose-head tensors moved and the switch does not cover them, which is why
   `adapter_off` does not return to the untouched baseline (2.6/9 against 3.4/9 on the
   Juglet, and `blue_pot`'s 6° → 53°). With the head frozen, "off" would mean off.
3. **Save clouds on every arm.** Without them a seating count cannot be separated
   from a relabelling count, and on the one arm where we could check, most of the
   score was relabelling.
4. **A 20-draw Juglet rerun is worth less than more pots, but it is not worthless.**
   The Juglet's reference is sound, so the question a rerun answers is a real one:
   whether the three arms differ from each other by more than run-to-run noise, which
   is the first ticket of `intent/O8`. Only 5 of the requested 20 draws ran here. What
   caps its value is the object count, not the answer key — one pot, and an incomplete
   one. The better spend is the **eight Fractura ceramics** established by ticket 11 —
   real pots, real ground truth, four of them with a valid unworn control — instead of
   the six-object bone-contaminated file this job used, with the Juglet arms carried
   along at full draw count since they cost little.

## Reproduce

```bash
# fetch (12 arms, ~14 MB)
./scripts/remote/fetch_artifacts.sh eval_runs/lorav3_* ./artifacts/lorav3_29880370/runs/

# the honest read-out: free anchor named, no pooled mean, bones reported apart
PYTHONPATH=scripts python scripts/summarise_lorav3.py --runs artifacts/lorav3_29880370/runs

# the paired per-object comparison in section 1
PYTHONPATH=scripts python scripts/compare_lorav3_arms.py --runs artifacts/lorav3_29880370/runs

# the render, per sherd, all five draws, both rulers
PYTHONPATH=scripts python scripts/render_lorav3_juglet_arms.py --runs artifacts/lorav3_29880370/runs
```
