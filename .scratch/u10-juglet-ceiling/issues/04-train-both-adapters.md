# 04: Train both adapters

**What to build:** The ceiling adapter and the generic adapter, trained from the same
untouched model on equal numbers of breakages, for the same number of passes. After each
pass, each adapter is scored on its own 5 choosing vessels with the own-place count, and
the best pass is kept. The Juglet is never used to choose.

Spec: the umbrella `.scratch/u10-juglet-ceiling/spec.md`, module 7.

**Answers:** U10

**Blocked by:**
- CSC `u10-juglet-ceiling` 04 (both arms broken);
- 01 (the own-place scorer);
- 02 (writer and audit);
- 03 (the gate).

**Status:** ready-for-agent (run plan amended 2026-09-24)

- [x] Both arms' training files are written, and the audit passes on each; the recipe
      hash matches CSC ticket 03. (Ticket 02, 2026-09-21: 0 failures on 885 breakages,
      hash 422081368edc…f424.)
- [ ] Wear v3's recipe:
      - rank 128, alpha 256, dropout 0.1;
      - the four attention projections in all six blocks;
      - learning rate 2e-5;
      - head frozen.

      Same number of passes for both arms: 20, as wear v3. A pass is one real pass over
      the 349: the data config sets `min_dataset_size` at or below 349. The loader's
      default (2000) would repeat the file about six times and call that one pass, and
      "the best is pass 0" would then mean something different from wear v3's.
- [ ] Choosing uses the own-place count on the choosing vessels, never the count that
      allows swaps (conservator, 2026-09-14).
- [ ] Every pass's choosing score is reported per arm, the kept pass is named, and the
      ticket says plainly if the best is pass 0 or 1. Wear v3 peaked at pass 0.
- [ ] The ticket 03 gates pass on both trained adapters.
- [ ] Every `sbatch` has a laptop-side poll. The final `sacct` State/ExitCode and the GPU
      hours are recorded here.
- [ ] Written back: U10 gets a line with each arm's kept pass and choosing score, and the
      date.

## How it runs on Spartan (amended 2026-09-24)

The conservator asked for no long queue waits, and a held allocation for the debugging at
the start. What the sizes are, measured rather than guessed:
- Wear v3's whole job took **1 h 14 min** on one A100 (job 29880370). That covers the
  smoke test, 20 passes over 1,169 examples with validation every pass, and 12
  evaluation runs.
- Each U10 arm trains on **349** examples, under a third as many.
- 20 Juglet draws took **under 5 min** (job 30130049).
- So no step here needs the 7-day `gpu-a100` partition. Everything fits
  `gpu-a100-short` (4 h wall, `docs/agents/slurm.md`).

- **Debugged first in ticket 03's held allocation.** One full epoch of each arm, the
  own-place score on the choosing set printed, and time and memory read off. No training
  job is submitted until that has worked once.
- **Then each arm is its own job**, `gpu-a100-short`, the two submitted together and
  independent, so they can run side by side on the partition's two nodes. Each job runs
  the freeze test, reversibility check, training and strict diff. It stops before saving
  anything as "kept" if the diff fails.
- **Sized from the held-allocation epoch, not from this estimate.** The wall is set to
  about twice the measured 20 passes. If that exceeds 4 h, the run is split into
  consecutive jobs chained `afterok`. `train.py` resumes from `last.ckpt` in its output
  folder (`train.py:52-74`, `ckpt_path: ${log_dir}/last.ckpt`), so a split run is the
  same run. The choosing score is then read over the whole chain, not per job.
- **If ticket 03's session still has hours on it**, the two arms train there back to
  back instead, with no queue at all.
- Each job carries the `job_status.log` exit trap, and each gets its own laptop-side
  poll.

## Progress (2026-09-24)

Both arms trained back to back in ticket 03's holder **31200602**, with no queue.

**Ceiling** (`TORA/output/u10_train_ceiling_31200602_163555/`, 16:35–17:16 AEST, 20 passes,
exit 0). Kept: **`epoch-0.ckpt`**, the first pass. Strict diff PASS on it: only the 48
adapter tensors differ from the untouched model.

Choosing score per pass (share of sherds in their own place on the 5 choosing vessels,
solid sherds):

| pass | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| own place | **.893** | .893 | .881 | .870 | .787 | .769 | .794 | .803 | .804 | .816 | .790 | .815 | .818 | .825 | .817 | .822 | .829 | .809 | .822 | .815 |
| part acc | .931 | .923 | .918 | .856 | .832 | .855 | .860 | .856 | .868 | .861 | .875 | .873 | .888 | .881 | .883 | .888 | .870 | .877 | .886 | .870 |

Training made the choosing score **worse**: from 89% after the first pass to 77% by the
sixth, with a partial recovery to about 82%. The kept model has had one pass at lr 2e-5,
so it is close to the untouched model. How close cannot be read yet, because the untouched
model's score on these 5 vessels was never measured. That is the `baseline` step
(tora `8b6a4c0`), queued in the same holder after the generic run.

Weight: 5 choosing vessels, one training run, and one draw per vessel per pass. A few
points of movement between passes is within noise. The fall from .89 to .77 is not.

**Generic** (`TORA/output/u10_train_generic_31200602_171624/`, 17:16–17:48 AEST, 20 passes,
exit 0). Kept: **`epoch-1.ckpt`**. Strict diff PASS.

| pass | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| own place | .944 | **.949** | .940 | .940 | .928 | .896 | .906 | .889 | .897 | .912 | .893 | .910 | .910 | .905 | .892 | .906 | .899 | .894 | .895 | .912 |
| part acc | .969 | .966 | .961 | .960 | .951 | .937 | .932 | .913 | .925 | .948 | .925 | .936 | .932 | .929 | .919 | .923 | .921 | .915 | .928 | .926 |

**The untouched model on the same choosing sets** (`baseline` step, lr 0, strict PASS so
nothing moved):

| arm's choosing set | untouched | best adapter pass | last pass (19) |
|---|---|---|---|
| ceiling | **.897** | .893 (pass 0) | .815 |
| generic | **.958** | .949 (pass 1) | .912 |

**Reading.** Neither adapter beats the untouched model on its own choosing vessels, at any
pass. Training at lr 2e-5 makes both worse, and the damage is visible from about pass 4.
The kept adapters are the least-trained ones, so they are close to the untouched model.

What this does and does not show:
- It does **not** show the method failed on the Juglet. The choosing vessels are synthetic
  fresh breaks, where the untouched model already seats 90–96% of sherds. The Juglet seats
  3 of 9. There is almost no room on the choosing set for an adapter to show a gain, so
  choosing on it selects "changed least". The choosing ruler may be blind to the thing U10
  is testing (a measurement problem, not yet a method failure).
- It **does** show that on vessels like the training ones, 20 passes at lr 2e-5 hurt. That
  is the method on in-distribution data, and it is real at this weight: 5 vessels, one
  run, one draw per pass, a fall of 5–13 points against a pass-to-pass noise of about 2.

Ticket 05 as written would compare the untouched model with two near-copies of it. Held
for the conservator's decision before any Juglet run.
