# 10: A turn limit in the answer key's "right way round"

**What to build:** "right way round" also requires a sherd to be turned less than 90° from
home, then every labelled attempt re-labelled and everything that read the labels re-read.

**Answers:** U17

**Working in:** tora `scripts/own_place.py` (`TURN_LIMIT_DEG`), `scripts/label_attempts.py`,
`scripts/u17_relabel_diff.py`, `scripts/hpc/u17_relabel.slurm`

**Blocked by:** 09

**Status:** ready-for-agent

Why: on TORA narrow_bottle3 pick 3 the green sherd is turned 163.5° yet its points sit
6.36 mm from home on average, under the 7.07 mm limit, so the key called it right way
round; the conservator saw it inside out (ticket 09). **Reference answer wrong.** The
offset limit stays as it was; the turn limit is added beside it. 90° sits in the empty
60-120° gap of attempts' turns (juglet-cause 14), so its exact value moves nothing that
is not half-turned. The Juglet's purple case (ticket 07: offset limit flagging a 13-15°
turn the eye calls fine) is the offset limit erring the other way and is not changed here.

- [x] `own_place.py`: `oriented` adds turn < 90°; `oriented_point` keeps the old count;
      self-test adds a thin sherd flipped over its long axis (offset passes, turn 180°,
      now counted out); all checks pass
- [ ] Re-label GARF Fractura (70 runs), TORA Fractura (28 runs), GARF Juglet (70 runs);
      the offset-only count must reproduce the old label files exactly
- [ ] Per pot: genuine and near-miss counts before and after, and which attempts moved
- [ ] Re-read with the new labels, cut-offs unchanged: the calibration's genuine
      percentiles (does the profile cut-off move?), the GARF and TORA tests
- [ ] Every number in U17 and tickets 05-09 that rests on a moved label is marked

**Prediction, written before the run.** Few labels move: a half-turn that keeps the
offset under 7% of pot needs a long thin sherd. TORA narrow_bottle3 loses at least one
genuine (pick 3). The Juglet's 2 genuine / 19 near-miss stay. The profile cut-off can only
fall or stay (fewer genuine attempts), by little.

## Log
