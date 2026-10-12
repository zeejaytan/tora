# 03: Robustness side-checks

**What to build:** evidence that the Juglet ranking judges the reassembly, not the point
sampling or the level of detail, with agreement across attempts reported beside it.

**Answers:** U17

**Blocked by:** 02

**Working in:** tora `scripts/l2_measure.py` (`--seed`), `scripts/u17_redraw.py`, `scripts/hpc/u17_redraw.slurm`

**Status:** ready-for-agent

- [ ] The same ranking run on the coarse 5,000-point attempt cloud; genuine ranks compared
      with the full-detail run
- [x] Re-drawn point sample: overlap of the two top-5 lists reported (U17's refute
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
- 32803836 `u17_redraw.slurm` (c11c059) — COMPLETED 0:0, 45 s, run by the Spartan
  workspace thread; log in the project's shared folder (`u17_redraw_32803836.log`).
  - Control: seed 3 re-run reproduces the original top 5 exactly (score is repeatable).
  - **Verdict: WEAKENED** (pre-registered rule; not refuted, not passed).

    | draw | top 5 kept | genuine ranks | top-5 hit | worst-gap change, mm (median / 90% / max) |
    |---|---|---|---|---|
    | original (seed 3) | - | 1, 13 | yes | - |
    | seed 11 | 4 of 5 | 2, 18 | yes | 0.13 / 0.45 / 2.02 |
    | seed 12 | 4 of 5 | 3, 26 | yes | 0.15 / 0.49 / 1.51 |
    | seed 13 | 2 of 5 | 1, 8 | yes | 0.13 / 0.46 / 2.05 |

  - Read: a new draw moves an attempt's worst-sherd gap by about 0.13 mm typically and
    up to 2 mm, against rank 1's 0.027 mm lead. So the order inside the top 5 is set
    partly by the draw (prediction held: rank 1 changed in 2 of 3 draws). The confirmed
    correct reassembly stayed in the top 3 in every draw, so a conservator shown the top
    5 would still have received it each time (better than predicted). Named: a
    measurement of limited resolution, not a method failure. Weight: one pot, three draws.
  - Side read (same job): the inside-out rule from juglet-cause 14 flags no sherd in any of
    the Juglet's top 5, so sherd 7 in picks 2-5 (turned 173-177°) is spun end for end with
    its outer face still outward, which that rule cannot see (ticket 14: "nothing
    reference-free here can yet").
