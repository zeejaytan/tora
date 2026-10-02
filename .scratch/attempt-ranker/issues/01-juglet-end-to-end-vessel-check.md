# 01: First run end to end: the Juglet, with the vessel check only

**What to build:** GARF's 1,400 Juglet attempts ranked without the answer key, using
only Layer 1 (does it form a vessel), with the rank of the 2 genuine full reassemblies
reported against random choice. This is the thinnest complete path: converter → attempt
bundles → ranker → report, run on Spartan. See `../spec.md`.

**Answers:** U17

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Converter turns one GARF evaluation run's rigid ("solid") attempts plus the Juglet's
      full-detail sherds into one bundle per attempt, each moved to a random position; the
      id-to-attempt map is a separate file only the report reads
- [ ] Converter's own check: a genuine attempt re-posed and scored with `own_place.py`
      comes back 9 own place, 9 right way round
- [ ] Ranker Layer 1: axis fit and wall-profile deviation in mm (7 mm bins), inside-out
      sherds (reuse `check_inside_out.py`'s test); attempts failing either go to the bottom
- [ ] Test: the same bundle under two random moves gives the same scores
- [ ] Test: the ranker runs with reference files unreadable and its output is unchanged;
      any attempt to open one fails the test
- [ ] Pre-registration file (all cut-offs in mm and degrees) committed **before** the
      labelled run; the report prints its commit hash
- [ ] Spartan CPU batch job ranks all 1,400 attempts; laptop-side poll; final sacct
      State/ExitCode recorded here
- [ ] Report: rank of each genuine attempt, whether one is in the top 5, random baseline
      (~0.7%), how many attempts Layer 1 drops, and where the 19 near-misses land
