# 01: Can the right Juglet arrangement be picked out of TORA's own attempts?

**What to build:** nothing new; this records an exploration run 2026-09-21 on the 20
saved baseline draws (job 30130049, `artifacts/jugdraw/jugdraw_baseline_30130049/`),
asking whether any check that needs no answer key can tell TORA's right placements from
its wrong ones on the Juglet. Scripts in `scripts/` beside this folder (throwaway, run
from `tora/`, scored with `scripts/own_place.py`: a sherd is "home" within 7.1% of pot
size, ~4.6 mm on the 65 mm Juglet).

**Answers:** O9

**Blocked by:** none

**Status:** ready-for-human — analyses done; only the write-back to O9 remains, held until
the other session commits O9

## Base rate

Per-sherd home counts over 20 draws, sherd 0 held: [20,15,3,4,2,2,0,14,0]. Of the 160
non-held placements, 40 are home (**25%**). Any filter must beat 25% on what it keeps.

## Findings

1. **Holding several sherds.** TORA's sampler can clamp any set of parts, but the model
   trained with exactly one held sherd (the largest; `multi_anchor` false everywhere).
   More than one is out of distribution. Not run.
2. **Agreement across draws does not mark correctness.** Where the 20 draws agree most,
   they agree on the wrong place for 4 and 6 (16/20 and 18/20 agree, modal placement
   11-16% of pot size off home). Consistency = systematic, not right.
   `artifacts/u10/consistency_baseline_30130049.json`, `consistency_modal_placements.png`.
3. **SARe-style geometric check (reimplemented; SARe has no code).** Keep pairs whose
   break faces touch and do not interpenetrate, keep the group joined to the held sherd.
   With break-face labels taken from the answer key (better than SARe's learned head could
   do) and at 1, 2, 3 mm: kept sherds home **25-28%**, i.e. chance. Without labels 25-26%.
   The strictest setting reached ~55% but kept few sherds, and large groups chain in snug
   but wrong lower-body sherds (draw 14). Measurement caveat: 5000 points per pot is coarse
   for a 1 mm contact test. `artifacts/u10/verify_{1,2,3}.0mm.json`, `verify_kept_groups.png`.
4. **More draws will not help.** The errors repeat (finding 2), so a filter at chance
   level keeps as many wrong as right no matter how many draws feed it.
5. **A correct foundation does not pull the rest in.** Draws with {0,1,7} all home
   (13/20) placed 0.46 of the other six home vs 0.71 in draws without it: no benefit.
6. **What predicts a good placement is touching the held sherd.** Sherds 1 and 7 share
   the longest edge with sherd 0 (41%, 48% of their break edge); 4, 5, 6 share none.
   Across the 8 Fractura ceramics (CERAMARM 30337242, baseline arm): sherds touching the held sherd
   home 0.61 vs 0.28, holding within small and medium size bands.
   `artifacts/u10/why_1_and_7.png`, `anchorcontact_ceramarm*.npy`. Correlational; the
   causal test is `.scratch/anchor-choice/issues/01-which-sherd-is-fixed.md` (job 30917498).

## What it means for O9

On the Juglet, selection among draws is not the fix: TORA's errors are systematic, and
the only reference-free check tried (SARe-style contact) is at chance. This is one pot,
20 draws, a point cloud at 5000 points: it bears "not on this object with this check",
not "selection never works". O9's seam-closure selector is untested here and is a
different criterion.

- [x] Base rate stated
- [x] Consistency, SARe-style check, foundation and contact analyses run and rendered
- [ ] Written back to O9 (O9 is currently another session's uncommitted file; do it
      once that lands)
