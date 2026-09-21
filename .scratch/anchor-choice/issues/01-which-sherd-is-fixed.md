# 01: Move the fixed sherd and see whether good placements follow it

**What to build:** Juglet, untouched baseline model, 20 draws each with the held
(anchor) sherd set to 0 (default), 6 (the base) and 4 (lower body), via the new
test-only `+data.anchor_part` override. Score each sherd by own-place (home within
7.1% of pot size, ~4.6 mm) and render one representative draw per arm.
Job: `scripts/hpc/juglet_anchor_choice.slurm`.

**Answers:** O8

**Blocked by:** none

**Status:** ready-for-agent

**Why:** on baseline job 30130049 the sherds sharing the longest break edge with the
held sherd (1, 7) went home 15/20 and 14/20; sherds not touching it (4, 5, 6) 0-2/20.
Fractura shows the same pattern within size bands (0.61 vs 0.28). All correlational.
If contact with the held sherd is the mechanism, moving the held sherd moves the
good placements.

**Predictions, written before the run (2026-09-21):**

- anchor0 reproduces 30130049 home counts [20,15,3,4,2,2,0,14,0] (same seed). If
  not, the other arms are compared against the new anchor0, not the old job.
- **Supported:** anchor6 -> sherds 3, 4, 5, 8 rise above their anchor0 counts
  together, while 1 and 7 fall. anchor4 -> 2, 5, 6, 7 rise. Both arms must show it.
- **Refuted:** the neighbours of the new held sherd do no better than before, and
  1 and 7 stay high -> something about 1 and 7 themselves (shape, size, position on
  the pot), not contact, makes them easy.
- **Inconclusive:** every sherd drops in anchor6 and anchor4. The model only trained
  with the largest sherd held; a small held sherd is out of distribution and a
  general collapse says that, not anything about contact.

- [ ] Job run, final sacct State/ExitCode recorded here
- [ ] anchor0 reproduction checked
- [ ] Per-sherd home counts, three arms, table
- [ ] One draw per arm rendered and looked at before any verdict
- [ ] Verdict against the predictions above, written back to O8
