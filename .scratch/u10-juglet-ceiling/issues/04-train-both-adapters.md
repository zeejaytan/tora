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
