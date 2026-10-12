# 11: The inside-out rule as a gate again, with a sherd-size guard

**What to build:** Revision 3 plus a gate: an attempt fails if the inside-out rule flags a
sherd inside a size band chosen on the calibration pots. See `../preregistration-io-guard.md`.

**Answers:** U17

**Working in:** tora `scripts/u17_io_guard.py`, `scripts/hpc/u17_relabel.slurm`

**Blocked by:** 10

**Status:** ready-for-agent

- [ ] Band chosen on the calibration pots by the fixed rule; per-sherd sizes and misfire
      rates printed
- [ ] Applied unchanged to GARF test pots and TORA's seen pots; Revision 3 beside it
- [ ] Every rejected genuine attempt off the calibration pots named (sherd, size)
- [ ] Result in U17 with its weight (seen pots only)

## Log
