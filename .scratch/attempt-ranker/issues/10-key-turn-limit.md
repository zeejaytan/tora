# 10: A turn limit in the answer key's "right way round"

**What to build:** "right way round" also requires a sherd to be turned less than 90° from
home, then every labelled attempt re-labelled and everything that read the labels re-read.

**Answers:** U17

**Working in:** tora `scripts/own_place.py` (`TURN_LIMIT_DEG`), `scripts/label_attempts.py`,
`scripts/u17_relabel_diff.py`, `scripts/hpc/u17_relabel.slurm`

**Blocked by:** 09

**Status:** resolved (2026-10-12): moves labels only where a small or thin sherd was half-turned; ranker cut-offs unchanged

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
- [x] Re-label GARF Fractura (70 runs), TORA Fractura (28 runs), GARF Juglet (70 runs);
      the offset-only count must reproduce the old label files exactly
- [x] Per pot: genuine and near-miss counts before and after, and which attempts moved
- [x] Re-read with the new labels, cut-offs unchanged: the calibration's genuine
      percentiles (does the profile cut-off move?), the GARF and TORA tests
- [x] Every number in U17 and tickets 05-09 that rests on a moved label is marked

**Prediction, written before the run.** Few labels move: a half-turn that keeps the
offset under 7% of pot needs a long thin sherd. TORA narrow_bottle3 loses at least one
genuine (pick 3). The Juglet's 2 genuine / 19 near-miss stay. The profile cut-off can only
fall or stay (fewer genuine attempts), by little.

## Log
- 32806074 `u17_relabel.slurm` (1da2be7) — COMPLETED 0:0, by the Spartan workspace thread;
  log in the shared folder (`u17_relabel_32806074.log`). Offset-only labels reproduce both
  old label files exactly (11,200 GARF, 4,480 TORA attempts).
  - **Moved:** GARF plate genuine 741 -> 235 (506 attempts now near-miss); TORA plate 5 -> 0;
    TORA narrow_bottle3 9 -> 7 (pick 3 of ticket 09 among them). Nothing else moved on any
    pot, GARF or TORA; the Juglet stays 2 genuine / 19 near-miss.
  - Not yet looked at: which plate sherd the 506 turn on (the plate's floor sherds are 1%
    and 3% of the pot, where a half-turn barely moves the points). Until looked at, the
    plate's labels rest on the turn reading of a tiny sherd.
  - **Cut-offs:** Layer 1 profile 0.87% of pot (unchanged; plate's q99 0.80); Layer 2
    "unfixable" 2.31 -> 1.57% (reported only, not in the order). The ranker does not change.
  - **Tests re-read:** GARF narrow_bottle3 and galli_pot unchanged (top 5 all genuine, best
    rank 1). TORA narrow_bottle3: top 5 now reads genuine, genuine, near, near, genuine, the
    same as the conservator's blind look. TORA plate: no genuine attempt left, so it is no
    longer a test pot (it was a miss; now there is nothing to find).
- [x] Marked in U17 (2026-10-12).

