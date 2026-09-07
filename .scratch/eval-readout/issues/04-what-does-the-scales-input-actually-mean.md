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

**Status:** ready-for-agent

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

- [ ] The trained band is **measured** from the training corpus, not derived from the
      mesh convention, and the distribution (not just a point value) is written down
- [ ] The fresh, worn-sweep and Juglet rows are placed on that measured axis, and each is
      stated as inside or outside it
- [ ] The ⚠️ on `WEAR_TEST_RESULTS.md` §4 is either removed with a reason, or upheld with
      the correct numbers and a statement of what must be re-scored
- [ ] Whichever way it lands, all three hard-coded copies of the band agree with the
      measurement (`readout.py`, `check_scale_conditioning.py`, `audit_run_provenance.py`)
- [ ] States which of the three: method failed, ruler broken, reference wrong
- [ ] `check_intent_links.py` clean

## What would make this not worth pursuing

Nothing yet — it costs a CPU job and it can refute a published conclusion. That is the
cheapest test on the board. It stops being worth pursuing only if the measurement shows
the sweep rows comfortably inside the band, in which case the answer is one line in the
note and the constant fixed.
