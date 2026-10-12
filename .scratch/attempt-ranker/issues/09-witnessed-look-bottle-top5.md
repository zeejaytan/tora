# 09: Witnessed look at a bottle's top 5 (TORA narrow_bottle3)

**What to build:** the conservator's blind verdict on the 5 attempts the ranker would show
for a held-out pot, done as ticket 07 did the Juglet: so U17's "a conservator shown the top
5 gets a correct reassembly" rests on more than the development pot.

**Answers:** U17

**Needs-eye:** TORA narrow_bottle3's top 5, staged as five singles from
`visual-qa/viewer/pairs/u17_nb3_tora_top{1..5}.json`; closes on a witnessed look plus a
conservator note, never on numbers alone.

**Working in:** tora `scripts/u17_top5_export.py`, `scripts/hpc/u17_redraw.slurm`; visual-qa
pair descs

**Blocked by:** 06

**Status:** resolved (2026-10-12): eye and key agree on 4 of 5; on pick 3 the eye is right and the key is wrong

Why this pot: held out of calibration, TORA's attempts (560), and the key's top 5 is not
all one class, so the look can disagree with it. GARF's narrow_bottle3 top 20 are all
genuine by the key, which a look could only confirm.

- [x] Export (blind, no labels read) to Spartan `TORA/rank_u17/nb3_tora_top5/`, in the
      job of ticket 03's re-draw
- [x] The visual-qa-helper stages the five descs; gates pass
- [x] Pass 1, blind: the conservator's verdict per pick recorded before any label is read
- [x] Unblind: key labels and per-sherd turn angles (`scripts/u17_top5_turns.py`) beside
      each verdict; every disagreement named as method, measurement or reference
- [x] Every note gets a same-round agent reply

## Log

- 2026-10-12: five blind `single:` descs written (scale nominal: Fractura has no real
  size, longest side set to 100 mm). Export rides in `u17_redraw.slurm`.
- 32803836 `u17_redraw.slurm` — COMPLETED 0:0; export in `TORA/rank_u17/nb3_tora_top5/`
  (picks by id: 51a92f23c7564bb8, be55b677ac63a1bb, 5e4c97cb5048a8f9, b014d3a12f41949d,
  f980ae8058546941). Staged by the Spartan workspace thread, share link 2026-10-12; gates
  passed (two unrelated loader gates fail on retired sample manifests).
- **Blind verdicts, conservator, 2026-10-12 15:42, recorded before any label was read**
  (colours: blue 0, orange 1, green 2, red 3):
  1. "looks like good assembly"
  2. "looks fine too"
  3. "green sherd is inside out"
  4. "same with 4" (green sherd inside out)
  5. "looks have more overlap but position and rotation all looks fine"
- **Unblinded** (Spartan workspace thread, 2026-10-12 15:44, `u17_top5_turns.py`, ranks.json,
  test.json of 32330575). Right-way limit 7.07 mm (SEAT_PCT, nominal 100 mm pot).

  | pick | eye (blind) | key class | green (sherd 2) turn, offset | inside-out rule |
  |---|---|---|---|---|
  | 1 | good | genuine | 8.5°, 3.53 mm | none |
  | 2 | fine | genuine | 7.5°, 3.90 mm | none |
  | 3 | green inside out | **genuine** | **163.5°, 6.36 mm** | **[2]** |
  | 4 | green inside out | near-miss | 177.6°, 7.45 mm | [2] |
  | 5 | more overlap, placement fine | genuine | 10.0°, 2.87 mm | none |

  Other sherds 0.0-5.0°, 0.01-2.96 mm in every pick. All five pass Layer 1.
- **Read.** Eye and key agree on picks 1, 2, 4, 5. On pick 3 they disagree and the eye is
  right: green is turned 163.5°, yet its points sit 6.36 mm from home on average, under the
  7.07 mm limit, so the key counts it right way round. **Named: the reference answer was
  wrong** (the key's right-way rule, an offset limit with no turn limit, passes a half-turned
  sherd that is long and thin enough). The Juglet look (ticket 07) caught the same rule
  erring the other way on purple. So the ranker's top 5 here holds 3 correct reassemblies
  (1, 2, 5), not the 4 the key reported; pick 1 is correct, so the conservator still gets one
  first.
- **The earlier inside-out rule (juglet-cause 14) flags exactly picks 3 and 4, sherd 2,** and
  nothing in 1, 2, 5: 2 of 2 caught, no false flags. Revision 3 reports it but does not gate
  on it (`--io-gate off`), because it misfires on narrow_bottle4 (all genuine), plate and a
  galli_pot chip. Gated here, picks 3 and 4 would drop out. One pot, five picks: a lead.
- Overlap on pick 5: the conservator saw more overlap with placement right; Revision 6
  (job 32804500, running) reads it.

