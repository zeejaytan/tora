# 05: Does the out-of-band size input actually cost the wear result anything?

**Type:** `wayfinder:task` (AFK)

**What to build:** A **measured** cost, in sherds seated, for scoring the wear sweep at a
size the model was never trained on. Ticket 04 established that the warning on
`WEAR_TEST_RESULTS.md` §4 is real — every real pot is presented to the model as unusually
small, two of them smaller than anything in training. It did **not** establish that this
costs anything. This ticket runs the sweep again with that one number moved into the
middle of the trained band and reads the difference.

**Answers:** O2

**Blocked by:** None. 04 is resolved and supplies the measured band.

**Status:** phase 1 done; phase 2 ready-for-agent

## Why it exists

The wear verdict rests on one paired comparison: the baseline model seats **0.843** of the
loose sherds on fresh pots and **0.645** on the same pots worn. Ticket 04 showed both rows
were produced with the model told a size of 0.319–0.383, against a trained band of
0.375–0.811 (median 0.550). It also showed the handicap is held nearly constant across the
ladder (largest within-pot drift 2.0%), so it cannot have *opened* the twenty-point gap.

What is still unknown is the **level**. Both numbers may be depressed, and until that is
measured the wear result is a lower bound on a handicapped model rather than a measurement
of the model we actually want to talk about. Wear v3's success criterion is written against
0.645 and 0.843, so it should not be built until those two numbers are known to be the
right ones.

## What the existing evidence already says — and why it does not close this

**This experiment is partly pre-answered, and the prior points at "no cost".** Two ladder
jobs already varied exactly this input on real pots:

| job | range of `scales` tested | result |
|---|---|---|
| 29891327 | 0.5 → 5, and up to 100 | flat from 0.5 to 5; collapse between 15 and 50 |
| 30130045 | 0.04 → 0.5 (rungs 0.04, 0.08, 0.15, 0.25, 0.5) | **flat and non-monotone** |

Job 30130045 is the relevant one and it is strong: eight pots, ten draws each, five rungs,
400 draws, with `check_scale_conditioning.py` asserting that only `scales` moved. Seven of
eight pots shifted by a few degrees across a **twelvefold** change in stored size, and the
renders at the two ends were indistinguishable. Three of the six sweep pots (`blue_pot`,
`galli_pot`, `plate`) were in it.
`.scratch/juglet-cause/issues/03-low-side-out-of-band-scale.md`.

**Three gaps keep this open, and the first is the one that matters:**

1. **Both ladders were read in rotation, and rotation is the metric this project has
   already been burned by.** Ticket 05 of the juglet-cause map established that wear moves
   **turn by about 3°** and **seating by twenty points**, and that a null measured in turn
   against a ±27.7° between-pot floor carries no information. The scale ladders measured
   turn. They may be repeating that error one level up: *flat in the metric the effect does
   not live in*. The wear finding is stated in seating, so the cost must be measured in
   seating.
2. **The ladders used fresh pots only.** Whether out-of-band conditioning interacts with
   **wear** — whether a model leans harder on the size prior when the break faces have been
   degraded — is untested. That interaction, not the main effect, is the one that could
   bend the §4 gap.
3. `coxae`, `limb3` and `vert9` were in neither ladder, and `coxae` is one of the two pots
   sitting below everything training showed.

## One worry this ticket does not have to carry

**The seating measure is scale-invariant by construction, so `scales` cannot distort the
ruler.** `part_accuracy` — the field `readout.py` reads — is computed in the unit-box frame
(`tora/eval/evaluator.py:87`, on `pts_gt / unit_box_scale(pts_gt)`), which is independent of
`scales`. The saturation to 9-of-9 recorded at size 0.0408 in juglet-cause ticket 03 was
`part_accuracy_absolute`, the **pre-fix** scoring, on runs from before commit `0d6a85f`.

So this ticket asks about the **model's behaviour**, not about the measurement. Of the
three: if something turns up here it is **the method genuinely failing** on out-of-band
input, not a broken ruler.

## The experiment

**No data rebuild.** The dataset already has the knob, and it was built for exactly this:
`normalize_object_scale` restates the object at max|coord| = 0.5 *after* centring on the
point centroid and *before* the [-1, 1] normalisation, and `scale_multiplier` restates it
again (`tora/data/dataset.py:421-424`). The coordinates the network sees are unchanged;
only `scales` moves. Rung *m* gives `scales` = 0.5 × *m* **exactly**, for every object, so

    +data.normalize_object_scale=true +data.scale_multiplier=1.1     ->  scales = 0.550

lands every pot at the measured median of the trained band.

**Do not reach for `scripts/normalize_real_hdf5.py` to do this.** File-level normalisation
is what produced `juglet_norm`'s 0.041 — it scaled by distance from the *file's* origin
while the pot sat 0.48 away from it, shrinking the pot elevenfold (ticket 04, and
`artifacts/scale_band/juglet_layouts_zoom.png`). The runtime knob normalises about the
object's own centroid, which is the right origin.

**Gate first, on CPU, before any GPU time.** `scripts/check_scale_conditioning.py` on
`erosion_sweep.hdf5` and on `real_heldout_norm.hdf5`. It costs seconds and it decides
whether the run means anything: if the knob also perturbed the coordinates or the normals,
a change in score would not isolate the conditioning input. `eval_scale_ladder.slurm`
already runs this gate and stops on failure — copy that pattern.

**Four arms, one job, one settings set.** Baseline checkpoint `bbad_everyday_cka.ckpt`,
the same one §4 used:

| arm | data | size told to model |
|---|---|---|
| A | `real_heldout_norm` (fresh) | as stored, 0.319–0.383 — reproduces §4 |
| B | `real_heldout_norm` (fresh) | 0.550 |
| C | `erosion_sweep` (worn ladder) | as stored, 0.319–0.321 — reproduces §4 |
| D | `erosion_sweep` (worn ladder) | 0.550 |

A and C are controls and are not optional: they are what proves the rest of the settings
match §4 rather than merely resembling it. The comparison to read is **(B − A) against
(D − C)**.

**Draws.** §4 ran at `model.n_generations=3`, which is too few to read a seating difference
against draw-to-draw scatter. Run at 10 and report the per-draw spread beside every mean,
so a difference smaller than the scatter is visible as such rather than quoted as a result.

**Read through `scripts/readout.py`** — the only admissible reader — and **render** arm C
against arm D on the same pot at the heaviest wear, at individual-sherd placement, not
whole-pot outline. On these objects the outline survives even in the worst draw.

## Stated in advance, so it can fail

**Prediction, from the flat ladders: seating will move by less than the draw-to-draw
scatter in all four arms, and the gap (D − C) will match (B − A) to within that scatter.**

- **If that holds**, the ⚠️ downgrades from "a real handicap of unknown cost" to "out of
  band, measured cost near nil", and 0.843 / 0.645 stand at full strength as levels, not
  just as a difference. Wear v3 can be built on them.
- **If both rows rise together**, the wear finding is confirmed at full strength and the
  §4 numbers are restated at the corrected level.
- **If the gap closes**, part of the twenty points was an artefact of scoring a handicapped
  model. That is the outcome that would refute the current framing, it is the reason the
  job is worth running despite the prior, and it must be reported if it happens.

## Acceptance criteria

- [ ] The CPU gate passes on both datasets before any GPU time is spent
- [ ] Four arms in one job with one settings set and one job id; A and C reproduce §4's
      0.843 and 0.645 to within draw scatter, or the discrepancy is explained before the
      other two arms are read
- [ ] The result stated in **seating**, with per-draw spread beside every mean; turn
      reported alongside as context only
- [ ] A render of arm C against arm D at individual-sherd placement, made **before** any
      claim is written
- [ ] The prediction above explicitly marked held or failed
- [ ] Names which of the three: method failed, ruler broken, reference wrong
- [ ] `WEAR_TEST_RESULTS.md` §4 and `intent/O2-valid-evaluation.md` updated with the
      measured cost, and the ⚠️ either downgraded or sharpened

## Limitations to state in the answer, not discover afterwards

- Renormalising sets **every** object to exactly 0.550, which erases the real size
  differences between pots. This is acceptable here because the design is paired and the
  same flattening applies to all four arms — and because training's own ±25% jitter already
  swamped genuine size variation — but it means arms B and D do not describe a model that
  knows how big these pots really are.
- One checkpoint. The result says "this model is insensitive to the size number", not "no
  model could be".
- Six objects. A seating difference of a few points on six pots is a lead, not a finding.

## What would make this not worth running

If the gate fails — if the knob moves anything besides `scales` — stop. The experiment
cannot isolate the conditioning input and nothing downstream of it would mean anything.

Beyond that: the prior from job 30130045 is strong enough that a flat result is the likely
outcome. That is not a reason to skip it. The job is short, it is the last thing standing
between the wear numbers and the wear v3 curriculum, and the outcome that would change the
project's mind is on the table.


---

# Answer — job 30187601, COMPLETED 0:0, 2026-09-07T13:10:19

**Prediction: PARTLY FAILED.** Seating did *not* stay flat on the fresh pots. The
refuting outcome — the wear gap closing once the size is corrected — **did not happen**;
the gap widened instead.

**The controls passed, but only after a correction to how they were read.** Arm A first
appeared to miss §4 by 25 points (0.597 against 0.843). That was my error, not the job's:
**job 29308186 ran 2026-08-17 and the unit-box scoring fix `0d6a85f` landed 2026-09-02**,
so §4's `part_accuracy` is the retired size-dependent score and this job's is the corrected
one — the same field name carrying two different rulers. Scored on §4's own ruler the
controls reproduce: **arm A 0.774 vs §4's 0.843, arm C 0.679 vs §4's 0.645**, both inside
the draw scatter for pots with only two loose sherds.

## What the size input costs, on the corrected ruler

| arm | pots | size told | seated (loose) | draw scatter |
|---|---|---|---|---|
| A fresh, as stored | 6 | 0.321–0.412 | **0.597** | ±15.0 |
| B fresh, at 0.550 | 6 | 0.550 | **0.671** | ±23.3 |
| C worn, as stored | 30 | 0.320–0.413 | **0.560** | ±14.2 |
| D worn, at 0.550 | 30 | 0.550 | **0.544** | ±18.4 |

- **B − A = +7.5 points**, 95% CI over 6 pots **[+0.8, +17.1]**, draw scatter ±19.6
- **D − C = −1.6 points**, 95% CI **[−18.1, +9.5]** — covers zero
- wear gap **A−C = +3.7**, **B−D = +12.7**
- erosion ladder e000→e100: arm C **0.610 → 0.423**, arm D **0.632 → 0.318**

So on fresh pots the correction helps by about seven points, on an interval that barely
clears zero and is a third the width of the draw-to-draw scatter. On worn pots it does
nothing on average. Six pots, one checkpoint: a lead, not a finding.

## The average hides a mixture, and the render is why we know

`D − C` is not a null. It is one genuine collapse, one case where the metric and the eye
disagree, and four pots where nothing visible changed. `artifacts/scale_cost/e100_all_CvD.png`
and `limb3_e100_CvD.png`, drawn before any of this was written:

- **`limb3` is a real collapse.** 1.000 at every wear level in arm C, and 0.600 / 1.000 /
  0.900 / 0.500 / **0.000** in arm D. The picture agrees with the number: arm C rebuilds
  the bone correctly at heaviest wear, arm D drives the condyle into the middle of the
  shaft. This single pot is what cancels the gains elsewhere.
- **`plate` is the disagreement.** The metric says arm D is *worse* (0.560 → 0.460); the
  first-attempt render shows arm D visibly *closer* to a whole plate while arm C has
  fragments flung clear. The render shows one attempt and the metric averages ten, so the
  two can honestly disagree — but it means the plate row should not be quoted on its own.
- **`blue_pot`, `galli_pot`** gained on the metric (+25, +22 at e100) with **no visible
  difference** in the first attempt. **`coxae`, `vert9`** are near-total failures in both
  arms and the pictures show it.

## Which of the three

**The measurement was broken** — twice, and neither time is it the model.

1. §4's headline numbers are on a **retired ruler**. That is not a new error introduced
   here; it is the size-dependent chamfer threshold `0d6a85f` was made to remove, and §4
   was never re-scored afterwards, only re-pooled for the free anchor on 09-05.
2. The size input itself costs the model little that can be separated from draw scatter.
   There is no evidence here of *the method genuinely failing* because of out-of-band
   conditioning.

## What this changes

The `⚠️` on §4 is **replaced, not downgraded**. The out-of-band size is no longer the main
caveat on those numbers — the ruler is. Corrected-ruler baseline levels, measured here at
10 draws: **fresh 0.597, worn sweep 0.560**, against §4's 0.843 and 0.645. The 20-point
fresh-versus-worn gap in §4 becomes **3.7 points** on the corrected ruler.

**The wear effect itself survives**, but it must be read as the ladder, not as that gap:
seating falls **0.610 → 0.423** across the erosion ladder in arm C and **0.632 → 0.318**
in arm D. Both fall; wear still costs seating.

**What is now open, and was not before:** §4's *model comparison* — wear_v1 and wear_v2
against baseline — has never been scored on the corrected ruler. This job re-ran the
baseline only. Wear v3's success criterion is written against 0.843 / 0.645 and cannot
stand as written.

## Acceptance criteria

- [x] CPU gate passed on both datasets before GPU time (`PASS: every compared tensor
      matched to 0.00e+00 (tol 1e-04)`, twice)
- [x] Four arms, one job, one settings set, one job id (30187601); A and C reproduce §4
      once the ruler difference is accounted for, and that discrepancy is explained above
      before the other two arms are read
- [x] Result stated in seating with per-draw spread beside every mean; turn as context only
- [x] Render of arm C against arm D at individual-sherd placement, made before any claim
- [x] Prediction explicitly marked — partly failed
- [x] Names which of the three — the measurement was broken
- [x] `WEAR_TEST_RESULTS.md` §4 and `intent/O2-valid-evaluation.md` updated

## Limitations

- Six pots, one checkpoint, 10 draws. Draw scatter (±15–23 points) is larger than every
  effect measured here except `limb3`'s collapse.
- Renormalising sets every object to exactly 0.550 and erases real size differences
  between pots, as anticipated. Arms B and D do not describe a model that knows how big
  these pots really are.
- The renders show the first attempt only; the metrics average ten.
- The corrected-ruler levels (0.597 / 0.560) come from a 10-draw run and are **not** a
  like-for-like restatement of §4's 3-draw rows; they are a fresh measurement.


---

# Phase 2 — rescore the wear table on the corrected ruler

**Amended 2026-09-07**, because phase 1 answered its own question and opened a larger one
it is not honest to leave in a closing paragraph.

## What phase 1 left broken

Phase 1 rescored the **baseline only** — its arms A and C. So §4 now has corrected
*levels* for one of its three models and none of its *comparisons*. Every ranking in that
table — wear_v1 and wear_v2 against baseline, on all three sets — still rests entirely on
the retired ruler, and those rankings are the whole argument that wear training helps.

This is not a caveat to note. **Nothing currently establishes that wear training does
anything at all**, and wear v3's success criterion is written against 0.843 / 0.645.

## What is being varied

**Nothing.** This is job 29308186 re-run on today's code: the same three checkpoints, the
same three test sets, the same data configs, resolved from **29308186's own saved
`.hydra/overrides.yaml`** rather than from the finetune script (which selects `$BEST` by
mtime and would not necessarily resolve to the same file today).

| model | checkpoint |
|---|---|
| baseline | `checkpoints/bbad_everyday_cka.ckpt` |
| wear_v1 | `output/wear_finetune_28231335/last.ckpt` |
| wear_v2 | `output/wear_finetune_v2_29308186/last.ckpt` |

Three deliberate differences, all stated in the job header:

1. **Today's evaluator.** That is the point of the job.
2. **10 draws, not 3 and 5.** §4's fresh rows rest on three draws and its Juglet rows on
   five. Two of the six pots have only **two loose sherds**, so one flip moves the six-pot
   mean by 17 points — which is how 0.843 came to be quoted to three digits off three
   draws. Ten draws also makes the new rows directly comparable with phase 1's arms A and C.
3. **Clouds saved, images not.** `save_assembly_npz` gives `render_assembly_grid.py`
   everything it needs. Mitsuba was most of phase 1's 16 minutes and can be run afterwards
   on whichever rows turn out to be decision-relevant.

## Two gates, both on the exact failure being repaired

A prose rule did not stop this happening once, so it becomes a check that exits non-zero.

- **Gate 1, before any GPU time:** `git merge-base --is-ancestor 0d6a85f HEAD`. Scoring
  nine runs on a pre-fix checkout would silently reproduce the retired table and read as a
  confirmation.
- **Gate 2, on this job's own first output:** `scripts/check_post_fix_marker.py` asserts
  `part_accuracy_absolute` is present in the result files the job is writing. Gate 1
  checks the source; gate 2 checks the artefact, which is what `readout.py` keys on.

`check_post_fix_marker.py` is new and is the reusable half — it is the gate form of
`readout.py`'s existing `FLAG_PRE_UNIT_BOX`, which worked correctly and was bypassed
because the comparison was made against **a number quoted in a document**. A figure in
prose carries no provenance.

## Stated in advance, so it can fail

**Prediction: the levels all fall, the ranking survives.** The corrected ruler is stricter
and the baseline already fell 0.843 → 0.597, so every row should drop. But wear_v2 should
still lead baseline on the worn sweep by more than the draw-to-draw scatter.

- **If the ranking survives**, the wear programme is intact at corrected levels and wear v3
  can be built, with its criterion rewritten against the new numbers.
- **If the ranking collapses or reverses**, wear training was never shown to help, and the
  entire wear line of work rests on a retired metric. That is the refuting outcome and it
  must be reported.
- **Second, cheaper prediction:** the Juglet ranking will not move either — §4 already says
  wear training does not fix it. If the corrected ruler makes wear_v1/v2 look *better* than
  baseline on the Juglet, that is new information about the one object this project is about.

## Acceptance criteria

- [ ] Both gates pass before the table is read
- [ ] Nine runs, one job, one settings set, one job id
- [ ] Result stated in seating with draw scatter beside every mean; turn as context only
- [ ] Paired model comparisons with intervals, on the fresh set and on the worn sweep
- [ ] The erosion ladder printed per model on the corrected ruler
- [ ] A render of baseline against wear_v2 at individual-sherd placement, made **before**
      any claim is written — clouds are saved for exactly this
- [ ] Both predictions explicitly marked held or failed
- [ ] Names which of the three
- [ ] §4 rewritten with the corrected table; `intent/O2` updated; wear v3's criterion
      restated or explicitly blocked

## Limitations to state in the answer

- Six fresh pots, thirty worn variants of the same six, one Juglet. Draw scatter on these
  objects ran ±15–23 points in phase 1, larger than most effects it measured.
- The Juglet has **no valid archaeological ground truth**. Its rows are scored against the
  conservator's hand assembly and must be quoted that way.
- `wear_v2` is one finetuning run, not a method. A ranking between three checkpoints is
  evidence about these checkpoints.
