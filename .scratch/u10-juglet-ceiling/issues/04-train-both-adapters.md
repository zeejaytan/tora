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

**Status:** ready-for-agent

- [ ] Both arms' training files are written, and the audit passes on each; the recipe
      hash matches CSC ticket 03.
- [ ] Wear v3's recipe:
      - rank 128, alpha 256, dropout 0.1;
      - the four attention projections in all six blocks;
      - learning rate 2e-5;
      - head frozen.

      Same number of passes for both arms.
- [ ] Choosing uses the own-place count on the choosing vessels, never the count that
      allows swaps (conservator, 2026-09-14).
- [ ] Every pass's choosing score is reported per arm, the kept pass is named, and the
      ticket says plainly if the best is pass 0 or 1. Wear v3 peaked at pass 0.
- [ ] The ticket 03 gates pass on both trained adapters.
- [ ] Every `sbatch` has a laptop-side poll. The final `sacct` State/ExitCode and the GPU
      hours are recorded here.
- [ ] Written back: U10 gets a line with each arm's kept pass and choosing score, and the
      date.
