# 02: Hold one sherd in each half and see whether both halves come right

**What to build:** `+data.anchor_part` accepts a list (test-only; each held sherd
treated as the single one is: true orientation in, pinned by the sampler). Juglet,
untouched baseline model, 20 draws each: held {0} (in-job control), {0,6} (neck +
base), {0,4} (neck + lower body). Score own-place per sherd, render the median draw
per arm. Job: `scripts/hpc/juglet_two_held.slurm`.

**Answers:** O8

**Blocked by:** none

**Status:** done

**Why:** ticket 01 showed which half comes right is caused by which sherd is held,
never both halves. The halves share long breaks (0-3, 1-5, 7-4), so it is not lack of
contact. Test: is each half failing only for want of a fixed reference?

**Predictions, written before the run (2026-09-21):**

- **Reference is what's missing:** with {0,6} and {0,4}, upper (1, 7) AND lower
  (3, 4/6, 5) sherds go home together, most draws; non-held home rises well above
  the {0} control. If 2 and 8 also come right -> the failure was carrying placement
  across the pot. If they stay wrong -> they are a separate problem (8 smallest,
  2 borders the missing piece).
- **Not the reference:** one half still fails with a sherd held in it -> something
  about that half itself, not the lack of a fixed point.
- **Inconclusive:** everything drops below the {0} control -> two held sherds are out
  of distribution for this model (trained with one), not a statement about the pot.
- Both held sherds must sit at 0.000% offset in every draw, or the override failed.

- [x] Job run, final sacct State/ExitCode recorded -- job 30919372, `COMPLETED|0:0`,
      4 min 49 s, ended 2026-09-21 21:04 (laptop poll died early twice; state read
      from `sacct` directly)
- [x] Both held sherds at home in every draw -- worst held offset 0.000% in all three arms
- [x] Per-sherd home counts, three arms
- [x] Median draw per arm rendered and looked at before any verdict; best draw of {0,6}
      rendered separately because it is the headline
- [x] Verdict against the predictions, written back to O8

## Result (2026-09-24)

Attempts out of 20 in which each sherd went home (own-place, SEAT_PCT 7.1% of pot size,
about 4.6 mm):

| held | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | not-held home | best attempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| {0} control | held | 20 | 1 | 4 | 0 | 5 | 0 | 19 | 0 | 49/160 (31%) | 4 of 8 |
| {0,6} neck + base | held | 20 | 6 | 16 | 18 | 16 | held | **7** | 7 | **90/140 (64%)** | **7 of 7** |
| {0,4} neck + lower body | held | 17 | 4 | 0 | held | 8 | 10 | 18 | 0 | 57/140 (41%) | 5 of 7 |

Median attempt: {0} 3/9 home, {0,6} 6/9, {0,4} 5/9 (counting held sherds).

**Against the predictions:**

- **Reference is what's missing: supported for the lower half, with the base.** With neck
  and base held, 3, 4 and 5 go home 16-18 of 20 (control: 4, 0, 5). Not-held placements
  roughly double. One attempt (attempt 4) put all seven free sherds home -- the only
  whole-Juglet attempt on record here.
- **But it is not "both halves together".** Sherd 7 (upper body, touches the neck) fell
  from 19 to 7 of 20 once the base was also held. The shift of 12 is beyond the ~5-in-20
  run-to-run noise. Holding more does not simply add; something is traded.
- **2 and 8 improve but stay mostly wrong** (1 -> 6, 0 -> 7 of 20). They remain a
  separate problem, as predicted if they did not come right.
- **Sherd 4 is a weaker second reference than the base** (41% vs 64%): 3 never comes home
  with 4 held, 6 only 10 of 20.
- **Not out of distribution:** both two-held arms beat the control, so two held sherds did
  not break the model trained with one.

**Best attempt of {0,6}, per-sherd offset (% of pot size, ~mm):** 1: 2.0 (1.3),
2: 4.9 (3.2), 3: 1.3 (0.8), 4: 5.6 (3.7), 5: 2.1 (1.3), 7: 7.0 (4.5), 8: 2.2 (1.4).
Sherd 7 sits right at the 7.1% edge. The whole-pot render reads as a closed juglet, but
that view cannot resolve a 3-5 mm miss; it needs the conservator's eye at a join-level
view before it is called a correct reassembly.

**Which of the three:** the method, given a correct reference in each half, places most
of the lower body -- not a measurement fault (held sherds exactly at 0.000%; same ruler as
ticket 01) and the Juglet answer key is the validated one. The held sherds come **from
the answer key**; in use a person would seat them.

**Weight:** one pot, one job, 20 attempts per arm. The 31% -> 64% rise is far beyond
noise; the single all-home attempt is one of 20 and cannot be picked out without the
answer key (the draw filters tried are at chance, `.scratch/juglet-draw-selection/`).

Render: `artifacts/twoheld/two_held_30919372.png` (median per arm),
`artifacts/twoheld/two_held_best_30919372.png` (best {0,6}). Scripts:
`.scratch/anchor-choice/scripts/twoheld.py`, `render_twoheld.py`, `render_best.py`.
