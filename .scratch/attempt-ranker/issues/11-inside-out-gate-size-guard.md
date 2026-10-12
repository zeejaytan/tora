# 11: The inside-out rule as a gate again, with a sherd-size guard

**What to build:** Revision 3 plus a gate: an attempt fails if the inside-out rule flags a
sherd inside a size band chosen on the calibration pots. See `../preregistration-io-guard.md`.

**Answers:** U17

**Working in:** tora `scripts/u17_io_guard.py`, `scripts/hpc/u17_relabel.slurm`

**Blocked by:** 10

**Status:** resolved (2026-10-12): fails its own rule on galli_pot (chips); not adopted

- [x] Band chosen on the calibration pots by the fixed rule; per-sherd sizes and misfire
      rates printed
- [x] Applied unchanged to GARF test pots and TORA's seen pots; Revision 3 beside it
- [x] Every rejected genuine attempt off the calibration pots named (sherd, size)
- [x] Result in U17 with its weight (seen pots only)

## Log
- 32806074 (same job as ticket 10). Calibration pots, sherd size / flag rate on genuine:
  narrow_bottle4 sherds 1 (47%) and 3 (28%) flagged on 100%; plate sherd 5 (1%) on 1%;
  every other calibration sherd 0%. **Band chosen: 0-25% of the pot.**
- Applied: **TORA narrow_bottle3 top 5 becomes all genuine** (removes the two flipped picks
  the conservator saw; 0 genuine lost, 9 near-misses removed). GARF narrow_bottle3 unchanged.
  GARF plate (calibration) removes 716 near-misses, 2 genuine. **galli_pot: rejects 274 of 305
  genuine attempts, keeps 1 of 1,400 overall**; best genuine falls to 2.
- **Named: measurement broken, on galli_pot.** Its sherd 7 is a 3% chip whose fitted sphere is
  noise, flagged on every genuine attempt (juglet-cause 14 saw this). The calibration pots
  have no such chip, so the rule could not learn a lower size limit, and lo came out 0.
  Fails the decision rule (at most 1% of genuine rejected). Not adopted; not retuned on
  these results. Revision 3 stands.
- What it shows: on mid-sized sherds the inside-out rule caught exactly the flips the eye
  saw on TORA narrow_bottle3, with no false flags. A version that also skips chips (lo set
  from a calibration set that holds one) is the next try; every pot here is now seen, so it
  would again be a design check.

