# Handoff — attempt ranker (live file; overwrite, don't pile up)

- Now (2026-10-05): Revision 3 calibration done (holder 32274553, COMPLETED 0:0). It
  stands: no genuine attempt on the 5 pots has an unjudged sherd. Cut-offs: Layer 1
  profile **0.873% of pot**, Layer 2 unfixable 2.31%. Juglet: both genuine kept, Layers
  1+2 rank them 1 and 13 (top 5 hit). Results logged in tickets 05 and 01.
- Renders `TORA/rank_u17/calib_32274553/{plate,narrow_bottle4}.png` described via the
  Spartan thread: same as Revision 2, every sherd on one outline (ticket 05). Conservator
  looked, 2026-10-05: "they look ok". The holder is released. Spartan requests from cloud threads go through
  the Connect Spartan workspace thread (via the coordinator).
- Next: commit the test pre-registration (narrow_bottle3, galli_pot; check for handles)
  with these cut-offs fixed, then rank them, report. Ticket 02 leftovers (L2 order into
  rank_attempts.py, small-move control still failing, wall direction). Ticket 07 waits on
  the conservator.
- Open faults, stated not fixed: inside-out flags 100% of genuine narrow_bottle4 and 55%
  of plate (not gating); Layer 1 keeps 68% of Juglet attempts, so ranking rests on Layer 2.
- Holder rule: keep it while Spartan work continues; release only when none is foreseeable.
- Synthetic check: `scripts/l1_synthetic.py` (Spartan only).
