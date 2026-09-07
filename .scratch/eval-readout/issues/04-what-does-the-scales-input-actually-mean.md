# 04: What is the number the model is told about the pot's size, and is our warning about it real?

**Type:** `wayfinder:task` (AFK)

**What to build:** A **measured** answer to what value the `scales` conditioning input
takes on the corpus TORA was actually trained on — replacing the value we currently
*derive on paper* and hard-code in three separate files. Either the warning stamped on
the wear table is real, and every fresh and worn-sweep number was produced with the model
told a size it had never been trained on; or the warning is comparing two different
measurements of "size" and is spurious, and the table stands.

**Answers:** O2

**Blocked by:** None. 01–03 are done; this uses `readout.py` as it stands.

**Status:** resolved 2026-09-07, job 30185814 — **the warning is real, the hypothesis
in this ticket was wrong, and the wear comparison survives it.** See Answer.

## Why it exists

The wear verdict — candidate 5 ruled in, the juglet-cause map closed — rests on one
table, `docs/notes/WEAR_TEST_RESULTS.md` §4: the baseline model seats **0.843** of the
loose sherds on fresh pots and **0.645** on the same pots worn. Both of those rows carry
a warning we wrote ourselves and never tested:

> ⚠️ **The fresh and sweep sets were scored at a stored object size of 0.319–0.383, at or
> below the trained floor of 0.375** — a handicap at source, separate from the reading
> error, and untested.

**In plain terms.** TORA is not only shown the sherds. It is also *told how big the pot
is* — a single number per object that is fed into the model at every step of its
reconstruction, not bookkeeping (`tora/modeling/tora.py` passes `scales` into the flow
model; `PointCloudEncodingManager` turns it into a code attached to all 5000 points,
`flow_model/embedding.py:151`). If we scored those runs while telling the model a size
outside anything it saw in training, the model was handicapped before the wear question
was even asked, and the twenty-point drop is not cleanly attributable to wear.

**Which of the three this is about: the measurement was broken** — and the direction is
not yet known. It could equally turn out that our *warning* is the broken measurement.

## What has already been eliminated, by reading the code

**Augmentation is not running at evaluation time.** This was the obvious explanation and
it is wrong. `tora/data/dataset.py:428` multiplies the size by a random 0.75–1.25 only
`if self.random_scale_range is not None`, and `tora/data/datamodule.py` passes
`random_scale_range` **only** to the training dataset (line 152, inside the
`stage == "fit"` branch). The validation dataset in that same branch, the `"validate"`
stage branch, and the `["test", "predict"]` branch all omit it, so
`PointCloudDataset`'s default `None` applies and the jitter is skipped. Evaluation reads
a deterministic size.

## The surviving hypothesis, and why it is plausible

**The observed number and the band it is judged against may be measured on different
things.**

- The **band** `[0.375, 0.625]` is arithmetic, not observation: `0.5 × [0.75, 1.25]`,
  where 0.5 is the *mesh* convention (Breaking Bad objects arrive at max|v| = 0.5) and
  0.75–1.25 is the training jitter. It is hard-coded identically in three places and has
  never been measured through the pipeline — `scripts/readout.py:59-61`
  (`TRAINED_SCALE_BAND`), `scripts/check_scale_conditioning.py:45-47`, and
  `scripts/audit_run_provenance.py:22`.
- The **observed** number is not the mesh's max|v|. `dataset.py:427` computes
  `scale = np.max(np.abs(pts_gt))` on the **sampled 5000-point cloud**, *after*
  `center_pcd` and `_make_y_up`. Points sampled from a surface do not reach the mesh's
  extreme vertex, and re-centering and rotating move the extremes again. That value is
  necessarily **smaller** than 0.5, and by an amount nobody here has measured.

If the training corpus emits, say, ~0.42 through the same pipeline, then the real
trained band is ~[0.315, 0.525] and the worn sweep's 0.319–0.321 sits **inside** it. The
warning is then spurious, the wear table is sound, and three files need their constant
corrected. If the training corpus emits ~0.5 after all, the warning is real and the fresh
and sweep rows must be re-scored before they can carry the map's conclusion.

## How to answer it

Measure, do not derive. `scripts/check_scale_conditioning.py:70` already builds a
`PointCloudDataset` with `random_scale_range=None, disable_augmentation=True,
num_threads=1` — the harness exists.

1. Read the empirical distribution of `scales` over the **training** split of the corpus
   the baseline model was trained on, with augmentation off. Report min / 5th / median /
   95th / max, not just a mean.
2. Multiply by the training jitter `(0.75, 1.25)` to get the band the model was *actually*
   conditioned on, and compare against 0.319–0.383.
3. Do the same read on `real_heldout_norm` and `erosion_sweep` so the fresh and worn rows
   are placed on the same axis as the training distribution.
4. If the band moves, correct all three hard-coded copies **and** re-read
   `WEAR_TEST_RESULTS.md` §4's flags through `readout.py` so the ⚠️ is either removed or
   restated with the right numbers.

CPU only, no GPU — this reads the dataset, it does not run the model. Heavy data is
HPC-side, so it runs on Spartan; every submit gets a laptop-side
`scripts/slurm_poll.sh <JOBID>` per the standing rule.

## Acceptance criteria

- [x] The trained band is **measured** from the training corpus, not derived from the
      mesh convention, and the distribution (not just a point value) is written down
- [x] The fresh, worn-sweep and Juglet rows are placed on that measured axis, and each is
      stated as inside or outside it
- [x] The ⚠️ on `WEAR_TEST_RESULTS.md` §4 is either removed with a reason, or upheld with
      the correct numbers and a statement of what must be re-scored
- [x] Whichever way it lands, all three hard-coded copies of the band agree with the
      measurement (`readout.py`, `check_scale_conditioning.py`, `audit_run_provenance.py`)
- [x] States which of the three: method failed, ruler broken, reference wrong
- [x] `check_intent_links.py` clean

## What would make this not worth pursuing

Nothing yet — it costs a CPU job and it can refute a published conclusion. That is the
cheapest test on the board. It stops being worth pursuing only if the measurement shows
the sweep rows comfortably inside the band, in which case the answer is one line in the
note and the constant fixed.


---

## Answer (2026-09-07, job 30185814 — CPU only, 3.5 minutes, COMPLETED 0:0)

Full write-up: `docs/notes/SCALE_CONDITIONING_MEASURED.md`. Pictures:
`artifacts/scale_band/scale_band.png`, `juglet_layouts_zoom.png`.

### The hypothesis in this ticket was wrong

I expected the pipeline value to come out **below** the mesh convention of 0.5, because
sampled points do not reach the mesh's furthest vertex — which would have made the
band too high and the warning spurious. **It comes out above 0.5.** Re-centring on the
point centroid moves the object off the origin it was normalised about, and that pushes
the extreme coordinate outward by more than the sampling loses.

Measured on 400 of the 35,114 objects in the Breaking Bad `everyday` train split, the
corpus `bbad_everyday_cka.ckpt` was trained on:

| | base `scales`, no jitter |
|---|---|
| min | 0.4929 |
| p5 | 0.5022 |
| median | **0.5446** |
| p95 | 0.6313 |
| max | 0.7116 |

With the 0.75–1.25 jitter the **train split alone** receives, what the model was told
in training spans **0.375 → 0.811**.

**The assumed floor of 0.375 is correct to 0.0001** (measured minimum 0.3751) — and
correct by luck, two errors cancelling. **The assumed ceiling of 0.625 was wrong**; the
real ceiling is 0.811. Nothing load-bearing was flagged high, so no published number
moves, but all three hard-coded copies are corrected.

### So the warning is real

| object | `scales` | where it sits in training |
|---|---|---|
| `plate` | 0.3210 | **below everything training showed** |
| `coxae` | 0.3324 | **below everything training showed** |
| `vert9` | 0.3804 | lowest 0.2% |
| `galli_pot` | 0.3848 | lowest 0.5% |
| `limb3` | 0.4094 | lowest 4.3% |
| `blue_pot` | 0.4096 | lowest 4.3% |

Every real pot we score is presented to the model as an unusually small object, and two
of them as smaller than anything it has ever seen.

### And the wear comparison survives it

`scales` is held fixed across the erosion ladder — largest within-pot drift **2.0%**
from e000 to e100 (`vert9`), most under 1.3% — and the fresh held-out set matches the
sweep's own unworn variants to within 0.9% per object. So 0.843 fresh against 0.645 worn
is a **paired** comparison carrying an identical handicap on both sides. A constant
offset cannot open a twenty-point gap.

What it does mean: **both numbers are depressed**, and the wear result is a lower bound
measured on a handicapped model.

### The harness was validated against the runs it audits

It reproduces the `scales` that job 29308186 saved itself, object by object, to within
0.05–0.8% (`blue_pot` 0.4096 vs 0.4101; `plate` 0.3210 vs 0.3194; the Juglet 0.5114 vs
0.5114 exactly), and independently reproduces `readout.py`'s already-recorded 0.041 for
`juglet_norm`.

### Side finding, rendered before being reported

`juglet_norm.hdf5` hands the model **0.0408**, eleven times below the floor, while
`juglet_gt.hdf5` — which §4 uses — hands it 0.5114. Both store max|v| = 0.5 and both
hold the same nine sherds in the same arrangement. `juglet_norm` was normalised about an
origin the pot sits **0.48** away from, so the 0.5 is almost entirely the offset and the
division shrank the pot to a tenth of its intended size. §4's Juglet rows are sound;
the *earlier* normalised-Juglet evaluations were not.

### Which of the three

**The measurement was broken** — one of our own constants, in the ceiling rather than
the floor, and the flag it produced on the floor was right. Not the model, not the
reference.

### What this hands forward

One well-posed GPU experiment: re-run the erosion sweep with the objects rescaled so
`scales` lands near 0.55, the middle of the measured band. If both the fresh and worn
seating figures rise together, the wear finding is confirmed at full strength; if the gap
closes, part of it was an artefact of scoring a handicapped model. This should happen
**before** the wear v3 curriculum, whose evaluation protocol already requires "stored
object size inside the trained band" and now knows what that means.
