# 03: Robustness side-checks

**What to build:** evidence that the Juglet ranking judges the reassembly, not the point
sampling or the level of detail, with agreement across attempts reported beside it.

**Answers:** U17

**Blocked by:** 02

**Working in:** tora `scripts/l2_measure.py` (`--seed`), `scripts/u17_redraw.py`, `scripts/hpc/u17_redraw.slurm`

**Status:** ready-for-agent

- [ ] The same ranking run on the coarse 5,000-point attempt cloud; genuine ranks compared
      with the full-detail run
- [ ] Re-drawn point sample: overlap of the two top-5 lists reported (U17's refute
      condition: a top 5 that changes completely ranks the sampling)
- [ ] Layer 3: how often each pair of sherds sits side by side across all attempts;
      reported alone, never used in the rank; where the genuine attempts' arrangement sits
      in it

## Log

- 2026-10-12: the conservator asked for the re-draw first (the refute condition); the
  coarse-cloud run and Layer 3 stay open. Layer 1 reads mesh vertices and has no random
  step, so only Layer 2's point draw is changed: `l2_measure.py --seed`, three new draws
  (11, 12, 13) and a same-seed control (3). Pre-registration
  `../preregistration-redraw.md`, committed before any re-drawn score; prediction written
  there: rank 1's 0.027 mm lead likely does not survive every draw. Job
  `scripts/hpc/u17_redraw.slurm`.
