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

**Status:** ready-for-human

Why this pot: held out of calibration, TORA's attempts (560), and the key's top 5 is not
all one class, so the look can disagree with it. GARF's narrow_bottle3 top 20 are all
genuine by the key, which a look could only confirm.

- [ ] Export (blind, no labels read) to Spartan `TORA/rank_u17/nb3_tora_top5/`, in the
      job of ticket 03's re-draw
- [ ] The visual-qa-helper stages the five descs; gates pass
- [ ] Pass 1, blind: the conservator's verdict per pick recorded before any label is read
- [ ] Unblind: key labels and per-sherd turn angles (`scripts/u17_top5_turns.py`) beside
      each verdict; every disagreement named as method, measurement or reference
- [ ] Every note gets a same-round agent reply

## Log

- 2026-10-12: five blind `single:` descs written (scale nominal: Fractura has no real
  size, longest side set to 100 mm). Export rides in `u17_redraw.slurm`.
