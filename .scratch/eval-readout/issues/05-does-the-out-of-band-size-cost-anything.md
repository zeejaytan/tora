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

**Status:** ready-for-agent

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
