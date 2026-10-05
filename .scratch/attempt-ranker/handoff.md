# Handoff — attempt ranker (live file; overwrite, don't pile up)

- Now (2026-10-05): Revision 3 (calibration-fractura.md; judge near joins only, 12% of pot;
  a sherd touching no neighbour fails) running inside CPU holder 32274553 (16 CPU, ends
  ~20:37): recalibration -> `TORA/rank_u17/calib_32274553/`, then Juglet rerun ->
  `jug_v2_32274553/`. Logs `u17_calib_holder_32274553.log`, `jug_v2_holder_32274553.log`;
  exit codes in `holder_32274553.done`.
- Read first: unjudged_share of genuine on the 5 pots must be ~0, else Revision 3 fails.
  Look at plate/narrow_bottle4 pngs and the Juglet genuine before believing numbers.
- Next: commit the test pre-registration (narrow_bottle3, galli_pot; check for handles),
  rank them, report. Ticket 02 leftovers (L2 order into rank_attempts.py, small-move control,
  wall direction). Ticket 07 waits on the conservator.
- Holder rule: keep it while Spartan work continues; release only when none is foreseeable.
- Synthetic check: `scripts/l1_synthetic.py` (Spartan only).
